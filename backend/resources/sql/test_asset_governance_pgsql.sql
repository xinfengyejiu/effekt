-- AI test asset governance tables, menu, and permissions.
-- PostgreSQL, idempotent.

BEGIN;

CREATE TABLE IF NOT EXISTS public.test_asset_scan (
    id BIGSERIAL PRIMARY KEY,
    scan_no VARCHAR(64) NOT NULL UNIQUE,
    product_id BIGINT,
    product_name VARCHAR(128),
    project_id BIGINT NOT NULL,
    project_name VARCHAR(128),
    title VARCHAR(255) NOT NULL,
    scan_type VARCHAR(64) NOT NULL DEFAULT 'full',
    options_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    health_score INTEGER,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_by BIGINT,
    started_time TIMESTAMP,
    finished_time TIMESTAMP,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.test_asset_scan IS '测试资产治理扫描任务';
COMMENT ON COLUMN public.test_asset_scan.scan_no IS '扫描编号';
COMMENT ON COLUMN public.test_asset_scan.options_json IS '扫描选项JSON';
COMMENT ON COLUMN public.test_asset_scan.summary_json IS '扫描摘要JSON';

CREATE TABLE IF NOT EXISTS public.test_asset_issue (
    id BIGSERIAL PRIMARY KEY,
    scan_id BIGINT NOT NULL,
    product_id BIGINT,
    project_id BIGINT NOT NULL,
    module_id BIGINT,
    module_name VARCHAR(128),
    issue_type VARCHAR(64) NOT NULL,
    severity VARCHAR(32) NOT NULL DEFAULT 'medium',
    title VARCHAR(255) NOT NULL,
    description TEXT,
    evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    suggestion_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    related_case_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    action_status VARCHAR(32) NOT NULL DEFAULT 'open',
    assigned_to BIGINT,
    resolved_by BIGINT,
    resolved_time TIMESTAMP,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.test_asset_issue IS '测试资产治理问题';
COMMENT ON COLUMN public.test_asset_issue.issue_type IS 'duplicate_case/weak_case/stale_case/coverage_gap/ai_suggestion';
COMMENT ON COLUMN public.test_asset_issue.evidence_json IS '问题证据JSON';
COMMENT ON COLUMN public.test_asset_issue.suggestion_json IS '治理建议JSON';

CREATE TABLE IF NOT EXISTS public.test_asset_action (
    id BIGSERIAL PRIMARY KEY,
    issue_id BIGINT NOT NULL,
    action_type VARCHAR(64) NOT NULL,
    action_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(32) NOT NULL DEFAULT 'success',
    error_message TEXT,
    created_by BIGINT,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.test_asset_action IS '测试资产治理动作记录';

CREATE INDEX IF NOT EXISTS idx_test_asset_scan_project
ON public.test_asset_scan(project_id, status)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_test_asset_scan_product
ON public.test_asset_scan(product_id)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_test_asset_scan_created_time
ON public.test_asset_scan(created_time DESC);

CREATE INDEX IF NOT EXISTS idx_test_asset_issue_scan
ON public.test_asset_issue(scan_id, action_status)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_test_asset_issue_project
ON public.test_asset_issue(project_id, issue_type, severity)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_test_asset_issue_module
ON public.test_asset_issue(module_id)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_test_asset_issue_created_time
ON public.test_asset_issue(created_time DESC);

CREATE INDEX IF NOT EXISTS idx_test_asset_action_issue
ON public.test_asset_action(issue_id, created_time DESC);

INSERT INTO public.sys_permission (code, name, module, action, description, status, is_delete, created_time, updated_time) VALUES
('test_asset_governance:list', '测试资产治理列表', 'test_asset_governance', 'list', '查看测试资产治理扫描列表', 1, 0, NOW(), NOW()),
('test_asset_governance:create', '测试资产治理创建', 'test_asset_governance', 'create', '创建测试资产治理扫描', 1, 0, NOW(), NOW()),
('test_asset_governance:detail', '测试资产治理详情', 'test_asset_governance', 'detail', '查看测试资产治理扫描详情', 1, 0, NOW(), NOW()),
('test_asset_governance:execute', '测试资产治理执行', 'test_asset_governance', 'execute', '执行测试资产治理扫描', 1, 0, NOW(), NOW()),
('test_asset_governance:issue:update', '测试资产治理问题更新', 'test_asset_governance', 'issue:update', '更新测试资产治理问题状态', 1, 0, NOW(), NOW()),
('test_asset_governance:action', '测试资产治理动作', 'test_asset_governance', 'action', '执行测试资产治理动作', 1, 0, NOW(), NOW())
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
          code IN ('test_platform', 'case_cycle', 'quality_collaboration')
          OR name IN ('测试平台', '用例周期', '智能质量协同')
      )
    ORDER BY CASE
        WHEN code = 'test_platform' OR name = '测试平台' THEN 1
        WHEN name = '用例周期' THEN 2
        WHEN code = 'quality_collaboration' OR name = '智能质量协同' THEN 3
        ELSE 9
    END, id
    LIMIT 1
), 0), '测试资产治理', 'test_asset_governance', 2, '/test-asset-governance', 'TestAssetGovernance/ScanList', 'el-icon-s-data', 'test_asset_governance:list', 24, 1, 1, 0, NOW(), NOW()
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
    ('新增扫描', 'test_asset_governance_create', 'test_asset_governance:create', 1),
    ('查看详情', 'test_asset_governance_detail', 'test_asset_governance:detail', 2),
    ('执行扫描', 'test_asset_governance_execute', 'test_asset_governance:execute', 3),
    ('更新问题', 'test_asset_governance_issue_update', 'test_asset_governance:issue:update', 4),
    ('执行动作', 'test_asset_governance_action', 'test_asset_governance:action', 5)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'test_asset_governance'
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
  AND p.module = 'test_asset_governance'
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
  AND (m.code = 'test_asset_governance' OR m.code LIKE 'test_asset_governance_%')
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
