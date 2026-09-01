-- 性能测试菜单与权限初始化脚本

BEGIN;

INSERT INTO public.sys_permission (code, name, module, action, description, status, is_delete, created_time, updated_time) VALUES
('performance:scenario:list', '性能场景列表', 'performance', 'scenario:list', '查看性能场景列表', 1, 0, NOW(), NOW()),
('performance:scenario:create', '性能场景新增', 'performance', 'scenario:create', '新增性能场景', 1, 0, NOW(), NOW()),
('performance:scenario:update', '性能场景编辑', 'performance', 'scenario:update', '编辑性能场景', 1, 0, NOW(), NOW()),
('performance:scenario:delete', '性能场景删除', 'performance', 'scenario:delete', '删除性能场景', 1, 0, NOW(), NOW()),
('performance:script:list', '性能脚本列表', 'performance', 'script:list', '查看性能脚本资产', 1, 0, NOW(), NOW()),
('performance:script:upload', '性能脚本上传', 'performance', 'script:upload', '上传性能脚本包', 1, 0, NOW(), NOW()),
('performance:script:generate', 'AI生成性能脚本', 'performance', 'script:generate', '通过AI生成性能压测方案和脚本', 1, 0, NOW(), NOW()),
('performance:script:download', '性能脚本下载', 'performance', 'script:download', '下载性能脚本包', 1, 0, NOW(), NOW()),
('performance:config:list', '性能执行配置列表', 'performance', 'config:list', '查看性能执行配置', 1, 0, NOW(), NOW()),
('performance:config:save', '性能执行配置保存', 'performance', 'config:save', '新增或编辑性能执行配置', 1, 0, NOW(), NOW()),
('performance:run:list', '性能执行记录列表', 'performance', 'run:list', '查看性能执行记录', 1, 0, NOW(), NOW()),
('performance:run:execute', '发起性能压测', 'performance', 'run:execute', '发起Jenkins性能压测任务', 1, 0, NOW(), NOW()),
('performance:run:detail', '性能执行详情', 'performance', 'run:detail', '查看性能执行详情', 1, 0, NOW(), NOW()),
('performance:run:stop', '停止性能压测', 'performance', 'run:stop', '停止性能压测任务', 1, 0, NOW(), NOW()),
('performance:run:retry', '重试性能压测', 'performance', 'run:retry', '重试性能压测任务', 1, 0, NOW(), NOW()),
('performance:report:list', '性能报告列表', 'performance', 'report:list', '查看性能报告列表', 1, 0, NOW(), NOW()),
('performance:report:detail', '性能报告详情', 'performance', 'report:detail', '查看性能报告详情', 1, 0, NOW(), NOW()),
('performance:report:ai', '性能报告AI分析', 'performance', 'report:ai', '生成性能报告AI分析', 1, 0, NOW(), NOW()),
('performance:baseline:list', '性能基线列表', 'performance', 'baseline:list', '查看性能基线', 1, 0, NOW(), NOW()),
('performance:baseline:save', '性能基线保存', 'performance', 'baseline:save', '设置或废弃性能基线', 1, 0, NOW(), NOW()),
('performance:gate:list', '性能门禁规则列表', 'performance', 'gate:list', '查看性能门禁规则', 1, 0, NOW(), NOW()),
('performance:gate:save', '性能门禁规则保存', 'performance', 'gate:save', '新增或编辑性能门禁规则', 1, 0, NOW(), NOW()),
('performance:machine:list', '测试机资源池列表', 'performance', 'machine:list', '查看性能测试机资源池', 1, 0, NOW(), NOW()),
('performance:machine:save', '测试机资源池保存', 'performance', 'machine:save', '新增或编辑性能测试机', 1, 0, NOW(), NOW()),
('performance:machine:delete', '测试机资源池删除', 'performance', 'machine:delete', '删除性能测试机', 1, 0, NOW(), NOW()),
('performance:monitor:list', '性能监控源列表', 'performance', 'monitor:list', '查看性能监控源配置', 1, 0, NOW(), NOW()),
('performance:monitor:save', '性能监控源保存', 'performance', 'monitor:save', '新增或编辑性能监控源', 1, 0, NOW(), NOW()),
('performance:monitor:delete', '性能监控源删除', 'performance', 'monitor:delete', '删除性能监控源', 1, 0, NOW(), NOW()),
('performance:jenkins:callback', '性能Jenkins回调', 'performance', 'jenkins:callback', 'Jenkins回传性能测试执行结果', 1, 0, NOW(), NOW())
ON CONFLICT (code) DO UPDATE SET name=EXCLUDED.name, module=EXCLUDED.module, action=EXCLUDED.action, description=EXCLUDED.description, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
VALUES (0, '性能测试', 'performance_test', 1, '/performance', 'performance/index', 'el-icon-data-line', 'performance:scenario:list', 20, 1, 1, 0, NOW(), NOW())
ON CONFLICT (code) DO UPDATE SET parent_id=0, name=EXCLUDED.name, type=EXCLUDED.type, path=EXCLUDED.path, component=EXCLUDED.component, icon=EXCLUDED.icon, permission_code=EXCLUDED.permission_code, sort=EXCLUDED.sort, visible=1, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT p.id, v.name, v.code, v.type, v.path, v.component, v.icon, v.permission_code, v.sort, v.visible, 1, 0, NOW(), NOW()
FROM public.sys_menu p
CROSS JOIN (VALUES
    ('性能场景', 'performance_scenario', 2, '/performance/scenarios', 'performance/scenarios', 'el-icon-document', 'performance:scenario:list', 1, 1),
    ('发起压测', 'performance_run_wizard', 2, '/performance/run-wizard', 'performance/run-wizard', 'el-icon-video-play', 'performance:run:execute', 2, 1),
    ('执行记录', 'performance_run_list', 2, '/performance/runs', 'performance/runs', 'el-icon-tickets', 'performance:run:list', 3, 1),
    ('性能报告', 'performance_report', 2, '/performance/reports', 'performance/reports', 'el-icon-data-analysis', 'performance:report:list', 4, 1),
    ('测试机资源池', 'performance_test_machine', 2, '/performance/machines', 'performance/machines', 'el-icon-monitor', 'performance:machine:list', 5, 1)
) AS v(name, code, type, path, component, icon, permission_code, sort, visible)
WHERE p.code = 'performance_test'
ON CONFLICT (code) DO UPDATE SET parent_id=EXCLUDED.parent_id, name=EXCLUDED.name, type=EXCLUDED.type, path=EXCLUDED.path, component=EXCLUDED.component, icon=EXCLUDED.icon, permission_code=EXCLUDED.permission_code, sort=EXCLUDED.sort, visible=EXCLUDED.visible, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT m.id, v.name, v.code, 3, '', '', '', v.permission_code, v.sort, 1, 1, 0, NOW(), NOW()
FROM public.sys_menu m
CROSS JOIN (VALUES
    ('新增场景', 'performance_scenario_create', 'performance:scenario:create', 1),
    ('编辑场景', 'performance_scenario_update', 'performance:scenario:update', 2),
    ('删除场景', 'performance_scenario_delete', 'performance:scenario:delete', 3),
    ('上传脚本', 'performance_script_upload', 'performance:script:upload', 4),
    ('AI生成脚本', 'performance_script_generate', 'performance:script:generate', 5),
    ('下载脚本', 'performance_script_download', 'performance:script:download', 6),
    ('保存执行配置', 'performance_config_save', 'performance:config:save', 7),
    ('发起压测', 'performance_run_execute', 'performance:run:execute', 8),
    ('停止压测', 'performance_run_stop', 'performance:run:stop', 9),
    ('重试压测', 'performance_run_retry', 'performance:run:retry', 10),
    ('AI分析报告', 'performance_report_ai', 'performance:report:ai', 11),
    ('设置基线', 'performance_baseline_save', 'performance:baseline:save', 12),
    ('保存门禁', 'performance_gate_save', 'performance:gate:save', 13)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'performance_scenario'
ON CONFLICT (code) DO UPDATE SET parent_id=EXCLUDED.parent_id, name=EXCLUDED.name, type=EXCLUDED.type, permission_code=EXCLUDED.permission_code, sort=EXCLUDED.sort, visible=1, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT m.id, v.name, v.code, 3, '', '', '', v.permission_code, v.sort, 1, 1, 0, NOW(), NOW()
FROM public.sys_menu m
CROSS JOIN (VALUES
    ('新增测试机', 'performance_machine_create', 'performance:machine:save', 1),
    ('编辑测试机', 'performance_machine_update', 'performance:machine:save', 2),
    ('删除测试机', 'performance_machine_delete', 'performance:machine:delete', 3)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'performance_test_machine'
ON CONFLICT (code) DO UPDATE SET parent_id=EXCLUDED.parent_id, name=EXCLUDED.name, type=EXCLUDED.type, permission_code=EXCLUDED.permission_code, sort=EXCLUDED.sort, visible=1, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT m.id, v.name, v.code, 3, '', '', '', v.permission_code, v.sort, 1, 1, 0, NOW(), NOW()
FROM public.sys_menu m
CROSS JOIN (VALUES
    ('查看执行详情', 'performance_run_detail', 'performance:run:detail', 1),
    ('停止压测', 'performance_run_stop_button', 'performance:run:stop', 2),
    ('重试压测', 'performance_run_retry_button', 'performance:run:retry', 3)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'performance_run_list'
ON CONFLICT (code) DO UPDATE SET parent_id=EXCLUDED.parent_id, name=EXCLUDED.name, type=EXCLUDED.type, permission_code=EXCLUDED.permission_code, sort=EXCLUDED.sort, visible=1, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT m.id, v.name, v.code, 3, '', '', '', v.permission_code, v.sort, 1, 1, 0, NOW(), NOW()
FROM public.sys_menu m
CROSS JOIN (VALUES
    ('查看报告详情', 'performance_report_detail', 'performance:report:detail', 1),
    ('AI分析报告', 'performance_report_ai_button', 'performance:report:ai', 2)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'performance_report'
ON CONFLICT (code) DO UPDATE SET parent_id=EXCLUDED.parent_id, name=EXCLUDED.name, type=EXCLUDED.type, permission_code=EXCLUDED.permission_code, sort=EXCLUDED.sort, visible=1, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT m.id, v.name, v.code, 3, '', '', '', v.permission_code, v.sort, 1, 1, 0, NOW(), NOW()
FROM public.sys_menu m
CROSS JOIN (VALUES
    ('查看性能脚本', 'performance_script_list_button', 'performance:script:list', 1),
    ('查看执行配置', 'performance_config_list_button', 'performance:config:list', 2),
    ('查看性能基线', 'performance_baseline_list_button', 'performance:baseline:list', 3),
    ('查看监控源', 'performance_monitor_list_button', 'performance:monitor:list', 4),
    ('保存监控源', 'performance_monitor_save_button', 'performance:monitor:save', 5),
    ('删除监控源', 'performance_monitor_delete_button', 'performance:monitor:delete', 6)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'performance_scenario'
ON CONFLICT (code) DO UPDATE SET parent_id=EXCLUDED.parent_id, name=EXCLUDED.name, type=EXCLUDED.type, permission_code=EXCLUDED.permission_code, sort=EXCLUDED.sort, visible=1, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.sys_role_permission (role_id, permission_id, is_delete, created_time)
SELECT r.id, p.id, 0, NOW()
FROM public.sys_role r
CROSS JOIN public.sys_permission p
WHERE r.status = 1
  AND r.is_delete = 0
  AND p.module = 'performance'
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
  AND (m.code = 'performance_test' OR m.code LIKE 'performance_%')
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

