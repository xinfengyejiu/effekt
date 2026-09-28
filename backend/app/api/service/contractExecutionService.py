# encoding: UTF-8
"""契约套件执行：真实请求 + Schema Diff + 通知。"""
import json
import logging
import re
import time
import uuid
from datetime import datetime
from urllib.parse import urljoin

import requests

from app.api.dao.contractDao import ContractDao
from app.api.service.contractDiffService import ContractDiffService
from app.api.service.contractNotifyService import ContractNotifyService
from app.api.service.contractAiService import ContractAiService

logger = logging.getLogger(__name__)

RESPONSE_EXCERPT_LIMIT = 8000


class ContractExecutionService(object):

    @staticmethod
    def trigger_suite_run(db, suite_id, trigger_type='manual', user_id=None):
        suite = ContractDao.get_suite(db, suite_id)
        if not suite:
            return None, '套件不存在'
        items = ContractDao.list_items(db, suite_id, enabled_only=True)
        if not items:
            return None, '套件没有启用的接口项'

        run_no = 'CTR{}{}'.format(datetime.now().strftime('%Y%m%d%H%M%S'), uuid.uuid4().hex[:6].upper())
        run = ContractDao.create_run(db, {
            'run_no': run_no,
            'suite_id': suite.id,
            'project_id': suite.project_id,
            'trigger_type': trigger_type or 'manual',
            'status': 1,
            'total_count': len(items),
            'trigger_by': user_id,
            'start_time': datetime.now(),
        })
        db.commit()

        pass_count = drift_count = error_count = breaking_count = 0
        top_findings = []
        t0 = time.time()

        for item in items:
            item_result = ContractExecutionService._execute_item(db, suite, run, item)
            status = item_result.get('result_status')
            if status == 'pass':
                pass_count += 1
            elif status == 'drift':
                drift_count += 1
            else:
                error_count += 1
            breaking_count += int(item_result.get('breaking_count') or 0)
            for f in item_result.get('breaking_findings') or []:
                if len(top_findings) < 5:
                    top_findings.append(f)

        duration_ms = int((time.time() - t0) * 1000)
        ai_summaries = []
        for item_row in ContractDao.list_run_items(db, run.id):
            analysis = item_row.ai_analysis if isinstance(getattr(item_row, 'ai_analysis', None), dict) else None
            if analysis and analysis.get('summary'):
                ai_summaries.append({
                    'interface': item_row.name or item_row.path,
                    'summary': analysis.get('summary'),
                    'category': analysis.get('category'),
                    'action': analysis.get('action'),
                })
        ContractDao.update_run(db, run.id, {
            'status': 2,
            'pass_count': pass_count,
            'drift_count': drift_count,
            'error_count': error_count,
            'breaking_count': breaking_count,
            'end_time': datetime.now(),
            'duration_ms': duration_ms,
            'summary': {
                'suite_name': suite.name,
                'base_url': suite.base_url,
                'top_findings': top_findings[:3],
                'ai_summaries': ai_summaries[:5],
            },
        })
        suite.last_run_at = datetime.now()
        db.commit()

        notify_status = 0
        if breaking_count > 0 and suite.notify_webhook:
            ok, _ = ContractNotifyService.send_breaking_summary(
                suite.notify_type,
                suite.notify_webhook,
                {
                    'suite_name': suite.name,
                    'run_no': run_no,
                    'breaking_count': breaking_count,
                    'drift_count': drift_count,
                    'error_count': error_count,
                    'top_findings': top_findings,
                    'ai_summaries': ai_summaries[:3],
                },
            )
            notify_status = 1 if ok else 2
            ContractDao.update_run(db, run.id, {'notify_status': notify_status})
            db.commit()

        return ContractExecutionService.get_run_detail(db, run.id), ''

    @staticmethod
    def _execute_item(db, suite, run, item):
        method = (item.method or 'GET').upper()
        path = ContractExecutionService._render_path(item.path, item.path_params or {})
        url = urljoin(suite.base_url.rstrip('/') + '/', path.lstrip('/'))
        headers = {}
        if isinstance(suite.default_headers, dict):
            headers.update(suite.default_headers)
        timeout = int(item.timeout_seconds or 30)
        query = item.query_params if isinstance(item.query_params, dict) else {}
        body = item.body_template

        start = time.time()
        http_status = None
        excerpt = ''
        error_message = None
        actual_json = None
        result_status = 'error'
        max_severity = None
        breaking_findings = []
        findings = []

        try:
            resp = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=query or None,
                json=body if body is not None and method in ('POST', 'PUT', 'PATCH') else None,
                timeout=timeout,
            )
            http_status = resp.status_code
            text = resp.text or ''
            excerpt = text[:RESPONSE_EXCERPT_LIMIT]
            if http_status < 200 or http_status >= 300:
                error_message = 'HTTP {}'.format(http_status)
            else:
                try:
                    actual_json = resp.json()
                except Exception:
                    error_message = '响应不是合法 JSON'
                    actual_json = None

            if error_message is None and actual_json is not None:
                schema = item.response_schema or {}
                if isinstance(schema, str):
                    try:
                        schema = json.loads(schema)
                    except Exception:
                        schema = {}
                findings = ContractDiffService.compare(schema, actual_json)
                max_severity = ContractDiffService.max_severity(findings)
                if findings:
                    result_status = 'drift'
                else:
                    result_status = 'pass'
        except Exception as e:
            error_message = str(e)
            result_status = 'error'
            excerpt = ''

        duration_ms = int((time.time() - start) * 1000)
        ai_analysis = None
        if result_status in ('drift', 'error'):
            # 执行路径默认用规则 stub，保证不拖慢套件；详情页可点「AI 重新分析」走真实 LLM
            ai_analysis = ContractAiService.build_stub_analysis(
                findings, result_status=result_status,
                max_severity=max_severity, error_message=error_message,
            )

        run_item = ContractDao.create_run_item(db, {
            'run_id': run.id,
            'suite_item_id': item.id,
            'name': item.name,
            'method': method,
            'path': path,
            'http_status': http_status,
            'result_status': result_status,
            'max_severity': max_severity,
            'duration_ms': duration_ms,
            'response_excerpt': excerpt,
            'error_message': error_message,
            'ai_analysis': ai_analysis,
        })

        for f in findings:
            ContractDao.create_finding(db, {
                'run_id': run.id,
                'run_item_id': run_item.id,
                'json_path': f.get('json_path') or '$',
                'severity': f.get('severity') or 'info',
                'drift_type': f.get('drift_type') or 'unknown',
                'expected': f.get('expected'),
                'actual': f.get('actual'),
                'message': f.get('message') or '',
            })
            if f.get('severity') == 'breaking':
                breaking_findings.append({
                    'json_path': f.get('json_path'),
                    'severity': f.get('severity'),
                    'message': f.get('message'),
                    'interface': item.name,
                })

        db.commit()
        return {
            'result_status': result_status,
            'breaking_count': len(breaking_findings),
            'breaking_findings': breaking_findings,
        }

    @staticmethod
    def _render_path(path_template, params):
        path = path_template or '/'
        params = params or {}

        def repl(match):
            key = match.group(1)
            if key in params:
                return str(params[key])
            return match.group(0)

        path = re.sub(r'\{([^}/]+)\}', repl, path)
        path = re.sub(r':([A-Za-z0-9_]+)', lambda m: str(params.get(m.group(1), m.group(0))), path)
        return path

    @staticmethod
    def list_runs(db, params):
        items, total = ContractDao.list_runs(
            db,
            project_id=params.get('project_id'),
            suite_id=params.get('suite_id'),
            page_no=params.get('page_no', 1),
            page_size=params.get('page_size', 20),
        )
        rows = []
        for run in items:
            row = run.to_dict()
            suite = ContractDao.get_suite(db, run.suite_id)
            row['suite_name'] = suite.name if suite else None
            rows.append(row)
        return {'items': rows, 'total': total}

    @staticmethod
    def get_run_detail(db, run_id):
        run = ContractDao.get_run(db, run_id)
        if not run:
            return None
        data = run.to_dict()
        suite = ContractDao.get_suite(db, run.suite_id)
        data['suite_name'] = suite.name if suite else None
        data['base_url'] = suite.base_url if suite else None
        items = []
        for item in ContractDao.list_run_items(db, run_id):
            row = item.to_dict()
            row['findings'] = [f.to_dict() for f in ContractDao.list_findings(db, run_id, item.id)]
            items.append(row)
        data['items'] = items
        return data

    @staticmethod
    def analyze_run_item(db, run_item_id, use_llm=True):
        """对单个执行项做 AI 分析并写回。"""
        from app.api.model.contractModel import ContractRunItem

        item = db.query(ContractRunItem).filter(ContractRunItem.id == int(run_item_id)).first()
        if not item:
            return None, '执行项不存在'
        findings = [f.to_dict() for f in ContractDao.list_findings(db, item.run_id, item.id)]
        schema = {}
        if item.suite_item_id:
            suite_item = ContractDao.get_item(db, item.suite_item_id) if hasattr(ContractDao, 'get_item') else None
            if suite_item is None:
                from app.api.model.contractModel import ContractSuiteItem
                suite_item = db.query(ContractSuiteItem).filter(
                    ContractSuiteItem.id == int(item.suite_item_id)
                ).first()
            if suite_item:
                schema = suite_item.response_schema or {}

        analysis = None
        err = ''
        if use_llm:
            analysis, err = ContractAiService.analyze_drift({
                'name': item.name,
                'method': item.method,
                'path': item.path,
                'result_status': item.result_status,
                'max_severity': item.max_severity,
                'findings': findings,
                'response_schema': schema,
                'response_excerpt': item.response_excerpt,
                'error_message': item.error_message,
            })
        if not analysis:
            analysis = ContractAiService.build_stub_analysis(
                findings,
                result_status=item.result_status,
                max_severity=item.max_severity,
                error_message=item.error_message or err,
            )
            if err:
                analysis['ai_error'] = err
        item.ai_analysis = analysis
        db.commit()
        return {'run_item_id': item.id, 'ai_analysis': analysis}, ''
