# encoding: UTF-8
"""执行失败根因归因（规则优先 MVP）。"""
from __future__ import print_function

import logging
import re
from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy import desc

from app.api.model.automationModel import AutoExecution, AutoExecutionCase
from app.api.model.inspectionModel import InspectionExecution, InspectionExecutionItem

logger = logging.getLogger(__name__)

FAILURE_CLASSES = ('env', 'case', 'code', 'data', 'unknown')

_ENV_PATTERNS = [
    r'timeout', r'timed?\s*out', r'connection\s*(refused|reset|error)',
    r'connect(ion)?\s*error', r'network', r'dns', r'errno\s*111',
    r'无法连接', r'连接超时', r'连接被拒绝', r'网络', r'服务不可用',
    r'502', r'503', r'504', r'ECONNREFUSED', r'ETIMEDOUT',
]
_DATA_PATTERNS = [
    r'duplicate\s*key', r'unique\s*constraint', r'foreign\s*key',
    r'not\s*found.*data', r'无数据', r'数据不存在', r'脏数据',
    r'constraint', r'integrity',
]
_CASE_PATTERNS = [
    r'assertion', r'assert\s', r'expected', r'期望', r'断言',
    r'element\s*not\s*(found|visible)', r'找不到元素', r'selector',
    r'locator', r'NoSuchElement',
]
_CODE_PATTERNS = [
    r'Traceback', r'NullPointer', r'TypeError', r'AttributeError',
    r'500\b', r'Internal\s*Server\s*Error', r'空指针', r'空引用',
    r'IndexError', r'KeyError', r'SyntaxError',
]


class FailureAttributionService(object):

    @staticmethod
    def classify_text(error_message='', result_message='', stack_trace='', status=None):
        blob = ' '.join([
            str(error_message or ''),
            str(result_message or ''),
            str(stack_trace or '')[:2000],
        ])
        if not blob.strip():
            return 'unknown', '无错误文本，无法归因', []

        evidence = []
        lower = blob.lower()

        def _hit(patterns, label):
            for p in patterns:
                if re.search(p, blob, re.I) or re.search(p, lower, re.I):
                    evidence.append({'rule': p, 'class': label})
                    return True
            return False

        if _hit(_ENV_PATTERNS, 'env'):
            return 'env', '命中超时/连接/网关类规则，偏向环境或依赖不可用', evidence[:3]
        if _hit(_DATA_PATTERNS, 'data'):
            return 'data', '命中约束/数据缺失类规则，偏向测试数据问题', evidence[:3]
        if _hit(_CASE_PATTERNS, 'case'):
            return 'case', '命中断言/定位器类规则，偏向用例本身过时或过严', evidence[:3]
        if _hit(_CODE_PATTERNS, 'code'):
            return 'code', '命中服务端异常/堆栈类规则，偏向代码缺陷', evidence[:3]
        return 'unknown', '未命中明确规则，需人工查看证据', evidence

    @staticmethod
    def classify_and_store_auto_case(session, execution_case):
        if not execution_case:
            return None
        # 仅失败/阻塞/异常
        if int(getattr(execution_case, 'status', 0) or 0) not in (3, 4, 6):
            return None
        failure_class, reason, evidence = FailureAttributionService.classify_text(
            execution_case.error_message,
            execution_case.result_message,
            execution_case.stack_trace,
            execution_case.status,
        )
        ext = dict(execution_case.ext or {})
        ext['failureClass'] = failure_class
        ext['failureReason'] = reason
        ext['failureEvidence'] = evidence
        ext['failureClassAt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        execution_case.ext = ext
        session.flush()
        return failure_class

    @staticmethod
    def classify_and_store_inspection_item(session, item):
        if not item:
            return None
        if int(getattr(item, 'status', 0) or 0) not in (3, 4):
            return None
        result = item.result if isinstance(item.result, dict) else {}
        failure_class, reason, evidence = FailureAttributionService.classify_text(
            item.error_message,
            str(result.get('message') or result.get('summary') or ''),
            str(result.get('stack') or result.get('detail') or ''),
            item.status,
        )
        merged = dict(result or {})
        merged['failureClass'] = failure_class
        merged['failureReason'] = reason
        merged['failureEvidence'] = evidence
        item.result = merged
        session.flush()
        return failure_class

    @staticmethod
    def summary(session, project_id, hours=24):
        if not project_id:
            return None, 'projectId 为必传参数'
        project_id = int(project_id)
        hours = max(1, min(int(hours or 24), 24 * 14))
        since = datetime.now() - timedelta(hours=hours)

        counter = Counter()
        samples = []

        # 自动化失败明细
        auto_rows = session.query(AutoExecutionCase, AutoExecution).join(
            AutoExecution, AutoExecution.id == AutoExecutionCase.execution_id
        ).filter(
            AutoExecution.project_id == project_id,
            AutoExecutionCase.status.in_([3, 4, 6]),
            AutoExecutionCase.updated_time >= since,
        ).order_by(desc(AutoExecutionCase.updated_time)).limit(200).all()

        for case_row, exe in auto_rows:
            ext = case_row.ext if isinstance(case_row.ext, dict) else {}
            fc = ext.get('failureClass')
            if not fc:
                fc = FailureAttributionService.classify_and_store_auto_case(session, case_row) or 'unknown'
                ext = case_row.ext if isinstance(case_row.ext, dict) else {}
            counter[fc] += 1
            if len(samples) < 20:
                samples.append({
                    'source': 'automation',
                    'executionId': exe.id,
                    'caseId': case_row.case_id,
                    'caseKey': case_row.case_key,
                    'title': case_row.case_title,
                    'failureClass': fc,
                    'failureReason': ext.get('failureReason'),
                    'errorMessage': (case_row.error_message or case_row.result_message or '')[:200],
                })

        # 巡检失败项
        insp_rows = session.query(InspectionExecutionItem, InspectionExecution).join(
            InspectionExecution, InspectionExecution.id == InspectionExecutionItem.execution_id
        ).filter(
            InspectionExecution.project_id == project_id,
            InspectionExecutionItem.status.in_([3, 4]),
            InspectionExecutionItem.end_time >= since,
        ).order_by(desc(InspectionExecutionItem.id)).limit(200).all()

        for item, exe in insp_rows:
            result = item.result if isinstance(item.result, dict) else {}
            fc = result.get('failureClass')
            if not fc:
                fc = FailureAttributionService.classify_and_store_inspection_item(session, item) or 'unknown'
                result = item.result if isinstance(item.result, dict) else {}
            counter[fc] += 1
            if len(samples) < 30:
                samples.append({
                    'source': 'inspection',
                    'executionId': exe.id,
                    'itemId': item.item_id,
                    'failureClass': fc,
                    'failureReason': result.get('failureReason'),
                    'errorMessage': (item.error_message or '')[:200],
                })

        try:
            session.commit()
        except Exception:
            session.rollback()

        total = sum(counter.values())
        dist = [
            {
                'failureClass': k,
                'count': v,
                'ratio': round(float(v) / total, 4) if total else 0,
            }
            for k, v in counter.most_common()
        ]
        top = dist[0]['failureClass'] if dist else 'unknown'
        label_map = {
            'env': '环境/依赖',
            'case': '用例',
            'code': '代码',
            'data': '数据',
            'unknown': '未知',
        }
        return {
            'projectId': project_id,
            'hours': hours,
            'totalFailures': total,
            'distribution': dist,
            'topClass': top,
            'topClassLabel': label_map.get(top, top),
            'samples': samples[:15],
            'note': '规则优先归因；未命中规则记为 unknown，需人工复核',
        }, ''
