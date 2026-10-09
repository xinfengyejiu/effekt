# encoding: UTF-8
"""AI 对号查数：连接管理 + 只读 NL/业务号查数。"""
from __future__ import unicode_literals

import hashlib
import json
import re
import time
from datetime import datetime

import psycopg2

from common.sceneSchemaProbe import SceneSchemaProbe
from common.sceneSqlRunner import SceneSqlRunner
from logger import logger
from ..dao.aiDataProbeDao import AiDataProbeDao
from ..model.aiDataProbeModel import (
    AiDataProbeConnection,
    AiDataProbeMessage,
    AiDataProbeSession,
)
from ..service.aiService import AIService

PASSWORD_MASK = '******'
MAX_SQLS_PER_TURN = 3
MAX_EVIDENCE_ROWS = 20
MAX_CELL_CHARS = 200
CONNECT_TIMEOUT_SEC = 5
QUERY_MAX_ROWS = 100

SQL_JSON_SYSTEM = (
    '你是测试同学的只读查数助手。根据业务库表结构、以及（若有）项目代码中的实体/表映射，'
    '生成用于对号核对的 PostgreSQL SELECT。'
    '若用户明确要求看代码/配置/枚举/逻辑且不需要查库，可返回空 sqls，并在 reason 写 code_only。'
    '硬性要求：只输出 JSON；禁止 INSERT/UPDATE/DELETE/DDL；每条 SQL 必须带 LIMIT（<=100）；'
    '最多 3 条 SQL；优先使用代码中出现的真实表名与字段；不确定表/字段时 sqls 可为空并在 reason 说明。'
    'JSON 格式：{"sqls":["SELECT ..."],"reason":"..."}'
)

CONCLUSION_SYSTEM = (
    '你是测试数据对号助手。根据用户问题与只读查询结果，给出简短结论。'
    '只输出 JSON：{"status":"matched|mismatch|not_found|insufficient","conclusion":"...","highlights":["..."]}'
    'status 含义：matched=与描述一致；mismatch=不一致；not_found=查无；insufficient=信息不足。'
)

CODE_ANSWER_SYSTEM = (
    '你是熟悉本项目代码的测试助手。用户在问业务逻辑、配置、枚举、流程或「有多少种」等代码级问题。'
    '请只基于提供的代码摘录回答；引用具体文件路径；把能确定的枚举/配置项列清楚。'
    '禁止编造代码中不存在的常量或分支；若摘录不够，说明还缺哪些文件/关键词。'
    '只输出 JSON：{"status":"matched|insufficient","conclusion":"...","highlights":["文件或要点..."],"mode":"code"}'
)


class AiDataProbeService(object):

    # ---------- connection ----------

    @staticmethod
    def list_connections(session, req_data):
        items, total = AiDataProbeDao.list_connections(session, req_data)
        return {
            'list': [AiDataProbeService._conn_to_dict(x) for x in items],
            'total': total,
        }, ''

    @staticmethod
    def create_connection(session, req_data, user_id=None):
        values, err = AiDataProbeService._parse_connection_payload(req_data, require_password=True)
        if err:
            return {}, err
        values['created_by'] = user_id
        values['is_delete'] = 0
        obj, err = AiDataProbeDao.create(session, AiDataProbeConnection, values)
        if err:
            return {}, err
        return AiDataProbeService._conn_to_dict(obj), ''

    @staticmethod
    def update_connection(session, req_data, user_id=None):
        conn_id = AiDataProbeService._get(req_data, 'id', 'connectionId', 'connection_id')
        if conn_id in (None, ''):
            return {}, 'id 为必传参数'
        existing = AiDataProbeDao.get_by_id(session, AiDataProbeConnection, conn_id)
        if not existing:
            return {}, '连接不存在'
        values, err = AiDataProbeService._parse_connection_payload(req_data, require_password=False)
        if err:
            return {}, err
        password = AiDataProbeService._get(req_data, 'password')
        if not password or password == PASSWORD_MASK:
            values.pop('password', None)
        _, err = AiDataProbeDao.update_by_id(session, AiDataProbeConnection, conn_id, values)
        if err:
            return {}, err
        obj = AiDataProbeDao.get_by_id(session, AiDataProbeConnection, conn_id)
        return AiDataProbeService._conn_to_dict(obj), ''

    @staticmethod
    def delete_connection(session, req_data, user_id=None):
        conn_id = AiDataProbeService._get(req_data, 'id', 'connectionId', 'connection_id')
        if conn_id in (None, ''):
            return {}, 'id 为必传参数'
        _, err = AiDataProbeDao.update_by_id(session, AiDataProbeConnection, conn_id, {'is_delete': 1})
        if err:
            return {}, err
        return {'id': int(conn_id)}, ''

    @staticmethod
    def test_connection(session, req_data, user_id=None):
        """测试连通：可用已保存 id，或临时表单字段。"""
        conn_id = AiDataProbeService._get(req_data, 'id', 'connectionId', 'connection_id')
        db_config = None
        env = (AiDataProbeService._get(req_data, 'env') or 'test').strip()
        if conn_id not in (None, ''):
            obj = AiDataProbeDao.get_by_id(session, AiDataProbeConnection, conn_id)
            if not obj:
                return {}, '连接不存在'
            db_config = AiDataProbeService._conn_db_config(obj)
            env = obj.env or env
        else:
            values, err = AiDataProbeService._parse_connection_payload(req_data, require_password=True)
            if err:
                return {}, err
            db_config = {
                'host': values['host'],
                'port': values['port'],
                'user': values['username'],
                'password': values['password'],
                'database': values['database_name'],
            }
            env = values.get('env') or env

        env_key, err = SceneSqlRunner.validate_env(env)
        if err:
            return {}, err

        started = time.time()
        conn = None
        try:
            conn = psycopg2.connect(
                host=db_config['host'],
                port=int(db_config['port']),
                user=db_config['user'],
                password=db_config['password'],
                dbname=db_config['database'],
                connect_timeout=CONNECT_TIMEOUT_SEC,
            )
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
                cur.fetchone()
            latency_ms = int((time.time() - started) * 1000)
            return {'ok': True, 'latencyMs': latency_ms, 'env': env_key}, ''
        except Exception as exc:
            logger.warning('ai_data_probe test_connection failed: %s', exc)
            return {}, '连通失败：{}'.format(exc)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    @staticmethod
    def list_tables(session, req_data, user_id=None):
        """列出连接对应库的全部业务表。"""
        conn_id = AiDataProbeService._get(req_data, 'connectionId', 'connection_id', 'id')
        if conn_id in (None, ''):
            return {}, 'connectionId 不能为空'
        obj = AiDataProbeDao.get_by_id(session, AiDataProbeConnection, conn_id)
        if not obj or not obj.enabled:
            return {}, '连接不存在或已禁用'
        env_key, err = SceneSqlRunner.validate_env(obj.env)
        if err:
            return {}, err
        keyword = AiDataProbeService._get(req_data, 'keyword', 'q')
        with_columns_raw = AiDataProbeService._get(req_data, 'withColumns', 'with_columns')
        with_columns = with_columns_raw in (True, 1, '1', 'true', 'True')
        data, err = SceneSchemaProbe.list_tables_from_db_config(
            AiDataProbeService._conn_db_config(obj),
            keyword=keyword,
            with_columns=with_columns,
        )
        if err:
            return {}, err
        data['connectionId'] = int(conn_id)
        data['env'] = env_key
        return data, ''

    @staticmethod
    def table_columns(session, req_data, user_id=None):
        """查看单表字段。"""
        conn_id = AiDataProbeService._get(req_data, 'connectionId', 'connection_id', 'id')
        table_name = AiDataProbeService._get(req_data, 'tableName', 'table_name', 'table')
        if conn_id in (None, ''):
            return {}, 'connectionId 不能为空'
        obj = AiDataProbeDao.get_by_id(session, AiDataProbeConnection, conn_id)
        if not obj or not obj.enabled:
            return {}, '连接不存在或已禁用'
        _, err = SceneSqlRunner.validate_env(obj.env)
        if err:
            return {}, err
        data, err = SceneSchemaProbe.list_table_columns_from_db_config(
            AiDataProbeService._conn_db_config(obj),
            table_name,
        )
        if err:
            return {}, err
        data['connectionId'] = int(conn_id)
        return data, ''

    @staticmethod
    def import_from_project(session, req_data, user_id=None):
        project_id = AiDataProbeService._get(req_data, 'projectId', 'project_id')
        env = (AiDataProbeService._get(req_data, 'env') or 'test').strip()
        name = (AiDataProbeService._get(req_data, 'name') or '').strip()
        if project_id in (None, ''):
            return {}, 'projectId 为必传参数'
        config, err = SceneSqlRunner.load_project_env_db_config(project_id, env)
        if err or not config:
            return {}, err or '项目环境未配置数据库连接'
        product_id = AiDataProbeService._to_int_or_none(
            AiDataProbeService._get(req_data, 'productId', 'product_id')
        )
        product_name = AiDataProbeService._get(req_data, 'productName', 'product_name') or ''
        project_name = AiDataProbeService._get(req_data, 'projectName', 'project_name') or ''
        values = {
            'name': name or '项目{}-{}'.format(project_id, env),
            'db_type': 'postgresql',
            'host': config['host'],
            'port': int(config['port']),
            'database_name': config['database'],
            'username': config['user'],
            'password': config['password'],
            'product_id': product_id,
            'product_name': product_name[:128] if product_name else '',
            'project_id': int(project_id),
            'project_name': project_name,
            'env': (env or 'test').strip().lower(),
            'remark': '从项目环境导入',
            'enabled': 1,
            'created_by': user_id,
            'is_delete': 0,
        }
        obj, err = AiDataProbeDao.create(session, AiDataProbeConnection, values)
        if err:
            return {}, err
        return AiDataProbeService._conn_to_dict(obj), ''

    # ---------- session / chat ----------

    @staticmethod
    def list_sessions(session, req_data):
        items, total = AiDataProbeDao.list_sessions(session, req_data)
        return {
            'list': [AiDataProbeService._session_to_dict(x) for x in items],
            'total': total,
        }, ''

    @staticmethod
    def create_session(session, req_data, user_id=None):
        connection_id = AiDataProbeService._get(req_data, 'connectionId', 'connection_id')
        if connection_id in (None, ''):
            return {}, 'connectionId 为必传参数'
        conn = AiDataProbeDao.get_by_id(session, AiDataProbeConnection, connection_id)
        if not conn or not conn.enabled:
            return {}, '连接不存在或已禁用'
        title = (AiDataProbeService._get(req_data, 'title') or '智能问数').strip()[:255]
        session_no = AiDataProbeService._next_session_no(session)
        obj, err = AiDataProbeDao.create(session, AiDataProbeSession, {
            'session_no': session_no,
            'connection_id': int(connection_id),
            'project_id': conn.project_id,
            'title': title or '智能问数',
            'status': 'active',
            'created_by': user_id,
            'meta': {},
            'is_delete': 0,
        })
        if err:
            return {}, err
        return AiDataProbeService._session_to_dict(obj), ''

    @staticmethod
    def session_detail(session, req_data):
        session_id = AiDataProbeService._get(req_data, 'sessionId', 'session_id', 'id')
        if session_id in (None, ''):
            return {}, 'sessionId 为必传参数'
        obj = AiDataProbeDao.get_by_id(session, AiDataProbeSession, session_id)
        if not obj:
            return {}, '会话不存在'
        messages = AiDataProbeDao.list_messages(session, session_id)
        data = AiDataProbeService._session_to_dict(obj)
        data['messages'] = [
            {
                'id': m.id,
                'role': m.role,
                'content': m.content or {},
                'createdTime': AiDataProbeService._fmt_time(m.created_time),
            }
            for m in messages
        ]
        conn = AiDataProbeDao.get_by_id(session, AiDataProbeConnection, obj.connection_id)
        data['connection'] = AiDataProbeService._conn_to_dict(conn) if conn else None
        return data, ''

    @staticmethod
    def rename_session(session, req_data, user_id=None):
        """重命名会话标题。"""
        session_id = AiDataProbeService._get(req_data, 'sessionId', 'session_id', 'id')
        title = (AiDataProbeService._get(req_data, 'title', 'name') or '').strip()
        if session_id in (None, ''):
            return {}, 'sessionId 为必传参数'
        if not title:
            return {}, '标题不能为空'
        if len(title) > 255:
            return {}, '标题过长（最多 255 字）'
        obj = AiDataProbeDao.get_by_id(session, AiDataProbeSession, session_id)
        if not obj:
            return {}, '会话不存在'
        # 直接改 ORM 对象，避免 update(synchronize_session=False) 后缓存仍是旧 title
        obj.title = title[:255]
        obj.updated_time = datetime.now()
        err = session.done(close=False)
        if err:
            return {}, '更新失败：{}'.format(err)
        return AiDataProbeService._session_to_dict(obj), ''

    @staticmethod
    def ask(session, req_data, user_id=None):
        """主路径：NL/业务号 → schema → SQL → 只读执行 → 对号结论。"""
        final = None
        err = ''
        for evt in AiDataProbeService.ask_stream(session, req_data, user_id=user_id):
            if not isinstance(evt, dict):
                continue
            if evt.get('type') == 'error':
                err = evt.get('message') or '智能问数失败'
            elif evt.get('type') == 'done':
                final = evt.get('result') or {}
        if err and not final:
            return {}, err
        return final or {}, ''

    @staticmethod
    def ask_stream(session, req_data, user_id=None):
        """流式对号查数：逐步 yield {type, ...}，最后 done/error。"""
        question = (AiDataProbeService._get(req_data, 'question', 'text', 'content') or '').strip()
        if not question:
            yield {'type': 'error', 'message': 'question 不能为空'}
            return
        if len(question) > 20000:
            yield {'type': 'error', 'message': '问题过长（最多 20000 字），请精简后再试'}
            return

        session_id = AiDataProbeService._get(req_data, 'sessionId', 'session_id')
        connection_id = AiDataProbeService._get(req_data, 'connectionId', 'connection_id')
        execute = AiDataProbeService._get(req_data, 'execute')
        if execute is None:
            execute = True
        else:
            execute = execute in (True, 1, '1', 'true', 'True')

        probe_session = None
        if session_id not in (None, ''):
            probe_session = AiDataProbeDao.get_by_id(session, AiDataProbeSession, session_id)
            if not probe_session:
                yield {'type': 'error', 'message': '会话不存在'}
                return
            connection_id = probe_session.connection_id
        if connection_id in (None, ''):
            yield {'type': 'error', 'message': 'connectionId 或 sessionId 必传其一'}
            return

        conn = AiDataProbeDao.get_by_id(session, AiDataProbeConnection, connection_id)
        if not conn or not conn.enabled:
            yield {'type': 'error', 'message': '连接不存在或已禁用'}
            return
        env_key, err = SceneSqlRunner.validate_env(conn.env)
        if err:
            yield {'type': 'error', 'message': err}
            return
        db_config = AiDataProbeService._conn_db_config(conn)

        if probe_session is None:
            created, err = AiDataProbeService.create_session(session, {
                'connectionId': connection_id,
                'title': question[:40],
            }, user_id=user_id)
            if err:
                yield {'type': 'error', 'message': err}
                return
            probe_session = AiDataProbeDao.get_by_id(session, AiDataProbeSession, created['id'])

        AiDataProbeDao.create(session, AiDataProbeMessage, {
            'session_id': probe_session.id,
            'role': 'user',
            'content': {'question': question},
            'created_by': user_id,
            'is_delete': 0,
        })
        yield {
            'type': 'session',
            'sessionId': probe_session.id,
            'sessionNo': probe_session.session_no,
            'connectionId': conn.id,
        }

        custom_sql = (AiDataProbeService._get(req_data, 'sql', 'customSql') or '').strip()
        embedded_sql = custom_sql or AiDataProbeService._extract_embedded_sql(question)
        prefer_code = AiDataProbeService._is_code_logic_question(question)

        yield {'type': 'status', 'message': '正在探查表结构与项目代码…'}
        hint, schema_meta = SceneSchemaProbe.build_hint_from_db_config(db_config, question)
        code_hint, code_meta = AiDataProbeService._probe_code_hint(
            conn.project_id, question, schema_meta.get('matchedTables')
        )
        # 代码问答时再补一轮不带表约束的检索，避免表名干扰关键词
        if prefer_code and not (code_hint or '').strip():
            code_hint2, code_meta2 = AiDataProbeService._probe_code_hint(conn.project_id, question, None)
            if code_hint2:
                code_hint, code_meta = code_hint2, code_meta2
        merged_hint = '\n\n'.join([x for x in [hint, code_hint] if x])
        if len(merged_hint) > 8000:
            merged_hint = merged_hint[:8000] + '\n...(上下文已截断)'

        plan_err = ''
        sql_plan = {'sqls': [], 'reason': ''}
        sqls = []
        evidence = []
        exec_results = []
        answer_mode = 'sql'
        conclusion_payload = {'status': 'insufficient', 'conclusion': '', 'highlights': []}

        # ---- 代码逻辑优先：跳过 SQL，直接基于 Git 代码回答 ----
        if prefer_code and not embedded_sql:
            answer_mode = 'code'
            yield {'type': 'status', 'message': '识别为代码/配置问题，正在结合项目 Git 代码分析…'}
            yield {'type': 'sqls', 'sqls': [], 'reason': 'code_only', 'matchedTables': schema_meta.get('matchedTables') or []}
            if not (code_hint or '').strip():
                tip = (
                    code_meta.get('missingRepoTip')
                    or code_meta.get('codeError')
                    or '项目代码中未匹配到相关文件，请确认已在项目设置配置 Git，或换关键词再问。'
                )
                conclusion_payload = {
                    'status': 'insufficient',
                    'conclusion': tip,
                    'highlights': ['mode=code', '未命中代码文件'],
                }
                for i in range(0, len(tip), 18):
                    yield {'type': 'delta', 'text': tip[i:i + 18]}
            else:
                streamed_text = []
                for piece in AiDataProbeService._answer_code_stream(question, code_hint, code_meta):
                    if isinstance(piece, dict) and piece.get('final'):
                        conclusion_payload = piece['final']
                    elif isinstance(piece, dict) and piece.get('error'):
                        yield {'type': 'status', 'message': piece.get('error')}
                    elif isinstance(piece, str) and piece:
                        streamed_text.append(piece)
                        yield {'type': 'delta', 'text': piece}
                if not (conclusion_payload.get('conclusion') or '').strip() and streamed_text:
                    conclusion_payload['conclusion'] = ''.join(streamed_text).strip()
                    conclusion_payload['status'] = conclusion_payload.get('status') or 'matched'
        else:
            if embedded_sql:
                sqls = [embedded_sql]
                sql_plan = {'sqls': sqls, 'reason': '检测到用户提供的 SQL，直接执行'}
                yield {'type': 'status', 'message': '检测到 SQL，跳过模型生成，准备执行…'}
            else:
                yield {'type': 'status', 'message': '正在生成对号 SQL…'}
                sql_plan, plan_err = AiDataProbeService._plan_sqls(question, merged_hint, schema_meta, code_meta)
                sqls = sql_plan.get('sqls') or []
                reason_l = (sql_plan.get('reason') or plan_err or '').lower()
                if (not sqls) and code_hint and ('code_only' in reason_l or prefer_code):
                    answer_mode = 'code'

            yield {
                'type': 'sqls',
                'sqls': sqls,
                'reason': sql_plan.get('reason') or plan_err or '',
                'matchedTables': schema_meta.get('matchedTables') or [],
            }

            if answer_mode == 'code' and code_hint and not sqls:
                yield {'type': 'status', 'message': '未生成 SQL，改为根据项目代码作答…'}
                streamed_text = []
                for piece in AiDataProbeService._answer_code_stream(question, code_hint, code_meta):
                    if isinstance(piece, dict) and piece.get('final'):
                        conclusion_payload = piece['final']
                    elif isinstance(piece, dict) and piece.get('error'):
                        yield {'type': 'status', 'message': piece.get('error')}
                    elif isinstance(piece, str) and piece:
                        streamed_text.append(piece)
                        yield {'type': 'delta', 'text': piece}
                if not (conclusion_payload.get('conclusion') or '').strip() and streamed_text:
                    conclusion_payload['conclusion'] = ''.join(streamed_text).strip()
            else:
                if execute and sqls:
                    yield {'type': 'status', 'message': '正在执行只读查询…'}
                    for idx, sql in enumerate(sqls[:MAX_SQLS_PER_TURN]):
                        yield {'type': 'status', 'message': '正在执行 SQL ({}/{})…'.format(idx + 1, min(len(sqls), MAX_SQLS_PER_TURN))}
                        started = time.time()
                        result, run_err = SceneSqlRunner.run_readonly(
                            sql_text=sql,
                            db_config=db_config,
                            env=env_key,
                            max_rows=QUERY_MAX_ROWS,
                        )
                        latency_ms = int((time.time() - started) * 1000)
                        rows = (result or {}).get('rows') or []
                        preview = AiDataProbeService._mask_rows(rows[:MAX_EVIDENCE_ROWS])
                        item = {
                            'sql': SceneSqlRunner.ensure_limit(sql, QUERY_MAX_ROWS),
                            'rowCount': (result or {}).get('rowCount') if not run_err else 0,
                            'rows': preview,
                            'error': run_err or '',
                            'latencyMs': latency_ms,
                        }
                        exec_results.append(item)
                        if preview:
                            evidence.extend(preview)
                        AiDataProbeDao.add_audit(session, {
                            'session_id': probe_session.id,
                            'connection_id': conn.id,
                            'sql_text': item['sql'],
                            'sql_hash': hashlib.sha256(item['sql'].encode('utf-8')).hexdigest()[:64],
                            'row_count': item['rowCount'] or 0,
                            'latency_ms': latency_ms,
                            'success': 0 if run_err else 1,
                            'error_message': run_err or '',
                            'created_by': user_id,
                        })
                        yield {'type': 'exec', 'index': idx, 'item': item}
                elif not execute:
                    exec_results = [{'sql': SceneSqlRunner.ensure_limit(s, QUERY_MAX_ROWS), 'rowCount': 0, 'rows': [], 'error': '', 'skipped': True}
                                    for s in sqls[:MAX_SQLS_PER_TURN]]

                total_rows = sum(int(x.get('rowCount') or 0) for x in exec_results)
                # 查库无结果但有代码上下文时，自动补一轮代码问答
                if (not sqls or total_rows == 0) and code_hint and not embedded_sql:
                    yield {'type': 'status', 'message': '库表结果不足，正在结合项目代码补充分析…'}
                    streamed_text = []
                    for piece in AiDataProbeService._answer_code_stream(question, code_hint, code_meta):
                        if isinstance(piece, dict) and piece.get('final'):
                            conclusion_payload = piece['final']
                            answer_mode = 'code'
                        elif isinstance(piece, dict) and piece.get('error'):
                            yield {'type': 'status', 'message': piece.get('error')}
                        elif isinstance(piece, str) and piece:
                            streamed_text.append(piece)
                            yield {'type': 'delta', 'text': piece}
                    if not (conclusion_payload.get('conclusion') or '').strip() and streamed_text:
                        conclusion_payload['conclusion'] = ''.join(streamed_text).strip()
                        answer_mode = 'code'
                else:
                    yield {'type': 'status', 'message': '正在归纳结论…'}
                    streamed_text = []
                    for piece in AiDataProbeService._conclude_stream(question, exec_results, schema_meta, plan_err, code_hint=code_hint):
                        if isinstance(piece, dict) and piece.get('final'):
                            conclusion_payload = piece['final']
                        elif isinstance(piece, dict) and piece.get('error'):
                            yield {'type': 'status', 'message': piece.get('error')}
                        elif isinstance(piece, str) and piece:
                            streamed_text.append(piece)
                            yield {'type': 'delta', 'text': piece}
                    if not (conclusion_payload.get('conclusion') or '').strip() and streamed_text:
                        conclusion_payload['conclusion'] = ''.join(streamed_text).strip()
                        if not conclusion_payload.get('status'):
                            conclusion_payload['status'] = 'insufficient'

        assistant_content = {
            'question': question,
            'mode': answer_mode,
            'sqls': [x.get('sql') for x in exec_results] if exec_results else sqls,
            'execResults': exec_results,
            'evidence': evidence[:MAX_EVIDENCE_ROWS],
            'conclusion': conclusion_payload.get('conclusion') or '',
            'status': conclusion_payload.get('status') or 'insufficient',
            'highlights': conclusion_payload.get('highlights') or [],
            'schemaMeta': {
                'matchedTables': schema_meta.get('matchedTables') or [],
                'tableCount': schema_meta.get('tableCount') or 0,
                'schemaError': schema_meta.get('schemaError') or '',
            },
            'codeMeta': {
                'repoUrl': code_meta.get('repoUrl') or '',
                'branch': code_meta.get('branch') or '',
                'codeFiles': code_meta.get('codeFiles') or [],
                'codeError': code_meta.get('codeError') or '',
                'repos': code_meta.get('repos') or [],
                'missingRepoTip': code_meta.get('missingRepoTip') or '',
                'synced': bool(code_meta.get('synced')),
                'usedCache': bool(code_meta.get('usedCache')),
                'projectId': conn.project_id,
            },
            'planReason': sql_plan.get('reason') or plan_err or '',
        }
        AiDataProbeDao.create(session, AiDataProbeMessage, {
            'session_id': probe_session.id,
            'role': 'assistant',
            'content': assistant_content,
            'created_by': user_id,
            'is_delete': 0,
        })
        AiDataProbeDao.update_by_id(session, AiDataProbeSession, probe_session.id, {
            'title': (probe_session.title or question[:40])[:255],
            'updated_time': datetime.now(),
        })
        result = {
            'sessionId': probe_session.id,
            'sessionNo': probe_session.session_no,
            'connectionId': conn.id,
            **assistant_content,
        }
        yield {'type': 'done', 'result': result}

    @staticmethod
    def rerun_sql(session, req_data, user_id=None):
        """用户改 SQL 后只读重跑。"""
        req = dict(req_data or {})
        sql = (AiDataProbeService._get(req, 'sql', 'customSql') or '').strip()
        if not sql:
            return {}, 'sql 不能为空'
        question = (AiDataProbeService._get(req, 'question', 'text') or '按用户修订的 SQL 对号').strip()
        req['question'] = question
        req['sql'] = sql
        req['execute'] = True
        return AiDataProbeService.ask(session, req, user_id=user_id)

    # ---------- internals ----------

    @staticmethod
    def _is_code_logic_question(question):
        """判断是否更偏代码/配置逻辑问答，而非查库。"""
        text = (question or '').strip()
        if not text:
            return False
        strong = [
            r'不要查表', r'别查表', r'不查表', r'不查库', r'不要查库',
            r'直接查代码', r'直接看代码', r'问代码', r'看代码', r'代码里',
            r'代码配置', r'代码逻辑', r'源码', r'仓库里',
        ]
        if any(re.search(p, text) for p in strong):
            return True
        soft_hits = 0
        soft = [
            r'有多少种', r'有几种', r'枚举', r'常量', r'配置项', r'开关',
            r'选了?ip', r'选择.?ip', r'场景图', r'怎么实现', r'逻辑是',
            r'配置了', r'硬编码', r'写死',
        ]
        for p in soft:
            if re.search(p, text, re.I):
                soft_hits += 1
        # 明确「有多少种/几种」+ 非典型查数词 → 倾向代码
        if soft_hits >= 2:
            return True
        if soft_hits >= 1 and not re.search(r'(表|库里|多少条|多少行|查询结果|select\b)', text, re.I):
            return True
        return False

    @staticmethod
    def _answer_code_stream(question, code_hint, code_meta=None):
        """基于代码摘录流式作答；yield 文本片段，最后 {'final': payload}。"""
        code_meta = code_meta or {}
        files = code_meta.get('codeFiles') or []
        prompt = (
            '用户问题：\n{}\n\n'
            '已匹配代码文件：{}\n\n'
            '代码摘录：\n{}\n'
        ).format(
            question if len(question) <= 4000 else (question[:4000] + '\n...(已截断)'),
            ', '.join(files[:12]) or '(无明确文件列表)',
            (code_hint or '')[:8000],
        )
        collected = []
        stream_err = ''
        for piece in AIService.chat_plain_stream(
            prompt,
            system_prompt=CODE_ANSWER_SYSTEM,
            read_timeout=75,
            max_tokens=1200,
        ):
            if isinstance(piece, dict) and piece.get('error'):
                stream_err = piece.get('error') or ''
                break
            if isinstance(piece, str) and piece:
                collected.append(piece)

        text = ''.join(collected).strip()
        final = None
        if text:
            parsed = AiDataProbeService._extract_json(text)
            if isinstance(parsed, dict) and parsed.get('conclusion'):
                status = (parsed.get('status') or 'matched').strip()
                if status not in ('matched', 'insufficient', 'not_found', 'mismatch'):
                    status = 'matched'
                highlights = parsed.get('highlights') or []
                if files and not highlights:
                    highlights = files[:6]
                final = {
                    'status': status,
                    'conclusion': str(parsed.get('conclusion')),
                    'highlights': highlights,
                    'mode': 'code',
                }
            else:
                final = {
                    'status': 'matched',
                    'conclusion': text[:2500],
                    'highlights': files[:6],
                    'mode': 'code',
                }
        if not final:
            if stream_err:
                yield {'error': stream_err}
            tip = stream_err or code_meta.get('codeError') or '未能从代码摘录中得出结论'
            final = {
                'status': 'insufficient',
                'conclusion': tip,
                'highlights': files[:6],
                'mode': 'code',
            }
        # 结论文本伪流式输出（避免把中间 JSON 直接刷到对话里）
        out = (final.get('conclusion') or '').strip()
        step = 18
        for i in range(0, len(out), step):
            yield out[i:i + step]
        yield {'final': final}

    @staticmethod
    def _extract_embedded_sql(question):
        """从用户长文本中识别可直接执行的 SELECT/WITH SQL。"""
        text = (question or '').strip()
        if not text:
            return ''
        if re.match(r'(?is)^\s*(with\b|select\b)', text) and len(text) >= 20:
            return text.rstrip(';').strip()
        # 正文里夹带 SQL 块
        blocks = re.findall(
            r'(?is)((?:with\s+[\w\"]+\s+as\s*\([\s\S]+?\)\s*,?\s*)*select\b[\s\S]{20,}?)(?:;|\n\s*\n|$)',
            text,
        )
        if not blocks:
            return ''
        candidate = max(blocks, key=len).strip().rstrip(';').strip()
        if len(candidate) < 40:
            return ''
        # 避免把普通中文叙述误判为 SQL
        if candidate.count(' ') + candidate.count('\n') < 3 and ' from ' not in candidate.lower():
            return ''
        return candidate

    @staticmethod
    def _probe_code_hint(project_id, user_text, matched_tables=None):
        empty = {
            'repoUrl': '', 'branch': '', 'codeFiles': [], 'codeError': '',
            'repos': [], 'missingRepoTip': '', 'synced': False, 'usedCache': False,
        }
        if project_id in (None, ''):
            empty['codeError'] = '连接未绑定项目，跳过代码探查'
            empty['missingRepoTip'] = '想要更准确查询，建议先为连接选择项目，并在项目设置中配置 Git 代码仓库哦'
            return '', empty
        try:
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
            from common.sceneCodeProbe import SceneCodeProbe

            def _job():
                return SceneCodeProbe.build_hint(project_id, user_text, matched_tables=matched_tables)

            executor = ThreadPoolExecutor(max_workers=1)
            try:
                return executor.submit(_job).result(timeout=50)
            except FuturesTimeout:
                empty['codeError'] = '代码探查超时，已跳过代码上下文'
                empty['missingRepoTip'] = ''
                return '', empty
            finally:
                executor.shutdown(wait=False)
        except Exception as exc:
            logger.warning('对号查数代码探查失败 project_id=%s err=%s', project_id, exc)
            empty['codeError'] = '代码探查异常：{}'.format(exc)
            return '', empty

    @staticmethod
    def _plan_sqls(question, hint, schema_meta, code_meta=None):
        tables = schema_meta.get('matchedTables') or []
        code_meta = code_meta or {}
        code_note = ''
        if code_meta.get('codeFiles'):
            code_note = '已结合代码文件：{}'.format(', '.join((code_meta.get('codeFiles') or [])[:8]))
        elif code_meta.get('missingRepoTip') or code_meta.get('codeError'):
            code_note = code_meta.get('codeError') or code_meta.get('missingRepoTip') or ''
        prompt = (
            '用户问题：\n{}\n\n'
            '表结构 + 代码上下文：\n{}\n\n'
            '匹配表：{}\n'
            '代码备注：{}\n'
            '请生成只读对号 SQL（优先代码中的真实表/字段）。'
        ).format(
            question if len(question) <= 6000 else (question[:6000] + '\n...(问题已截断)'),
            (hint or '(无表结构/代码)')[:4000],
            ', '.join(tables) or '(无)',
            code_note or '(无)',
        )
        text, err = AIService.chat_plain(
            prompt,
            system_prompt=SQL_JSON_SYSTEM,
            read_timeout=60,
            max_tokens=1200,
        )
        if err or not text:
            fallback = AiDataProbeService._fallback_sqls(question, schema_meta)
            if fallback:
                return {'sqls': fallback, 'reason': 'LLM 不可用，使用启发式 SQL'}, err or ''
            return {'sqls': [], 'reason': err or '未能生成 SQL'}, err or '未能生成 SQL'
        parsed = AiDataProbeService._extract_json(text)
        sqls = []
        if isinstance(parsed, dict):
            raw = parsed.get('sqls') or []
            if isinstance(raw, str):
                raw = [raw]
            for item in raw:
                s = (item or '').strip().rstrip(';')
                if s:
                    sqls.append(s)
            reason = parsed.get('reason') or ''
        else:
            reason = '模型输出非 JSON'
            # 尝试从文本抠 SELECT
            for block in re.findall(r'(?is)\b(SELECT\b.+?)(?:;|$)', text):
                sqls.append(block.strip())
        sqls = sqls[:MAX_SQLS_PER_TURN]
        if not sqls:
            fallback = AiDataProbeService._fallback_sqls(question, schema_meta)
            if fallback:
                return {'sqls': fallback, 'reason': reason or '回退启发式 SQL'}, ''
        return {'sqls': sqls, 'reason': reason}, ''

    @staticmethod
    def _fallback_sqls(question, schema_meta):
        """无 LLM 时：对匹配表用业务号做简单 LIKE 查询。"""
        tables = schema_meta.get('matchedTables') or []
        details = schema_meta.get('tableDetails') or []
        if not tables:
            return []
        tokens = re.findall(r'[A-Za-z0-9_\-]{4,64}', question or '')
        if not tokens:
            return []
        key = tokens[0]
        sqls = []
        for detail in details[:2]:
            table = detail.get('table')
            cols = [c.get('name') for c in (detail.get('columns') or []) if c.get('name')]
            text_cols = [c for c in cols if re.search(r'(no|code|id|name|phone|mobile|order|uid)', c or '', re.I)]
            if not text_cols:
                text_cols = cols[:3]
            if not table or not text_cols:
                continue
            wheres = ["CAST({} AS TEXT) ILIKE '%{}%'".format(c, key.replace("'", "''")) for c in text_cols[:3]]
            sqls.append(
                'SELECT * FROM "{}" WHERE {} LIMIT 20'.format(table, ' OR '.join(wheres))
            )
        return sqls[:MAX_SQLS_PER_TURN]

    @staticmethod
    def _conclude_stream(question, exec_results, schema_meta, plan_err, code_hint=None):
        """流式结论：yield 文本片段；最后 yield {'final': payload}。"""
        # 无执行结果时直接规则结论，并伪流式输出
        if not exec_results and plan_err and not code_hint:
            final = {
                'status': 'insufficient',
                'conclusion': plan_err or '未能生成可执行 SQL',
                'highlights': [],
            }
            text = final['conclusion']
            step = 20
            for i in range(0, len(text), step):
                yield text[i:i + step]
            yield {'final': final}
            return

        total_rows = sum(int(x.get('rowCount') or 0) for x in exec_results)
        errors = [x.get('error') for x in exec_results if x.get('error')]
        preview = []
        for item in exec_results:
            preview.append({
                'sql': item.get('sql'),
                'rowCount': item.get('rowCount'),
                'error': item.get('error'),
                'rows': (item.get('rows') or [])[:5],
            })
        q_for_llm = question if len(question) <= 4000 else (question[:4000] + '\n...(已截断)')
        code_part = ''
        if code_hint:
            code_part = '\n\n项目代码摘录（可辅助判断）：\n{}'.format((code_hint or '')[:3500])
        prompt = (
            '用户问题：\n{}\n\n查询结果摘要：\n{}\n\n表匹配：{}{}\n'
        ).format(
            q_for_llm,
            json.dumps(preview, ensure_ascii=False)[:6000],
            ', '.join(schema_meta.get('matchedTables') or []),
            code_part,
        )

        collected = []
        stream_err = ''
        for piece in AIService.chat_plain_stream(
            prompt,
            system_prompt=CONCLUSION_SYSTEM,
            read_timeout=60,
            max_tokens=800,
        ):
            if isinstance(piece, dict) and piece.get('error'):
                stream_err = piece.get('error') or ''
                break
            if isinstance(piece, str) and piece:
                collected.append(piece)

        text = ''.join(collected).strip()
        final = None
        if text:
            parsed = AiDataProbeService._extract_json(text)
            if isinstance(parsed, dict) and parsed.get('conclusion'):
                status = (parsed.get('status') or 'insufficient').strip()
                if status not in ('matched', 'mismatch', 'not_found', 'insufficient'):
                    status = 'insufficient'
                final = {
                    'status': status,
                    'conclusion': str(parsed.get('conclusion')),
                    'highlights': parsed.get('highlights') or [],
                }
            else:
                final = {
                    'status': 'matched' if total_rows > 0 else 'insufficient',
                    'conclusion': text[:2000],
                    'highlights': [],
                }

        if not final:
            if stream_err:
                yield {'error': stream_err}
            if errors and total_rows == 0:
                final = {
                    'status': 'insufficient',
                    'conclusion': '查询执行失败：{}'.format(errors[0]),
                    'highlights': [],
                }
            elif total_rows == 0:
                final = {
                    'status': 'not_found',
                    'conclusion': '未查到匹配数据，请确认业务号/表名或补充条件。',
                    'highlights': [],
                }
            else:
                final = {
                    'status': 'matched',
                    'conclusion': '已查到 {} 行相关数据，请核对证据字段是否符合预期。'.format(total_rows),
                    'highlights': [],
                }

        # 结论文本伪流式输出（避免把中间 JSON 直接刷到对话里）
        out = (final.get('conclusion') or '').strip()
        step = 18
        for i in range(0, len(out), step):
            yield out[i:i + step]
        yield {'final': final}

    @staticmethod
    def _conclude(question, exec_results, schema_meta, plan_err):
        final = {
            'status': 'insufficient',
            'conclusion': plan_err or '未能生成可执行 SQL',
            'highlights': [],
        }
        for piece in AiDataProbeService._conclude_stream(question, exec_results, schema_meta, plan_err):
            if isinstance(piece, dict) and piece.get('final'):
                final = piece['final']
        return final

    @staticmethod
    def _mask_rows(rows):
        masked = []
        for row in rows or []:
            if not isinstance(row, dict):
                continue
            item = {}
            for key, value in row.items():
                text = '' if value is None else str(value)
                if len(text) > MAX_CELL_CHARS:
                    text = text[:MAX_CELL_CHARS] + '…'
                key_l = (key or '').lower()
                if re.search(r'(phone|mobile|tel)', key_l) and len(text) >= 7:
                    text = text[:3] + '****' + text[-4:]
                elif re.search(r'(id_card|idcard|identity)', key_l) and len(text) >= 8:
                    text = text[:4] + '**********' + text[-4:]
                item[key] = text
            masked.append(item)
        return masked

    @staticmethod
    def _extract_json(text):
        raw = (text or '').strip()
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            pass
        match = re.search(r'\{[\s\S]*\}', raw)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except Exception:
            return None

    @staticmethod
    def _parse_connection_payload(req_data, require_password=True):
        name = (AiDataProbeService._get(req_data, 'name') or '').strip()
        host = (AiDataProbeService._get(req_data, 'host') or '').strip()
        port = AiDataProbeService._get(req_data, 'port')
        database_name = (
            AiDataProbeService._get(req_data, 'databaseName', 'database_name', 'database') or ''
        ).strip()
        username = (AiDataProbeService._get(req_data, 'username', 'user') or '').strip()
        password = AiDataProbeService._get(req_data, 'password')
        if password is None:
            password = ''
        env = (AiDataProbeService._get(req_data, 'env') or 'test').strip().lower()
        db_type = (AiDataProbeService._get(req_data, 'dbType', 'db_type') or 'postgresql').strip().lower()
        if db_type not in ('postgresql', 'postgres', 'mysql'):
            return {}, '暂仅支持 postgresql / mysql（一期执行仅 postgresql）'
        if db_type == 'postgres':
            db_type = 'postgresql'
        if not name:
            return {}, 'name 为必传参数'
        if not host or port in (None, '') or not database_name or not username:
            return {}, 'host/port/database/username 为必传参数'
        if require_password and not str(password):
            return {}, 'password 为必传参数'
        try:
            port = int(port)
        except (TypeError, ValueError):
            return {}, 'port 必须为数字'
        env_key, err = SceneSqlRunner.validate_env(env)
        if err:
            return {}, err
        enabled = AiDataProbeService._get(req_data, 'enabled')
        if enabled in (None, ''):
            enabled = 1
        else:
            enabled = 1 if enabled in (True, 1, '1', 'true', 'True') else 0
        values = {
            'name': name[:128],
            'db_type': db_type,
            'host': host[:256],
            'port': port,
            'database_name': database_name[:128],
            'username': username[:128],
            'password': str(password),
            'product_id': AiDataProbeService._to_int_or_none(
                AiDataProbeService._get(req_data, 'productId', 'product_id')
            ),
            'product_name': (AiDataProbeService._get(req_data, 'productName', 'product_name') or '')[:128],
            'project_id': AiDataProbeService._to_int_or_none(
                AiDataProbeService._get(req_data, 'projectId', 'project_id')
            ),
            'project_name': (AiDataProbeService._get(req_data, 'projectName', 'project_name') or '')[:128],
            'env': env_key,
            'remark': AiDataProbeService._get(req_data, 'remark') or '',
            'enabled': enabled,
        }
        return values, ''

    @staticmethod
    def _conn_db_config(obj):
        return {
            'host': obj.host,
            'port': obj.port,
            'user': obj.username,
            'password': obj.password or '',
            'database': obj.database_name,
        }

    @staticmethod
    def _conn_to_dict(obj):
        if not obj:
            return {}
        return {
            'id': obj.id,
            'name': obj.name,
            'dbType': obj.db_type,
            'host': obj.host,
            'port': obj.port,
            'databaseName': obj.database_name,
            'username': obj.username,
            'password': PASSWORD_MASK if obj.password else '',
            'hasPassword': bool(obj.password),
            'productId': getattr(obj, 'product_id', None),
            'productName': getattr(obj, 'product_name', None),
            'projectId': obj.project_id,
            'projectName': obj.project_name,
            'env': obj.env,
            'remark': obj.remark,
            'enabled': obj.enabled,
            'createdTime': AiDataProbeService._fmt_time(obj.created_time),
            'updatedTime': AiDataProbeService._fmt_time(obj.updated_time),
        }

    @staticmethod
    def _session_to_dict(obj):
        if not obj:
            return {}
        return {
            'id': obj.id,
            'sessionNo': obj.session_no,
            'connectionId': obj.connection_id,
            'projectId': obj.project_id,
            'title': obj.title,
            'status': obj.status,
            'createdTime': AiDataProbeService._fmt_time(obj.created_time),
            'updatedTime': AiDataProbeService._fmt_time(obj.updated_time),
        }

    @staticmethod
    def _next_session_no(session):
        stamp = datetime.now().strftime('%Y%m%d%H%M%S')
        prefix = 'ADP{}'.format(stamp)
        count = session.query(AiDataProbeSession).filter(
            AiDataProbeSession.session_no.like(prefix + '%')
        ).count()
        return '{}{:03d}'.format(prefix, (count or 0) + 1)

    @staticmethod
    def _fmt_time(value):
        if not value:
            return ''
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return str(value)

    @staticmethod
    def _get(data, *keys):
        if not isinstance(data, dict):
            return None
        for key in keys:
            if key in data and data.get(key) not in (None,):
                return data.get(key)
        return None

    @staticmethod
    def _to_int_or_none(value):
        if value in (None, ''):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
