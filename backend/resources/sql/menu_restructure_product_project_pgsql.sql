-- Reorganize left navigation around product/project workflows.
-- Idempotent for PostgreSQL. It keeps existing route/permission records and only
-- changes menu grouping/sort.

INSERT INTO public.sys_menu
    (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
VALUES
    (0, '基础配置', 'base_config', 1, '', '', 'el-icon-setting', NULL, 10, 1, 1, 0, NOW(), NOW()),
    (0, '项目工作台', 'project_workspace', 1, '', '', 'el-icon-s-operation', NULL, 20, 1, 1, 0, NOW(), NOW()),
    (0, 'AI质量助手', 'ai_quality_assistant', 1, '', '', 'el-icon-cpu', NULL, 30, 1, 1, 0, NOW(), NOW()),
    (0, '测试支撑工具', 'test_support_tools', 1, '', '', 'el-icon-s-tools', NULL, 40, 1, 1, 0, NOW(), NOW())
ON CONFLICT (code) DO UPDATE SET
    parent_id = 0,
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

WITH target_parent AS (
    SELECT id FROM public.sys_menu WHERE code = 'project_workspace' AND is_delete = 0
)
UPDATE public.sys_menu m
SET parent_id = target_parent.id,
    sort = CASE
        WHEN m.path = '/requirement-qa' OR m.name = '需求问答' THEN 10
        WHEN m.path = '/test-platform/case' OR m.name = '用例管理' THEN 20
        WHEN m.path = '/test-platform/plan' OR m.name = '测试计划' THEN 30
        WHEN m.path = '/test-platform/report' OR m.name = '测试报告' THEN 40
        WHEN m.path = '/bug' OR m.name = 'Bug管理' THEN 50
        ELSE m.sort
    END,
    visible = 1,
    status = 1,
    is_delete = 0,
    updated_time = NOW()
FROM target_parent
WHERE m.is_delete = 0
  AND (
      m.path IN ('/requirement-qa', '/test-platform/case', '/test-platform/plan', '/test-platform/report', '/bug')
      OR m.name IN ('需求问答', '用例管理', '测试计划', '测试报告', 'Bug管理')
  );

WITH target_parent AS (
    SELECT id FROM public.sys_menu WHERE code = 'ai_quality_assistant' AND is_delete = 0
)
UPDATE public.sys_menu m
SET parent_id = target_parent.id,
    sort = CASE
        WHEN m.path = '/test-platform/ai-platform' OR m.name = 'AI测试中枢' THEN 10
        WHEN m.path = '/ai-review' OR m.name = 'AI测试评审' THEN 20
        WHEN m.path = '/test-asset-governance' OR m.name = '测试资产治理' THEN 30
        WHEN m.path = '/precise' OR m.name = '精准测试' THEN 40
        ELSE m.sort
    END,
    visible = 1,
    status = 1,
    is_delete = 0,
    updated_time = NOW()
FROM target_parent
WHERE m.is_delete = 0
  AND (
      m.path IN ('/test-platform/ai-platform', '/ai-review', '/test-asset-governance', '/precise')
      OR m.name IN ('AI测试中枢', 'AI测试评审', '测试资产治理', '精准测试')
  );

WITH target_parent AS (
    SELECT id FROM public.sys_menu WHERE code = 'test_support_tools' AND is_delete = 0
)
UPDATE public.sys_menu m
SET parent_id = target_parent.id,
    sort = CASE
        WHEN m.path = '/data-tools' OR m.name = '造数工具' OR m.code = 'data_tools' THEN 10
        WHEN m.path = '/performance' OR m.name = '性能测试' THEN 20
        WHEN m.path = '/mock' OR m.name IN ('mock服务', 'Mock服务') THEN 30
        ELSE m.sort
    END,
    visible = 1,
    status = 1,
    is_delete = 0,
    updated_time = NOW()
FROM target_parent
WHERE m.is_delete = 0
  AND (
      m.path IN ('/data-tools', '/performance', '/mock')
      OR m.code IN ('data_tools', 'performance_test', 'mock_service')
      OR m.name IN ('造数工具', '性能测试', 'mock服务', 'Mock服务')
  );

WITH data_tools_parent AS (
    SELECT id
    FROM public.sys_menu
    WHERE is_delete = 0
      AND (code = 'data_tools' OR path = '/data-tools' OR name = '造数工具')
    ORDER BY CASE WHEN code = 'data_tools' THEN 0 ELSE 1 END, id
    LIMIT 1
)
UPDATE public.sys_menu m
SET parent_id = data_tools_parent.id,
    sort = CASE
        WHEN m.path = '/data-tools/db-builder' OR m.name = '数据库造数' THEN 10
        WHEN m.path = '/data-tools/factory' OR m.name = '造数工厂' THEN 20
        ELSE m.sort
    END,
    visible = 1,
    status = 1,
    is_delete = 0,
    updated_time = NOW()
FROM data_tools_parent
WHERE m.is_delete = 0
  AND (
      m.path IN ('/data-tools/db-builder', '/data-tools/factory')
      OR m.code IN ('data_builder_manage', 'data_factory_manage', 'sql_project')
      OR m.name IN ('数据库造数', '造数工厂')
  );

WITH target_parent AS (
    SELECT id FROM public.sys_menu WHERE code = 'base_config' AND is_delete = 0
)
UPDATE public.sys_menu m
SET parent_id = target_parent.id,
    sort = CASE
        WHEN m.path = '/test-platform/product' OR m.name = '产品管理' THEN 10
        WHEN m.path = '/test-platform/project' OR m.name = '项目管理' THEN 20
        WHEN m.path = '/test-platform/skill-rules' OR m.name IN ('业务技能配置', '配置技能与规则') THEN 30
        ELSE m.sort
    END,
    visible = 1,
    status = 1,
    is_delete = 0,
    updated_time = NOW()
FROM target_parent
WHERE m.is_delete = 0
  AND (
      m.path IN ('/test-platform/product', '/test-platform/project', '/test-platform/skill-rules')
      OR m.name IN ('产品管理', '项目管理', '业务技能配置', '配置技能与规则', '测试 Skills', '业务规则')
  );

-- Hide old broad containers after their children are moved to the new groups.
UPDATE public.sys_menu
SET visible = 0,
    status = 1,
    updated_time = NOW()
WHERE is_delete = 0
  AND type = 1
  AND code NOT IN ('project_workspace', 'ai_quality_assistant', 'test_support_tools', 'base_config')
  AND (
      code IN ('test_platform', 'quality_collaboration')
      OR name IN ('测试平台', '用例周期', '智能质量协同')
  );

-- Keep system management after the product/project workflow groups.
UPDATE public.sys_menu
SET sort = 50,
    updated_time = NOW()
WHERE is_delete = 0
  AND (path = '/system' OR name = '系统管理' OR code = 'system');

-- Grant the new grouping menus to existing roles. Child menu permissions remain unchanged.
INSERT INTO public.sys_role_menu (role_id, menu_id, is_delete, created_time)
SELECT r.id, m.id, 0, NOW()
FROM public.sys_role r
CROSS JOIN public.sys_menu m
WHERE r.is_delete = 0
  AND m.code IN ('project_workspace', 'ai_quality_assistant', 'test_support_tools', 'base_config')
  AND m.is_delete = 0
  AND NOT EXISTS (
      SELECT 1
      FROM public.sys_role_menu rm
      WHERE rm.role_id = r.id
        AND rm.menu_id = m.id
  );

UPDATE public.sys_role_menu rm
SET is_delete = 0
FROM public.sys_role r, public.sys_menu m
WHERE rm.role_id = r.id
  AND rm.menu_id = m.id
  AND r.is_delete = 0
  AND m.code IN ('project_workspace', 'ai_quality_assistant', 'test_support_tools', 'base_config')
  AND m.is_delete = 0;

SELECT setval(pg_get_serial_sequence('public.sys_menu', 'id'), COALESCE((SELECT MAX(id) FROM public.sys_menu), 1));
