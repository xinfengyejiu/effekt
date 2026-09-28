-- Chat issue import (Feishu/Doubao summary → candidates → AI analyze → confirm bug).
-- PostgreSQL, idempotent.

BEGIN;

CREATE TABLE IF NOT EXISTS public.chat_issue_import (
    id BIGSERIAL PRIMARY KEY,
    session_no VARCHAR(64) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    source_type VARCHAR(32) NOT NULL DEFAULT 'paste',
    raw_text TEXT,
    product_id BIGINT,
    product_name VARCHAR(128),
    project_id BIGINT NOT NULL,
    project_name VARCHAR(128),
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    day_label VARCHAR(64),
    created_by BIGINT,
    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.chat_issue_import IS '聊天问题导入 Session/批次';
COMMENT ON COLUMN public.chat_issue_import.status IS 'draft/ready/partial/done';
COMMENT ON COLUMN public.chat_issue_import.day_label IS '来源日期分段，如 9月17日（周四）';

CREATE TABLE IF NOT EXISTS public.chat_issue_item (
    id BIGSERIAL PRIMARY KEY,
    import_id BIGINT NOT NULL,
    sort_no INTEGER NOT NULL DEFAULT 0,
    title VARCHAR(500) NOT NULL,
    detail TEXT,
    suggest_type VARCHAR(32) NOT NULL DEFAULT 'bug',
    severity INTEGER DEFAULT 2,
    item_status VARCHAR(32) NOT NULL DEFAULT 'parsed',
    ai_analysis JSONB NOT NULL DEFAULT '{}'::jsonb,
    linked_bug_id BIGINT,
    linked_case_id BIGINT,
    source_ref VARCHAR(128),
    created_by BIGINT,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.chat_issue_item IS '聊天导入候选问题';
COMMENT ON COLUMN public.chat_issue_item.item_status IS 'parsed/analyzed/confirmed/dismissed';
COMMENT ON COLUMN public.chat_issue_item.suggest_type IS 'bug/case/both';

CREATE INDEX IF NOT EXISTS idx_chat_issue_import_project
ON public.chat_issue_import(project_id, status)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_chat_issue_import_created
ON public.chat_issue_import(created_time DESC);

CREATE INDEX IF NOT EXISTS idx_chat_issue_item_import
ON public.chat_issue_item(import_id, sort_no)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_chat_issue_item_status
ON public.chat_issue_item(import_id, item_status)
WHERE is_delete = 0;

INSERT INTO public.sys_permission (code, name, module, action, description, status, is_delete, created_time, updated_time) VALUES
('chat_issue:list', '聊天问题导入列表', 'chat_issue', 'list', '查看聊天问题导入', 1, 0, NOW(), NOW()),
('chat_issue:import', '聊天问题导入', 'chat_issue', 'import', '粘贴/文件导入候选', 1, 0, NOW(), NOW()),
('chat_issue:analyze', '聊天问题AI分析', 'chat_issue', 'analyze', 'AI分析原因与建议', 1, 0, NOW(), NOW()),
('chat_issue:generate', '聊天问题转正', 'chat_issue', 'generate', '确认转Bug/用例', 1, 0, NOW(), NOW())
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
    SELECT id FROM public.sys_menu
    WHERE is_delete = 0 AND (code = 'data_tools' OR name = '造数工具')
    ORDER BY id LIMIT 1
), 0), '聊天问题导入', 'chat_issue_import', 2, '/chat-issue', 'ChatIssueImport/ImportList', 'el-icon-chat-dot-round', 'chat_issue:list', 40, 1, 1, 0, NOW(), NOW()
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
    ('导入', 'chat_issue_import_create', 'chat_issue:import', 1),
    ('分析', 'chat_issue_analyze', 'chat_issue:analyze', 2),
    ('转正', 'chat_issue_generate', 'chat_issue:generate', 3)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'chat_issue_import'
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
  AND p.module = 'chat_issue' AND p.is_delete = 0
  AND NOT EXISTS (
      SELECT 1 FROM public.sys_role_permission rp
      WHERE rp.role_id = r.id AND rp.permission_id = p.id AND rp.is_delete = 0
  );

INSERT INTO public.sys_role_menu (role_id, menu_id, is_delete, created_time)
SELECT r.id, m.id, 0, NOW()
FROM public.sys_role r
CROSS JOIN public.sys_menu m
WHERE r.status = 1 AND r.is_delete = 0
  AND (m.code = 'chat_issue_import' OR m.code LIKE 'chat_issue_%')
  AND m.is_delete = 0
  AND NOT EXISTS (
      SELECT 1 FROM public.sys_role_menu rm
      WHERE rm.role_id = r.id AND rm.menu_id = m.id AND rm.is_delete = 0
  );

SELECT setval(pg_get_serial_sequence('public.sys_permission', 'id'), COALESCE((SELECT MAX(id) FROM public.sys_permission), 1));
SELECT setval(pg_get_serial_sequence('public.sys_menu', 'id'), COALESCE((SELECT MAX(id) FROM public.sys_menu), 1));

COMMIT;
