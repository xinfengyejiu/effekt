-- AI workload estimate menu and permissions.
-- PostgreSQL, idempotent.

BEGIN;

INSERT INTO public.sys_permission (code, name, module, action, description, status, is_delete, created_time, updated_time) VALUES
('ai_workload_estimate:list', 'AI工作量预估列表', 'ai_workload_estimate', 'list', '查看AI工作量预估列表', 1, 0, NOW(), NOW()),
('ai_workload_estimate:create', 'AI工作量预估创建', 'ai_workload_estimate', 'create', '创建AI工作量预估任务', 1, 0, NOW(), NOW()),
('ai_workload_estimate:detail', 'AI工作量预估详情', 'ai_workload_estimate', 'detail', '查看AI工作量预估详情', 1, 0, NOW(), NOW()),
('ai_workload_estimate:execute', 'AI工作量预估执行', 'ai_workload_estimate', 'execute', '执行或重新执行AI工作量预估', 1, 0, NOW(), NOW()),
('ai_workload_estimate:assign', 'AI工作量预估分配', 'ai_workload_estimate', 'assign', '分配AI工作量预估负责人', 1, 0, NOW(), NOW()),
('ai_workload_estimate:confirm', 'AI工作量预估确认', 'ai_workload_estimate', 'confirm', '确认AI工作量预估结果', 1, 0, NOW(), NOW()),
('ai_workload_estimate:actual:update', 'AI工作量预估真实数据维护', 'ai_workload_estimate', 'actual:update', '维护AI工作量预估真实数据', 1, 0, NOW(), NOW()),
('ai_workload_estimate:delete', 'AI工作量预估删除', 'ai_workload_estimate', 'delete', '删除AI工作量预估任务', 1, 0, NOW(), NOW())
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    module = EXCLUDED.module,
    action = EXCLUDED.action,
    description = EXCLUDED.description,
    status = 1,
    is_delete = 0,
    updated_time = NOW();

INSERT INTO public.sys_menu
    (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
VALUES
    (0, 'AI质量助手', 'ai_quality_assistant', 1, '', '', 'el-icon-cpu', NULL, 30, 1, 1, 0, NOW(), NOW())
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

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT p.id, 'AI工作量预估', 'ai_workload_estimate', 2, '/ai-workload-estimate', 'AIWorkloadEstimate/EstimateList', 'el-icon-time', 'ai_workload_estimate:list', 35, 1, 1, 0, NOW(), NOW()
FROM public.sys_menu p
WHERE p.code = 'ai_quality_assistant'
  AND p.is_delete = 0
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
    ('新增预估', 'ai_workload_estimate_create', 'ai_workload_estimate:create', 1),
    ('查看详情', 'ai_workload_estimate_detail', 'ai_workload_estimate:detail', 2),
    ('执行预估', 'ai_workload_estimate_execute', 'ai_workload_estimate:execute', 3),
    ('分配负责人', 'ai_workload_estimate_assign', 'ai_workload_estimate:assign', 4),
    ('确认预估', 'ai_workload_estimate_confirm', 'ai_workload_estimate:confirm', 5),
    ('维护真实数据', 'ai_workload_estimate_actual_update', 'ai_workload_estimate:actual:update', 6),
    ('删除预估', 'ai_workload_estimate_delete', 'ai_workload_estimate:delete', 7)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'ai_workload_estimate'
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
  AND p.module = 'ai_workload_estimate'
  AND p.is_delete = 0
  AND NOT EXISTS (
      SELECT 1 FROM public.sys_role_permission rp
      WHERE rp.role_id = r.id
        AND rp.permission_id = p.id
        AND rp.is_delete = 0
  );

UPDATE public.sys_role_permission rp
SET is_delete = 0
FROM public.sys_role r, public.sys_permission p
WHERE rp.role_id = r.id
  AND rp.permission_id = p.id
  AND r.status = 1
  AND r.is_delete = 0
  AND p.module = 'ai_workload_estimate'
  AND p.is_delete = 0;

INSERT INTO public.sys_role_menu (role_id, menu_id, is_delete, created_time)
SELECT r.id, m.id, 0, NOW()
FROM public.sys_role r
CROSS JOIN public.sys_menu m
WHERE r.status = 1
  AND r.is_delete = 0
  AND (m.code IN ('ai_quality_assistant', 'ai_workload_estimate') OR m.code LIKE 'ai_workload_estimate_%')
  AND m.is_delete = 0
  AND NOT EXISTS (
      SELECT 1 FROM public.sys_role_menu rm
      WHERE rm.role_id = r.id
        AND rm.menu_id = m.id
        AND rm.is_delete = 0
  );

UPDATE public.sys_role_menu rm
SET is_delete = 0
FROM public.sys_role r, public.sys_menu m
WHERE rm.role_id = r.id
  AND rm.menu_id = m.id
  AND r.status = 1
  AND r.is_delete = 0
  AND (m.code IN ('ai_quality_assistant', 'ai_workload_estimate') OR m.code LIKE 'ai_workload_estimate_%')
  AND m.is_delete = 0;

SELECT setval(pg_get_serial_sequence('public.sys_permission', 'id'), COALESCE((SELECT MAX(id) FROM public.sys_permission), 1));
SELECT setval(pg_get_serial_sequence('public.sys_menu', 'id'), COALESCE((SELECT MAX(id) FROM public.sys_menu), 1));

COMMIT;
