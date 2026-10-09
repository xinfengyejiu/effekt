# encoding: UTF-8
from datetime import date, datetime
from decimal import Decimal

from common.sqlSession import SqlSession
from common.getUserInfo import UserInfo
from common.cronRequest import CronRequest

from ..service.updateSqlProjectService import UpdateSqlProjectService
from ..model.updateSqlProjectModel import UpdateSqlProject

from const import EXECUTE_DB_CONFIG, QE_DOMAIN

from logger import logger

"""
创建和更新场景
"""


class UpdateSqlProjectController(object):
    def __init__(self, req_json):
        self.session = SqlSession()
        self.run_env = req_json.get('runEnv')
        self.sql = req_json.get('sql')
        self.sql_id = req_json.get('sqlId')
        self.project = req_json.get('project')
        self.page_num = req_json.get('pageNo')
        self.page_size = req_json.get('pageSize')
        self.remark = req_json.get('remark')
        self.run_group = req_json.get('runGroup')
        self.creator = req_json.get('creator')
        self.qe_domain = QE_DOMAIN

    def close_session(self):
        if self.session:
            self.session.close()

    def create_sql_project(self):
        project = self.project.strip().strip('"') if isinstance(self.project, str) else self.project
        run_env = self.run_env.strip().strip('"') if isinstance(self.run_env, str) else self.run_env
        sql = self.sql.strip().strip('"') if isinstance(self.sql, str) else self.sql
        if not project or not run_env or not sql:
            return 0, 'project、runEnv、sql 为必传参数'
        sql_id = self.sql_id
        if isinstance(sql_id, str):
            sql_id = sql_id.strip().strip('"')
        remark = self.remark.strip() if isinstance(self.remark, str) else self.remark
        remark = remark if remark not in ('', None) else None
        run_group = self.run_group.strip() if isinstance(self.run_group, str) else self.run_group
        run_group = run_group if run_group not in ('', None) else ''
        creator = self.creator.strip() if isinstance(self.creator, str) else self.creator
        creator = creator if creator not in ('', None) else 'admin'
        save_info = {
            'project': project,
            'run_env': run_env,
            'sql': sql,
            'remark': remark,
            'run_group': run_group,
            'creator': creator,
            'is_delete': 0
        }
        if sql_id not in (None, ''):
            update_res, err_msg = UpdateSqlProjectService.update_sql_project(
                self.session, sql_id, save_info
            )
            return update_res, err_msg
        create_id, err_msg = UpdateSqlProjectService.create_sql_project(self.session, save_info)
        return create_id, err_msg

    @staticmethod
    def _format_value(value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(value, date):
            return value.strftime('%Y-%m-%d')
        if isinstance(value, Decimal):
            return float(value)
        return value

    @classmethod
    def _serialize_item(cls, item):
        item_dict = item.to_dict()
        for key, value in item_dict.items():
            item_dict[key] = cls._format_value(value)
        return item_dict

    def query_smart_manage_sql_data(self):
        """
        查询对应填写的sql语句列表数据
        """
        page_num = self.page_num or 1
        page_size = self.page_size or 20
        project = self.project
        creator = self.creator
        run_group = self.run_group
        run_env = self.run_env
        if isinstance(project, str):
            project = project.strip().strip('"')
        if isinstance(creator, str):
            creator = creator.strip().strip('"')
        if isinstance(run_group, str):
            run_group = run_group.replace('\u3000', ' ').strip().strip('"')
        filter_list = list()
        if project:
            filter_list.append(UpdateSqlProject.project == project)
        if creator:
            filter_list.append(UpdateSqlProject.creator == creator)
        if run_env:
            filter_list.append(UpdateSqlProject.run_env == run_env)
        if run_group:
            filter_list.append(UpdateSqlProject.run_group.isnot(None))
            filter_list.append(UpdateSqlProject.run_group != '')
            filter_list.append(UpdateSqlProject.run_group == run_group)
        test_info, count_num = UpdateSqlProjectService.get_sql_list_by_filters(
            session=self.session,
            filter_list=filter_list,
            page_num=page_num,
            page_size=page_size
        )
        result_list = [self._serialize_item(item) for item in test_info]
        return {'list': result_list, 'total': count_num}

    def get_sql_project_detail(self):
        sql_id = self.sql_id
        if isinstance(sql_id, str):
            sql_id = sql_id.strip().strip('"')
        if not sql_id:
            return {}, 'sqlId 为必传参数'
        sql_project = UpdateSqlProjectService.get_sql_project_by_id(self.session, sql_id)
        if not sql_project:
            return {}, '未查询到对应记录！'
        detail = self._serialize_item(sql_project)
        detail.pop('is_delete', None)
        return detail, ''

    def delete_sql_project(self):
        sql_id = self.sql_id
        if isinstance(sql_id, str):
            sql_id = sql_id.strip().strip('"')
        if not sql_id:
            return 0, 'sqlId 为必传参数'
        return UpdateSqlProjectService.delete_sql_project_by_id(self.session, sql_id)

    def execute_sql_project(self):
        sql_id = self.sql_id
        if isinstance(sql_id, str):
            sql_id = sql_id.strip().strip('"')
        if not sql_id:
            return {}, 'sqlId 为必传参数'
        sql_project = UpdateSqlProjectService.get_sql_project_by_id(self.session, sql_id)
        if not sql_project:
            return {}, '未查询到对应SQL记录！'
        project = (sql_project.project or '').strip()
        run_env = (sql_project.run_env or '').strip().lower()
        project_config = EXECUTE_DB_CONFIG.get(project) or EXECUTE_DB_CONFIG.get(project.upper()) or EXECUTE_DB_CONFIG.get(project.lower())
        target_config = (project_config or {}).get(run_env)
        if not target_config:
            return {}, '未配置对应项目环境的数据库连接信息！'
        execute_session = SqlSession(SqlSession.build_postgres_uri(
            target_config['host'],
            target_config['port'],
            target_config['user'],
            target_config['password'],
            target_config['database']
        ))
        try:
            result = execute_session.execute(sql_project.sql)
            if result.returns_rows:
                rows = []
                for row in result.fetchall():
                    row_dict = {key: self._format_value(value) for key, value in dict(row._mapping).items()}
                    rows.append(row_dict)
                execute_session.session.rollback()
                execute_session.close()
                return {'sqlId': int(sql_id), 'rows': rows, 'rowCount': len(rows)}, ''
            err = execute_session.done(close=False)
            if err:
                execute_session.close()
                return {}, f'执行SQL失败！{err}'
            row_count = result.rowcount
            execute_session.close()
            return {'sqlId': int(sql_id), 'rowCount': row_count}, ''
        except Exception as e:
            execute_session.session.rollback()
            execute_session.close()
            logger.warning(f'execute_sql_project执行失败！sql_id: {sql_id}, err: {e}')
            return {}, f'执行SQL失败！{e}'
