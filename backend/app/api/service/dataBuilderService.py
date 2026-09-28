# encoding: UTF-8
"""造数工厂服务：执行 steps + AI 场景生成。"""
from __future__ import unicode_literals

import json
import re
from datetime import datetime

from common.dataBuilderExecutor import DataBuilderExecutor
from logger import logger
from ..dao.dataBuilderDao import DataBuilderDao
from ..model.dataBuilderModel import DataBuilder, DataTask
from .aiService import AIService


class DataBuilderService(object):
    @staticmethod
    def create(session, model_cls, add_info):
        return DataBuilderDao.create(session, model_cls, add_info)

    @staticmethod
    def update_by_id(session, model_cls, obj_id, update_info, soft_delete=True):
        return DataBuilderDao.update_by_id(session, model_cls, obj_id, update_info, soft_delete)

    @staticmethod
    def get_by_id(session, model_cls, obj_id, soft_delete=True):
        return DataBuilderDao.get_by_id(session, model_cls, obj_id, soft_delete)

    @staticmethod
    def list_by_filters(session, model_cls, filter_list, page_num=1, page_size=20, order_column=None):
        return DataBuilderDao.list_by_filters(
            session, model_cls, filter_list, int(page_num), int(page_size), order_column
        )

    @staticmethod
    def delete_by_id(session, model_cls, obj_id):
        return DataBuilderDao.delete_by_id(session, model_cls, obj_id)

    @staticmethod
    def execute_builder(session, builder_id, params=None, created_by=None):
        builder = DataBuilderDao.get_by_id(session, DataBuilder, builder_id)
        if not builder:
            return {}, '未查询到对应造数器！'
        params = params or {}
        task_info = {
            'builder_id': builder.id,
            'project_id': builder.project_id,
            'params': params,
            'status': 1,
            'created_by': created_by,
        }
        task_id, err_msg = DataBuilderDao.create(session, DataTask, task_info)
        if err_msg:
            return {}, err_msg
        try:
            executor = DataBuilderExecutor(
                builder.definition or {}, {}, project_id=builder.project_id
            )
            result_data = executor.execute(params)
            DataBuilderDao.update_by_id(session, DataTask, task_id, {
                'status': 2,
                'result_data': result_data,
                'completed_time': datetime.now(),
            }, soft_delete=False)
            return {'taskId': task_id, 'data': result_data}, ''
        except Exception as e:
            DataBuilderDao.update_by_id(session, DataTask, task_id, {
                'status': 3,
                'error_message': str(e),
                'completed_time': datetime.now(),
            }, soft_delete=False)
            return {}, '执行造数失败！{}'.format(e)

    @staticmethod
    def list_tasks(session, project_id=None, builder_id=None, page_no=1, page_size=20):
        filters = []
        if project_id not in (None, ''):
            filters.append(DataTask.project_id == int(project_id))
        if builder_id not in (None, ''):
            filters.append(DataTask.builder_id == int(builder_id))
        items, total = DataBuilderDao.list_by_filters(
            session, DataTask, filters, int(page_no), int(page_size), DataTask.created_time
        )
        return items, total

    @classmethod
    def ai_generate(cls, prompt, project_id=None, db_project=None, env=None, hint=None,
                    product_name=None, project_name=None):
        text = (prompt or '').strip()
        if not text:
            return {}, 'prompt 为必传参数'
        env_key = (env or 'st').strip() or 'st'
        dbp = (db_project or '').strip() or ('project' if project_id not in (None, '') else 'ZHYY')
        context = cls._context_label(product_name, project_name, project_id)
        schema_hint, schema_meta = cls._probe_schema_hint(project_id, env_key, text)
        code_hint, code_meta = cls._probe_code_hint(
            project_id, text, schema_meta.get('matchedTables') or []
        )
        merged_hint = '\n\n'.join([x for x in [(hint or '').strip(), schema_hint, code_hint] if x])
        fallback = cls._fallback_scene(
            text, dbp, env_key,
            product_name=product_name,
            project_name=project_name,
            matched_tables=schema_meta.get('matchedTables') or [],
            table_details=schema_meta.get('tableDetails') or [],
        )
        system_prompt = cls._build_generate_prompt(
            text, dbp, env_key, merged_hint,
            product_name=product_name, project_name=project_name, project_id=project_id,
            has_schema=bool(schema_hint),
            has_code=bool(code_hint),
        )
        parsed, err = cls._ai_json(system_prompt, fallback)
        draft = cls._normalize_draft(parsed, fallback)
        draft = cls._repair_sql_steps_with_schema(draft, schema_meta.get('tableDetails') or [], project_name or '')
        draft = cls._stamp_sql_connection(draft, dbp, env_key)
        draft['meta'] = {
            'projectId': project_id,
            'productName': product_name or '',
            'projectName': project_name or '',
            'context': context,
            'env': env_key,
            'matchedTables': schema_meta.get('matchedTables') or [],
            'tableCount': schema_meta.get('tableCount') or 0,
            'schemaError': schema_meta.get('schemaError') or '',
            'repoUrl': code_meta.get('repoUrl') or '',
            'repoBranch': code_meta.get('branch') or '',
            'codeFiles': code_meta.get('codeFiles') or [],
            'codeError': code_meta.get('codeError') or '',
            'generatedBy': 'ai' if not err else 'fallback',
            'aiError': err or '',
        }
        return draft, ''

    @classmethod
    def ai_refine(cls, draft, instruction, env=None, db_project=None, project_id=None,
                  product_name=None, project_name=None):
        draft = draft or {}
        instruction = (instruction or '').strip()
        if not instruction:
            return {}, 'instruction 为必传参数'
        meta = draft.get('meta') or {}
        env_key = (env or meta.get('env') or 'st').strip() or 'st'
        dbp = (db_project or '').strip() or ('project' if (project_id or meta.get('projectId')) else 'ZHYY')
        product_name = product_name or meta.get('productName') or ''
        project_name = project_name or meta.get('projectName') or ''
        context = cls._context_label(product_name, project_name, project_id or meta.get('projectId'))
        schema_hint, schema_meta = cls._probe_schema_hint(
            project_id or meta.get('projectId'), env_key, instruction
        )
        code_hint, code_meta = cls._probe_code_hint(
            project_id or meta.get('projectId'),
            instruction,
            schema_meta.get('matchedTables') or meta.get('matchedTables') or [],
        )
        fallback = cls._normalize_draft(
            draft,
            cls._fallback_scene(
                instruction, dbp, env_key,
                product_name=product_name,
                project_name=project_name,
                matched_tables=schema_meta.get('matchedTables') or meta.get('matchedTables') or [],
                table_details=schema_meta.get('tableDetails') or [],
            ),
        )
        prompt = (
            '你是测试造数助手。请基于当前场景草稿按用户指令修改，只输出 JSON。\n'
            '字段：name, description, tags, inputSchema, params, definition(steps/output)。\n'
            'steps.type 仅允许 sql/set_var/assert；sql step 需含 db_project/env/sql。\n'
            '当前上下文：{context}；默认 env={env} db_project={dbp}。\n'
            '必须围绕该产品/项目业务造数，禁止使用无关的默认演示项目/演示库占位名。\n'
            '若下方提供了真实表结构/代码，必须改用真实表 INSERT 造数，禁止 SELECT 1 / demo_data。\n'
            'INSERT 字段必须来自真实表结构，禁止臆造 name 等不存在字段。\n'
            '禁止 DROP/TRUNCATE/ALTER；禁止生产环境 env。\n'
            '表结构：\n{schema}\n\n代码上下文：\n{code}\n'
            '当前草稿：{draft}\n用户指令：{instruction}\n'
        ).format(
            context=context,
            env=env_key,
            dbp=dbp,
            schema=schema_hint or '（无自动表结构，请基于现有草稿修改）',
            code=code_hint or '（无代码上下文）',
            draft=json.dumps(fallback, ensure_ascii=False)[:8000],
            instruction=instruction,
        )
        parsed, err = cls._ai_json(prompt, fallback)
        result = cls._normalize_draft(parsed, fallback)
        result = cls._repair_sql_steps_with_schema(
            result, schema_meta.get('tableDetails') or [], project_name or ''
        )
        result = cls._stamp_sql_connection(result, dbp, env_key)
        result['meta'] = {
            'projectId': project_id or meta.get('projectId'),
            'productName': product_name,
            'projectName': project_name,
            'context': context,
            'env': env_key,
            'matchedTables': schema_meta.get('matchedTables') or meta.get('matchedTables') or [],
            'tableCount': schema_meta.get('tableCount') or meta.get('tableCount') or 0,
            'schemaError': schema_meta.get('schemaError') or '',
            'repoUrl': code_meta.get('repoUrl') or meta.get('repoUrl') or '',
            'repoBranch': code_meta.get('branch') or meta.get('repoBranch') or '',
            'codeFiles': code_meta.get('codeFiles') or meta.get('codeFiles') or [],
            'codeError': code_meta.get('codeError') or '',
            'generatedBy': 'ai' if not err else 'fallback',
            'aiError': err or '',
        }
        return result, ''

    @classmethod
    def draft_from_sql(cls, sql_text, project_id=None, db_project=None, env=None, name=None,
                       product_name=None, project_name=None):
        from common.sceneSqlRunner import SceneSqlRunner
        sql, err = SceneSqlRunner.validate_sql(sql_text)
        if err:
            return {}, err
        env_key, err = SceneSqlRunner.validate_env(env or 'st')
        if err:
            return {}, err
        dbp = (db_project or '').strip() or ('project' if project_id not in (None, '') else 'ZHYY')
        context = cls._context_label(product_name, project_name, project_id)
        title = (name or '').strip() or 'SQL造数-{}'.format(project_name or '对话')
        draft = {
            'name': title,
            'description': '由对话直接粘贴 SQL 生成的草稿（{}），确认前不写库。'.format(context),
            'tags': ['SQL', '对话'],
            'inputSchema': {'type': 'object', 'properties': {}},
            'params': {},
            'definition': {
                'steps': [{
                    'type': 'sql',
                    'name': 'run_sql',
                    'db_project': dbp,
                    'env': env_key,
                    'sql': sql,
                }],
                'output': {},
            },
            'meta': {
                'projectId': project_id,
                'productName': product_name or '',
                'projectName': project_name or '',
                'context': context,
                'env': env_key,
                'generatedBy': 'sql',
                'aiError': '',
            },
        }
        return draft, ''

    @classmethod
    def ocr_generate(cls, image_bytes, mime_type=None, project_id=None, db_project=None, env=None, prompt=None,
                     product_name=None, project_name=None):
        """截图识图 → 造数草稿。确认前不写库。"""
        if not image_bytes:
            return {}, '图片内容为空'
        if len(image_bytes) > 5 * 1024 * 1024:
            return {}, '图片超过 5MB 上限'
        mime = (mime_type or 'image/png').split(';')[0].strip().lower()
        if mime not in ('image/png', 'image/jpeg', 'image/jpg', 'image/webp'):
            return {}, '仅支持 png/jpeg/webp'
        env_key = (env or 'st').strip() or 'st'
        dbp = (db_project or '').strip() or ('project' if project_id not in (None, '') else 'ZHYY')
        context = cls._context_label(product_name, project_name, project_id)
        schema_hint, schema_meta = cls._probe_schema_hint(project_id, env_key, prompt or '')
        code_hint, code_meta = cls._probe_code_hint(
            project_id, prompt or '', schema_meta.get('matchedTables') or []
        )
        ocr_prompt = (
            '你是测试造数助手。请识别图片中与造数相关的文字（表名、字段、示例数据、SQL 或需求说明），'
            '并生成可审阅的造数场景 JSON（不要执行）。'
            '只输出 JSON：name, description, tags, inputSchema, params, definition(steps/output)。'
            'steps.type 仅 sql/set_var/assert；sql 需 db_project/env/sql。'
            '当前上下文：{}。默认 db_project={} env={}。'
            '必须围绕该产品/项目业务造数，禁止使用无关默认演示项目名。'
            '若提供了真实表结构/代码，优先用真实表 INSERT 造数，禁止 SELECT 1 / demo_data。'
            '禁止生产 env，禁止 DROP/TRUNCATE/ALTER。'
            '表结构：\n{}\n\n代码上下文：\n{}\n'
            '用户补充：{}'
        ).format(
            context, dbp, env_key,
            schema_hint or '（无）',
            code_hint or '（无）',
            (prompt or '无').strip()[:500],
        )
        result, err = AIService.chat_with_image(ocr_prompt, image_bytes, mime)
        fallback = cls._fallback_scene(
            '截图造数：{}'.format((prompt or '识别结果')[:40]),
            dbp,
            env_key,
            product_name=product_name,
            project_name=project_name,
            matched_tables=schema_meta.get('matchedTables') or [],
        )
        if err or not result:
            # 降级：把失败信息放进 description，仍给可编辑草稿
            fallback['description'] = '截图识别失败（{}）。请改用自然语言或 SQL，或更换支持识图的模型。'.format(err or '无返回')
            fallback = cls._stamp_sql_connection(fallback, dbp, env_key)
            fallback['meta'] = {
                'projectId': project_id,
                'productName': product_name or '',
                'projectName': project_name or '',
                'context': context,
                'env': env_key,
                'matchedTables': schema_meta.get('matchedTables') or [],
                'tableCount': schema_meta.get('tableCount') or 0,
                'schemaError': schema_meta.get('schemaError') or '',
                'repoUrl': code_meta.get('repoUrl') or '',
                'repoBranch': code_meta.get('branch') or '',
                'codeFiles': code_meta.get('codeFiles') or [],
                'codeError': code_meta.get('codeError') or '',
                'generatedBy': 'ocr_fallback',
                'aiError': err or 'AI无返回',
                'ocrText': '',
            }
            return fallback, ''
        parsed, parse_err = cls._parse_ai_json_text(result, fallback)
        draft = cls._normalize_draft(parsed, fallback)
        draft = cls._stamp_sql_connection(draft, dbp, env_key)
        draft['meta'] = {
            'projectId': project_id,
            'productName': product_name or '',
            'projectName': project_name or '',
            'context': context,
            'env': env_key,
            'matchedTables': schema_meta.get('matchedTables') or [],
            'tableCount': schema_meta.get('tableCount') or 0,
            'schemaError': schema_meta.get('schemaError') or '',
            'repoUrl': code_meta.get('repoUrl') or '',
            'repoBranch': code_meta.get('branch') or '',
            'codeFiles': code_meta.get('codeFiles') or [],
            'codeError': code_meta.get('codeError') or '',
            'generatedBy': 'ocr' if not parse_err else 'ocr_fallback',
            'aiError': parse_err or '',
            'ocrText': (result or '')[:2000],
        }
        return draft, ''

    @classmethod
    def save_as_scene(cls, session, payload, created_by=None):
        payload = payload or {}
        project_id = payload.get('projectId') or payload.get('project_id')
        name = (payload.get('name') or '').strip()
        definition = payload.get('definition')
        if not project_id or not name or definition is None:
            return 0, 'projectId、name、definition 为必传参数'
        tags = payload.get('tags') or []
        if isinstance(tags, str):
            tags = [t.strip() for t in re.split(r'[,，]', tags) if t.strip()]
        add_info = {
            'project_id': int(project_id),
            'name': name,
            'description': payload.get('description') or '',
            'builder_type': int(payload.get('builderType') or payload.get('builder_type') or 1),
            'definition': definition,
            'input_schema': payload.get('inputSchema') or payload.get('input_schema') or {},
            'output_example': payload.get('outputExample') or payload.get('output_example') or {},
            'tags': tags,
            'source': payload.get('source') or 'saved_from_task',
            'scene_key': payload.get('sceneKey') or payload.get('scene_key') or None,
            'created_by': created_by,
            'is_delete': 0,
        }
        return DataBuilderDao.create(session, DataBuilder, add_info)

    @staticmethod
    def _probe_code_hint(project_id, user_text, matched_tables=None):
        if project_id in (None, ''):
            return '', {'codeFiles': [], 'codeError': '缺少 projectId，跳过代码探查', 'repoUrl': '', 'branch': ''}
        try:
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
            from common.sceneCodeProbe import SceneCodeProbe

            def _job():
                return SceneCodeProbe.build_hint(project_id, user_text, matched_tables=matched_tables)

            executor = ThreadPoolExecutor(max_workers=1)
            try:
                return executor.submit(_job).result(timeout=45)
            except FuturesTimeout:
                return '', {
                    'codeFiles': [],
                    'codeError': '代码探查超时，已跳过代码上下文',
                    'repoUrl': '',
                    'branch': '',
                }
            finally:
                executor.shutdown(wait=False)
        except Exception as exc:
            logger.warning('代码探查失败 project_id=%s err=%s', project_id, exc)
            return '', {
                'codeFiles': [],
                'codeError': '代码探查异常：{}'.format(exc),
                'repoUrl': '',
                'branch': '',
            }

    @staticmethod
    def _probe_schema_hint(project_id, env, user_text):
        if project_id in (None, '') or not (env or '').strip():
            return '', {'matchedTables': [], 'tableCount': 0, 'schemaError': '缺少 projectId/env，跳过探表'}
        try:
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
            from common.sceneSchemaProbe import SceneSchemaProbe

            def _job():
                return SceneSchemaProbe.build_hint(project_id, env, user_text)

            executor = ThreadPoolExecutor(max_workers=1)
            try:
                return executor.submit(_job).result(timeout=20)
            except FuturesTimeout:
                return '', {
                    'matchedTables': [],
                    'tableCount': 0,
                    'schemaError': '探表超时，已跳过表结构上下文',
                }
            finally:
                executor.shutdown(wait=False)
        except Exception as exc:
            logger.warning('探表失败 project_id=%s env=%s err=%s', project_id, env, exc)
            return '', {
                'matchedTables': [],
                'tableCount': 0,
                'schemaError': '探表异常：{}'.format(exc),
            }

    @staticmethod
    def _context_label(product_name=None, project_name=None, project_id=None):
        product = (product_name or '').strip() or '未指定产品'
        project = (project_name or '').strip()
        if not project:
            project = '项目#{}'.format(project_id) if project_id not in (None, '') else '未指定项目'
        return '产品={} / 项目={}'.format(product, project)

    @staticmethod
    def _build_generate_prompt(user_text, db_project, env, hint, product_name=None, project_name=None,
                               project_id=None, has_schema=False, has_code=False):
        hint_text = hint or '无额外表结构提示'
        context = DataBuilderService._context_label(product_name, project_name, project_id)
        schema_rule = (
            '已提供真实表结构：必须选用其中的表与字段生成可执行 INSERT（可 RETURNING），'
            '禁止 SELECT 1 / demo_data / 演示项目 等占位 SQL；有外键时先插父表再插子表；'
            '禁止写入表结构中不存在的字段（例如表无 name 就不要写 name）。\n'
            if has_schema else
            '未拿到真实表结构时，可用可运行演示 SQL，并在 description 说明需补充表信息。\n'
        )
        code_rule = (
            '已提供业务代码摘录：请结合实体/Mapper/SQL 逻辑理解必填字段、默认值与关联，'
            '不要编造代码中不存在的表或字段。\n'
            if has_code else
            '未提供代码上下文时，仅依据表结构与用户需求生成。\n'
        )
        return (
            '你是测试平台造数助手。根据用户需求生成可审阅的造数场景 JSON，不要执行。\n'
            '只输出 JSON 对象，字段：name, description, tags(数组), '
            'inputSchema(JSON Schema 风格), params(默认参数对象), '
            'definition: {{steps:[], output:{{}}}}。\n'
            'steps 每项含 type/name；sql 类型必须含 db_project, env, sql，可选 extract。\n'
            'set_var 用 vars；assert 用 expr 如 steps.xxx.rowCount >= 1。\n'
            '当前上下文：{context}。默认 db_project={db_project} env={env}。\n'
            '必须围绕该产品/项目业务造数；name/description 请使用当前项目名称。\n'
            '{schema_rule}{code_rule}'
            '禁止生产 env，禁止 DROP/TRUNCATE/ALTER。\n'
            '表结构与代码提示：\n{hint}\n用户需求：{user_text}\n'
        ).format(
            context=context,
            db_project=db_project,
            env=env,
            schema_rule=schema_rule,
            code_rule=code_rule,
            hint=hint_text[:4000],
            user_text=user_text,
        )

    @staticmethod
    def _fallback_scene(user_text, db_project, env, product_name=None, project_name=None,
                        matched_tables=None, table_details=None):
        from common.sceneSchemaProbe import SceneSchemaProbe
        project_label = (project_name or '').strip() or '当前项目'
        short = (user_text or '{}造数'.format(project_label))[:40]
        details = table_details if isinstance(table_details, list) else []
        detail_map = {}
        for item in details:
            if isinstance(item, dict) and item.get('table'):
                detail_map[str(item.get('table'))] = item
        tables = [t for t in (matched_tables or []) if t and re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', str(t))]
        if not tables and details:
            tables = [d.get('table') for d in details if d.get('table')]
        table = tables[0] if tables else None
        if table:
            columns = (detail_map.get(table) or {}).get('columns') or []
            sql, returning = SceneSchemaProbe.build_insert_sql(
                table, columns, project_label=project_label, user_text=user_text
            )
            if not sql:
                sql = "SELECT 1 AS id /* 表 {} 字段未知，请手工补 INSERT */".format(table)
                returning = 'id'
            desc = (
                'AI 兜底草稿（{}）：已按表 {} 真实字段生成 INSERT，请确认后执行。原始需求：{}'
            ).format(
                DataBuilderService._context_label(product_name, project_name),
                ', '.join(tables[:5]),
                user_text,
            )
            extract = {'demo_id': returning} if returning else {}
            steps = [{
                'type': 'sql',
                'name': 'insert_{}'.format(table),
                'db_project': db_project,
                'env': env,
                'sql': sql,
                'extract': extract,
            }]
        else:
            desc = 'AI 兜底草稿（产品={} / 项目={}）：未匹配到表，请补充表名。原始需求：{}'.format(
                (product_name or '').strip() or '未指定',
                project_label,
                user_text,
            )
            steps = [{
                'type': 'sql',
                'name': 'demo_select',
                'db_project': db_project,
                'env': env,
                'sql': "SELECT 1 AS id, '{}' AS project_name".format(project_label.replace("'", "''")),
                'extract': {'demo_id': 'id'},
            }]
        return {
            'name': '{}-{}'.format(project_label, short),
            'description': desc,
            'tags': ['AI', '草稿'],
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'phone': {'type': 'string', 'title': '手机号'},
                    'count': {'type': 'integer', 'title': '数量', 'default': 1},
                },
            },
            'params': {'phone': '', 'count': 1},
            'definition': {
                'steps': steps + [{
                    'type': 'set_var',
                    'name': 'bind',
                    'vars': {'demoId': '{{steps.' + steps[0]['name'] + '.demo_id}}'},
                }],
                'output': {
                    'demoId': '{{param.demoId}}',
                    'phone': '{{param.phone}}',
                },
            },
        }

    @staticmethod
    def _repair_sql_steps_with_schema(draft, table_details, project_label=''):
        """若 AI/兜底 SQL 使用了不存在字段（如 name），按真实表结构重写 INSERT。"""
        from common.sceneSchemaProbe import SceneSchemaProbe
        if not isinstance(draft, dict) or not table_details:
            return draft
        detail_map = {}
        for item in table_details:
            if isinstance(item, dict) and item.get('table'):
                detail_map[str(item.get('table')).lower()] = item
        definition = draft.get('definition') if isinstance(draft.get('definition'), dict) else {}
        steps = definition.get('steps') if isinstance(definition.get('steps'), list) else []
        changed = False
        for step in steps:
            if not isinstance(step, dict):
                continue
            if (step.get('type') or '').strip().lower() != 'sql':
                continue
            sql = (step.get('sql') or '').strip()
            matched = re.search(
                r'insert\s+into\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)',
                sql,
                re.I,
            )
            if not matched:
                continue
            table = matched.group(1)
            used_cols = [c.strip().strip('"') for c in matched.group(2).split(',') if c.strip()]
            detail = detail_map.get(table.lower())
            if not detail:
                continue
            real_cols = {(c.get('name') or '').lower() for c in (detail.get('columns') or [])}
            if not real_cols:
                continue
            invalid = [c for c in used_cols if c.lower() not in real_cols]
            if not invalid:
                continue
            new_sql, returning = SceneSchemaProbe.build_insert_sql(
                detail.get('table') or table,
                detail.get('columns') or [],
                project_label=project_label or '测试数据',
                user_text=draft.get('description') or '',
            )
            if not new_sql:
                continue
            step['sql'] = new_sql
            if returning:
                extract = step.get('extract') if isinstance(step.get('extract'), dict) else {}
                extract['demo_id'] = returning
                step['extract'] = extract
            changed = True
        if changed:
            definition['steps'] = steps
            draft['definition'] = definition
            desc = draft.get('description') or ''
            if '已按真实字段校正' not in desc:
                draft['description'] = (desc + '（已按真实字段校正 INSERT）').strip()
        return draft

    @staticmethod
    def _stamp_sql_connection(draft, db_project, env):
        """统一把草稿里 sql step 的 env/db_project 写成当前选择。"""
        if not isinstance(draft, dict):
            return draft
        definition = draft.get('definition') if isinstance(draft.get('definition'), dict) else {}
        steps = definition.get('steps') if isinstance(definition.get('steps'), list) else []
        for step in steps:
            if not isinstance(step, dict):
                continue
            if (step.get('type') or '').strip().lower() != 'sql':
                continue
            if env:
                step['env'] = env
            if db_project:
                step['db_project'] = db_project
        definition['steps'] = steps
        draft['definition'] = definition
        return draft

    @staticmethod
    def _normalize_draft(parsed, fallback):
        base = fallback if isinstance(fallback, dict) else {}
        data = parsed if isinstance(parsed, dict) else {}
        definition = data.get('definition') if isinstance(data.get('definition'), dict) else {}
        fb_def = base.get('definition') if isinstance(base.get('definition'), dict) else {}
        steps = definition.get('steps')
        if not isinstance(steps, list) or not steps:
            steps = fb_def.get('steps') or []
        output = definition.get('output')
        if output is None:
            output = fb_def.get('output') or {}
        tags = data.get('tags')
        if not isinstance(tags, list):
            tags = base.get('tags') or []
        return {
            'name': data.get('name') or base.get('name') or '未命名场景',
            'description': data.get('description') or base.get('description') or '',
            'tags': tags,
            'inputSchema': data.get('inputSchema') or data.get('input_schema') or base.get('inputSchema') or {},
            'params': data.get('params') if isinstance(data.get('params'), dict) else (base.get('params') or {}),
            'definition': {'steps': steps, 'output': output},
        }

    @staticmethod
    def _ai_json(prompt, fallback):
        system_prompt = (
            '你是测试造数助手。只输出一个合法 JSON 对象，不要 Markdown，不要解释，'
            '不要输出知识库问答格式。'
        )
        # 控制上下文体积，避免网关 504
        compact_prompt = (prompt or '')[:6000]
        result, err = AIService.chat_plain(
            compact_prompt,
            system_prompt=system_prompt,
            read_timeout=50,
            max_tokens=2048,
        )
        if err or not result:
            return fallback, err or 'AI无返回'
        return DataBuilderService._parse_ai_json_text(result, fallback)

    @staticmethod
    def _parse_ai_json_text(result, fallback):
        try:
            text = AIService._extract_json_text(result) if hasattr(AIService, '_extract_json_text') else result
            if not (text or '').strip().startswith('{'):
                match = re.search(r'\{[\s\S]*\}', text or '')
                text = match.group(0) if match else text
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                return fallback, 'AI JSON 不是对象'
            return parsed, ''
        except Exception as parse_err:
            logger.warning('造数 AI JSON 解析失败：%s', parse_err)
            return fallback, str(parse_err)
