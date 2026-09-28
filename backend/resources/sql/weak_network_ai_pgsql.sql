-- Weak network AI assist (phase 1). PostgreSQL, idempotent.

BEGIN;

CREATE TABLE IF NOT EXISTS public.weak_network_ai_task (
    id BIGSERIAL PRIMARY KEY,
    task_no VARCHAR(64) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    brief TEXT,
    product_id BIGINT,
    product_name VARCHAR(128),
    project_id BIGINT,
    project_name VARCHAR(128),
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    recommended_profiles JSONB NOT NULL DEFAULT '[]'::jsonb,
    selected_profile_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    weak_network_session_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_by BIGINT,
    remark TEXT,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.weak_network_ai_task IS '弱网 AI 任务';
COMMENT ON COLUMN public.weak_network_ai_task.status IS 'draft/ready/collecting/judged/closed';

CREATE TABLE IF NOT EXISTS public.weak_network_ai_checkpoint (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    sort_no INTEGER NOT NULL DEFAULT 0,
    title VARCHAR(500) NOT NULL,
    expect_text TEXT,
    profile_preset VARCHAR(64),
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    last_verdict VARCHAR(32),
    last_observation TEXT,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON COLUMN public.weak_network_ai_checkpoint.status IS 'pending/judged';
COMMENT ON COLUMN public.weak_network_ai_checkpoint.last_verdict IS 'acceptable/suspect/insufficient';

CREATE TABLE IF NOT EXISTS public.weak_network_ai_evidence (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    checkpoint_id BIGINT,
    file_path VARCHAR(512),
    note TEXT,
    mobile_execution_id BIGINT,
    created_by BIGINT,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.weak_network_ai_finding (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    checkpoint_id BIGINT,
    title VARCHAR(500) NOT NULL,
    detail TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'open',
    linked_bug_id BIGINT,
    ai_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON COLUMN public.weak_network_ai_finding.status IS 'open/confirmed/dismissed';

CREATE INDEX IF NOT EXISTS idx_wn_ai_task_project
ON public.weak_network_ai_task(project_id, status)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_wn_ai_checkpoint_task
ON public.weak_network_ai_checkpoint(task_id, sort_no)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_wn_ai_evidence_task
ON public.weak_network_ai_evidence(task_id)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_wn_ai_finding_task
ON public.weak_network_ai_finding(task_id, status)
WHERE is_delete = 0;

INSERT INTO public.sys_permission (code, name, module, action, description, status, is_delete, created_time, updated_time) VALUES
('weak_network_ai:list', '弱网AI任务列表', 'weak_network_ai', 'list', '查看弱网AI任务', 1, 0, NOW(), NOW()),
('weak_network_ai:manage', '弱网AI任务管理', 'weak_network_ai', 'manage', '创建/编排/确认弱网AI任务', 1, 0, NOW(), NOW()),
('weak_network_ai:judge', '弱网AI判定', 'weak_network_ai', 'judge', '上传证据并AI判定', 1, 0, NOW(), NOW()),
('weak_network_ai:generate', '弱网AI转Bug', 'weak_network_ai', 'generate', '确认存疑项转正式Bug', 1, 0, NOW(), NOW())
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
    WHERE is_delete = 0 AND (code = 'mobile_automation' OR code = 'weak_network')
    ORDER BY CASE WHEN code = 'mobile_automation' THEN 0 ELSE 1 END, id
    LIMIT 1
), 0), '弱网AI任务', 'weak_network_ai', 2, '/weak-network-ai', 'WeakNetworkAi/TaskList', 'el-icon-magic-stick', 'weak_network_ai:list', 55, 1, 1, 0, NOW(), NOW()
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
    ('管理', 'weak_network_ai_manage', 'weak_network_ai:manage', 1),
    ('判定', 'weak_network_ai_judge', 'weak_network_ai:judge', 2),
    ('转正', 'weak_network_ai_generate', 'weak_network_ai:generate', 3)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'weak_network_ai'
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
  AND p.module = 'weak_network_ai' AND p.is_delete = 0
  AND NOT EXISTS (
      SELECT 1 FROM public.sys_role_permission rp
      WHERE rp.role_id = r.id AND rp.permission_id = p.id AND rp.is_delete = 0
  );

INSERT INTO public.sys_role_menu (role_id, menu_id, is_delete, created_time)
SELECT r.id, m.id, 0, NOW()
FROM public.sys_role r
CROSS JOIN public.sys_menu m
WHERE r.status = 1 AND r.is_delete = 0
  AND (m.code = 'weak_network_ai' OR m.code LIKE 'weak_network_ai_%')
  AND m.is_delete = 0
  AND NOT EXISTS (
      SELECT 1 FROM public.sys_role_menu rm
      WHERE rm.role_id = r.id AND rm.menu_id = m.id AND rm.is_delete = 0
  );

SELECT setval(pg_get_serial_sequence('public.sys_permission', 'id'), COALESCE((SELECT MAX(id) FROM public.sys_permission), 1));
SELECT setval(pg_get_serial_sequence('public.sys_menu', 'id'), COALESCE((SELECT MAX(id) FROM public.sys_menu), 1));

COMMIT;
