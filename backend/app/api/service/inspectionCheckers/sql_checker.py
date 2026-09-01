# encoding: UTF-8
"""SQL 查询巡检引擎。"""
import logging
import time

logger = logging.getLogger(__name__)


class SqlChecker(object):
    """执行 SQL 查询并校验结果断言。"""

    def execute(self, config, timeout=30):
        """
        执行 SQL 巡检。
        config 包含:
            db_config_id: int — 引用 inspection_db_config.id（由调用方解析后传入 db_connection）
            db_connection: dict — {type, host, port, database, username, password}
            sql: str — SQL 查询语句
            assertions: list — 断言规则
        """
        db_conn = config.get('db_connection', {})
        sql = config.get('sql', '')
        assertions = config.get('assertions', [])
        req_timeout = config.get('timeout', timeout)

        if not sql:
            return {'status': 'error', 'result': {}, 'error_message': 'SQL 语句为空', 'duration_ms': 0}

        start = time.time()
        try:
            db_type = db_conn.get('type', 'postgresql')
            rows, columns = self._execute_sql(db_type, db_conn, sql, req_timeout)
            duration_ms = int((time.time() - start) * 1000)

            result = {
                'rows': rows[:100],   # 最多返回 100 行
                'columns': columns,
                'row_count': len(rows),
                'query_time': duration_ms,
                'assertion_results': [],
            }

            all_passed = True
            for assertion in assertions:
                a_result = self._check_assertion(assertion, rows, columns)
                result['assertion_results'].append(a_result)
                if not a_result.get('passed'):
                    all_passed = False

            status = 'pass' if all_passed else 'fail'
            return {
                'status': status,
                'result': result,
                'error_message': '' if all_passed else '断言校验失败',
                'duration_ms': duration_ms,
            }

        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            logger.warning('SQL 巡检异常: %s', str(e))
            return {'status': 'error', 'result': {}, 'error_message': str(e), 'duration_ms': duration_ms}

    @staticmethod
    def _execute_sql(db_type, db_conn, sql, timeout):
        """执行 SQL 并返回 (rows, columns)。"""
        if db_type == 'postgresql':
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(
                host=db_conn.get('host'),
                port=db_conn.get('port', 5432),
                database=db_conn.get('database_name', db_conn.get('database')),
                user=db_conn.get('username'),
                password=db_conn.get('password'),
                connect_timeout=min(timeout, 10),
            )
            try:
                cur = conn.cursor()
                cur.execute(sql)
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    rows = [dict(zip(columns, row)) for row in cur.fetchall()]
                else:
                    columns = []
                    rows = []
                conn.commit()
                cur.close()
                return rows, columns
            finally:
                conn.close()

        elif db_type == 'mysql':
            import pymysql
            conn = pymysql.connect(
                host=db_conn.get('host'),
                port=db_conn.get('port', 3306),
                database=db_conn.get('database_name', db_conn.get('database')),
                user=db_conn.get('username'),
                password=db_conn.get('password'),
                connect_timeout=min(timeout, 10),
                read_timeout=min(timeout, 10),
                cursorclass=pymysql.cursors.DictCursor,
            )
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    if cur.description:
                        columns = [desc[0] for desc in cur.description]
                        rows = cur.fetchall()
                    else:
                        columns = []
                        rows = []
                conn.commit()
                return rows, columns
            finally:
                conn.close()
        else:
            raise ValueError('暂不支持 {} 类型的数据库'.format(db_type))

    @staticmethod
    def _check_assertion(assertion, rows, columns):
        """校验单个断言。"""
        a_type = assertion.get('type', '')
        operator = assertion.get('operator', 'eq')
        expected = assertion.get('expected')
        a_result = {'type': a_type, 'expected': expected, 'operator': operator, 'passed': False}

        try:
            if a_type == 'row_count':
                actual = len(rows)
                a_result['actual'] = actual
                a_result['passed'] = SqlChecker._compare(actual, operator, expected)

            elif a_type == 'column_value':
                col = assertion.get('column', '')
                row_idx = assertion.get('row', 0)
                if row_idx < len(rows) and col in rows[row_idx]:
                    actual = rows[row_idx][col]
                    a_result['column'] = col
                    a_result['row'] = row_idx
                    a_result['actual'] = actual
                    a_result['passed'] = SqlChecker._compare(actual, operator, expected)
                else:
                    a_result['error'] = '列 {} 或行 {} 不存在'.format(col, row_idx)

            elif a_type == 'not_empty':
                a_result['actual'] = len(rows) > 0
                a_result['passed'] = len(rows) > 0

            elif a_type == 'is_empty':
                a_result['actual'] = len(rows) == 0
                a_result['passed'] = len(rows) == 0

        except Exception as e:
            a_result['error'] = str(e)
            a_result['passed'] = False

        return a_result

    @staticmethod
    def _compare(actual, operator, expected):
        if operator == 'eq':
            return actual == expected
        elif operator == 'ne':
            return actual != expected
        elif operator == 'gt':
            return actual > expected
        elif operator == 'gte':
            return actual >= expected
        elif operator == 'lt':
            return actual < expected
        elif operator == 'lte':
            return actual <= expected
        elif operator == 'contains':
            return str(expected) in str(actual)
        return False
