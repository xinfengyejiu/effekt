-- Exploratory testing session tables, menu, and permissions.
-- PostgreSQL, idempotent.

BEGIN;

CREATE TABLE IF NOT EXISTS public.explore_session (
    id BIGSERIAL PRIMARY KEY,
    session_no VARCHAR(64) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    charter TEXT,
    out_of_scope TEXT,
    product_id BIGINT,
    product_name VARCHAR(128),
    project_id BIGINT NOT NULL,
    project_name VARCHAR(128),
    plan_id BIGINT,
    environment VARCHAR(64),
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    summary TEXT,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    created_by BIGINT,
    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.explore_session IS '探索性测试 Session';
COMMENT ON COLUMN public.explore_session.status IS 'draft/active/ended/archived';
COMMENT ON COLUMN public.explore_session.charter IS '章程：测什么';
COMMENT ON COLUMN public.explore_session.out_of_scope IS '不测什么';

CREATE TABLE IF NOT EXISTS public.explore_session_entry (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL,
    entry_type VARCHAR(32) NOT NULL,
    content TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    sort_no INTEGER NOT NULL DEFAULT 0,
    linked_bug_id BIGINT,
    linked_case_id BIGINT,
    created_by BIGINT,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.explore_session_entry IS '探索 Session 时间线条目';
COMMENT ON COLUMN public.explore_session_entry.entry_type IS 'note/step/screenshot/finding/blocker';

CREATE INDEX IF NOT EXISTS idx_explore_session_project
ON public.explore_session(project_id, status)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_explore_session_created_by
ON public.explore_session(created_by)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_explore_session_created_time
ON public.explore_session(created_time DESC);

CREATE INDEX IF NOT EXISTS idx_explore_session_entry_session
ON public.explore_session_entry(session_id, sort_no)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_explore_session_entry_type
ON public.explore_session_entry(session_id, entry_type)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_explore_session_entry_created_time
ON public.explore_session_entry(created_time DESC);

INSERT INTO public.sys_permission (code, name, module, action, description, status, is_delete, created_time, updated_time) VALUES
('explore_session:list', '探索Session列表', 'explore_session', 'list', '查看探索Session列表', 1, 0, NOW(), NOW()),
('explore_session:detail', '探索Session详情', 'explore_session', 'detail', '查看探索Session详情', 1, 0, NOW(), NOW()),
('explore_session:create', '探索Session创建', 'explore_session', 'create', '创建探索Session', 1, 0, NOW(), NOW()),
('explore_session:update', '探索Session更新', 'explore_session', 'update', '更新/开始/结束/归档探索Session', 1, 0, NOW(), NOW()),
('explore_session:entry', '探索Session条目', 'explore_session', 'entry', '增删改时间线条目', 1, 0, NOW(), NOW()),
('explore_session:upload', '探索Session上传', 'explore_session', 'upload', '上传探索截图', 1, 0, NOW(), NOW()),
('explore_session:to_bug', '探索转Bug', 'explore_session', 'to_bug', '时间线转为Bug', 1, 0, NOW(), NOW()),
('explore_session:to_case', '探索转用例', 'explore_session', 'to_case', '时间线转为用例草稿', 1, 0, NOW(), NOW())
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    module = EXCLUDED.module,
    action = EXCLUDED.action,
    description = EXCLUDED.description,
    status = 1,
    is_delete = 0,
    updated_time = NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT COALESCE((
    SELECT id
    FROM public.sys_menu
    WHERE is_delete = 0
      AND (
          code IN ('test_support', 'data_tools', 'test_platform', 'quality_collaboration')
          OR name IN ('测试支撑', '造数工具', '测试平台', '智能质量协同')
      )
    ORDER BY CASE
        WHEN code = 'test_support' OR name = '测试支撑' THEN 1
        WHEN code = 'data_tools' OR name = '造数工具' THEN 2
        WHEN code = 'test_platform' OR name = '测试平台' THEN 3
        ELSE 9
    END, id
    LIMIT 1
), 0), '探索Session', 'explore_session', 2, '/explore-session', 'ExploratorySession/SessionList', 'el-icon-edit-outline', 'explore_session:list', 35, 1, 1, 0, NOW(), NOW()
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
SELECT m.id, v.name, v.code, 3, '', '', '', v.permission_code, v.sort, 1, 1, 0, NOW(), NOW()
FROM public.sys_menu m
CROSS JOIN (VALUES
    ('新建', 'explore_session_create', 'explore_session:create', 1),
    ('详情', 'explore_session_detail', 'explore_session:detail', 2),
    ('更新', 'explore_session_update', 'explore_session:update', 3),
    ('时间线', 'explore_session_entry', 'explore_session:entry', 4),
    ('上传截图', 'explore_session_upload', 'explore_session:upload', 5),
    ('转Bug', 'explore_session_to_bug', 'explore_session:to_bug', 6),
    ('转用例', 'explore_session_to_case', 'explore_session:to_case', 7)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'explore_session'
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
WHERE r.status = 1
  AND r.is_delete = 0
  AND p.module = 'explore_session'
  AND p.is_delete = 0
  AND NOT EXISTS (
      SELECT 1 FROM public.sys_role_permission rp
      WHERE rp.role_id = r.id
        AND rp.permission_id = p.id
        AND rp.is_delete = 0
  );

INSERT INTO public.sys_role_menu (role_id, menu_id, is_delete, created_time)
SELECT r.id, m.id, 0, NOW()
FROM public.sys_role r
CROSS JOIN public.sys_menu m
WHERE r.status = 1
  AND r.is_delete = 0
  AND (m.code = 'explore_session' OR m.code LIKE 'explore_session_%')
  AND m.is_delete = 0
  AND NOT EXISTS (
      SELECT 1 FROM public.sys_role_menu rm
      WHERE rm.role_id = r.id
        AND rm.menu_id = m.id
        AND rm.is_delete = 0
  );

SELECT setval(pg_get_serial_sequence('public.sys_permission', 'id'), COALESCE((SELECT MAX(id) FROM public.sys_permission), 1));
SELECT setval(pg_get_serial_sequence('public.sys_menu', 'id'), COALESCE((SELECT MAX(id) FROM public.sys_menu), 1));

COMMIT;
