# encoding: UTF-8
"""契约套件 CRUD 与契约源预览。"""
import json
import logging

from app.api.dao.contractDao import ContractDao
from app.api.model.mockModel import MockDocument, MockInterface
from app.api.service.mockParserService import MockParserService

logger = logging.getLogger(__name__)


def _parse_schema_field(raw):
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return {}
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                # mock 可能存 {type, properties} 或包在 response 下
                if 'properties' in data or 'type' in data or 'items' in data:
                    return data
                if isinstance(data.get('response'), dict):
                    return data.get('response') or {}
                return data
        except Exception:
            return {}
    return {}


class ContractSuiteService(object):

    @staticmethod
    def list_suites(db, params):
        items, total = ContractDao.list_suites(
            db,
            project_id=params.get('project_id'),
            product_id=params.get('product_id'),
            page_no=params.get('page_no', 1),
            page_size=params.get('page_size', 20),
        )
        result = []
        for suite in items:
            row = suite.to_dict()
            row['item_count'] = len(ContractDao.list_items(db, suite.id))
            result.append(row)
        return {'items': result, 'total': total}

    @staticmethod
    def get_suite_detail(db, suite_id):
        suite = ContractDao.get_suite(db, suite_id)
        if not suite:
            return None
        data = suite.to_dict()
        data['items'] = [i.to_dict() for i in ContractDao.list_items(db, suite_id)]
        return data

    @staticmethod
    def preview_source(db, data):
        """从 mock_document 或 openapi 文本预览可勾选接口。"""
        source_type = data.get('source_type') or 'mock_document'
        interfaces = []

        if source_type == 'mock_document':
            document_id = data.get('mock_document_id') or data.get('document_id')
            if not document_id:
                return None, '缺少 mock_document_id'
            doc = db.query(MockDocument).filter(
                MockDocument.id == int(document_id), MockDocument.is_delete == 0
            ).first()
            if not doc:
                return None, 'Mock 文档不存在'
            rows = db.query(MockInterface).filter(
                MockInterface.document_id == int(document_id),
                MockInterface.is_delete == 0,
            ).order_by(MockInterface.id.asc()).all()
            for row in rows:
                interfaces.append({
                    'mock_interface_id': row.id,
                    'name': row.name,
                    'method': row.method,
                    'path': row.path,
                    'response_schema': _parse_schema_field(row.response_schema),
                    'enabled': 1 if row.status == 1 else 0,
                })
            return {'document_id': doc.id, 'document_name': doc.name, 'interfaces': interfaces}, ''

        if source_type == 'openapi_upload':
            content = data.get('openapi_content') or data.get('content') or ''
            if not content.strip():
                return None, '缺少 openapi_content'
            parsed, issues = MockParserService.parse('openapi', content)
            for item in parsed or []:
                schema = item.get('response') or {}
                if isinstance(schema, str):
                    schema = _parse_schema_field(schema)
                interfaces.append({
                    'mock_interface_id': None,
                    'name': item.get('name') or item.get('path'),
                    'method': (item.get('method') or 'GET').upper(),
                    'path': item.get('path') or '/',
                    'response_schema': schema if isinstance(schema, dict) else {},
                    'enabled': 1,
                })
            return {
                'document_id': None,
                'document_name': 'openapi_upload',
                'interfaces': interfaces,
                'parse_issues': issues or [],
            }, ''

        return None, '不支持的 source_type'

    @staticmethod
    def create_suite(db, data, user_id=None):
        if not data.get('name'):
            return None, '缺少 name'
        if not data.get('project_id'):
            return None, '缺少 project_id'
        if not data.get('product_id'):
            return None, '缺少 product_id'
        if not data.get('base_url'):
            return None, '缺少 base_url'

        values = {
            'product_id': int(data['product_id']),
            'project_id': int(data['project_id']),
            'name': data['name'],
            'description': data.get('description') or '',
            'source_type': data.get('source_type') or 'mock_document',
            'mock_document_id': data.get('mock_document_id'),
            'openapi_content': data.get('openapi_content'),
            'base_url': (data.get('base_url') or '').rstrip('/'),
            'default_headers': data.get('default_headers') or {},
            'notify_type': data.get('notify_type'),
            'notify_webhook': data.get('notify_webhook'),
            'schedule_type': data.get('schedule_type') or 'manual',
            'cron_expression': data.get('cron_expression'),
            'interval_seconds': data.get('interval_seconds'),
            'enabled': int(data.get('enabled', 1)),
            'created_by': user_id,
        }
        suite = ContractDao.create_suite(db, values)
        items = data.get('items') or []
        if items:
            ContractDao.replace_items(db, suite.id, items)
        db.commit()
        ContractSuiteService._reload_schedule(suite)
        return ContractSuiteService.get_suite_detail(db, suite.id), ''

    @staticmethod
    def update_suite(db, suite_id, data):
        suite = ContractDao.get_suite(db, suite_id)
        if not suite:
            return None, '套件不存在'

        allow = {
            'name', 'description', 'source_type', 'mock_document_id', 'openapi_content',
            'base_url', 'default_headers', 'notify_type', 'notify_webhook',
            'schedule_type', 'cron_expression', 'interval_seconds', 'enabled',
            'product_id', 'project_id',
        }
        values = {}
        for key in allow:
            if key in data:
                values[key] = data[key]
        if 'base_url' in values and values['base_url']:
            values['base_url'] = str(values['base_url']).rstrip('/')
        ContractDao.update_suite(db, suite_id, values)
        if 'items' in data:
            ContractDao.replace_items(db, suite_id, data.get('items') or [])
        db.commit()
        suite = ContractDao.get_suite(db, suite_id)
        ContractSuiteService._reload_schedule(suite)
        return ContractSuiteService.get_suite_detail(db, suite_id), ''

    @staticmethod
    def delete_suite(db, suite_id):
        suite = ContractDao.get_suite(db, suite_id)
        if not suite:
            return None, '套件不存在'
        ContractDao.delete_suite(db, suite_id)
        ContractDao.soft_delete_items_by_suite(db, suite_id)
        db.commit()
        ContractSuiteService._remove_schedule(suite_id)
        return {'id': int(suite_id)}, ''

    @staticmethod
    def toggle_suite(db, suite_id):
        suite = ContractDao.get_suite(db, suite_id)
        if not suite:
            return None, '套件不存在'
        suite.enabled = 0 if suite.enabled == 1 else 1
        db.commit()
        ContractSuiteService._reload_schedule(suite)
        return suite.to_dict(), ''

    @staticmethod
    def _reload_schedule(suite):
        try:
            from app.core.contractScheduler import contract_scheduler
            if suite and suite.enabled == 1 and suite.schedule_type in ('cron', 'interval'):
                contract_scheduler.reload_suite(suite)
            elif suite:
                contract_scheduler.remove_suite(suite.id)
        except Exception as e:
            logger.warning('刷新契约调度失败: %s', str(e))

    @staticmethod
    def _remove_schedule(suite_id):
        try:
            from app.core.contractScheduler import contract_scheduler
            contract_scheduler.remove_suite(suite_id)
        except Exception as e:
            logger.warning('移除契约调度失败: %s', str(e))
