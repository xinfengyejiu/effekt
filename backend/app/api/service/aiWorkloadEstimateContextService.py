# encoding: UTF-8
import json
import re
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func

from ..model.bugModel import Bug
from ..model.caseModel import Module
from ..model.documentSourceModel import DocumentSource


class AiWorkloadEstimateContextService(object):
    RISK_KEYWORDS = [
        '权限', '角色', '审批', '支付', '退款', '状态', '流程', '批量', '导入', '导出',
        '消息', '通知', '跨端', '库存', '回滚', '接口', '第三方', '兼容', '异常', '配置'
    ]

    @staticmethod
    def build_context(session, estimate):
        document_ids = AiWorkloadEstimateContextService._normalize_ids(estimate.document_ids)
        if not document_ids:
            raise ValueError('至少选择1个本次PRD文档')
        current_prds = AiWorkloadEstimateContextService._load_current_prds(session, estimate, document_ids)
        reference_documents = AiWorkloadEstimateContextService._load_reference_documents(session, estimate, document_ids)
        raw_text = AiWorkloadEstimateContextService._compact_text([item.get('content') for item in current_prds])
        reference_summary = AiWorkloadEstimateContextService._build_reference_summary(reference_documents)
        bug_summary = AiWorkloadEstimateContextService._build_bug_summary(session, estimate)
        context = {
            'currentPrds': current_prds,
            'referenceDocuments': reference_documents,
            'referenceSummary': reference_summary,
            'bugSummary': bug_summary,
            'rawText': raw_text,
            'statistics': {
                'currentPrdCount': len(current_prds),
                'rawTextLength': len(raw_text),
                'referenceDocumentCount': len(reference_documents),
                'bugCount': bug_summary.get('totalCount', 0)
            }
        }
        return AiWorkloadEstimateContextService._json_safe(context), ''

    @staticmethod
    def _load_current_prds(session, estimate, document_ids):
        rows = session.query(DocumentSource).filter(
            DocumentSource.id.in_([int(item) for item in document_ids]),
            DocumentSource.product_id == int(estimate.product_id),
            DocumentSource.project_id == int(estimate.project_id),
            DocumentSource.is_delete == 0
        ).order_by(DocumentSource.id.asc()).all()
        found_ids = {int(item.id) for item in rows}
        missing_ids = [str(item) for item in document_ids if int(item) not in found_ids]
        if missing_ids:
            raise ValueError(f'本次PRD文档不存在或不属于当前产品项目：{",".join(missing_ids)}')
        result = []
        for item in rows:
            content = (item.content or '').strip()
            if not content:
                raise ValueError('本次PRD未解析，请先在需求问答中解析文档')
            result.append({
                'id': item.id,
                'source': item.source,
                'type': item.type,
                'version': item.version,
                'status': item.status,
                'content': content,
                'contentLength': len(content),
                'createdBy': item.created_by,
                'createdTime': item.created_time
            })
        return result

    @staticmethod
    def _load_reference_documents(session, estimate, current_document_ids):
        rows = session.query(DocumentSource).filter(
            DocumentSource.product_id == int(estimate.product_id),
            DocumentSource.is_delete == 0,
            DocumentSource.id.notin_([int(item) for item in current_document_ids])
        ).order_by(DocumentSource.created_time.desc(), DocumentSource.id.desc()).limit(10).all()
        result = []
        for item in rows:
            content = (item.content or '').strip()
            if not content:
                continue
            result.append({
                'id': item.id,
                'source': item.source,
                'type': item.type,
                'version': item.version,
                'status': item.status,
                'summary': AiWorkloadEstimateContextService._snippet(content, 500),
                'contentLength': len(content),
                'createdTime': item.created_time
            })
        return result

    @staticmethod
    def _build_reference_summary(reference_documents):
        joined = '\n'.join([item.get('summary') or '' for item in reference_documents])
        risk_keywords = [keyword for keyword in AiWorkloadEstimateContextService.RISK_KEYWORDS if keyword in joined]
        similar_modules = AiWorkloadEstimateContextService._extract_candidate_modules(joined)
        return {
            'documentCount': len(reference_documents),
            'riskKeywords': risk_keywords[:20],
            'similarModules': similar_modules[:20],
            'note': '历史文档仅用于复杂度参考，不作为本次范围'
        }

    @staticmethod
    def _build_bug_summary(session, estimate):
        query = session.query(Bug).filter(
            Bug.product_id == int(estimate.product_id),
            Bug.project_id == int(estimate.project_id),
            Bug.is_delete == 0
        )
        total_count = query.count()
        if not total_count:
            return {
                'totalCount': 0,
                'criticalCount': 0,
                'seriousCount': 0,
                'highSeverityCount': 0,
                'openCount': 0,
                'highSeverityRate': 0,
                'openRate': 0,
                'riskLevel': 'low',
                'topModules': [],
                'note': '当前产品项目暂无历史缺陷数据，复杂度主要参考PRD和历史文档'
            }

        critical_count = query.filter(Bug.severity == 1).count()
        serious_count = query.filter(Bug.severity == 2).count()
        high_severity_count = critical_count + serious_count
        open_count = query.filter(Bug.status.in_([0, 1, 2])).count()
        high_severity_rate = round(high_severity_count / float(total_count), 4)
        open_rate = round(open_count / float(total_count), 4)
        if total_count >= 50 or high_severity_rate >= 0.3 or (high_severity_count >= 8 and open_rate >= 0.35):
            risk_level = 'high'
        elif total_count >= 15 or high_severity_rate >= 0.15 or open_rate >= 0.35:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        module_rows = session.query(
            Module.name,
            func.count(Bug.id)
        ).outerjoin(Module, Bug.module_id == Module.id).filter(
            Bug.product_id == int(estimate.product_id),
            Bug.project_id == int(estimate.project_id),
            Bug.is_delete == 0
        ).group_by(Module.name).order_by(func.count(Bug.id).desc()).limit(8).all()
        top_modules = [{'moduleName': name or '未分类', 'bugCount': count} for name, count in module_rows]
        return {
            'totalCount': total_count,
            'criticalCount': critical_count,
            'seriousCount': serious_count,
            'highSeverityCount': high_severity_count,
            'openCount': open_count,
            'highSeverityRate': high_severity_rate,
            'openRate': open_rate,
            'riskLevel': risk_level,
            'topModules': top_modules,
            'note': '缺陷数据用于复杂度和执行风险校准，不直接扩大本次PRD范围'
        }

    @staticmethod
    def _extract_candidate_modules(text):
        if not text:
            return []
        candidates = []
        patterns = [
            r'([\u4e00-\u9fa5A-Za-z0-9]{2,20})(?:模块|管理|中心|配置|设置)',
            r'(?:模块|功能)[:：]\s*([\u4e00-\u9fa5A-Za-z0-9]{2,30})'
        ]
        for pattern in patterns:
            for match in re.findall(pattern, text):
                name = str(match).strip()
                if name and name not in candidates:
                    candidates.append(name)
                if len(candidates) >= 20:
                    return candidates
        return candidates

    @staticmethod
    def _normalize_ids(value):
        if value in (None, ''):
            return []
        if isinstance(value, list):
            raw_items = value
        elif isinstance(value, tuple):
            raw_items = list(value)
        elif isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            try:
                parsed = json.loads(text)
                raw_items = parsed if isinstance(parsed, list) else [parsed]
            except Exception:
                raw_items = [item for item in re.split(r'[,，]', text) if item]
        else:
            raw_items = [value]
        result = []
        for item in raw_items:
            if item in (None, ''):
                continue
            item_id = int(item)
            if item_id not in result:
                result.append(item_id)
        return result

    @staticmethod
    def _compact_text(values):
        return '\n\n'.join([str(value).strip() for value in values if value not in (None, '') and str(value).strip()])

    @staticmethod
    def _snippet(content, size=500):
        text = re.sub(r'\s+', ' ', content or '').strip()
        if len(text) <= size:
            return text
        return text[:size] + '...'

    @staticmethod
    def _json_safe(data):
        return json.loads(json.dumps(data, ensure_ascii=False, default=AiWorkloadEstimateContextService._json_default))

    @staticmethod
    def _json_default(value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(value, date):
            return value.strftime('%Y-%m-%d')
        if isinstance(value, Decimal):
            return float(value)
        return str(value)
