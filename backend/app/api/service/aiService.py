# encoding: UTF-8
"""
AI服务类 - 用于调用大模型生成测试用例、测试 Skill 和业务规则
"""
import copy
import hashlib
import json
import queue
import re
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from flask import current_app, has_app_context
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)
_CANCELLED_GENERATIONS = set()
_GENERATION_STATUS = {}
_GENERATION_STATUS_LOCK = threading.Lock()
_GENERATION_STATUS_KEEP_SECONDS = 60 * 60
_GENERATION_LOG_LIMIT = 50
_EMBEDDING_PROVIDER_UNAVAILABLE_UNTIL = {}
_EMBEDDING_PROVIDER_COOLDOWN_SECONDS = 5 * 60
_AI_REQUEST_SEMAPHORE = None
_AI_REQUEST_SEMAPHORE_SIZE = 0
_AI_REQUEST_SEMAPHORE_LOCK = threading.Lock()
_AI_REQUEST_THROTTLE_LOCK = threading.Lock()
_AI_LAST_REQUEST_TS = 0


def _now_ts():
    return time.time()


def _prune_generation_status_locked():
    now = _now_ts()
    expired_ids = [
        generation_id for generation_id, item in _GENERATION_STATUS.items()
        if item.get('status') in ('done', 'cancelled', 'error') and now - item.get('updatedAt', now) > _GENERATION_STATUS_KEEP_SECONDS
    ]
    for generation_id in expired_ids:
        _GENERATION_STATUS.pop(generation_id, None)


def init_generation_status(generation_id, project_id=None, document_ids=None):
    if not generation_id:
        return
    now = _now_ts()
    with _GENERATION_STATUS_LOCK:
        _prune_generation_status_locked()
        _GENERATION_STATUS[str(generation_id)] = {
            'generationId': str(generation_id),
            'projectId': str(project_id) if project_id is not None else '',
            'documentIds': document_ids or [],
            'status': 'running',
            'createdAt': now,
            'updatedAt': now,
            'chunkIndex': 0,
            'totalChunks': 0,
            'chunkTitle': '',
            'agentCount': 0,
            'totalCasesSoFar': 0,
            'totalImported': 0,
            'totalSkipped': 0,
            'logs': [],
            'errors': [],
            'failedChunks': []
        }


def update_generation_status(generation_id, event_type=None, data=None):
    if not generation_id:
        return
    data = data or {}
    now = _now_ts()
    with _GENERATION_STATUS_LOCK:
        status = _GENERATION_STATUS.get(str(generation_id))
        if not status:
            status = {
                'generationId': str(generation_id),
                'status': 'running',
                'createdAt': now,
                'logs': [],
                'errors': [],
                'failedChunks': []
            }
            _GENERATION_STATUS[str(generation_id)] = status
        status['updatedAt'] = now
        if event_type in ('start', 'preparing', 'prepared', 'agent_plan', 'agent_start', 'chunk_start', 'heartbeat', 'ai_retry', 'agent_log', 'progress'):
            if status.get('status') != 'stopping':
                status['status'] = 'running'
        if event_type == 'agent_plan':
            status['totalChunks'] = data.get('totalChunks', status.get('totalChunks', 0))
            status['agentCount'] = data.get('agentCount', status.get('agentCount', 0))
            status['chunkTitle'] = data.get('message') or status.get('chunkTitle', '')
        if event_type in ('agent_start', 'chunk_start', 'heartbeat', 'ai_retry', 'progress'):
            status['chunkIndex'] = data.get('chunkIndex') or status.get('chunkIndex', 0)
            status['totalChunks'] = data.get('totalChunks') or status.get('totalChunks', 0)
            status['chunkTitle'] = data.get('chunkTitle') or status.get('chunkTitle', '')
            status['agentName'] = data.get('agentName') or status.get('agentName', '')
        if event_type == 'progress':
            status['casesCount'] = data.get('casesCount', status.get('casesCount', 0))
            status['totalCasesSoFar'] = data.get('totalCasesSoFar', status.get('totalCasesSoFar', 0))
            status['totalImported'] = status.get('totalImported', 0) + int(data.get('importedCount') or 0)
            status['totalSkipped'] = status.get('totalSkipped', 0) + int(data.get('skippedCount') or 0)
            if data.get('importError'):
                status.setdefault('errors', []).append({'chunkIndex': data.get('chunkIndex'), 'error': data.get('importError')})
        if event_type == 'chunk_error':
            status['status'] = 'running'
            err = {'chunkIndex': data.get('chunkIndex'), 'chunkTitle': data.get('chunkTitle', ''), 'error': data.get('error', '')}
            status.setdefault('errors', []).append(err)
            status.setdefault('failedChunks', []).append(err)
        if event_type in ('agent_log', 'ai_retry'):
            logs = status.setdefault('logs', [])
            logs.append({
                'time': now,
                'level': data.get('level') or ('warning' if event_type == 'ai_retry' else 'info'),
                'agentName': data.get('agentName', ''),
                'message': data.get('message') or data.get('chunkTitle') or 'agent 状态更新'
            })
            status['logs'] = logs[-_GENERATION_LOG_LIMIT:]
        if event_type == 'done':
            status['status'] = 'done'
            status['totalCasesSoFar'] = data.get('totalCases', status.get('totalCasesSoFar', 0))
            status['totalImported'] = data.get('totalImported', data.get('importedCount', status.get('totalImported', 0)))
            status['totalSkipped'] = data.get('totalSkipped', data.get('skippedCount', status.get('totalSkipped', 0)))
            status['failedChunks'] = data.get('failedChunks', status.get('failedChunks', []))
        if event_type == 'cancelled':
            status['status'] = 'cancelled'
            status['totalCasesSoFar'] = data.get('totalCases', status.get('totalCasesSoFar', 0))
            status['totalImported'] = data.get('totalImported', data.get('importedCount', status.get('totalImported', 0)))
            status['totalSkipped'] = data.get('totalSkipped', data.get('skippedCount', status.get('totalSkipped', 0)))
        if event_type == 'error':
            status['status'] = 'error'
            if data.get('failedChunks'):
                status['failedChunks'] = data.get('failedChunks')
            status.setdefault('errors', []).append({'error': data.get('message', '未知错误')})


def get_generation_status(generation_id=None, project_id=None):
    with _GENERATION_STATUS_LOCK:
        _prune_generation_status_locked()
        if generation_id:
            item = _GENERATION_STATUS.get(str(generation_id))
            return copy.deepcopy(item) if item else None
        candidates = list(_GENERATION_STATUS.values())
        if project_id is not None and str(project_id):
            candidates = [item for item in candidates if str(item.get('projectId', '')) == str(project_id)]
        running = [item for item in candidates if item.get('status') in ('running', 'stopping')]
        if not running:
            return None
        return copy.deepcopy(max(running, key=lambda item: item.get('updatedAt', 0)))


def cancel_generation(generation_id):
    if generation_id:
        _CANCELLED_GENERATIONS.add(str(generation_id))
        with _GENERATION_STATUS_LOCK:
            status = _GENERATION_STATUS.get(str(generation_id))
            if status:
                status['status'] = 'stopping'
                status['updatedAt'] = _now_ts()
                logs = status.setdefault('logs', [])
                logs.append({
                    'time': _now_ts(),
                    'level': 'warning',
                    'agentName': '',
                    'message': '已请求停止生成，等待后台任务退出'
                })
                status['logs'] = logs[-_GENERATION_LOG_LIMIT:]


def is_generation_cancelled(generation_id):
    return bool(generation_id and str(generation_id) in _CANCELLED_GENERATIONS)


def clear_cancel_generation(generation_id):
    if generation_id:
        _CANCELLED_GENERATIONS.discard(str(generation_id))


def shutdown_executor(executor):
    try:
        executor.shutdown(wait=False, cancel_futures=True)
    except TypeError:
        executor.shutdown(wait=False)


class AIService:
    """AI服务类"""

    @staticmethod
    def generate_test_cases(document_content, template=None):
        try:
            from openai import OpenAI
            from config.ai_config import AIConfig
            import httpx

            api_key = AIConfig.get_api_key()
            api_base = AIConfig.get_api_base()
            model = AIConfig.get_model()
            provider = AIConfig.MODEL_PROVIDER
            key_source = AIConfig.get_api_key_source()
            if not api_key or api_key == '请替换为你的Meteor API Key':
                return [], '未配置API密钥，请在.env中配置METEOR_API_KEY'

            is_plan_key = '/plan/' in api_base
            request_base = AIService._normalize_plan_api_base(api_base) if is_plan_key else AIService._normalize_api_base(api_base)
            logger.info(f'AI配置: provider={provider}, base={request_base}, model={model}, key_source={key_source}, key_prefix={api_key[:8]}, plan_key={is_plan_key}')

            skill_content = AIService._load_skill_content()
            chunks = AIService._split_test_case_generation_content(document_content)
            # 文档越长 chunk 越多，按 chunk 数量比例放大单次 read_timeout，
            # 避免长文档某段超过默认 120s 触发 ReadTimeout。
            chunk_count = max(1, len(chunks))
            per_chunk_read_timeout = max(AIConfig.READ_TIMEOUT, 60 * chunk_count)
            timeout = httpx.Timeout(
                connect=AIConfig.CONNECT_TIMEOUT,
                read=per_chunk_read_timeout,
                write=per_chunk_read_timeout,
                pool=AIConfig.CONNECT_TIMEOUT,
            )
            all_cases = []
            for chunk_index, chunk in enumerate(chunks, 1):
                prompt = AIService._build_prompt(chunk['content'], template, skill_content, chunk_index, len(chunks), chunk['title'])
                result = AIService._request_model(OpenAI, AIConfig, api_key, request_base, model, is_plan_key, prompt, timeout, httpx)
                logger.info(f'AI第{chunk_index}/{len(chunks)}段响应长度: {len(result) if result else 0}')
                try:
                    parsed_result = json.loads(AIService._extract_json_text(result))
                    chunk_cases = AIService._normalize_cases(parsed_result, template, chunk['title'])
                    logger.info(f'AI第{chunk_index}/{len(chunks)}段解析出{len(chunk_cases)}条用例')
                    all_cases.extend(chunk_cases)
                except json.JSONDecodeError:
                    logger.error(f'AI第{chunk_index}段JSON解析失败, 原始响应前500字符: {result[:500]}')
                    return [], f'第{chunk_index}段解析结果失败: {result[:200]}'
            logger.info(f'AI生成完成, 共{len(all_cases)}条用例(去重前)')
            deduped = AIService._deduplicate_cases(all_cases)
            logger.info(f'AI生成完成, 去重后{len(deduped)}条用例')
            return deduped, ''
        except Exception as e:
            logger.error(f'AI生成测试用例失败: {str(e)}')
            logger.error(traceback.format_exc())
            return [], f'AI生成失败: {str(e)}'

    @staticmethod
    def generate_test_cases_streaming(document_content, template=None, session=None, session_factory=None, document_id=None, user_id=None, generation_id=None, document_ids=None, resume_mode='resume'):
        """
        流式生成测试用例。主管线程按 Skill/文档分段拆任务，多个子 agent 并发生成；任一子 agent 完成后立即入库并返回进度。
        """
        try:
            from openai import OpenAI
            from config.ai_config import AIConfig
            from app.api.service.documentSourceService import DocumentSourceService
            import httpx

            api_key = AIConfig.get_api_key()
            api_base = AIConfig.get_api_base()
            model = AIConfig.get_model()
            provider = AIConfig.MODEL_PROVIDER
            key_source = AIConfig.get_api_key_source()
            if not api_key or api_key == '请替换为你的Meteor API Key':
                yield {"type": "error", "message": "未配置API密钥，请在.env中配置METEOR_API_KEY"}
                return

            is_plan_key = '/plan/' in api_base
            request_base = AIService._normalize_plan_api_base(api_base) if is_plan_key else AIService._normalize_api_base(api_base)
            logger.info(f'AI配置: provider={provider}, base={request_base}, model={model}, key_source={key_source}, key_prefix={api_key[:8]}, plan_key={is_plan_key}')

            skill_content = AIService._load_skill_content()
            chunks = AIService._split_test_case_generation_content(document_content)
            tasks = AIService._build_generation_agent_tasks(chunks, template)
            if not tasks:
                yield {"type": "error", "message": "没有可生成的测试点任务"}
                return

            project_id = int((template or {}).get('project_id') or 0)
            document_id_list = document_ids or ([document_id] if document_id else [])
            checkpoint_scope = AIService._build_generation_checkpoint_scope(project_id, document_id_list, template)
            resume_mode = (resume_mode or 'resume').lower()
            skipped_resume_tasks = []
            if checkpoint_scope and session_factory:
                if resume_mode == 'restart':
                    AIService._reset_generation_checkpoints(session_factory, checkpoint_scope)
                else:
                    completed_keys = AIService._load_completed_generation_task_keys(session_factory, checkpoint_scope)
                    if completed_keys:
                        pending_tasks = []
                        for task in tasks:
                            if task.get('task_key') in completed_keys:
                                skipped_resume_tasks.append(task)
                            else:
                                pending_tasks.append(task)
                        tasks = pending_tasks
            original_task_count = len(tasks) + len(skipped_resume_tasks)
            if skipped_resume_tasks:
                yield {
                    "type": "agent_log",
                    "level": "info",
                    "message": f"断点续跑已跳过{len(skipped_resume_tasks)}个已完成生成点，从剩余{len(tasks)}个生成点继续"
                }
            if not tasks:
                yield {
                    "type": "done",
                    "cases": [],
                    "totalCases": 0,
                    "totalImported": 0,
                    "totalSkipped": 0,
                    "failedChunks": [],
                    "chunkImportResults": [],
                    "resumeSkippedCount": len(skipped_resume_tasks),
                    "message": "所有生成点已完成，无需继续生成"
                }
                return
            for run_index, task in enumerate(tasks, 1):
                task['runIndex'] = run_index

            task_count = len(tasks)
            per_chunk_read_timeout = max(AIConfig.READ_TIMEOUT, 120 * max(1, len(chunks)))
            timeout = httpx.Timeout(
                connect=AIConfig.CONNECT_TIMEOUT,
                read=per_chunk_read_timeout,
                write=per_chunk_read_timeout,
                pool=AIConfig.CONNECT_TIMEOUT,
            )
            configured_agent_count = int(getattr(AIConfig, 'CASE_GENERATION_AGENT_CONCURRENCY', 0) or 0)
            max_agent_workers = max(1, int(getattr(AIConfig, 'CASE_GENERATION_AGENT_MAX_WORKERS', 64) or 64))
            if configured_agent_count > 0:
                max_workers = max(1, min(configured_agent_count, task_count))
            else:
                max_workers = max(1, min(task_count, max_agent_workers))
            event_queue = queue.Queue()
            running_tasks = {}
            running_tasks_lock = threading.Lock()
            all_cases = []
            failed_chunks = []
            chunk_import_results = []
            completed_tasks = 0
            total_imported = 0
            total_skipped = 0

            request_concurrency = max(1, int(getattr(AIConfig, 'REQUEST_CONCURRENCY', 1) or 1))
            logger.info(f'AI并发生成计划: task_count={task_count}, agent_count={max_workers}, request_concurrency={request_concurrency}, generation_id={generation_id}, resume_mode={resume_mode}, skipped={len(skipped_resume_tasks)}')
            yield {
                "type": "agent_plan",
                "totalChunks": task_count,
                "originalTotalChunks": original_task_count,
                "resumeSkippedCount": len(skipped_resume_tasks),
                "agentCount": max_workers,
                "message": f"已拆分为{original_task_count}个测试点任务，跳过已完成{len(skipped_resume_tasks)}个，剩余{task_count}个测试点按subagent并发执行，启动{max_workers}个agent"
            }
            yield {
                "type": "agent_log",
                "level": "info",
                "message": f"主管agent已拆分{task_count}个测试点任务，按一个测试点一个subagent启动{max_workers}个agent；模型请求并发上限{request_concurrency}"
            }

            def run_agent(task):
                if is_generation_cancelled(generation_id):
                    event_queue.put({"type": "agent_done", "task": task, "cancelled": True})
                    return
                task_id = task['index']
                run_index = task.get('runIndex') or task_id
                task_title = task['title']
                with running_tasks_lock:
                    running_tasks[run_index] = {
                        "chunkIndex": run_index,
                        "totalChunks": task_count,
                        "chunkTitle": task_title,
                        "agentName": task['agent_name'],
                        "startedAt": time.time(),
                        "heartbeatCount": 0
                    }
                if checkpoint_scope and session_factory:
                    AIService._upsert_generation_checkpoint(
                        session_factory, checkpoint_scope, task, 'running', generation_id=generation_id, user_id=user_id
                    )
                logger.info(f"{task['agent_name']}开始执行: task_id={task_id}, title={task_title}")
                event_queue.put({
                    "type": "agent_start",
                    "chunkIndex": run_index,
                    "totalChunks": task_count,
                    "chunkTitle": task_title,
                    "agentName": task['agent_name']
                })
                event_queue.put({
                    "type": "agent_log",
                    "level": "info",
                    "chunkIndex": run_index,
                    "totalChunks": task_count,
                    "chunkTitle": task_title,
                    "agentName": task['agent_name'],
                    "message": f"开始生成测试点[{run_index}/{task_count}]：{task_title}"
                })
                event_queue.put({
                    "type": "chunk_start",
                    "chunkIndex": run_index,
                    "totalChunks": task_count,
                    "chunkTitle": task_title,
                    "totalCasesSoFar": 0
                })
                try:
                    prompt = AIService._build_prompt(
                        task['content'], task['template'], skill_content, task_id, task_count, task_title
                    )
                    result = AIService._request_model_until_success(
                        OpenAI, AIConfig, api_key, request_base, model, is_plan_key, prompt, timeout, httpx,
                        event_queue, generation_id, run_index, task_count, task_title, task['agent_name']
                    )
                    if is_generation_cancelled(generation_id):
                        with running_tasks_lock:
                            running_tasks.pop(run_index, None)
                        event_queue.put({"type": "agent_done", "task": task, "cancelled": True})
                        return
                    logger.info(f"{task['agent_name']}模型返回完成: task_id={task_id}, response_length={len(result) if result else 0}")
                    event_queue.put({
                        "type": "agent_log",
                        "level": "info",
                        "chunkIndex": run_index,
                        "totalChunks": task_count,
                        "chunkTitle": task_title,
                        "agentName": task['agent_name'],
                        "message": f"{task['agent_name']}模型返回完成，开始解析结果"
                    })
                    parsed_result = json.loads(AIService._extract_json_text(result))
                    chunk_cases = AIService._normalize_cases(parsed_result, task['template'], task_title)
                    logger.info(f"{task['agent_name']}解析完成: task_id={task_id}, cases={len(chunk_cases)}")
                    event_queue.put({
                        "type": "agent_log",
                        "level": "info",
                        "chunkIndex": run_index,
                        "totalChunks": task_count,
                        "chunkTitle": task_title,
                        "agentName": task['agent_name'],
                        "message": f"测试点[{run_index}/{task_count}] {task_title}：模型生成{len(chunk_cases)}条用例，开始入库"
                    })
                    chunk_saved = 0
                    chunk_skipped = 0
                    chunk_save_error = ''
                    if (session or session_factory) and document_id and user_id and chunk_cases:
                        chunk_session_owner = None
                        chunk_session = session
                        try:
                            if session_factory:
                                chunk_session_owner = session_factory()
                                chunk_session = chunk_session_owner
                            import_result = DocumentSourceService.import_cases(
                                chunk_session, document_id, chunk_cases, user_id, auto_create_module=True, return_detail=True
                            )
                            chunk_saved = int(import_result.get('successCount') or 0)
                            chunk_skipped = int(import_result.get('skippedCount') or 0)
                            chunk_save_error = import_result.get('error') or ''
                            if not chunk_save_error:
                                chunk_session.commit()
                            else:
                                chunk_session.rollback()
                        except Exception as save_err:
                            chunk_save_error = str(save_err)
                            logger.error(f'agent任务{task_id}入库失败: {str(save_err)}')
                            try:
                                if chunk_session:
                                    chunk_session.rollback()
                            except Exception as rollback_err:
                                logger.warning(f'agent任务{task_id}入库回滚失败: {str(rollback_err)}')
                        finally:
                            if chunk_session_owner:
                                chunk_session_owner.close()
                    log_level = "warning" if chunk_save_error else "info"
                    if chunk_save_error:
                        log_message = f"{task['agent_name']}入库失败：{chunk_save_error}"
                    else:
                        skip_text = f"，跳过重复{chunk_skipped}条" if chunk_skipped else ""
                        log_message = f"测试点[{run_index}/{task_count}] {task_title}：生成{len(chunk_cases)}条用例，已入库{chunk_saved}条{skip_text}"
                    if chunk_save_error:
                        if checkpoint_scope and session_factory:
                            AIService._upsert_generation_checkpoint(
                                session_factory, checkpoint_scope, task, 'failed', generation_id=generation_id,
                                user_id=user_id, imported_count=chunk_saved, skipped_count=chunk_skipped, error_message=chunk_save_error
                            )
                        logger.warning(log_message)
                    else:
                        if checkpoint_scope and session_factory:
                            AIService._upsert_generation_checkpoint(
                                session_factory, checkpoint_scope, task, 'success', generation_id=generation_id,
                                user_id=user_id, imported_count=chunk_saved, skipped_count=chunk_skipped, error_message=''
                            )
                        logger.info(log_message)
                    event_queue.put({
                        "type": "agent_log",
                        "level": log_level,
                        "chunkIndex": run_index,
                        "totalChunks": task_count,
                        "chunkTitle": task_title,
                        "agentName": task['agent_name'],
                        "message": log_message
                    })
                    with running_tasks_lock:
                        running_tasks.pop(run_index, None)
                    event_queue.put({
                        "type": "agent_done",
                        "task": task,
                        "cases": chunk_cases,
                        "importedCount": chunk_saved,
                        "skippedCount": chunk_skipped,
                        "importError": chunk_save_error
                    })
                except json.JSONDecodeError:
                    err_msg = f"{task_title} JSON解析失败"
                    logger.error(f"{task['agent_name']}执行失败: {err_msg}")
                    event_queue.put({
                        "type": "agent_log",
                        "level": "error",
                        "chunkIndex": run_index,
                        "totalChunks": task_count,
                        "chunkTitle": task_title,
                        "agentName": task['agent_name'],
                        "message": err_msg
                    })
                    if checkpoint_scope and session_factory:
                        AIService._upsert_generation_checkpoint(
                            session_factory, checkpoint_scope, task, 'failed', generation_id=generation_id,
                            user_id=user_id, error_message=err_msg
                        )
                    with running_tasks_lock:
                        running_tasks.pop(run_index, None)
                    event_queue.put({"type": "agent_error", "task": task, "error": err_msg})
                except Exception as e:
                    err_msg = str(e)
                    logger.error(f"{task['agent_name']}执行失败: {err_msg}")
                    event_queue.put({
                        "type": "agent_log",
                        "level": "error",
                        "chunkIndex": run_index,
                        "totalChunks": task_count,
                        "chunkTitle": task_title,
                        "agentName": task['agent_name'],
                        "message": f"{task['agent_name']}执行失败：{err_msg}"
                    })
                    if checkpoint_scope and session_factory:
                        AIService._upsert_generation_checkpoint(
                            session_factory, checkpoint_scope, task, 'failed', generation_id=generation_id,
                            user_id=user_id, error_message=err_msg
                        )
                    with running_tasks_lock:
                        running_tasks.pop(run_index, None)
                    event_queue.put({"type": "agent_error", "task": task, "error": err_msg})

            executor = ThreadPoolExecutor(max_workers=max_workers)
            try:
                for task in tasks:
                    executor.submit(run_agent, task)
                while completed_tasks < task_count:
                    if is_generation_cancelled(generation_id):
                        shutdown_executor(executor)
                        yield {
                            "type": "cancelled",
                            "totalCases": len(all_cases),
                            "totalImported": total_imported,
                            "failedChunks": failed_chunks,
                            "chunkImportResults": chunk_import_results
                        }
                        return
                    try:
                        event = event_queue.get(timeout=10)
                    except queue.Empty:
                        with running_tasks_lock:
                            running_snapshot = list(running_tasks.values())
                            for item in running_snapshot:
                                item["heartbeatCount"] = int(item.get("heartbeatCount") or 0) + 1
                        if running_snapshot:
                            item = running_snapshot[(completed_tasks + len(running_snapshot)) % len(running_snapshot)]
                            elapsed = int(time.time() - float(item.get("startedAt") or time.time()))
                            yield {
                                "type": "heartbeat",
                                "chunkIndex": item.get("chunkIndex") or completed_tasks + 1,
                                "totalChunks": item.get("totalChunks") or task_count,
                                "chunkTitle": item.get("chunkTitle") or "并发agent仍在生成测试用例",
                                "agentName": item.get("agentName") or "",
                                "elapsedSeconds": elapsed,
                                "message": f"{item.get('agentName') or 'agent'}仍在生成测试点：{item.get('chunkTitle') or ''}，已等待{elapsed}秒"
                            }
                        else:
                            yield {
                                "type": "heartbeat",
                                "chunkIndex": completed_tasks + 1,
                                "totalChunks": task_count,
                                "chunkTitle": "等待agent返回结果",
                                "elapsedSeconds": 0,
                                "message": "等待agent返回结果"
                            }
                        continue

                    event_type = event.get('type')
                    if event_type in ('agent_start', 'agent_log', 'chunk_start', 'heartbeat', 'ai_retry'):
                        yield event
                    elif event_type == 'agent_done':
                        completed_tasks += 1
                        if event.get('cancelled'):
                            continue
                        task = event['task']
                        chunk_cases = event.get('cases') or []
                        imported_count = event.get('importedCount', 0)
                        import_error = event.get('importError', '')
                        skipped_count = int(event.get('skippedCount') or 0)
                        all_cases.extend(chunk_cases)
                        total_imported += imported_count
                        total_skipped += skipped_count
                        chunk_import_results.append({
                            "chunkIndex": task.get('runIndex') or completed_tasks,
                            "taskIndex": task['index'],
                            "importedCount": imported_count,
                            "skippedCount": skipped_count,
                            "error": import_error,
                            "agentName": task['agent_name']
                        })
                        logger.info(f"主管agent收到结果: agent={task['agent_name']}, completed={completed_tasks}/{task_count}, cases={len(chunk_cases)}, imported={imported_count}, skipped={skipped_count}, import_error={import_error}")
                        yield {
                            "type": "progress",
                            "chunkIndex": completed_tasks,
                            "totalChunks": task_count,
                            "chunkTitle": task['title'],
                            "agentName": task['agent_name'],
                            "cases": chunk_cases,
                            "casesCount": len(chunk_cases),
                            "totalCasesSoFar": len(all_cases),
                            "importedCount": imported_count,
                            "skippedCount": skipped_count,
                            "totalSkipped": total_skipped,
                            "importError": import_error
                        }
                    elif event_type == 'agent_error':
                        completed_tasks += 1
                        task = event['task']
                        err_msg = event.get('error') or '未知错误'
                        failed_chunks.append({
                            "chunkIndex": task.get('runIndex') or completed_tasks,
                            "taskIndex": task['index'],
                            "chunkTitle": task['title'],
                            "agentName": task['agent_name'],
                            "error": err_msg
                        })
                        yield {
                            "type": "chunk_error",
                            "chunkIndex": completed_tasks,
                            "totalChunks": task_count,
                            "chunkTitle": task['title'],
                            "error": err_msg
                        }
            finally:
                shutdown_executor(executor)

            logger.info(f'AI并发生成完成, 共{len(all_cases)}条用例, 已入库{total_imported}条, 跳过重复{total_skipped}条, {len(failed_chunks)}个任务失败')
            if failed_chunks and not all_cases and total_imported == 0:
                error_summary = '; '.join(item.get('error') or '未知错误' for item in failed_chunks[:3])
                yield {"type": "error", "message": f"AI生成失败：{error_summary}", "failedChunks": failed_chunks}
                return
            yield {
                "type": "done",
                "cases": all_cases,
                "totalCases": len(all_cases),
                "totalImported": total_imported,
                "totalSkipped": total_skipped,
                "failedChunks": failed_chunks,
                "chunkImportResults": chunk_import_results
            }
        except Exception as e:
            logger.error(f'AI流式生成测试用例失败: {str(e)}')
            logger.error(traceback.format_exc())
            yield {"type": "error", "message": f"AI生成失败: {str(e)}"}

    @staticmethod
    def _build_generation_agent_tasks(chunks, template):
        template = template or {}
        skill_contexts = template.get('skill_contexts') or []
        tasks = []
        task_index = 1
        for chunk_index, chunk in enumerate(chunks, 1):
            related_skills = skill_contexts or [None]
            for skill in related_skills:
                task_template = copy.deepcopy(template)
                if skill:
                    task_template['skill_contexts'] = [skill]
                    skill_name = skill.get('name') or f"Skill{skill.get('id')}"
                    agent_name = f"agent-{task_index}-{skill_name}"
                    task_title = f"{chunk.get('title') or '文档内容'} / {skill_name}"
                    task_content = f"测试点拆分依据：请只围绕 Skill「{skill_name}」覆盖当前文档分段。\n\n{chunk.get('content') or ''}"
                else:
                    agent_name = f"agent-{task_index}"
                    task_title = chunk.get('title') or '文档内容'
                    task_content = chunk.get('content') or ''
                task_key = AIService._make_generation_task_key(chunk_index, task_title, task_content, task_template, skill)
                tasks.append({
                    'index': task_index,
                    'chunkIndex': chunk_index,
                    'title': task_title,
                    'content': task_content,
                    'template': task_template,
                    'agent_name': agent_name,
                    'task_key': task_key,
                    'skill_id': skill.get('id') if skill else None,
                    'skill_name': skill.get('name') if skill else ''
                })
                task_index += 1
        return tasks

    @staticmethod
    def _make_generation_task_key(chunk_index, task_title, task_content, task_template, skill=None):
        template = task_template or {}
        payload = {
            'chunkIndex': chunk_index,
            'title': task_title or '',
            'contentHash': hashlib.sha256((task_content or '').encode('utf-8')).hexdigest(),
            'priority': template.get('priority'),
            'caseType': template.get('case_type'),
            'tags': sorted([str(item) for item in (template.get('tags') or [])]),
            'ruleIds': sorted([str(item) for item in (template.get('rule_ids') or [])]),
            'skillId': str((skill or {}).get('id') or ''),
            'skillName': (skill or {}).get('name') or ''
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    @staticmethod
    def _build_generation_checkpoint_scope(project_id, document_ids, template):
        if not project_id:
            return None
        normalized_doc_ids = sorted([int(item) for item in (document_ids or []) if str(item).strip()])
        if not normalized_doc_ids:
            return None
        template = template or {}
        template_payload = {
            'priority': template.get('priority'),
            'caseType': template.get('case_type'),
            'tags': sorted([str(item) for item in (template.get('tags') or [])]),
            'skillIds': sorted([str(item) for item in (template.get('skill_ids') or [])]),
            'ruleIds': sorted([str(item) for item in (template.get('rule_ids') or [])])
        }
        doc_raw = ','.join(str(item) for item in normalized_doc_ids)
        template_raw = json.dumps(template_payload, ensure_ascii=False, sort_keys=True)
        return {
            'project_id': int(project_id),
            'document_ids': normalized_doc_ids,
            'document_scope_key': hashlib.sha256(doc_raw.encode('utf-8')).hexdigest(),
            'template_key': hashlib.sha256(template_raw.encode('utf-8')).hexdigest()
        }

    @staticmethod
    def _ensure_generation_checkpoint_table(session):
        session.execute("""
            CREATE TABLE IF NOT EXISTS case_generation_checkpoint (
                id BIGSERIAL PRIMARY KEY,
                project_id BIGINT NOT NULL,
                document_scope_key VARCHAR(128) NOT NULL,
                document_ids BIGINT[] DEFAULT '{}'::BIGINT[],
                template_key VARCHAR(128) NOT NULL,
                task_key VARCHAR(128) NOT NULL,
                task_index INTEGER NOT NULL,
                chunk_index INTEGER DEFAULT 0,
                chunk_title VARCHAR(512),
                agent_name VARCHAR(255),
                skill_id BIGINT,
                skill_name VARCHAR(255),
                status VARCHAR(32) DEFAULT 'pending',
                imported_count INTEGER DEFAULT 0,
                skipped_count INTEGER DEFAULT 0,
                error_message TEXT,
                generation_id VARCHAR(64),
                created_by BIGINT,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        session.execute("""
            CREATE INDEX IF NOT EXISTS idx_case_generation_checkpoint_scope
            ON case_generation_checkpoint(project_id, document_scope_key, template_key)
        """)
        session.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uk_case_generation_checkpoint_task
            ON case_generation_checkpoint(project_id, document_scope_key, template_key, task_key)
        """)
        session.commit()

    @staticmethod
    def _load_completed_generation_task_keys(session_factory, scope):
        from app.api.model.caseModel import CaseGenerationCheckpoint

        session = session_factory()
        try:
            rows = session.query(CaseGenerationCheckpoint.task_key).filter(
                CaseGenerationCheckpoint.project_id == scope['project_id'],
                CaseGenerationCheckpoint.document_scope_key == scope['document_scope_key'],
                CaseGenerationCheckpoint.template_key == scope['template_key'],
                CaseGenerationCheckpoint.status == 'success'
            ).all()
            return {row[0] for row in rows}
        finally:
            session.close()

    @staticmethod
    def _reset_generation_checkpoints(session_factory, scope):
        from app.api.model.caseModel import CaseGenerationCheckpoint

        session = session_factory()
        try:
            AIService._ensure_generation_checkpoint_table(session)
            session.query(CaseGenerationCheckpoint).filter(
                CaseGenerationCheckpoint.project_id == scope['project_id'],
                CaseGenerationCheckpoint.document_scope_key == scope['document_scope_key'],
                CaseGenerationCheckpoint.template_key == scope['template_key']
            ).delete(synchronize_session=False)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def _upsert_generation_checkpoint(session_factory, scope, task, status, generation_id=None, user_id=None,
                                      imported_count=0, skipped_count=0, error_message=''):
        from app.api.model.caseModel import CaseGenerationCheckpoint

        session = session_factory()
        try:
            AIService._ensure_generation_checkpoint_table(session)
            row = session.query(CaseGenerationCheckpoint).filter(
                CaseGenerationCheckpoint.project_id == scope['project_id'],
                CaseGenerationCheckpoint.document_scope_key == scope['document_scope_key'],
                CaseGenerationCheckpoint.template_key == scope['template_key'],
                CaseGenerationCheckpoint.task_key == task.get('task_key')
            ).first()
            data = {
                'project_id': scope['project_id'],
                'document_scope_key': scope['document_scope_key'],
                'document_ids': scope['document_ids'],
                'template_key': scope['template_key'],
                'task_key': task.get('task_key'),
                'task_index': int(task.get('index') or 0),
                'chunk_index': int(task.get('chunkIndex') or 0),
                'chunk_title': task.get('title') or '',
                'agent_name': task.get('agent_name') or '',
                'skill_id': task.get('skill_id'),
                'skill_name': task.get('skill_name') or '',
                'status': status,
                'imported_count': int(imported_count or 0),
                'skipped_count': int(skipped_count or 0),
                'error_message': error_message or '',
                'generation_id': str(generation_id or ''),
                'created_by': user_id
            }
            if row:
                for key, value in data.items():
                    setattr(row, key, value)
            else:
                session.add(CaseGenerationCheckpoint(**data))
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def _request_model_until_success(OpenAI, AIConfig, api_key, request_base, model, is_plan_key, prompt, timeout, httpx,
                                     event_queue, generation_id, chunk_index, total_chunks, chunk_title, agent_name=''):
        gateway_retry_count = 0
        gateway_retry_delay = max(1.0, getattr(AIConfig, 'GATEWAY_RETRY_DELAY', 30.0))
        gateway_max_retries = max(0, getattr(AIConfig, 'GATEWAY_MAX_RETRIES', 3))
        agent_timeout = max(60.0, float(getattr(AIConfig, 'CASE_GENERATION_AGENT_TIMEOUT', 600) or 600))
        idle_timeout = max(30.0, float(getattr(AIConfig, 'CASE_GENERATION_AGENT_IDLE_TIMEOUT', 90) or 90))
        started_at = time.time()
        while True:
            request_queue = queue.Queue(maxsize=1)
            attempt_started_at = time.time()

            def request_chunk():
                try:
                    request_queue.put((True, AIService._request_model(
                        OpenAI, AIConfig, api_key, request_base, model, is_plan_key, prompt, timeout, httpx,
                        max_retries=1
                    )))
                except Exception as request_err:
                    request_queue.put((False, request_err))

            threading.Thread(target=request_chunk, daemon=True).start()
            heartbeat_count = 0
            while True:
                if is_generation_cancelled(generation_id):
                    raise RuntimeError('生成已取消')
                elapsed_seconds = time.time() - started_at
                attempt_elapsed = time.time() - attempt_started_at
                if elapsed_seconds >= agent_timeout:
                    raise RuntimeError(f'AI生成分段超时，已等待{int(elapsed_seconds)}秒，请稍后重试或减少文档/Skill数量')
                if attempt_elapsed >= idle_timeout:
                    retry_available = gateway_retry_count < gateway_max_retries
                    if retry_available:
                        gateway_retry_count += 1
                        retry_agent_name = f"{agent_name or 'agent'}-retry{gateway_retry_count}"
                        retry_message = f"测试点[{chunk_index}/{total_chunks}] {chunk_title}：AI agent超过{int(idle_timeout)}秒无响应，切换为{retry_agent_name}重新执行（{gateway_retry_count}/{gateway_max_retries}）"
                        logger.warning(retry_message)
                        event_queue.put({
                            "type": "ai_retry",
                            "level": "warning",
                            "chunkIndex": chunk_index,
                            "totalChunks": total_chunks,
                            "chunkTitle": chunk_title,
                            "agentName": retry_agent_name,
                            "retryCount": gateway_retry_count,
                            "retryDelay": 0,
                            "message": retry_message
                        })
                        event_queue.put({
                            "type": "agent_log",
                            "level": "info",
                            "chunkIndex": chunk_index,
                            "totalChunks": total_chunks,
                            "chunkTitle": chunk_title,
                            "agentName": retry_agent_name,
                            "message": f"{retry_agent_name}开始重新生成测试点：{chunk_title}"
                        })
                        break
                    raise RuntimeError(f'AI agent无响应超时，测试点[{chunk_index}/{total_chunks}]已等待{int(attempt_elapsed)}秒，重试{gateway_max_retries}次后仍未返回')
                try:
                    request_ok, request_result = request_queue.get(timeout=10)
                    if request_ok:
                        return request_result
                    err_str = str(request_result)
                    gateway_error = AIService._is_gateway_error(err_str)
                    retry_available = gateway_retry_count < gateway_max_retries
                    if gateway_error and retry_available:
                        gateway_retry_count += 1
                        retry_agent_name = f"{agent_name or 'agent'}-retry{gateway_retry_count}"
                        retry_message = f"测试点[{chunk_index}/{total_chunks}] {chunk_title}：AI网关504/503超时，等待{int(gateway_retry_delay)}秒后切换为{retry_agent_name}重新执行（{gateway_retry_count}/{gateway_max_retries}）"
                        logger.warning(f'{retry_message}: {err_str[:200]}')
                        event_queue.put({
                            "type": "ai_retry",
                            "level": "warning",
                            "chunkIndex": chunk_index,
                            "totalChunks": total_chunks,
                            "chunkTitle": chunk_title,
                            "agentName": retry_agent_name,
                            "retryCount": gateway_retry_count,
                            "retryDelay": gateway_retry_delay,
                            "message": retry_message
                        })
                        wait_until = time.time() + gateway_retry_delay
                        next_retry_heartbeat = time.time() + 10
                        while time.time() < wait_until:
                            if is_generation_cancelled(generation_id):
                                raise RuntimeError('生成已取消')
                            if time.time() >= next_retry_heartbeat:
                                event_queue.put({
                                    "type": "heartbeat",
                                    "chunkIndex": chunk_index,
                                    "totalChunks": total_chunks,
                                    "chunkTitle": chunk_title,
                                    "agentName": retry_agent_name,
                                    "elapsedSeconds": heartbeat_count * 10,
                                    "message": "AI网关超时，正在等待切换 retry agent"
                                })
                                next_retry_heartbeat += 10
                            time.sleep(min(1.0, wait_until - time.time()))
                        event_queue.put({
                            "type": "agent_log",
                            "level": "info",
                            "chunkIndex": chunk_index,
                            "totalChunks": total_chunks,
                            "chunkTitle": chunk_title,
                            "agentName": retry_agent_name,
                            "message": f"{retry_agent_name}开始重新生成测试点：{chunk_title}"
                        })
                        break
                    raise request_result
                except queue.Empty:
                    heartbeat_count += 1
                    event_queue.put({
                        "type": "heartbeat",
                        "chunkIndex": chunk_index,
                        "totalChunks": total_chunks,
                        "chunkTitle": chunk_title,
                        "agentName": agent_name,
                        "elapsedSeconds": heartbeat_count * 10,
                        "message": "AI agent仍在生成当前测试点"
                    })

    @staticmethod
    def get_embedding(text, model_setting=None):
        text = (text or '').strip()
        if not text:
            return [], ''
        model_setting = model_setting or {}
        try:
            from openai import OpenAI
            from config.ai_config import AIConfig
            import httpx

            api_key = AIConfig.get_api_key()
            if not api_key or api_key == '请替换为你的Meteor API Key':
                return AIService._hash_embedding(text), 'local-hash-128'
            provider = model_setting.get('provider') or AIConfig.MODEL_PROVIDER
            api_base = model_setting.get('apiBase') or model_setting.get('api_base') or AIConfig.get_api_base()
            embedding_model = model_setting.get('embeddingModel') or model_setting.get('embedding_model') or 'text-embedding-3-small'
            is_plan_key = '/plan/' in api_base
            request_base = AIService._normalize_plan_api_base(api_base) if is_plan_key else AIService._normalize_api_base(api_base)
            unavailable_key = f'{provider}:{request_base}:{embedding_model}'
            unavailable_until = _EMBEDDING_PROVIDER_UNAVAILABLE_UNTIL.get(unavailable_key, 0)
            if unavailable_until > time.time():
                return AIService._hash_embedding(text), 'local-hash-128'
            timeout = httpx.Timeout(connect=AIConfig.CONNECT_TIMEOUT, read=AIConfig.READ_TIMEOUT, write=AIConfig.READ_TIMEOUT, pool=AIConfig.CONNECT_TIMEOUT)
            client = OpenAI(api_key=api_key, base_url=request_base, http_client=httpx.Client(timeout=timeout, trust_env=False))
            response = client.embeddings.create(model=embedding_model, input=text[:6000])
            embedding = response.data[0].embedding if response.data else []
            if embedding:
                _EMBEDDING_PROVIDER_UNAVAILABLE_UNTIL.pop(unavailable_key, None)
                return embedding, embedding_model
            return AIService._hash_embedding(text), 'local-hash-128'
        except Exception as e:
            err_str = str(e)
            if 'no_available_providers' in err_str or 'No available providers' in err_str:
                try:
                    _EMBEDDING_PROVIDER_UNAVAILABLE_UNTIL[unavailable_key] = time.time() + _EMBEDDING_PROVIDER_COOLDOWN_SECONDS
                except UnboundLocalError:
                    pass
            if has_app_context():
                logger.warning(f'Embedding模型调用失败，使用本地向量兜底: {err_str}')
            return AIService._hash_embedding(text), 'local-hash-128'

    @staticmethod
    def _hash_embedding(text, dimensions=128):
        import hashlib
        import math
        vector = [0.0] * dimensions
        tokens = re.findall(r'[0-9A-Za-z_]+', text or '')
        for cn_text in re.findall(r'[\u4e00-\u9fa5]{2,}', text or ''):
            tokens.append(cn_text)
            for size in (2, 3, 4):
                for index in range(0, max(0, len(cn_text) - size + 1)):
                    tokens.append(cn_text[index:index + size])
        if not tokens:
            tokens = [text or 'empty']
        for token in tokens:
            digest = hashlib.md5(token.encode('utf-8')).digest()
            index = int.from_bytes(digest[:4], 'big') % dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            weight = 1.0 + min(len(token), 8) / 8.0
            vector[index] += sign * weight
        norm = math.sqrt(sum(item * item for item in vector)) or 1.0
        return [round(item / norm, 6) for item in vector]

    @staticmethod
    def chat_with_context(query, evidences=None, model_setting=None):
        try:
            from openai import OpenAI
            from config.ai_config import AIConfig
            import httpx

            evidences = evidences or []
            model_setting = model_setting or {}
            api_key = AIConfig.get_api_key()
            if not api_key or api_key == '请替换为你的Meteor API Key':
                return '', '未配置API密钥，请在.env中配置METEOR_API_KEY'
            provider = model_setting.get('provider') or AIConfig.MODEL_PROVIDER
            api_base = model_setting.get('apiBase') or model_setting.get('api_base') or AIConfig.get_api_base()
            model = model_setting.get('model') or AIConfig.get_model()
            temperature = float(model_setting.get('temperature') if model_setting.get('temperature') is not None else AIConfig.OPENAI_TEMPERATURE)
            max_tokens = int(model_setting.get('maxTokens') or model_setting.get('max_tokens') or AIConfig.OPENAI_MAX_TOKENS)
            # 通过 base URL 是否包含 /plan/ 来判断，不依赖 key 前缀（sk-5 开头的 key 也能正确识别）
            is_plan_key = '/plan/' in api_base
            request_base = AIService._normalize_plan_api_base(api_base) if is_plan_key else AIService._normalize_api_base(api_base)
            timeout = httpx.Timeout(connect=AIConfig.CONNECT_TIMEOUT, read=AIConfig.READ_TIMEOUT, write=AIConfig.READ_TIMEOUT, pool=AIConfig.CONNECT_TIMEOUT)
            prompt = AIService._build_rag_prompt(query, evidences)
            if is_plan_key:
                return AIService._create_plan_message(api_key, request_base, model, prompt, timeout), ''
            client = OpenAI(api_key=api_key, base_url=request_base, http_client=httpx.Client(timeout=timeout, trust_env=False))
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是测试平台的需求问答助手。只要 evidence-list 非空，必须优先依据证据内容回答，并按引用编号标注；不能在已有证据时笼统回答‘未找到充分依据’。证据确实没有覆盖问题时，再说明不足项。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content, ''
        except Exception as e:
            logger.error(f'知识库问答失败: {str(e)}')
            logger.error(traceback.format_exc())
            return '', f'模型调用失败: {str(e)}'

    @staticmethod
    def _build_rag_prompt(query, evidences):
        if evidences:
            parts = []
            for index, item in enumerate(evidences, 1):
                parts.append(f'[{index}] 文档ID：{item.get("documentId")}；分片：{item.get("chunkNo")}；相关度：{item.get("score")}\n标题：{item.get("title") or ""}\n内容：{item.get("snippet") or ""}')
            evidence_text = '\n\n'.join(parts)
        else:
            evidence_text = '无本地知识库证据。'
        return f'''
你是测试平台的需求问答助手。你只能基于给定需求文档证据回答。若 evidence-list 中存在证据，请先从证据中归纳直接答案，并标注引用；不要因为证据不完整就直接否定命中。只有 evidence-list 为“无本地知识库证据”或证据完全无关时，才说明“当前知识库未找到充分依据”，并列出需要补充的信息。

<evidence-list>
{evidence_text}
</evidence-list>

用户问题：{query}

请严格按以下 Markdown 结构输出，便于前端用“业务名称”作为脑图中心节点，并只截取“直接答案”生成脑图：

## 直接答案
业务名称：用不超过16个字概括当前回答对应的业务/模块/功能名称
- 一级要点名称：一句话说明
  - 二级要点：简短说明
  - 二级要点：简短说明
- 一级要点名称：一句话说明
  - 二级要点：简短说明

## 依据引用
- 按 [1]/[2] 标注对应依据。

## 测试关注点/风险点
- 如适用，列出测试关注点或风险点。

## 信息不足项
- 如有，列出仍需补充的信息；没有则写“无”。
'''.strip()

    @staticmethod
    def execute_test_case_by_ai(case_context):
        prompt = AIService._build_ai_case_execution_prompt(case_context or {})
        result, err_msg = AIService.request_json(
            prompt,
            error_prefix='AI执行用例',
            read_timeout=180,
            max_retries=1,
            max_tokens=2048,
            temperature=0.1,
            system_prompt='你是一个严格的测试执行助手。必须只输出可解析JSON，不要输出Markdown。'
        )
        if err_msg:
            return {}, err_msg
        if not isinstance(result, dict):
            return {}, 'AI执行结果格式错误'
        return result, ''

    @staticmethod
    def _build_ai_case_execution_prompt(case_context):
        def clean(value):
            if value is None:
                return ''
            if isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=False)
            return str(value)

        return f'''
你需要根据给定测试地址和测试用例信息，模拟资深测试工程师执行该用例，并判断执行结果。

重要规则：
1. 测试地址来自测试计划描述字段，必须作为本次测试对象：{clean(case_context.get('testUrl'))}
2. 如果用例步骤或预期结果信息不足，返回 blocked。
3. 如果根据测试地址、步骤、预期结果可以判断功能不满足，返回 failed，并写清失败原因。
4. 如果无法真实访问系统或缺少必要账号/数据，也返回 blocked，不要编造已真实点击页面。
5. 只输出 JSON，不要输出 Markdown 或解释性文本。

测试上下文：
- 计划名称：{clean(case_context.get('planName'))}
- 计划版本：{clean(case_context.get('planVersion'))}
- 测试地址：{clean(case_context.get('testUrl'))}
- 模块路径：{clean(case_context.get('modulePath'))}
- 模块名称：{clean(case_context.get('moduleName'))}
- 用例编号：{clean(case_context.get('caseKey'))}
- 用例名称：{clean(case_context.get('caseTitle'))}
- 前置条件：{clean(case_context.get('preconditions'))}
- 执行步骤：{clean(case_context.get('steps'))}
- 预期结果：{clean(case_context.get('expectedResults'))}

请输出以下 JSON 结构：
{{
  "status": "passed | failed | blocked",
  "actualResult": "执行或判定得到的实际结果",
  "reason": "未通过或阻塞的原因；通过时写通过依据",
  "evidence": "基于哪些步骤、页面地址、预期结果做出的判断",
  "suggestion": "失败或阻塞时的修复/补充建议，通过时可为空"
}}
'''.strip()

    @staticmethod
    def request_json(prompt, error_prefix='AI生成JSON', read_timeout=None, max_retries=None, max_tokens=None, temperature=None, system_prompt=None):
        try:
            from openai import OpenAI
            from config.ai_config import AIConfig
            import httpx

            api_key = AIConfig.get_api_key()
            api_base = AIConfig.get_api_base()
            model = AIConfig.get_model()
            provider = AIConfig.MODEL_PROVIDER
            if not api_key or api_key == '请替换为你的Meteor API Key':
                return {}, '未配置API密钥，请在.env中配置METEOR_API_KEY'
            is_plan_key = '/plan/' in api_base
            request_base = AIService._normalize_plan_api_base(api_base) if is_plan_key else AIService._normalize_api_base(api_base)
            current_read_timeout = read_timeout or AIConfig.READ_TIMEOUT
            timeout = httpx.Timeout(connect=AIConfig.CONNECT_TIMEOUT, read=current_read_timeout, write=current_read_timeout, pool=AIConfig.CONNECT_TIMEOUT)
            result = AIService._request_model(
                OpenAI, AIConfig, api_key, request_base, model, is_plan_key, prompt, timeout, httpx,
                max_retries=max_retries,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt
            )
            parsed_result = json.loads(AIService._extract_json_text(result))
            if not isinstance(parsed_result, (dict, list)):
                return {}, f'{error_prefix}格式错误'
            return parsed_result, ''
        except json.JSONDecodeError:
            return {}, f'{error_prefix}不是合法 JSON'
        except Exception as e:
            logger.error(f'{error_prefix}失败: {str(e)}')
            logger.error(traceback.format_exc())
            return {}, f'{error_prefix}失败: {str(e)}'

    @staticmethod
    def _request_model(OpenAI, AIConfig, api_key, request_base, model, is_plan_key, prompt, timeout, httpx,
                       max_retries=None, retry_delay=None, max_tokens=None, temperature=None, system_prompt=None):
        max_retries = max_retries if max_retries is not None else AIConfig.MAX_RETRIES
        retry_delay = retry_delay if retry_delay is not None else AIConfig.RETRY_DELAY
        max_tokens = max_tokens if max_tokens is not None else AIConfig.OPENAI_MAX_TOKENS
        temperature = temperature if temperature is not None else AIConfig.OPENAI_TEMPERATURE
        system_prompt = system_prompt or '你是一个专业的测试知识资产生成助手。必须最终只输出可解析JSON。'
        for attempt in range(max_retries):
            try:
                return AIService._execute_model_request(
                    OpenAI, AIConfig, api_key, request_base, model, is_plan_key, prompt,
                    timeout, httpx, max_tokens, temperature, system_prompt
                )
            except Exception as e:
                err_str = str(e)
                no_provider_error = 'no_available_providers' in err_str or 'No available providers' in err_str
                if no_provider_error:
                    logger.warning(f'AI服务暂无可用供应商，停止本次请求重试: {err_str[:200]}')
                    raise
                is_gateway_error = AIService._is_gateway_error(err_str)
                if attempt < max_retries - 1:
                    if is_gateway_error:
                        effective_delay = max(getattr(AIConfig, 'GATEWAY_RETRY_DELAY', 30.0), retry_delay * (2 ** attempt) * 5)
                        logger.warning(f'AI请求第{attempt + 1}次失败(网关超时)，{effective_delay}秒后重试: {err_str[:200]}')
                    else:
                        effective_delay = retry_delay * (2 ** attempt)
                        logger.warning(f'AI请求第{attempt + 1}次失败，{effective_delay}秒后重试: {err_str[:200]}')
                    time.sleep(effective_delay)
                else:
                    raise

    @staticmethod
    def _execute_model_request(OpenAI, AIConfig, api_key, request_base, model, is_plan_key, prompt,
                               timeout, httpx, max_tokens, temperature, system_prompt):
        semaphore = AIService._get_request_semaphore(AIConfig)
        with semaphore:
            AIService._wait_request_interval(AIConfig)
            if is_plan_key:
                return AIService._create_plan_message(api_key, request_base, model, prompt, timeout, max_tokens, temperature)
            client = OpenAI(api_key=api_key, base_url=request_base, http_client=httpx.Client(timeout=timeout, trust_env=False))
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content

    @staticmethod
    def _get_request_semaphore(AIConfig):
        global _AI_REQUEST_SEMAPHORE, _AI_REQUEST_SEMAPHORE_SIZE
        size = max(1, int(getattr(AIConfig, 'REQUEST_CONCURRENCY', 1) or 1))
        with _AI_REQUEST_SEMAPHORE_LOCK:
            if _AI_REQUEST_SEMAPHORE is None or _AI_REQUEST_SEMAPHORE_SIZE != size:
                _AI_REQUEST_SEMAPHORE = threading.BoundedSemaphore(size)
                _AI_REQUEST_SEMAPHORE_SIZE = size
            return _AI_REQUEST_SEMAPHORE

    @staticmethod
    def _wait_request_interval(AIConfig):
        global _AI_LAST_REQUEST_TS
        min_interval = max(0.0, float(getattr(AIConfig, 'REQUEST_MIN_INTERVAL', 0.0) or 0.0))
        if min_interval <= 0:
            return
        with _AI_REQUEST_THROTTLE_LOCK:
            now = time.time()
            wait_seconds = min_interval - (now - _AI_LAST_REQUEST_TS)
            if wait_seconds > 0:
                logger.info(f'AI请求限速等待{wait_seconds:.1f}秒')
                time.sleep(wait_seconds)
            _AI_LAST_REQUEST_TS = time.time()

    @staticmethod
    def _is_gateway_error(err_str):
        return '504' in err_str or 'Gateway Time-out' in err_str or 'Gateway Timeout' in err_str or '503' in err_str

    @staticmethod
    def _normalize_api_base(api_base):
        if not api_base:
            return 'https://api.routin.ai/v1'
        return api_base.rstrip('/').replace('/chat/completions', '')

    @staticmethod
    def _normalize_plan_api_base(api_base):
        if not api_base:
            return 'https://api.routin.ai/plan/v1'
        normalized = api_base.rstrip('/').replace('/chat/completions', '')
        if '/plan/v1' in normalized:
            return normalized
        return normalized.replace('/v1', '/plan/v1')

    @staticmethod
    def _create_plan_message(api_key, api_base, model, prompt, timeout, max_tokens=4096, temperature=0.7):
        import httpx
        response = httpx.post(
            f'{api_base}/messages',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': max_tokens, 'temperature': temperature},
            timeout=timeout,
            trust_env=False
        )
        response.raise_for_status()
        return AIService._extract_message_text(response.json())

    @staticmethod
    def _extract_message_text(data):
        if isinstance(data, dict):
            content = data.get('content')
            if isinstance(content, list):
                texts = [part['text'] for part in content if isinstance(part, dict) and part.get('text')]
                if texts:
                    return ''.join(texts)
            if isinstance(content, str):
                return content
        return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def _extract_json_text(result):
        text = result.strip()
        fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if fence_match:
            text = fence_match.group(1).strip()
        if text.startswith('{') or text.startswith('['):
            return text
        json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
        if json_match:
            return json_match.group(1).strip()
        return text

    @staticmethod
    def generate_skill_content(req_data):
        return AIService._generate_asset_content(
            req_data=req_data,
            prompt=AIService._build_skill_create_prompt(req_data),
            markdown_key='skill_md',
            normalizer=AIService._normalize_skill_markdown,
            error_prefix='AI生成 Skill 内容'
        )

    @staticmethod
    def generate_business_rule_content(req_data):
        return AIService._generate_asset_content(
            req_data=req_data,
            prompt=AIService._build_business_rule_create_prompt(req_data),
            markdown_key='rule_md',
            normalizer=AIService._normalize_rule_markdown,
            error_prefix='AI生成业务规则内容'
        )

    @staticmethod
    def _generate_asset_content(req_data, prompt, markdown_key, normalizer, error_prefix):
        try:
            from openai import OpenAI
            from config.ai_config import AIConfig
            import httpx

            api_key = AIConfig.get_api_key()
            api_base = AIConfig.get_api_base()
            model = AIConfig.get_model()
            provider = AIConfig.MODEL_PROVIDER
            if not api_key or api_key == '请替换为你的Meteor API Key':
                return {}, '未配置API密钥，请在.env中配置METEOR_API_KEY'
            is_plan_key = '/plan/' in api_base
            request_base = AIService._normalize_plan_api_base(api_base) if is_plan_key else AIService._normalize_api_base(api_base)
            timeout = httpx.Timeout(connect=AIConfig.CONNECT_TIMEOUT, read=AIConfig.READ_TIMEOUT, write=AIConfig.READ_TIMEOUT, pool=AIConfig.CONNECT_TIMEOUT)
            result = AIService._request_model(OpenAI, AIConfig, api_key, request_base, model, is_plan_key, prompt, timeout, httpx)
            parsed_result = json.loads(AIService._extract_json_text(result))
            if not isinstance(parsed_result, dict):
                return {}, f'{error_prefix}格式错误'
            md = parsed_result.get(markdown_key) or parsed_result.get(markdown_key.replace('_', ''))
            if not md or not isinstance(md, str):
                return {}, f'{error_prefix}缺少 {markdown_key}'
            parsed_result[markdown_key] = normalizer(md, req_data)
            return parsed_result, ''
        except json.JSONDecodeError:
            return {}, f'{error_prefix}不是合法 JSON'
        except Exception as e:
            logger.error(f'{error_prefix}失败: {str(e)}')
            logger.error(traceback.format_exc())
            return {}, f'{error_prefix}失败: {str(e)}'

    @staticmethod
    def _normalize_skill_markdown(skill_md, req_data):
        return AIService._normalize_markdown(skill_md, req_data, 'generated-skill')

    @staticmethod
    def _normalize_rule_markdown(rule_md, req_data):
        return AIService._normalize_markdown(rule_md, req_data, 'generated-rule')

    @staticmethod
    def _normalize_markdown(markdown, req_data, fallback_name):
        content = markdown.strip()
        content = re.sub(r'^```(?:markdown|md)?\s*', '', content)
        content = re.sub(r'\s*```$', '', content).strip()
        if content.startswith('---'):
            return content
        raw_name = str(req_data.get('name') or fallback_name).strip()
        frontmatter_name = re.sub(r'[^a-zA-Z0-9_-]+', '-', raw_name.lower()).strip('-') or fallback_name
        description = str(req_data.get('description') or raw_name).strip()
        return f'---\nname: {frontmatter_name}\ndescription: {description}\n---\n\n{content}'

    @staticmethod
    def get_default_case_generation_trigger_condition():
        return '当用户基于 PRD、需求文档、用户故事、功能说明、接口说明、UI 交互说明或业务规则生成、补充、优化、评审测试用例时触发。'

    @staticmethod
    def get_default_case_generation_output_spec():
        return '''输出必须兼容当前 AI 生成用例入库结构：最终只输出 JSON 对象，不输出 Markdown、解释文本或代码块。JSON 对象结构为 {"cases": [{"title": "用例名称/测试点名称", "module_name": "一级模块/二级模块/三级模块/四级模块", "precondition": "前置条件", "steps": "步骤1\\n步骤2", "expected_result": "预期结果1\\n预期结果2", "priority": 2, "case_type": 1, "tags": ["AI生成"]}]}。module_name 必须严格按照 PRD 编号层级和实际分析结果生成：用 PRD 标题编号确定一级、二级模块，模块名称尽量直接使用各编号对应的标题文本；三级、四级在无显式编号时按子标题、表格功能项、业务规则、验收项、流程节点和从属功能点分析生成；普通正文有序列表项不能当作一级或二级模块；最多四级，不要脱离 PRD 一级编号额外创建一级模块。每条用例 title 需要细化到具体场景，steps 和 expected_result 每一行带数字编号，信息不足时标记“待确认”，不能编造需求。'''

    @staticmethod
    def _load_skill_creator_content():
        skill_path = Path(__file__).resolve().parents[3] / 'config' / 'skills' / 'skill-creator' / 'SKILL.md'
        if not skill_path.exists():
            raise FileNotFoundError(f'Skill创建规则不存在: {skill_path}')
        return skill_path.read_text(encoding='utf-8')

    @staticmethod
    def _load_skill_content():
        skill_path = Path(__file__).resolve().parents[3] / 'config' / 'skills' / 'test-case-generator' / 'SKILL.md'
        if not skill_path.exists():
            raise FileNotFoundError(f'测试用例生成技能不存在: {skill_path}')
        return skill_path.read_text(encoding='utf-8')

    @staticmethod
    def _build_skill_create_prompt(req_data):
        skill_creator_content = AIService._load_skill_creator_content()
        default_trigger_condition = AIService.get_default_case_generation_trigger_condition()
        default_output_spec = AIService.get_default_case_generation_output_spec()
        return f'''
你现在要严格按照下面 skill-creator 的 SKILL.md 规范，为测试平台创建一个新的 Skill 文件。

<skill-creator-skill-md>
{skill_creator_content}
</skill-creator-skill-md>

<new-skill-input>
Skill 名称：{req_data.get('name') or ''}
用户补充描述：{req_data.get('description') or ''}
标签：{req_data.get('tags') or []}
Skill 类型枚举值：{req_data.get('skillType') or req_data.get('skill_type') or 1}
风险等级枚举值：{req_data.get('riskLevel') or req_data.get('risk_level') or 2}
</new-skill-input>

<platform-contract>
这个 Skill 的目标是增强当前平台“AI 根据 PRD/需求生成测试用例”的能力。
触发条件固定理解为：{default_trigger_condition}
输出规范固定理解为：{default_output_spec}
</platform-contract>

请只输出 JSON 对象：
{{
  "description": "适合列表展示的 Skill 简介，80字以内",
  "reasoning_path": "面向测试用例生成的推理路径摘要，简洁步骤描述",
  "tags": ["标签1", "标签2"],
  "skill_type": 1,
  "risk_level": 2,
  "skill_md": "完整的 SKILL.md 文件内容，包含 YAML frontmatter 和 Markdown body"
}}

约束：skill_md 必须包含 YAML frontmatter，至少包含 name 和 description；body 必须是面向测试用例生成的 Markdown 指令；不要复制 skill-creator 原文；不要输出代码块或额外说明。
'''.strip()

    @staticmethod
    def _build_business_rule_create_prompt(req_data):
        input_rule_content = req_data.get('ruleContent') or req_data.get('rule_content') or req_data.get('description') or ''
        return f'''
请为测试平台创建一条“业务规则”知识资产，用于增强 AI 根据 PRD/需求生成测试用例时对确定性业务约束、校验条件、状态流转、边界条件和异常处理的理解。

<business-rule-input>
规则名称：{req_data.get('name') or ''}
用户输入的规则原文：{input_rule_content}
用户补充描述：{req_data.get('description') or ''}
标签：{req_data.get('tags') or []}
优先级枚举值：{req_data.get('priority') or 2}
</business-rule-input>

硬性约束：
1. 不要随机生成、替换或改变“用户输入的规则原文”的业务含义。
2. 返回 JSON 中的 rule_content 必须逐字等于“用户输入的规则原文”。
3. 你只能基于用户输入补充 applicable_scene、example、tags、priority，并生成用于测试用例生成的 RULE.md。
4. RULE.md 的“## Rule”章节必须逐字包含“用户输入的规则原文”，不能改写成另一条规则。

请只输出 JSON 对象：
{{
  "rule_content": "逐字返回用户输入的规则原文",
  "applicable_scene": "该规则适用的业务场景",
  "example": "输入/场景/预期的示例",
  "tags": ["标签1", "标签2"],
  "priority": 2,
  "rule_md": "完整的 RULE.md 文件内容，包含 YAML frontmatter 和 Markdown body"
}}

RULE.md 要求：必须包含 YAML frontmatter，至少包含 name 和 description；body 建议包含规则说明、适用场景、测试关注点、正反例、生成用例时的约束；内容必须面向测试用例生成；priority 只能是 0、1、2、3；tags 最多 8 个；不要输出代码块或额外说明。
'''.strip()

    @staticmethod
    def _split_test_case_generation_content(document_content):
        content = (document_content or '').strip()
        if not content:
            return []
        chunks = AIService._split_by_headings(content)
        logger.info(f'测试用例生成已按模块拆分为{len(chunks)}个批次，不限制单批字符数')
        return chunks

    @staticmethod
    def _split_document_content(document_content, max_chars=8000):
        content = (document_content or '').strip()
        if not content:
            return []
        sections = AIService._split_by_headings(content)
        chunks = []
        current_parts = []
        current_len = 0
        current_title = '文档内容'
        for section in sections:
            section_text = section['content'].strip()
            if not section_text:
                continue
            if len(section_text) > max_chars:
                if current_parts:
                    chunks.append({'title': current_title, 'content': '\n\n'.join(current_parts)})
                    current_parts = []
                    current_len = 0
                chunks.extend(AIService._split_large_section(section['title'], section_text, max_chars))
                continue
            if current_parts and current_len + len(section_text) > max_chars:
                chunks.append({'title': current_title, 'content': '\n\n'.join(current_parts)})
                current_parts = []
                current_len = 0
            if not current_parts:
                current_title = section['title']
            current_parts.append(section_text)
            current_len += len(section_text)
        if current_parts:
            chunks.append({'title': current_title, 'content': '\n\n'.join(current_parts)})
        return chunks or [{'title': '文档内容', 'content': content}]

    @staticmethod
    def _split_by_headings(content):
        heading_pattern = re.compile(r'(?m)^(#{1,6}\s+.+|第[一二三四五六七八九十百千万\d]+[章节部分篇].*|\d+(?:\.\d+)+[、.．]?\s*.+|(?:模块|功能|业务流程|流程|页面|接口|菜单|场景)[:：].+)$')
        matches = list(heading_pattern.finditer(content))
        if not matches:
            return [{'title': '文档内容', 'content': content}]
        sections = []
        heading_stack = []
        if matches[0].start() > 0:
            sections.append({'title': '文档开头', 'content': content[:matches[0].start()].strip()})
        for index, match in enumerate(matches):
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
            raw_title = match.group(0).strip()
            title = raw_title.lstrip('#').strip()
            level = AIService._heading_level(raw_title, title)
            if index == 0 and re.match(r'^#\s+', raw_title):
                sections.append({'title': title[:120] or '文档内容', 'content': content[start:end].strip()})
                continue
            heading_stack = [item for item in heading_stack if item['level'] < level]
            heading_stack.append({'level': level, 'title': title})
            full_title = '/'.join(item['title'] for item in heading_stack)
            sections.append({'title': full_title[:120] or '文档内容', 'content': content[start:end].strip()})
        return sections

    @staticmethod
    def _heading_level(raw_title, title):
        markdown_match = re.match(r'^(#{1,6})\s+', raw_title)
        if markdown_match:
            return len(markdown_match.group(1))
        number_match = re.match(r'^(\d+(?:\.\d+)+)', title)
        if number_match:
            return number_match.group(1).count('.') + 1
        if re.match(r'^第[一二三四五六七八九十百千万\d]+[章节部分篇]', title):
            return 1
        return 6

    @staticmethod
    def _split_large_section(title, section_text, max_chars):
        paragraphs = re.split(r'\n\s*\n', section_text)
        chunks = []
        current_parts = []
        current_len = 0
        part_index = 1
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            while len(paragraph) > max_chars:
                if current_parts:
                    chunks.append({'title': f'{title}（第{part_index}部分）', 'content': '\n\n'.join(current_parts)})
                    part_index += 1
                    current_parts = []
                    current_len = 0
                chunks.append({'title': f'{title}（第{part_index}部分）', 'content': paragraph[:max_chars]})
                part_index += 1
                paragraph = paragraph[max_chars:]
            if current_parts and current_len + len(paragraph) > max_chars:
                chunks.append({'title': f'{title}（第{part_index}部分）', 'content': '\n\n'.join(current_parts)})
                part_index += 1
                current_parts = []
                current_len = 0
            current_parts.append(paragraph)
            current_len += len(paragraph)
        if current_parts:
            chunks.append({'title': f'{title}（第{part_index}部分）', 'content': '\n\n'.join(current_parts)})
        return chunks

    @staticmethod
    def _deduplicate_cases(cases):
        seen = {}
        deduplicated = []
        for case in cases:
            key = f"{case.get('module_name', '')}::{case.get('title', '')}".strip().lower()
            if not key or key in seen:
                continue
            seen[key] = True
            deduplicated.append(case)
        return deduplicated

    @staticmethod
    def _normalize_cases(parsed_result, template=None, chunk_title=''):
        template = template or {}
        raw_cases = AIService._collect_case_items(parsed_result)
        normalized = []
        for index, item in enumerate(raw_cases, 1):
            if not isinstance(item, dict):
                continue
            tags = item.get('tags') or item.get('标签') or template.get('tags', ['AI生成'])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in re.split(r'[,，]', tags) if tag.strip()]
            module_name = AIService._normalize_module_name(item.get('module_name') or item.get('所属模块') or item.get('module') or '未分类')
            if AIService._is_non_testable_module(module_name) or AIService._is_invalid_root_module(module_name):
                continue
            normalized.append({
                'selected': item.get('selected', True),
                'module_name': module_name,
                'title': item.get('title') or item.get('用例名称') or item.get('case_name') or item.get('name') or f'AI生成用例{index}',
                'precondition': item.get('precondition') or item.get('前置条件') or '',
                'steps': AIService._number_lines(item.get('steps') or item.get('步骤描述') or item.get('操作步骤') or ''),
                'expected_result': AIService._number_lines(item.get('expected_result') or item.get('expected_results') or item.get('预期结果') or item.get('期望结果') or ''),
                'priority': AIService._normalize_priority(item.get('priority') or item.get('用例等级'), template.get('priority', 2)),
                'case_type': AIService._normalize_case_type(item.get('case_type') or item.get('类型') or item.get('标签'), template.get('case_type', 1)),
                'tags': tags or ['AI生成']
            })
        return normalized

    @staticmethod
    def _collect_case_items(value):
        if isinstance(value, list):
            items = []
            for item in value:
                items.extend(AIService._collect_case_items(item))
            return items
        if not isinstance(value, dict):
            return []
        case_keys = {'title', '用例名称', 'case_name', 'name', 'steps', '步骤描述', '操作步骤', 'expected_result', '预期结果', '期望结果'}
        if any(key in value for key in case_keys):
            return [value]
        items = []
        for nested_value in value.values():
            items.extend(AIService._collect_case_items(nested_value))
        return items

    @staticmethod
    def _normalize_module_name(module_name):
        parts = [part.strip() for part in re.split(r'[/\\>＞｜|]', str(module_name or '')) if part.strip()]
        parts = [re.sub(r'^\d+(?:\.\d+)*[、.．]?\s*', '', part).strip() for part in parts]
        parts = [part for part in parts if part]
        return '/'.join(parts[:4]) if parts else '未分类'

    @staticmethod
    def _is_invalid_root_module(module_name):
        parts = [part.strip() for part in str(module_name or '').split('/') if part.strip()]
        if not parts:
            return False
        root = parts[0]
        generic_roots = {'功能说明', '业务规则', '验收标准', '待完善规则', '待完善内容'}
        return root in generic_roots or root.endswith('流程')

    @staticmethod
    def _is_non_testable_module(module_name):
        parts = [part.strip() for part in str(module_name or '').split('/') if part.strip()]
        if not parts:
            return False
        non_testable_keywords = (
            '文档说明', '文档目的', '资料来源', '产品定位', '用户角色说明',
            '版本规划', '待完善事项清单', '风险与注意事项', '附录', '字段说明'
        )
        return any(any(keyword in part for keyword in non_testable_keywords) for part in parts)

    @staticmethod
    def _number_lines(value):
        if isinstance(value, list):
            lines = [str(item).strip() for item in value if str(item).strip()]
        else:
            lines = [line.strip() for line in re.split(r'\n+', str(value or '')) if line.strip()]
        normalized = []
        for index, line in enumerate(lines, 1):
            cleaned_line = re.sub(r'^(?:步骤|预期结果)?\s*\d+\s*[.、．]\s*', '', line).strip()
            normalized.append(f'{index}. {cleaned_line}')
        return '\n'.join(normalized)

    @staticmethod
    def _normalize_priority(value, default=2):
        if isinstance(value, int):
            return value
        return {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3, 'P4': 3, 'P5': 3}.get(str(value).upper(), default)

    @staticmethod
    def _normalize_case_type(value, default=1):
        if isinstance(value, int):
            return value
        text = str(value or '')
        if '性能' in text:
            return 2
        if '安全' in text:
            return 3
        if '接口' in text or 'API' in text.upper():
            return 4
        return default

    @staticmethod
    def _build_generation_context(template):
        template = template or {}
        skill_contexts = template.get('skill_contexts') or []
        rule_contexts = template.get('rule_contexts') or []
        existing_case_context = template.get('existing_case_context') or ''
        if not skill_contexts and not rule_contexts and not existing_case_context:
            return ''
        parts = ['<selected-generation-context>']
        if skill_contexts:
            parts.append('请在生成测试用例时结合以下用户指定 Skill：')
            for item in skill_contexts:
                parts.append(f'''<selected-skill id="{item.get('id')}" name="{item.get('name')}">
{item.get('content') or ''}
</selected-skill>''')
        if rule_contexts:
            parts.append('请在生成测试用例时严格覆盖以下用户指定业务规则：')
            for item in rule_contexts:
                parts.append(f'''<selected-rule id="{item.get('id')}" name="{item.get('name')}">
{item.get('content') or ''}
</selected-rule>''')
        if existing_case_context:
            parts.append(f'''<existing-ai-cases>
{existing_case_context}
</existing-ai-cases>''')
        parts.append('</selected-generation-context>')
        return '\n\n'.join(parts)

    @staticmethod
    def _build_prompt(document_content, template=None, skill_content='', chunk_index=1, total_chunks=1, chunk_title='文档内容'): 
        template = template or {'priority': 2, 'case_type': 1, 'tags': ['AI生成']}
        generation_context = AIService._build_generation_context(template)
        return f'''
请使用下面的 test-case-generator skill 对需求文档分段进行深度测试用例设计。最终只输出 JSON。

<test-case-generator-skill>
{skill_content}
</test-case-generator-skill>

{generation_context}

<document-chunk-info>
当前分段：{chunk_index}/{total_chunks}
分段标题：{chunk_title}
</document-chunk-info>

<requirement-document-chunk>
{document_content}
</requirement-document-chunk>

平台入库配置：
- 默认优先级(priority): {template['priority']}
- 默认用例类型(case_type): {template['case_type']}
- 默认标签(tags): {template['tags']}

模块层级硬性要求：
- `module_name` 必须严格按照 PRD 编号层级生成，格式优先为 `一级模块/二级模块/三级模块/四级模块`，最多四级。
- 用 PRD 编号确定层级，但模块名称尽量直接使用各编号对应的标题文本，不要主动把数字编号前缀写进模块名。
- 先排除文档说明、文档目的、资料来源、产品定位、用户角色说明、版本规划、待完善事项清单、风险与注意事项、附录等只提供背景或元信息的非测试章节；这些章节只作为上下文，不生成测试用例模块。
- PRD 有几个可测试一级编号，就生成几个一级模块；不要脱离 PRD 可测试一级编号额外创建一级模块。
- 一级编号下有几个可测试子编号，就在该一级模块下生成对应数量的二级模块；继续按子编号和实际分析结果映射到三级、四级。
- 分段标题只用于定位当前内容，不允许直接把分段标题的最后一级（例如 `功能说明`、`多语言切换流程`）提升为一级模块；生成 `module_name` 时必须结合正文中的完整标题路径和最近父级模块，例如 `4. 客户端/4.3 多语言/功能说明` 应归入 `客户端/多语言/功能说明/...`。
- 普通正文中的有序列表项，例如 `1. 支持用户浏览...`、`4. 支持基本内容治理...`，如果不是标题或目录章节，不能当作一级或二级模块，只能作为最近父模块下的功能点、三级/四级分析依据或用例标题内容。
- 页面、按钮、入口、弹窗、字段、状态、异常提示或单个操作如果不是 PRD 编号标题，不能提升为一级模块，应放到下级模块或用例标题中。
- 如果 PRD 没有明确编号，必须先根据标题大小、目录结构、列表缩进、表格分区、功能组、用户流程和语义段落智能推断隐含编号层级，再按推断出的一级到四级模块生成；超过四级的更深细节放到用例标题中。

续生成与去重要求：
- 如果 `<existing-ai-cases>` 中已经存在相同模块、相同标题、相同步骤或相同预期的测试点，不要再次输出。
- 重新生成时只补充当前文档中尚未覆盖的新场景、新边界、新异常路径或遗漏规则。

输出 JSON 结构：
{{"cases":[{{"title":"用例名称/测试点名称","module_name":"一级模块/二级模块/三级模块/四级模块","precondition":"前置条件","steps":"步骤1\\n步骤2","expected_result":"预期结果1\\n预期结果2","priority":2,"case_type":1,"tags":["AI生成"]}}]}}
'''.strip()

    @staticmethod
    def parse_pdf_and_generate_cases(pdf_path, template=None):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
            content = ''
            for page in reader.pages:
                page_content = page.extract_text()
                if page_content:
                    content += page_content + '\n'
            if not content.strip():
                return [], 'PDF文件内容为空'
            return AIService.generate_test_cases(content, template)
        except Exception as e:
            logger.error(f'解析PDF并生成用例失败: {str(e)}')
            return [], f'解析PDF失败: {str(e)}'
