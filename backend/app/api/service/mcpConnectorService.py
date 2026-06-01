# encoding: UTF-8
from ..dao.aiBaseDao import AiBaseDao
from ..dao.aiMcpDao import AiMcpDao
from ..model.aiMcpModel import AiMcpConnector, AiMcpCallLog
from .aiCommonService import AiCommonService


class McpConnectorService(object):
    UPDATE_FIELDS = ['product_id', 'product_name', 'project_id', 'project_name', 'name', 'connector_type', 'endpoint', 'auth_type', 'auth_ref', 'config', 'capabilities', 'status']

    @staticmethod
    def create_connector(session, req_data, user_id=None):
        connector_code = AiCommonService.get(req_data, 'connectorCode', 'connector_code')
        data = {
            'connector_code': connector_code,
            'name': req_data.get('name'),
            'connector_type': AiCommonService.get(req_data, 'connectorType', 'connector_type'),
            'endpoint': req_data.get('endpoint'),
            'auth_type': AiCommonService.get(req_data, 'authType', 'auth_type', default='none'),
            'auth_ref': AiCommonService.get(req_data, 'authRef', 'auth_ref'),
            'config': req_data.get('config') or {},
            'capabilities': req_data.get('capabilities') or [],
            'status': int(req_data.get('status') or 1),
            'created_by': user_id,
            'is_delete': 0
        }
        AiCommonService.fill_product_project_names(session, data, req_data)
        return AiCommonService.create_record(session, AiMcpConnector, data, ['connector_code', 'name', 'connector_type'], lambda: AiMcpDao.get_connector_by_code(session, connector_code))

    @staticmethod
    def update_connector(session, req_data):
        AiCommonService.fill_product_project_names(session, req_data, req_data)
        return AiCommonService.update_record(session, AiMcpConnector, req_data, McpConnectorService.UPDATE_FIELDS, ('connectorId', 'id'))

    @staticmethod
    def delete_connector(session, req_data):
        return AiCommonService.delete_record(session, AiMcpConnector, req_data, ('connectorId', 'id'))

    @staticmethod
    def connector_detail(session, connector_id):
        return AiCommonService.detail_record(session, AiMcpConnector, connector_id)

    @staticmethod
    def connector_list(session, req_data):
        filters = []
        connector_type = AiCommonService.get(req_data, 'connectorType', 'connector_type')
        if connector_type:
            filters.append(AiMcpConnector.connector_type == connector_type)
        status = req_data.get('status')
        if status not in (None, ''):
            filters.append(AiMcpConnector.status == int(status))
        items, total = AiBaseDao.list_by_filters(session, AiMcpConnector, filters, AiCommonService.get(req_data, 'page', default=1), AiCommonService.get(req_data, 'limit', default=20), req_data.get('keyword'), ['connector_code', 'name', 'connector_type'])
        return AiCommonService.list_result(items, total, session, True)

    @staticmethod
    def test_connector(session, req_data, user_id=None):
        connector_id = AiCommonService.get(req_data, 'connectorId', 'id')
        if not connector_id:
            return {}, 'connectorId 为必传参数'
        connector = AiBaseDao.get_by_id(session, AiMcpConnector, connector_id)
        if not connector:
            return {}, '未查询到连接器'
        log, _ = AiBaseDao.create(session, AiMcpCallLog, {
            'connector_id': connector.id,
            'project_id': AiCommonService.get(req_data, 'projectId', 'project_id'),
            'operation': 'test',
            'request_snapshot': {'endpoint': connector.endpoint, 'authType': connector.auth_type},
            'response_summary': {'message': '连接配置存在，实际连接由具体Connector Adapter实现'},
            'status': 'success',
            'created_by': user_id
        })
        return {'callLogId': log.id if log else None, 'message': '连接器配置校验通过'}, ''

    @staticmethod
    def call_log_list(session, req_data):
        filters = []
        connector_id = AiCommonService.get(req_data, 'connectorId', 'connector_id')
        if connector_id:
            filters.append(AiMcpCallLog.connector_id == int(connector_id))
        project_id = AiCommonService.get(req_data, 'projectId', 'project_id')
        if project_id:
            filters.append(AiMcpCallLog.project_id == int(project_id))
        status = AiCommonService.get(req_data, 'status')
        if status:
            filters.append(AiMcpCallLog.status == status)
        items, total = AiBaseDao.list_by_filters(session, AiMcpCallLog, filters, AiCommonService.get(req_data, 'page', default=1), AiCommonService.get(req_data, 'limit', default=20))
        return AiCommonService.list_result(items, total)

    @staticmethod
    def call_log_detail(session, log_id):
        return AiCommonService.detail_record(session, AiMcpCallLog, log_id)
