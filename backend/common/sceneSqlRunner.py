# encoding: UTF-8
"""目标库 SQL 执行（优先读项目环境库连接，其次 EXECUTE_DB_CONFIG）。"""
from __future__ import unicode_literals

import re

from common.sqlSession import SqlSession
from const import EXECUTE_DB_CONFIG
from logger import logger

BLOCKED_ENVS = {'prod', 'production', 'prd', 'online'}
FORBIDDEN_SQL_RE = re.compile(r'\b(DROP|TRUNCATE|ALTER|CREATE\s+USER|GRANT|REVOKE)\b', re.I)
WRITE_SQL_HEAD_RE = re.compile(r'^\s*(INSERT|UPDATE|DELETE)\b', re.I)
WRITE_SQL_ANY_RE = re.compile(r'\b(INSERT|UPDATE|DELETE)\b', re.I)
CTE_HEAD_RE = re.compile(r'^\s*WITH\b', re.I)
MAX_SQL_CHARS = 4000


class SceneSqlRunner(object):

    @staticmethod
    def validate_env(env):
        env_key = (env or '').strip().lower()
        if not env_key:
            return '', 'env 为必传参数'
        if env_key in BLOCKED_ENVS:
            return '', '禁止在生产类环境执行造数 SQL（env={})'.format(env_key)
        return env_key, ''

    @staticmethod
    def validate_sql(sql_text):
        sql = (sql_text or '').strip()
        if not sql:
            return '', 'sql 为空'
        if len(sql) > MAX_SQL_CHARS:
            return '', 'SQL 超过长度上限 {}'.format(MAX_SQL_CHARS)
        if FORBIDDEN_SQL_RE.search(sql):
            return '', 'SQL 含禁止语句（DROP/TRUNCATE/ALTER 等）'
        return sql, ''

    @staticmethod
    def is_write_sql(sql_text):
        """判断是否为写库语句（含 INSERT/UPDATE/DELETE ... RETURNING，以及写库 CTE）。"""
        sql = sql_text or ''
        if WRITE_SQL_HEAD_RE.match(sql):
            return True
        if CTE_HEAD_RE.match(sql) and WRITE_SQL_ANY_RE.search(sql):
            return True
        return False
    @classmethod
    def normalize_db_config(cls, raw):
        """将环境 variables.dbConnection 规范为 host/port/user/password/database。"""
        if not isinstance(raw, dict):
            return None
        host = (raw.get('host') or '').strip()
        port = raw.get('port')
        user = (raw.get('user') or raw.get('username') or '').strip()
        password = raw.get('password')
        if password is None:
            password = ''
        database = (raw.get('database') or raw.get('database_name') or raw.get('databaseName') or '').strip()
        if not host or port in (None, '') or not user or not database:
            return None
        try:
            port = int(port)
        except (TypeError, ValueError):
            return None
        return {
            'host': host,
            'port': port,
            'user': user,
            'password': str(password),
            'database': database,
        }

    @classmethod
    def load_project_env_db_config(cls, project_id, env_name):
        """从项目环境 variables.dbConnection 读取库连接；无配置返回 None。"""
        if project_id in (None, '') or not (env_name or '').strip():
            return None, ''
        session_wrap = None
        try:
            from app.api.model.projectModel import Environment
            session_wrap = SqlSession()
            name = (env_name or '').strip()
            rows = session_wrap.session.query(Environment).filter(
                Environment.project_id == int(project_id),
                Environment.is_delete == 0,
            ).all()
            matched = None
            for row in rows:
                if (row.name or '').strip().lower() == name.lower():
                    matched = row
                    break
            if matched is None:
                return None, '项目未配置环境：{}'.format(name)
            variables = matched.variables or {}
            if not isinstance(variables, dict):
                variables = {}
            raw = (
                variables.get('dbConnection')
                or variables.get('db_connection')
                or variables.get('database')
            )
            config = cls.normalize_db_config(raw)
            if not config:
                return None, '请先在项目设置 → 环境配置中为「{}」配置数据库连接'.format(matched.name or name)
            return config, ''
        except Exception as exc:
            logger.warning('读取项目环境库连接失败 project_id=%s env=%s err=%s', project_id, env_name, exc)
            return None, '读取项目环境库连接失败：{}'.format(exc)
        finally:
            if session_wrap is not None:
                try:
                    session_wrap.close()
                except Exception:
                    pass

    @classmethod
    def resolve_target_config(cls, db_project, env_key, project_id=None):
        """
        解析目标库连接：
        1) 有 project_id 时，必须用项目环境里的 dbConnection（不再静默落到全局配置）
        2) 无 project_id 时，回退 EXECUTE_DB_CONFIG[db_project][env]
        """
        if project_id not in (None, ''):
            return cls.load_project_env_db_config(project_id, env_key)

        project = (db_project or '').strip()
        project_config = (
            EXECUTE_DB_CONFIG.get(project)
            or EXECUTE_DB_CONFIG.get(project.upper())
            or EXECUTE_DB_CONFIG.get(project.lower())
        )
        target_config = (project_config or {}).get(env_key)
        if not target_config:
            return None, '未配置对应项目环境的数据库连接：project={} env={}'.format(project, env_key)
        return target_config, ''

    @classmethod
    def run(cls, db_project, env, sql_text, project_id=None, db_config=None):
        """执行 SQL，返回 {rows, rowCount, firstRow} 或错误。"""
        env_key, err = cls.validate_env(env)
        if err:
            return {}, err
        sql, err = cls.validate_sql(sql_text)
        if err:
            return {}, err

        if db_config:
            target_config = cls.normalize_db_config(db_config)
            if not target_config:
                return {}, '数据库连接配置不完整（需 host/port/user/password/database）'
        else:
            target_config, err = cls.resolve_target_config(db_project, env_key, project_id=project_id)
            if err:
                return {}, err

        execute_session = SqlSession(SqlSession.build_postgres_uri(
            target_config['host'],
            target_config['port'],
            target_config['user'],
            target_config['password'],
            target_config['database'],
        ))
        try:
            result = execute_session.execute(sql)
            is_write = cls.is_write_sql(sql)
            if result.returns_rows:
                rows = []
                for row in result.fetchall():
                    rows.append({key: cls._format(value) for key, value in dict(row._mapping).items()})
                # INSERT/UPDATE/DELETE ... RETURNING 也必须提交，否则界面成功、库里无数据
                if is_write:
                    err = execute_session.done(close=False)
                    if err:
                        execute_session.close()
                        return {}, '执行SQL失败！{}'.format(err)
                else:
                    execute_session.session.rollback()
                execute_session.close()
                return {
                    'rows': rows,
                    'rowCount': len(rows) if not is_write else max(len(rows), result.rowcount or 0),
                    'firstRow': rows[0] if rows else {},
                }, ''
            err = execute_session.done(close=False)
            if err:
                execute_session.close()
                return {}, '执行SQL失败！{}'.format(err)
            row_count = result.rowcount if result.rowcount is not None else 0
            execute_session.close()
            return {'rows': [], 'rowCount': row_count, 'firstRow': {}}, ''
        except Exception as exc:
            try:
                execute_session.session.rollback()
                execute_session.close()
            except Exception:
                pass
            logger.warning(
                'SceneSqlRunner 失败 project_id=%s db_project=%s env=%s err=%s',
                project_id, db_project, env_key, exc
            )
            return {}, '执行SQL失败！{}'.format(exc)

    @staticmethod
    def _format(value):
        if hasattr(value, 'isoformat'):
            try:
                return value.isoformat(sep=' ', timespec='seconds')
            except TypeError:
                return value.isoformat()
        return value
