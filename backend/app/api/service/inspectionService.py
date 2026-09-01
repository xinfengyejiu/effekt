# encoding: UTF-8
"""巡检系统 CRUD 服务。"""
import logging
from app.api.dao.inspectionDao import InspectionDao

logger = logging.getLogger(__name__)


class InspectionService(object):
    """巡检组 / 任务 / 项 / 数据库连接 CRUD。"""

    # ────────────── Group ──────────────
    @staticmethod
    def list_groups(db, params):
        items, total = InspectionDao.list_groups(
            db,
            project_id=params.get('project_id'),
            page_no=params.get('page_no', 1),
            page_size=params.get('page_size', 20),
        )
        return {'items': [i.to_dict() for i in items], 'total': total}

    @staticmethod
    def get_group(db, group_id):
        obj = InspectionDao.get_group(db, group_id)
        return obj.to_dict() if obj else None

    @staticmethod
    def create_group(db, data, user_id=None):
        values = {
            'name': data.get('name'),
            'project_id': data.get('project_id'),
            'description': data.get('description', ''),
            'enabled': data.get('enabled', 1),
            'schedule_type': data.get('schedule_type', 'manual'),
            'cron_expression': data.get('cron_expression'),
            'interval_seconds': data.get('interval_seconds'),
            'notify_type': data.get('notify_type'),
            'notify_webhook': data.get('notify_webhook'),
            'created_by': user_id,
        }
        obj = InspectionDao.create_group(db, values)
        db.commit()
        result = obj.to_dict()
        InspectionService._reload_group_schedule(obj)
        return result

    @staticmethod
    def update_group(db, group_id, data):
        values = {}
        for k in ('name', 'project_id', 'description', 'enabled',
                   'schedule_type', 'cron_expression', 'interval_seconds',
                   'notify_type', 'notify_webhook'):
            if k in data:
                values[k] = data[k]
        obj = InspectionDao.update_group(db, group_id, values)
        db.commit()
        if obj:
            InspectionService._reload_group_schedule(obj)
            return obj.to_dict()
        return None

    @staticmethod
    def delete_group(db, group_id):
        # 检查组下是否有任务
        tasks, total = InspectionDao.list_tasks(db, group_id=group_id)
        if total > 0:
            return None, '该巡检组下还有任务，请先删除任务'
        InspectionDao.delete_group(db, group_id)
        db.commit()
        try:
            from app.core.inspectionScheduler import inspection_scheduler
            inspection_scheduler.remove_group(group_id)
        except Exception as e:
            logger.warning('移除组调度失败: %s', str(e))
        return {}, ''

    @staticmethod
    def toggle_group(db, group_id):
        group = InspectionDao.get_group(db, group_id)
        if not group:
            return None
        group.enabled = 0 if group.enabled == 1 else 1
        db.commit()
        InspectionService._reload_group_schedule(group)
        return group.to_dict()

    @staticmethod
    def _reload_group_schedule(group):
        """组 CRUD / 启停后热更新调度。"""
        try:
            from app.core.inspectionScheduler import inspection_scheduler
            if group.enabled == 1 and group.schedule_type in ('cron', 'interval'):
                inspection_scheduler.reload_group(group)
            else:
                inspection_scheduler.remove_group(group.id)
        except Exception as e:
            logger.warning('热更新组调度失败 [group=%s]: %s', getattr(group, 'id', None), str(e))

    # ────────────── Task ──────────────
    @staticmethod
    def list_tasks(db, params):
        items, total = InspectionDao.list_tasks(
            db,
            group_id=params.get('group_id'),
            project_id=params.get('project_id'),
            task_type=params.get('task_type'),
            page_no=params.get('page_no', 1),
            page_size=params.get('page_size', 20),
        )
        return {'items': [i.to_dict() for i in items], 'total': total}

    @staticmethod
    def get_task_detail(db, task_id):
        task = InspectionDao.get_task(db, task_id)
        if not task:
            return None
        result = task.to_dict()
        items = InspectionDao.list_items_by_task(db, task_id)
        result['items'] = [i.to_dict() for i in items]
        return result

    @staticmethod
    def create_task(db, data, user_id=None):
        values = {
            'group_id': data.get('group_id'),
            'project_id': data.get('project_id'),
            'name': data.get('name'),
            'task_type': data.get('task_type', 'mixed'),
            'schedule_type': data.get('schedule_type', 'manual'),
            'cron_expression': data.get('cron_expression'),
            'interval_seconds': data.get('interval_seconds'),
            'env_code': data.get('env_code'),
            'enabled': data.get('enabled', 1),
            'notify_type': data.get('notify_type'),
            'notify_webhook': data.get('notify_webhook'),
            'notify_config': data.get('notify_config', {}),
            'created_by': user_id,
        }
        obj = InspectionDao.create_task(db, values)
        db.commit()
        return obj.to_dict()

    @staticmethod
    def update_task(db, task_id, data):
        values = {}
        for k in ('group_id', 'project_id', 'name', 'task_type', 'schedule_type',
                   'cron_expression', 'interval_seconds', 'env_code', 'enabled',
                   'notify_type', 'notify_webhook', 'notify_config', 'ext'):
            if k in data:
                values[k] = data[k]
        if 'updated_by' in data:
            values['updated_by'] = data['updated_by']
        obj = InspectionDao.update_task(db, task_id, values)
        db.commit()
        return obj.to_dict() if obj else None

    @staticmethod
    def delete_task(db, task_id):
        InspectionDao.delete_task(db, task_id)
        db.commit()
        return {}, ''

    @staticmethod
    def toggle_task(db, task_id):
        task = InspectionDao.get_task(db, task_id)
        if task:
            task.enabled = 0 if task.enabled == 1 else 1
            db.commit()
            return task.to_dict()
        return None

    # ────────────── Item ──────────────
    @staticmethod
    def list_items(db, params):
        items, total = InspectionDao.list_items(
            db,
            task_id=params.get('task_id'),
            item_type=params.get('item_type'),
            page_no=params.get('page_no', 1),
            page_size=params.get('page_size', 100),
        )
        return {'items': [i.to_dict() for i in items], 'total': total}

    @staticmethod
    def create_item(db, data):
        values = {
            'task_id': data.get('task_id'),
            'item_type': data.get('item_type'),
            'name': data.get('name'),
            'ref_id': data.get('ref_id'),
            'sort_order': data.get('sort_order', 0),
            'config': data.get('config', {}),
            'timeout_seconds': data.get('timeout_seconds', 30),
            'enabled': data.get('enabled', 1),
        }
        obj = InspectionDao.create_item(db, values)
        db.commit()
        return obj.to_dict()

    @staticmethod
    def update_item(db, item_id, data):
        values = {}
        for k in ('task_id', 'item_type', 'name', 'ref_id', 'sort_order',
                   'config', 'timeout_seconds', 'enabled'):
            if k in data:
                values[k] = data[k]
        obj = InspectionDao.update_item(db, item_id, values)
        db.commit()
        return obj.to_dict() if obj else None

    @staticmethod
    def delete_item(db, item_id):
        InspectionDao.delete_item(db, item_id)
        db.commit()
        return {}, ''

    @staticmethod
    def batch_create_items(db, task_id, items_data):
        created = []
        for idx, data in enumerate(items_data):
            values = {
                'task_id': task_id,
                'item_type': data.get('item_type'),
                'name': data.get('name'),
                'ref_id': data.get('ref_id'),
                'sort_order': data.get('sort_order', idx),
                'config': data.get('config', {}),
                'timeout_seconds': data.get('timeout_seconds', 30),
            }
            obj = InspectionDao.create_item(db, values)
            created.append(obj.to_dict())
        db.commit()
        return created

    # ────────────── DbConfig ──────────────
    @staticmethod
    def list_db_configs(db, params):
        items, total = InspectionDao.list_db_configs(
            db,
            project_id=params.get('project_id'),
            page_no=params.get('page_no', 1),
            page_size=params.get('page_size', 100),
        )
        # 脱敏：不返回密码明文
        result_items = []
        for i in items:
            d = i.to_dict()
            if d.get('password'):
                d['password'] = '******'
            result_items.append(d)
        return {'items': result_items, 'total': total}

    @staticmethod
    def create_db_config(db, data, user_id=None):
        values = {
            'project_id': data.get('project_id'),
            'name': data.get('name'),
            'db_type': data.get('db_type'),
            'host': data.get('host'),
            'port': data.get('port'),
            'database_name': data.get('database_name'),
            'username': data.get('username'),
            'password': data.get('password'),
            'extra_params': data.get('extra_params', {}),
            'created_by': user_id,
        }
        obj = InspectionDao.create_db_config(db, values)
        db.commit()
        d = obj.to_dict()
        d['password'] = '******'
        return d

    @staticmethod
    def update_db_config(db, config_id, data):
        values = {}
        for k in ('project_id', 'name', 'db_type', 'host', 'port', 'database_name',
                   'username', 'extra_params'):
            if k in data:
                values[k] = data[k]
        if 'password' in data and data['password'] and data['password'] != '******':
            values['password'] = data['password']
        obj = InspectionDao.update_db_config(db, config_id, values)
        db.commit()
        if obj:
            d = obj.to_dict()
            d['password'] = '******'
            return d
        return None

    @staticmethod
    def delete_db_config(db, config_id):
        InspectionDao.delete_db_config(db, config_id)
        db.commit()
        return {}, ''

    @staticmethod
    def test_db_connection(db, config_data):
        """测试数据库连接是否可用（从效能平台后端所在机器发起）。"""
        try:
            db_type = config_data.get('db_type', 'postgresql')
            host = (config_data.get('host') or '').strip()
            port = int(config_data.get('port') or (5432 if db_type == 'postgresql' else 3306))
            if db_type == 'postgresql':
                import psycopg2
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    database=config_data.get('database_name'),
                    user=config_data.get('username'),
                    password=config_data.get('password'),
                    connect_timeout=8,
                )
                conn.close()
            elif db_type == 'mysql':
                import pymysql
                conn = pymysql.connect(
                    host=host,
                    port=port,
                    database=config_data.get('database_name'),
                    user=config_data.get('username'),
                    password=config_data.get('password'),
                    connect_timeout=8,
                )
                conn.close()
            else:
                return None, '暂不支持 {} 类型的数据库'.format(db_type)
            return {'connected': True}, ''
        except Exception as e:
            err = str(e) or e.__class__.__name__
            logger.warning('数据库连接测试失败: %s', err)
            low = err.lower()
            if 'timeout' in low or 'timed out' in low:
                return None, (
                    '连接超时：无法从效能平台服务器访问 {}:{}。'
                    '请确认填写的是对外可达端口（该主机常见映射为 8366 而非容器内 5432），'
                    '并检查防火墙 / 安全组是否放行后端所在网络。'
                    '原始错误: {}'
                ).format(
                    (config_data.get('host') or '').strip(),
                    config_data.get('port'),
                    err,
                )
            if 'password' in low or 'authentication' in low or 'auth' in low:
                return None, '认证失败，请检查用户名或密码。原始错误: {}'.format(err)
            if 'does not exist' in low or 'unknown database' in low:
                return None, '数据库不存在，请检查数据库名。原始错误: {}'.format(err)
            return None, '连接失败: {}'.format(err)

    # ────────────── Dashboard / Report ──────────────
    @staticmethod
    def get_dashboard(db, project_id=None):
        return InspectionDao.get_dashboard_stats(db, project_id)

    @staticmethod
    def get_trend(db, project_id=None, days=7):
        return InspectionDao.get_trend_data(db, project_id, days)
