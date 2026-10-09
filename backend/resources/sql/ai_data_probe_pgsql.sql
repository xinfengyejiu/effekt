-- AI data probe: connections + sessions (PostgreSQL, idempotent).

BEGIN;

CREATE TABLE IF NOT EXISTS public.ai_data_probe_connection (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    db_type VARCHAR(32) NOT NULL DEFAULT 'postgresql',
    host VARCHAR(256) NOT NULL,
    port INTEGER NOT NULL,
    database_name VARCHAR(128) NOT NULL,
    username VARCHAR(128) NOT NULL,
    password VARCHAR(512) NOT NULL DEFAULT '',
    product_id BIGINT,
    product_name VARCHAR(128),
    project_id BIGINT,
    project_name VARCHAR(128),
    env VARCHAR(64) NOT NULL DEFAULT 'test',
    remark TEXT,
    enabled SMALLINT NOT NULL DEFAULT 1,
    created_by BIGINT,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.ai_data_probe_connection IS 'AI智能问数-业务库连接';
COMMENT ON COLUMN public.ai_data_probe_connection.env IS '环境标签；prod/production/prd/online 禁止执行';

CREATE INDEX IF NOT EXISTS idx_ai_data_probe_connection_project
ON public.ai_data_probe_connection(project_id, enabled)
WHERE is_delete = 0;

CREATE TABLE IF NOT EXISTS public.ai_data_probe_session (
    id BIGSERIAL PRIMARY KEY,
    session_no VARCHAR(64) NOT NULL UNIQUE,
    connection_id BIGINT NOT NULL,
    project_id BIGINT,
    title VARCHAR(255) NOT NULL DEFAULT '',
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    created_by BIGINT,
    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.ai_data_probe_session IS 'AI智能问数-会话';

CREATE INDEX IF NOT EXISTS idx_ai_data_probe_session_conn
ON public.ai_data_probe_session(connection_id, created_time DESC)
WHERE is_delete = 0;

CREATE TABLE IF NOT EXISTS public.ai_data_probe_message (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL,
    role VARCHAR(32) NOT NULL,
    content JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by BIGINT,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.ai_data_probe_message IS 'AI智能问数-消息（含SQL/结论/预览，不含密码）';

CREATE INDEX IF NOT EXISTS idx_ai_data_probe_message_session
ON public.ai_data_probe_message(session_id, id)
WHERE is_delete = 0;

CREATE TABLE IF NOT EXISTS public.ai_data_probe_audit (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT,
    connection_id BIGINT,
    sql_text TEXT,
    sql_hash VARCHAR(64),
    row_count INTEGER NOT NULL DEFAULT 0,
    latency_ms INTEGER,
    success SMALLINT NOT NULL DEFAULT 0,
    error_message TEXT,
    created_by BIGINT,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.ai_data_probe_audit IS 'AI智能问数-SQL执行审计';

CREATE INDEX IF NOT EXISTS idx_ai_data_probe_audit_session
ON public.ai_data_probe_audit(session_id, created_time DESC);

INSERT INTO public.sys_permission (code, name, module, action, description, status, is_delete, created_time, updated_time) VALUES
('ai_data_probe:list', 'AI智能问数查看', 'ai_data_probe', 'list', '查看连接与会话', 1, 0, NOW(), NOW()),
('ai_data_probe:manage', 'AI智能问数管理', 'ai_data_probe', 'manage', '管理连接配置', 1, 0, NOW(), NOW()),
('ai_data_probe:query', 'AI智能问数查询', 'ai_data_probe', 'query', '发起智能问数', 1, 0, NOW(), NOW())
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    module = EXCLUDED.module,
    action = EXCLUDED.action,
    description = EXCLUDED.description,
    status = 1,
    is_delete = 0,
    updated_time = NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT parent.id, 'AI智能问数', 'ai_data_probe', 2, '/ai-data-probe', 'AiDataProbe/ProbeWorkspace', 'el-icon-search', 'ai_data_probe:list', 35, 1, 1, 0, NOW(), NOW()
FROM public.sys_menu parent
WHERE parent.code = 'data_tools' AND parent.is_delete = 0
ON CONFLICT (code) DO UPDATE SET
    parent_id = EXCLUDED.parent_id,
    name = EXCLUDED.name,
    type = EXCLUDED.type,
    path = EXCLUDED.path,
    component = EXCLUDED.component,
    icon = EXCLUDED.icon,
    permission_code = EXCLUDED.permission_code,
    sort = EXCLUDED.sort,
    visible = 1,
    status = 1,
    is_delete = 0,
    updated_time = NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT 0, 'AI智能问数', 'ai_data_probe', 2, '/ai-data-probe', 'AiDataProbe/ProbeWorkspace', 'el-icon-search', 'ai_data_probe:list', 96, 1, 1, 0, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM public.sys_menu WHERE code = 'ai_data_probe' AND is_delete = 0);

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT m.id, v.name, v.code, 3, '', '', '', v.permission_code, v.sort, 1, 1, 0, NOW(), NOW()
FROM public.sys_menu m
CROSS JOIN (VALUES
    ('管理连接', 'ai_data_probe_manage', 'ai_data_probe:manage', 1),
    ('发起查数', 'ai_data_probe_query', 'ai_data_probe:query', 2)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'ai_data_probe'
ON CONFLICT (code) DO UPDATE SET
    parent_id = EXCLUDED.parent_id,
    name = EXCLUDED.name,
    type = EXCLUDED.type,
    permission_code = EXCLUDED.permission_code,
    sort = EXCLUDED.sort,
    visible = 1,
    status = 1,
    is_delete = 0,
    updated_time = NOW();

INSERT INTO public.sys_role_permission (role_id, permission_id, is_delete, created_time)
SELECT r.id, p.id, 0, NOW()
FROM public.sys_role r
CROSS JOIN public.sys_permission p
WHERE r.status = 1 AND r.is_delete = 0
  AND p.module = 'ai_data_probe' AND p.is_delete = 0
  AND NOT EXISTS (
      SELECT 1 FROM public.sys_role_permission rp
      WHERE rp.role_id = r.id AND rp.permission_id = p.id AND rp.is_delete = 0
  );

INSERT INTO public.sys_role_menu (role_id, menu_id, is_delete, created_time)
SELECT r.id, m.id, 0, NOW()
FROM public.sys_role r
CROSS JOIN public.sys_menu m
WHERE r.status = 1 AND r.is_delete = 0
  AND (m.code = 'ai_data_probe' OR m.code LIKE 'ai_data_probe_%')
  AND m.is_delete = 0
  AND NOT EXISTS (
      SELECT 1 FROM public.sys_role_menu rm
      WHERE rm.role_id = r.id AND rm.menu_id = m.id AND rm.is_delete = 0
  );

SELECT setval(pg_get_serial_sequence('public.sys_permission', 'id'), COALESCE((SELECT MAX(id) FROM public.sys_permission), 1));
SELECT setval(pg_get_serial_sequence('public.sys_menu', 'id'), COALESCE((SELECT MAX(id) FROM public.sys_menu), 1));

COMMIT;
