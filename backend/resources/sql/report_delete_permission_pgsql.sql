-- Test report delete permission.

BEGIN;

INSERT INTO public.sys_permission (code, name, module, action, description, status, is_delete, created_time, updated_time) VALUES
('report:delete', '测试报告删除', 'report', 'delete', '删除测试报告', 1, 0, NOW(), NOW())
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    module = EXCLUDED.module,
    action = EXCLUDED.action,
    description = EXCLUDED.description,
    status = 1,
    is_delete = 0,
    updated_time = NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT m.id, '删除报告', 'report_delete', 3, '', '', '', 'report:delete', 3, 1, 1, 0, NOW(), NOW()
FROM public.sys_menu m
WHERE m.is_delete = 0
  AND (m.code IN ('report', 'test_report') OR m.path = '/test-platform/report' OR m.name = '测试报告')
ORDER BY CASE WHEN m.path = '/test-platform/report' THEN 1 ELSE 2 END, m.id
LIMIT 1
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
  AND p.code = 'report:delete'
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
  AND m.code = 'report_delete'
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
