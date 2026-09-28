# encoding: UTF-8
import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path

from logger import logger
from ..dao.weakNetworkAiDao import WeakNetworkAiDao
from ..model.bugModel import Bug
from ..model.weakNetworkAiModel import (
    WeakNetworkAiCheckpoint,
    WeakNetworkAiEvidence,
    WeakNetworkAiFinding,
    WeakNetworkAiTask,
)
from ..model.weakNetworkModel import WeakNetworkProfile
from ..service.bugService import BugService
from ..service.weakNetworkService import WeakNetworkService

EVIDENCE_DIR = Path(__file__).resolve().parents[3] / 'attachment' / 'weak_network_ai'


class WeakNetworkAiService(object):

    @staticmethod
    def list_tasks(session, req_data):
        items, total = WeakNetworkAiDao.list_tasks(session, req_data)
        return {
            'list': [WeakNetworkAiService._task_brief(x) for x in items],
            'total': total,
        }, ''

    @staticmethod
    def create_task(session, req_data, user_id=None):
        title = (WeakNetworkAiService._get(req_data, 'title') or '').strip()
        brief = (WeakNetworkAiService._get(req_data, 'brief') or '').strip()
        if not title and brief:
            title = brief[:80]
        if not title:
            return {}, 'title 或 brief 为必传参数'
        task_no = WeakNetworkAiService._next_task_no(session)
        obj, err = WeakNetworkAiDao.create(session, WeakNetworkAiTask, {
            'task_no': task_no,
            'title': title[:255],
            'brief': brief,
            'product_id': WeakNetworkAiService._to_int_or_none(
                WeakNetworkAiService._get(req_data, 'productId', 'product_id')
            ),
            'product_name': WeakNetworkAiService._get(req_data, 'productName', 'product_name') or '',
            'project_id': WeakNetworkAiService._to_int_or_none(
                WeakNetworkAiService._get(req_data, 'projectId', 'project_id')
            ),
            'project_name': WeakNetworkAiService._get(req_data, 'projectName', 'project_name') or '',
            'status': 'draft',
            'recommended_profiles': [],
            'selected_profile_ids': [],
            'weak_network_session_ids': [],
            'created_by': user_id,
            'remark': WeakNetworkAiService._get(req_data, 'remark') or '',
            'is_delete': 0,
        })
        if err:
            return {}, err
        return WeakNetworkAiService.detail(session, obj.id)

    @staticmethod
    def detail(session, task_id):
        try:
            inner = getattr(session, 'session', None) or getattr(session, '_session', None)
            if inner is not None:
                inner.expire_all()
        except Exception:
            pass
        task = WeakNetworkAiDao.get_by_id(session, WeakNetworkAiTask, task_id)
        if not task:
            return {}, '未查询到任务'
        checkpoints = WeakNetworkAiDao.list_checkpoints(session, task_id)
        evidence = WeakNetworkAiDao.list_evidence(session, task_id)
        findings = WeakNetworkAiDao.list_findings(session, task_id)
        return {
            'task': WeakNetworkAiService._task_brief(task),
            'checkpoints': [WeakNetworkAiService._checkpoint_dict(c) for c in checkpoints],
            'evidence': [WeakNetworkAiService._evidence_dict(e) for e in evidence],
            'findings': [WeakNetworkAiService._finding_dict(f) for f in findings],
        }, ''

    @staticmethod
    def update_task(session, req_data, user_id=None):
        task_id = WeakNetworkAiService._get(req_data, 'taskId', 'task_id', 'id')
        if not task_id:
            return {}, 'taskId 为必传参数'
        task = WeakNetworkAiDao.get_by_id(session, WeakNetworkAiTask, task_id)
        if not task:
            return {}, '未查询到任务'
        if task.status not in ('draft', 'ready', 'collecting'):
            return {}, '当前状态不可编辑'
        update_info = {}
        if 'title' in (req_data or {}):
            update_info['title'] = str(req_data.get('title') or '')[:255]
        if 'brief' in (req_data or {}):
            update_info['brief'] = req_data.get('brief') or ''
        if 'selectedProfileIds' in (req_data or {}) or 'selected_profile_ids' in (req_data or {}):
            ids = WeakNetworkAiService._get(req_data, 'selectedProfileIds', 'selected_profile_ids') or []
            update_info['selected_profile_ids'] = [int(x) for x in ids]
        if 'recommendedProfiles' in (req_data or {}) or 'recommended_profiles' in (req_data or {}):
            update_info['recommended_profiles'] = WeakNetworkAiService._get(
                req_data, 'recommendedProfiles', 'recommended_profiles'
            ) or []
        if update_info:
            _, err = WeakNetworkAiDao.update_by_id(session, WeakNetworkAiTask, task_id, update_info)
            if err:
                return {}, err
        checkpoints = WeakNetworkAiService._get(req_data, 'checkpoints')
        if checkpoints is not None:
            if not isinstance(checkpoints, list):
                return {}, 'checkpoints 必须为数组'
            WeakNetworkAiDao.soft_delete_checkpoints(session, task_id)
            for idx, cp in enumerate(checkpoints, start=1):
                title = (cp.get('title') or '').strip()
                if not title:
                    continue
                WeakNetworkAiDao.create(session, WeakNetworkAiCheckpoint, {
                    'task_id': int(task_id),
                    'sort_no': int(cp.get('sortNo') or cp.get('sort_no') or idx),
                    'title': title[:500],
                    'expect_text': cp.get('expect') or cp.get('expectText') or cp.get('expect_text') or '',
                    'profile_preset': cp.get('profilePreset') or cp.get('profile_preset') or cp.get('presetCode') or '',
                    'status': 'pending',
                    'is_delete': 0,
                })
        return WeakNetworkAiService.detail(session, task_id)

    @staticmethod
    def orchestrate(session, req_data, user_id=None):
        task_id = WeakNetworkAiService._get(req_data, 'taskId', 'task_id', 'id')
        if not task_id:
            return {}, 'taskId 为必传参数'
        task = WeakNetworkAiDao.get_by_id(session, WeakNetworkAiTask, task_id)
        if not task:
            return {}, '未查询到任务'
        brief = (WeakNetworkAiService._get(req_data, 'brief') or task.brief or '').strip()
        if not brief:
            return {}, 'brief 不能为空'
        parsed, source = WeakNetworkAiService._ai_orchestrate(brief)
        if not parsed:
            parsed = WeakNetworkAiService._fallback_orchestrate(brief)
            source = 'fallback'
        profiles = (parsed.get('profiles') or [])[:3]
        checkpoints = (parsed.get('checkpoints') or [])[:8]
        if len(checkpoints) < 3:
            checkpoints = WeakNetworkAiService._fallback_orchestrate(brief)['checkpoints']
            source = 'fallback'
        enabled_profiles = session.query(WeakNetworkProfile).filter(
            WeakNetworkProfile.is_delete == 0,
            WeakNetworkProfile.enabled == 1,
        ).all()
        by_code = {}
        for p in enabled_profiles:
            by_code.setdefault(p.preset_code, p)
        recommended = []
        selected_ids = []
        for item in profiles:
            code = (item.get('presetCode') or item.get('preset_code') or 'subway').strip()
            profile = by_code.get(code) or by_code.get('subway')
            if not profile and enabled_profiles:
                profile = enabled_profiles[0]
            if not profile:
                continue
            recommended.append({
                'presetCode': profile.preset_code,
                'profileId': profile.id,
                'name': profile.name,
                'reason': item.get('reason') or '',
            })
            if profile.id not in selected_ids:
                selected_ids.append(profile.id)
        if not selected_ids:
            for p in enabled_profiles:
                selected_ids.append(p.id)
                recommended.append({
                    'presetCode': p.preset_code,
                    'profileId': p.id,
                    'name': p.name,
                    'reason': '系统可用画像',
                })
                if len(selected_ids) >= 2:
                    break
        if not selected_ids:
            return {}, '没有可用的弱网画像，请先在弱网配置中启用画像'
        WeakNetworkAiDao.update_by_id(session, WeakNetworkAiTask, task_id, {
            'brief': brief,
            'recommended_profiles': recommended,
            'selected_profile_ids': selected_ids[:3],
            'status': 'draft',
        })
        WeakNetworkAiDao.soft_delete_checkpoints(session, task_id)
        for idx, cp in enumerate(checkpoints[:8], start=1):
            title = (cp.get('title') or '').strip()
            if not title:
                continue
            WeakNetworkAiDao.create(session, WeakNetworkAiCheckpoint, {
                'task_id': int(task_id),
                'sort_no': idx,
                'title': title[:500],
                'expect_text': cp.get('expect') or '',
                'profile_preset': cp.get('profilePreset') or cp.get('presetCode') or (
                    recommended[0]['presetCode'] if recommended else 'subway'
                ),
                'status': 'pending',
                'is_delete': 0,
            })
        detail, err = WeakNetworkAiService.detail(session, task_id)
        if err:
            return {}, err
        detail['orchestrateSource'] = source
        return detail, ''

    @staticmethod
    def confirm(session, req_data, user_id=None):
        task_id = WeakNetworkAiService._get(req_data, 'taskId', 'task_id', 'id')
        if not task_id:
            return {}, 'taskId 为必传参数'
        task = WeakNetworkAiDao.get_by_id(session, WeakNetworkAiTask, task_id)
        if not task:
            return {}, '未查询到任务'
        checkpoints = WeakNetworkAiDao.list_checkpoints(session, task_id)
        if not checkpoints:
            return {}, '请先生成或填写检查点'
        selected = task.selected_profile_ids or []
        if isinstance(selected, str):
            try:
                selected = json.loads(selected)
            except Exception:
                selected = []
        if not selected:
            return {}, '请至少选择一个弱网画像'
        session_ids = []
        for pid in selected:
            created, err = WeakNetworkService.create_session(session, {
                'profileId': int(pid),
                'productId': task.product_id,
                'projectId': task.project_id,
                'deviceSerial': WeakNetworkAiService._get(req_data, 'deviceSerial', 'device_serial') or '',
            }, user_id=user_id)
            if err:
                return {}, '创建弱网会话失败：{}'.format(err)
            session_ids.append(created.get('sessionId'))
        WeakNetworkAiDao.update_by_id(session, WeakNetworkAiTask, task_id, {
            'weak_network_session_ids': session_ids,
            'status': 'ready',
        })
        return WeakNetworkAiService.detail(session, task_id)

    @staticmethod
    def add_evidence(session, req_data, user_id=None, upload_file=None, filename=None):
        task_id = WeakNetworkAiService._get(req_data, 'taskId', 'task_id')
        if not task_id:
            return {}, 'taskId 为必传参数'
        task = WeakNetworkAiDao.get_by_id(session, WeakNetworkAiTask, task_id)
        if not task:
            return {}, '未查询到任务'
        if task.status in ('draft',):
            WeakNetworkAiDao.update_by_id(session, WeakNetworkAiTask, task_id, {'status': 'collecting'})
        elif task.status == 'ready':
            WeakNetworkAiDao.update_by_id(session, WeakNetworkAiTask, task_id, {'status': 'collecting'})
        rel_path = ''
        if upload_file is not None:
            EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
            ext = os.path.splitext(filename or 'shot.png')[1] or '.png'
            name = 't{}_{}{}'.format(task_id, uuid.uuid4().hex[:12], ext)
            dest = EVIDENCE_DIR / name
            dest.write_bytes(upload_file if isinstance(upload_file, (bytes, bytearray)) else upload_file.read())
            rel_path = 'attachment/weak_network_ai/{}'.format(name)
        note = WeakNetworkAiService._get(req_data, 'note') or ''
        checkpoint_id = WeakNetworkAiService._to_int_or_none(
            WeakNetworkAiService._get(req_data, 'checkpointId', 'checkpoint_id')
        )
        mobile_execution_id = WeakNetworkAiService._to_int_or_none(
            WeakNetworkAiService._get(req_data, 'mobileExecutionId', 'mobile_execution_id')
        )
        if not rel_path and not note:
            return {}, '请上传截图或填写备注'
        obj, err = WeakNetworkAiDao.create(session, WeakNetworkAiEvidence, {
            'task_id': int(task_id),
            'checkpoint_id': checkpoint_id,
            'file_path': rel_path,
            'note': note,
            'mobile_execution_id': mobile_execution_id,
            'created_by': user_id,
            'is_delete': 0,
        })
        if err:
            return {}, err
        return WeakNetworkAiService.detail(session, task_id)

    @staticmethod
    def judge(session, req_data, user_id=None):
        task_id = WeakNetworkAiService._get(req_data, 'taskId', 'task_id', 'id')
        if not task_id:
            return {}, 'taskId 为必传参数'
        task = WeakNetworkAiDao.get_by_id(session, WeakNetworkAiTask, task_id)
        if not task:
            return {}, '未查询到任务'
        checkpoints = WeakNetworkAiDao.list_checkpoints(session, task_id)
        if not checkpoints:
            return {}, '没有检查点可判定'
        evidence = WeakNetworkAiDao.list_evidence(session, task_id)
        verdicts = WeakNetworkAiService._ai_judge(task, checkpoints, evidence)
        if not verdicts:
            verdicts = WeakNetworkAiService._fallback_judge(checkpoints, evidence)
        for item in verdicts:
            cp_id = item.get('checkpointId') or item.get('checkpoint_id')
            verdict = (item.get('verdict') or 'insufficient').strip().lower()
            if verdict not in ('acceptable', 'suspect', 'insufficient'):
                verdict = 'insufficient'
            observation = (item.get('observation') or '').strip()
            cp = WeakNetworkAiDao.get_by_id(session, WeakNetworkAiCheckpoint, cp_id) if cp_id else None
            if not cp or int(cp.task_id) != int(task_id):
                continue
            WeakNetworkAiDao.update_by_id(session, WeakNetworkAiCheckpoint, cp.id, {
                'status': 'judged',
                'last_verdict': verdict,
                'last_observation': observation[:2000],
            })
            if verdict != 'suspect':
                continue
            existing_open = [
                f for f in WeakNetworkAiDao.list_findings(session, task_id, status='open')
                if f.checkpoint_id == cp.id
            ]
            payload = {'verdict': verdict, 'observation': observation, 'confidence': item.get('confidence')}
            if existing_open:
                WeakNetworkAiDao.update_by_id(session, WeakNetworkAiFinding, existing_open[0].id, {
                    'title': cp.title[:500],
                    'detail': observation[:4000],
                    'ai_payload': payload,
                })
            else:
                # do not touch confirmed findings
                confirmed = [
                    f for f in WeakNetworkAiDao.list_findings(session, task_id, status='confirmed')
                    if f.checkpoint_id == cp.id
                ]
                if confirmed:
                    continue
                WeakNetworkAiDao.create(session, WeakNetworkAiFinding, {
                    'task_id': int(task_id),
                    'checkpoint_id': cp.id,
                    'title': cp.title[:500],
                    'detail': observation[:4000],
                    'status': 'open',
                    'ai_payload': payload,
                    'is_delete': 0,
                })
        WeakNetworkAiDao.update_by_id(session, WeakNetworkAiTask, task_id, {'status': 'judged'})
        return WeakNetworkAiService.detail(session, task_id)

    @staticmethod
    def dismiss_findings(session, req_data, user_id=None):
        task_id = WeakNetworkAiService._get(req_data, 'taskId', 'task_id')
        finding_ids = WeakNetworkAiService._get(req_data, 'findingIds', 'finding_ids') or []
        if not task_id or not finding_ids:
            return {}, 'taskId、findingIds 为必传参数'
        if isinstance(finding_ids, str):
            finding_ids = [x.strip() for x in finding_ids.split(',') if x.strip()]
        for fid in finding_ids:
            finding = WeakNetworkAiDao.get_by_id(session, WeakNetworkAiFinding, fid)
            if not finding or int(finding.task_id) != int(task_id):
                continue
            if finding.status == 'confirmed':
                continue
            WeakNetworkAiDao.update_by_id(session, WeakNetworkAiFinding, fid, {'status': 'dismissed'})
        return WeakNetworkAiService.detail(session, task_id)

    @staticmethod
    def confirm_to_bug(session, req_data, user_id=None):
        task_id = WeakNetworkAiService._get(req_data, 'taskId', 'task_id')
        finding_ids = WeakNetworkAiService._get(req_data, 'findingIds', 'finding_ids') or []
        append_ai = WeakNetworkAiService._get(req_data, 'appendAiObservation', 'append_ai_observation')
        if append_ai is None:
            append_ai = True
        else:
            append_ai = append_ai in (True, 1, '1', 'true', 'True')
        if not task_id or not finding_ids:
            return {}, 'taskId、findingIds 为必传参数'
        if isinstance(finding_ids, str):
            finding_ids = [x.strip() for x in finding_ids.split(',') if x.strip()]
        task = WeakNetworkAiDao.get_by_id(session, WeakNetworkAiTask, task_id)
        if not task:
            return {}, '未查询到任务'
        if not task.product_id:
            return {}, '任务缺少 productId，无法创建 Bug'
        created = []
        for fid in finding_ids:
            finding = WeakNetworkAiDao.get_by_id(session, WeakNetworkAiFinding, fid)
            if not finding or int(finding.task_id) != int(task_id):
                continue
            if finding.linked_bug_id:
                created.append({'findingId': finding.id, 'bugId': finding.linked_bug_id, 'skipped': True})
                continue
            if finding.status == 'dismissed':
                continue
            cp = WeakNetworkAiDao.get_by_id(session, WeakNetworkAiCheckpoint, finding.checkpoint_id) if finding.checkpoint_id else None
            profile_label = (cp.profile_preset if cp else '') or ''
            description = (finding.detail or '').strip() or finding.title
            description = '【弱网AI任务 {}】\n画像: {}\n期望: {}\n现象/观察:\n{}'.format(
                task.task_no,
                profile_label,
                (cp.expect_text if cp else '') or '',
                description,
            )
            if append_ai:
                description += '\n\n【AI观察（仅供参考）】\n{}'.format(
                    (finding.ai_payload or {}).get('observation') or finding.detail or ''
                )
            bug_key = BugService.generate_bug_key(session)
            bug_id, err = BugService.create(session, Bug, {
                'bug_key': bug_key,
                'title': finding.title[:200],
                'description': description[:4000],
                'bug_type': 1,
                'severity': 2,
                'priority': 2,
                'status': 0,
                'reporter_id': user_id,
                'product_id': task.product_id,
                'project_id': task.project_id,
                'environment': 'weak_network',
                'steps': (cp.expect_text if cp else '') or '',
                'attachments': [],
                'is_delete': 0,
            })
            if err:
                return {}, '建 Bug 失败：{}'.format(err)
            WeakNetworkAiDao.update_by_id(session, WeakNetworkAiFinding, finding.id, {
                'linked_bug_id': bug_id,
                'status': 'confirmed',
            })
            created.append({'findingId': finding.id, 'bugId': bug_id, 'bugKey': bug_key})
        detail, _ = WeakNetworkAiService.detail(session, task_id)
        return {'created': created, 'detail': detail}, ''

    @staticmethod
    def _ai_orchestrate(brief):
        try:
            from ..service.aiService import AIService
            system = (
                '你是移动端弱网测试编排助手。只输出 JSON，不要 markdown。'
                '格式: {"profiles":[{"presetCode":"subway|elevator|poor_wifi","reason":"..."}],'
                '"checkpoints":[{"title":"...","expect":"...","presetCode":"subway"}]}。'
                'profiles 最多3个；checkpoints 3到8条。不要输出网络数值。'
            )
            prompt = '请为以下功能设计弱网检查点：\n{}'.format(brief[:3000])
            text, err = AIService.chat_plain(prompt, system_prompt=system, max_tokens=1200, read_timeout=20)
            if err or not text:
                return None, 'ai'
            data = WeakNetworkAiService._extract_json(text)
            if not data:
                return None, 'ai'
            return data, 'ai'
        except Exception as exc:
            logger.warning('weak network ai orchestrate failed: %s', exc)
            return None, 'ai'

    @staticmethod
    def _ai_judge(task, checkpoints, evidence):
        try:
            from ..service.aiService import AIService
            ev_lines = []
            for e in evidence:
                ev_lines.append('- checkpointId={} note={} file={}'.format(
                    e.checkpoint_id or '', (e.note or '')[:200], e.file_path or ''
                ))
            cp_lines = []
            for c in checkpoints:
                cp_lines.append('- id={} title={} expect={} preset={}'.format(
                    c.id, c.title, (c.expect_text or '')[:120], c.profile_preset or ''
                ))
            system = (
                '你是弱网测试结果判定助手。只输出 JSON 数组：'
                '[{"checkpointId":1,"verdict":"acceptable|suspect|insufficient","observation":"...","confidence":0.0}]。'
                '无备注且无截图时优先 insufficient。不要臆造未描述的画面。不要建议建 Bug。'
            )
            prompt = '任务:{}\nbrief:{}\n检查点:\n{}\n证据:\n{}'.format(
                task.title, (task.brief or '')[:1500], '\n'.join(cp_lines), '\n'.join(ev_lines) or '(无)'
            )
            text, err = AIService.chat_plain(prompt, system_prompt=system, max_tokens=1500, read_timeout=20)
            if err or not text:
                return None
            data = WeakNetworkAiService._extract_json(text)
            if isinstance(data, dict) and 'items' in data:
                data = data['items']
            if not isinstance(data, list):
                return None
            return data
        except Exception as exc:
            logger.warning('weak network ai judge failed: %s', exc)
            return None

    @staticmethod
    def _fallback_orchestrate(brief):
        text = brief or ''
        profiles = [
            {'presetCode': 'subway', 'reason': '通勤弱网常见'},
            {'presetCode': 'poor_wifi', 'reason': '低带宽抖动'},
        ]
        if any(k in text for k in ('支付', '上传', '登录', '断网', '重连', '电梯')):
            profiles.append({'presetCode': 'elevator', 'reason': '短时断连恢复'})
        checkpoints = [
            {'title': '弱网下首屏/关键页可出内容或明确加载态', 'expect': '不应长时间白屏无提示', 'presetCode': 'subway'},
            {'title': '弱网下核心按钮可点击且有反馈', 'expect': '点击后有 loading 或错误提示', 'presetCode': 'subway'},
            {'title': '差网下列表/详情加载失败有可读提示', 'expect': '失败可重试，文案可读', 'presetCode': 'poor_wifi'},
            {'title': '网络恢复后可继续业务或刷新成功', 'expect': '恢复后状态不丢或可恢复', 'presetCode': 'elevator'},
        ]
        return {'profiles': profiles[:3], 'checkpoints': checkpoints}

    @staticmethod
    def _fallback_judge(checkpoints, evidence):
        by_cp = {}
        for e in evidence:
            key = e.checkpoint_id or 0
            by_cp.setdefault(key, []).append(e)
        results = []
        for c in checkpoints:
            notes = by_cp.get(c.id, []) + by_cp.get(0, [])
            note_text = ' '.join([(x.note or '') for x in notes]).lower()
            has_file = any(x.file_path for x in notes)
            if not notes and not has_file:
                verdict, obs = 'insufficient', '无备注无截图，证据不足'
            elif any(k in note_text for k in ('白屏', '卡死', '无响应', '失败', '超时', '崩溃', '转圈')):
                verdict, obs = 'suspect', notes[0].note if notes else '用户备注显示异常'
            else:
                verdict, obs = 'acceptable', '有证据且备注未描述阻断性问题（规则兜底）'
            results.append({
                'checkpointId': c.id,
                'verdict': verdict,
                'observation': obs,
                'confidence': 0.4,
            })
        return results

    @staticmethod
    def _extract_json(text):
        if not text:
            return None
        text = text.strip()
        try:
            return json.loads(text)
        except Exception:
            pass
        m = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
        if not m:
            return None
        try:
            return json.loads(m.group(1))
        except Exception:
            return None

    @staticmethod
    def _next_task_no(session):
        stamp = datetime.now().strftime('%Y%m%d%H%M%S')
        prefix = 'WA{}'.format(stamp)
        count = session.query(WeakNetworkAiTask).filter(
            WeakNetworkAiTask.task_no.like(prefix + '%')
        ).count()
        return '{}{:02d}'.format(prefix, (count % 100) + 1)

    @staticmethod
    def _task_brief(task):
        data = task.to_dict() if hasattr(task, 'to_dict') else {}
        return {
            'taskId': task.id,
            'taskNo': task.task_no,
            'title': task.title,
            'brief': task.brief,
            'productId': task.product_id,
            'productName': task.product_name,
            'projectId': task.project_id,
            'projectName': task.project_name,
            'status': task.status,
            'recommendedProfiles': task.recommended_profiles or [],
            'selectedProfileIds': task.selected_profile_ids or [],
            'weakNetworkSessionIds': task.weak_network_session_ids or [],
            'createdBy': task.created_by,
            'createdTime': data.get('created_time') or data.get('createdTime'),
        }

    @staticmethod
    def _checkpoint_dict(cp):
        return {
            'checkpointId': cp.id,
            'taskId': cp.task_id,
            'sortNo': cp.sort_no,
            'title': cp.title,
            'expect': cp.expect_text,
            'profilePreset': cp.profile_preset,
            'status': cp.status,
            'lastVerdict': cp.last_verdict,
            'lastObservation': cp.last_observation,
        }

    @staticmethod
    def _evidence_dict(e):
        return {
            'evidenceId': e.id,
            'taskId': e.task_id,
            'checkpointId': e.checkpoint_id,
            'filePath': e.file_path,
            'note': e.note,
            'mobileExecutionId': e.mobile_execution_id,
        }

    @staticmethod
    def _finding_dict(f):
        return {
            'findingId': f.id,
            'taskId': f.task_id,
            'checkpointId': f.checkpoint_id,
            'title': f.title,
            'detail': f.detail,
            'status': f.status,
            'linkedBugId': f.linked_bug_id,
            'aiPayload': f.ai_payload or {},
        }

    @staticmethod
    def _to_int_or_none(value):
        if value in (None, ''):
            return None
        try:
            return int(value)
        except Exception:
            return None

    @staticmethod
    def _get(data, *keys):
        if not data:
            return None
        for k in keys:
            if k in data and data.get(k) is not None:
                return data.get(k)
        return None
