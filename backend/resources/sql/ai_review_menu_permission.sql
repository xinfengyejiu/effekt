-- AI test review assistant menu and permissions.

BEGIN;

INSERT INTO public.sys_permission (code, name, module, action, description, status, is_delete, created_time, updated_time) VALUES
('ai_review:list', 'AI测试评审列表', 'ai_review', 'list', '查看AI测试评审列表', 1, 0, NOW(), NOW()),
('ai_review:create', 'AI测试评审创建', 'ai_review', 'create', '创建AI测试评审任务', 1, 0, NOW(), NOW()),
('ai_review:detail', 'AI测试评审详情', 'ai_review', 'detail', '查看AI测试评审详情', 1, 0, NOW(), NOW()),
('ai_review:execute', 'AI测试评审执行', 'ai_review', 'execute', '执行AI测试评审', 1, 0, NOW(), NOW()),
('ai_review:confirm', 'AI测试评审确认', 'ai_review', 'confirm', '确认AI测试评审结论', 1, 0, NOW(), NOW()),
('ai_review:case:import', 'AI测试评审用例导入', 'ai_review', 'case:import', '导入或关联AI测试评审建议用例', 1, 0, NOW(), NOW())
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
          code IN ('test_platform', 'case_cycle', 'quality_collaboration', 'ai_platform')
          OR name IN ('用例周期', '测试平台', '智能质量协同', 'AI测试中枢')
      )
    ORDER BY CASE
        WHEN code = 'test_platform' OR name = '测试平台' THEN 1
        WHEN name = '用例周期' THEN 2
        WHEN code = 'ai_platform' OR name = 'AI测试中枢' THEN 3
        WHEN code = 'quality_collaboration' OR name = '智能质量协同' THEN 4
        ELSE 9
    END, id
    LIMIT 1
), 0), 'AI测试评审', 'ai_review', 2, '/ai-review', 'AIReview/ReviewList', 'el-icon-s-check', 'ai_review:list', 23, 1, 1, 0, NOW(), NOW()
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
    ('新增评审', 'ai_review_create', 'ai_review:create', 1),
    ('查看详情', 'ai_review_detail', 'ai_review:detail', 2),
    ('执行评审', 'ai_review_execute', 'ai_review:execute', 3),
    ('确认评审', 'ai_review_confirm', 'ai_review:confirm', 4),
    ('导入用例', 'ai_review_case_import', 'ai_review:case:import', 5)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'ai_review'
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
  AND p.module = 'ai_review'
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
  AND (m.code = 'ai_review' OR m.code LIKE 'ai_review_%')
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

