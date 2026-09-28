# encoding: UTF-8
"""从项目环境库探查表结构，供对话造数自动选表。"""
from __future__ import unicode_literals

import re

import psycopg2
from psycopg2.extras import RealDictCursor

from common.sceneSqlRunner import SceneSqlRunner
from logger import logger

# 中文业务词 → 表名常见英文片段
KEYWORD_ALIASES = {
    '订单': ['order', 'orders', 'trade', 'bill'],
    '用户': ['user', 'users', 'account', 'member', 'customer'],
    '会员': ['member', 'vip', 'customer'],
    '项目': ['project', 'projects', 'prj'],
    '产品': ['product', 'products', 'goods', 'sku', 'item'],
    '商品': ['product', 'goods', 'sku', 'item', 'spu'],
    '帖子': ['post', 'posts', 'article', 'feed', 'moment', 'topic'],
    '文章': ['article', 'post', 'posts', 'blog'],
    '评论': ['comment', 'comments', 'reply'],
    '支付': ['pay', 'payment', 'trade', 'cashier'],
    '组织': ['org', 'organization', 'dept', 'department'],
    '部门': ['dept', 'department'],
    '角色': ['role', 'roles'],
    '权限': ['perm', 'permission', 'auth'],
    '任务': ['task', 'job'],
    '计划': ['plan', 'schedule'],
    '用例': ['case', 'testcase'],
    '接口': ['api', 'interface', 'endpoint'],
    '设备': ['device', 'equipment'],
    '学校': ['school'],
    '班级': ['class', 'clazz'],
    '学生': ['student', 'pupil'],
    '老师': ['teacher', 'tutor'],
    '课程': ['course', 'lesson'],
    '优惠': ['coupon', 'promo', 'discount'],
    '库存': ['stock', 'inventory'],
    '地址': ['address', 'addr'],
    '日志': ['log', 'logs', 'audit'],
    '配置': ['config', 'setting'],
    '演示': ['demo'],
}

SKIP_TABLE_PREFIXES = (
    'pg_', 'sql_', 'flyway_', 'alembic_', 'django_', 'qrtz_',
)
SKIP_TABLE_NAMES = {
    'spatial_ref_sys', 'geography_columns', 'geometry_columns',
}
MAX_TABLE_CANDIDATES = 8
MAX_COLUMNS_PER_TABLE = 40
MAX_HINT_CHARS = 6000
CONNECT_TIMEOUT_SEC = 5


class SceneSchemaProbe(object):

    @classmethod
    def build_hint(cls, project_id, env, user_text):
        """
        返回 (hint_text, meta)。
        meta: {matchedTables, tableCount, schemaError}
        """
        meta = {
            'matchedTables': [],
            'tableCount': 0,
            'schemaError': '',
        }
        config, err = SceneSqlRunner.resolve_target_config('', (env or '').strip().lower(), project_id=project_id)
        if err or not config:
            meta['schemaError'] = err or '无法解析环境库连接'
            return '', meta

        conn = None
        try:
            conn = psycopg2.connect(
                host=config['host'],
                port=int(config['port']),
                user=config['user'],
                password=config['password'],
                dbname=config['database'],
                connect_timeout=CONNECT_TIMEOUT_SEC,
            )
            conn.autocommit = True
            tables = cls._list_tables(conn)
            meta['tableCount'] = len(tables)
            if not tables:
                meta['schemaError'] = '环境库未查到可用业务表'
                return '', meta

            keywords = cls._extract_keywords(user_text)
            ranked = cls._rank_tables(tables, keywords, user_text)
            selected = ranked[:MAX_TABLE_CANDIDATES]
            if not selected:
                selected = [(name, 0) for name in tables[:MAX_TABLE_CANDIDATES]]

            details = []
            for table_name, score in selected:
                cols = cls._list_columns(conn, table_name)
                fks = cls._list_foreign_keys(conn, table_name)
                details.append({
                    'table': table_name,
                    'score': score,
                    'columns': cols,
                    'foreignKeys': fks,
                })
            meta['matchedTables'] = [d['table'] for d in details]
            meta['tableDetails'] = details
            hint = cls._format_hint(details, keywords)
            return hint, meta
        except Exception as exc:
            logger.warning('SceneSchemaProbe 失败 project_id=%s env=%s err=%s', project_id, env, exc)
            meta['schemaError'] = '探查表结构失败：{}'.format(exc)
            return '', meta
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    @classmethod
    def _list_tables(cls, conn):
        sql = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            LIMIT 500
        """
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        names = []
        for row in rows:
            name = (row[0] or '').strip()
            if not name:
                continue
            lower = name.lower()
            if lower in SKIP_TABLE_NAMES:
                continue
            if any(lower.startswith(p) for p in SKIP_TABLE_PREFIXES):
                continue
            names.append(name)
        return names

    @classmethod
    def _list_columns(cls, conn, table_name):
        sql = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            LIMIT %s
        """
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (table_name, MAX_COLUMNS_PER_TABLE))
            rows = cur.fetchall()
        cols = []
        for mapping in rows:
            cols.append({
                'name': mapping.get('column_name'),
                'type': mapping.get('data_type'),
                'nullable': str(mapping.get('is_nullable') or '').upper() == 'YES',
                'default': mapping.get('column_default'),
            })
        return cols

    @classmethod
    def _list_foreign_keys(cls, conn, table_name):
        sql = """
            SELECT
                kcu.column_name AS column_name,
                ccu.table_name AS foreign_table,
                ccu.column_name AS foreign_column
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
             AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
              AND tc.table_name = %s
            LIMIT 30
        """
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (table_name,))
                rows = cur.fetchall()
        except Exception:
            return []
        fks = []
        for mapping in rows:
            fks.append({
                'column': mapping.get('column_name'),
                'refTable': mapping.get('foreign_table'),
                'refColumn': mapping.get('foreign_column'),
            })
        return fks

    @classmethod
    def _extract_keywords(cls, user_text):
        text = (user_text or '').strip().lower()
        keywords = set()
        for cn, aliases in KEYWORD_ALIASES.items():
            if cn in (user_text or ''):
                keywords.add(cn)
                keywords.update(aliases)
        for token in re.findall(r'[a-zA-Z][a-zA-Z0-9_]{1,40}', text):
            keywords.add(token.lower())
        for token in re.findall(r'[\u4e00-\u9fff]{2,6}', user_text or ''):
            keywords.add(token)
            if token in KEYWORD_ALIASES:
                keywords.update(KEYWORD_ALIASES[token])
        return [k for k in keywords if k]

    @classmethod
    def _rank_tables(cls, tables, keywords, user_text):
        scored = []
        for name in tables:
            lower = name.lower()
            score = 0
            for kw in keywords:
                kw_l = str(kw).lower()
                if not kw_l:
                    continue
                if kw_l == lower or kw_l in lower or lower in kw_l:
                    score += 8
                elif kw_l.replace('_', '') in lower.replace('_', ''):
                    score += 5
            if any(x in lower for x in ('order', 'user', 'project', 'product', 'member', 'task', 'post')):
                score += 1
            if any(x in lower for x in ('tmp', 'temp', 'backup', 'bak', 'hist', 'log')):
                score -= 2
            if score > 0:
                scored.append((name, score))
        scored.sort(key=lambda x: (-x[1], x[0]))
        if scored:
            return scored
        soft = []
        for name in tables:
            lower = name.lower()
            soft_score = 0
            if '_' in lower:
                soft_score += 1
            if not any(x in lower for x in ('log', 'hist', 'tmp', 'temp', 'bak')):
                soft_score += 1
            soft.append((name, soft_score))
        soft.sort(key=lambda x: (-x[1], x[0]))
        return soft

    @classmethod
    def _format_hint(cls, details, keywords):
        lines = [
            '以下表结构来自当前项目所选环境库（自动探查），请优先选用这些真实表造数：',
            '匹配关键词：{}'.format(', '.join(keywords[:20]) if keywords else '（按库内表启发式选取）'),
            '要求：',
            '1) 必须使用下列真实表名与字段，禁止 SELECT 1 / demo_data 这类占位 SQL；',
            '2) 造数优先 INSERT，必要时可先 INSERT 被外键依赖的父表，再写子表；',
            '3) 可写 RETURNING id 并 extract；禁止 DROP/TRUNCATE/ALTER；',
            '4) 若缺必填字段，用合理测试值；密码类字段用固定测试串。',
            '',
        ]
        for item in details:
            cols = item.get('columns') or []
            col_parts = []
            for col in cols:
                flag = 'NULL' if col.get('nullable') else 'NOT NULL'
                default = col.get('default')
                piece = '{} {} {}'.format(col.get('name'), col.get('type'), flag)
                if default not in (None, ''):
                    piece += ' default={}'.format(str(default)[:40])
                col_parts.append(piece)
            lines.append('表 {} (score={}):'.format(item.get('table'), item.get('score')))
            lines.append('  字段: {}'.format('; '.join(col_parts) if col_parts else '（无字段）'))
            fks = item.get('foreignKeys') or []
            if fks:
                fk_text = '; '.join(
                    '{} -> {}.{}'.format(f.get('column'), f.get('refTable'), f.get('refColumn'))
                    for f in fks
                )
                lines.append('  外键: {}'.format(fk_text))
            lines.append('')
        text = '\n'.join(lines).strip()
        if len(text) > MAX_HINT_CHARS:
            return text[:MAX_HINT_CHARS] + '\n...（表结构已截断）'
        return text

    @classmethod
    def build_insert_sql(cls, table_name, columns, project_label='测试数据', user_text=''):
        """按真实字段生成可执行 INSERT ... RETURNING。"""
        table = (table_name or '').strip()
        if not table or not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', table):
            return '', ''
        cols = columns or []
        insert_cols = []
        values = []
        for col in cols:
            name = (col.get('name') or '').strip()
            if not name or not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name):
                continue
            if cls._should_skip_column(col):
                continue
            sample = cls._sample_value(col, project_label, user_text)
            if sample is None:
                continue
            insert_cols.append(name)
            values.append(sample)
            if len(insert_cols) >= 12:
                break
        if not insert_cols:
            # 无法安全插入时，改成可读查询，避免瞎写不存在字段
            return "SELECT 1 AS id /* 表 {} 无可自动填充字段，请手工补 INSERT */".format(table), 'id'
        returning = 'id'
        col_names = {(c.get('name') or '').lower() for c in cols}
        if 'id' not in col_names:
            returning = insert_cols[0]
        sql = 'INSERT INTO {table} ({cols}) VALUES ({vals}) RETURNING {ret}'.format(
            table=table,
            cols=', '.join(insert_cols),
            vals=', '.join(values),
            ret=returning,
        )
        return sql, returning

    @classmethod
    def _should_skip_column(cls, col):
        name = (col.get('name') or '').lower()
        data_type = (col.get('type') or '').lower()
        default = str(col.get('default') or '').lower()
        nullable = bool(col.get('nullable'))
        if name in ('id', 'uuid', 'created_at', 'updated_at', 'deleted_at', 'create_time', 'update_time'):
            if default or 'nextval' in default or 'now(' in default or data_type in ('uuid',):
                return True
            if name == 'id' and ('int' in data_type or 'serial' in data_type):
                return True
        if 'nextval(' in default or 'identity' in default:
            return True
        if nullable and default:
            # 有默认值的可空字段可不写
            return True
        if name.endswith('_id') and nullable:
            # 外键可空先跳过，避免乱填
            return True
        return False

    @classmethod
    def _sample_value(cls, col, project_label, user_text):
        name = (col.get('name') or '').lower()
        data_type = (col.get('type') or '').lower()
        nullable = bool(col.get('nullable'))
        label = (project_label or '测试数据').replace("'", "''")[:40]
        tip = (user_text or '测试').replace("'", "''")[:30]

        if name in ('is_delete', 'is_deleted', 'deleted', 'status') and ('int' in data_type or data_type == 'smallint'):
            return '0'
        if 'bool' in data_type:
            return 'true'
        if data_type in ('uuid',):
            return "'00000000-0000-4000-8000-000000000001'"
        if any(x in data_type for x in ('int', 'numeric', 'decimal', 'double', 'real', 'float')):
            if name.endswith('_id') or name in ('user_id', 'author_id', 'creator_id', 'owner_id'):
                return '1'
            if 'count' in name or 'num' in name or 'qty' in name:
                return '1'
            return '1'
        if any(x in data_type for x in ('timestamp', 'date', 'time')):
            return 'NOW()'
        if 'json' in data_type:
            return "'{}'"
        # text-like
        if any(k in name for k in ('title', 'name', 'content', 'body', 'text', 'desc', 'remark', 'summary')):
            return "'{}-{}'".format(label, tip or '造数')
        if 'phone' in name or 'mobile' in name:
            return "'13800138000'"
        if 'email' in name:
            return "'test@example.com'"
        if 'url' in name or 'link' in name or 'avatar' in name or 'image' in name or 'cover' in name:
            return "'https://example.com/demo.png'"
        if nullable:
            return None
        return "'{}'".format(label)
