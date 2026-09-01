-- 移动自动化权限与菜单初始化（PostgreSQL，幂等执行）
-- 执行前请确认 sys_* 表为当前环境实际 RBAC 表。

BEGIN;

INSERT INTO sys_permission (code, name, module, action, description, status, is_delete)
SELECT item.code, item.name, 'mobile_automation', item.action, item.description, 1, 0
FROM (VALUES
    ('mobile_automation:device:list', '查看移动设备', 'device:list', '查看移动设备列表'),
    ('mobile_automation:device:manage', '管理移动设备', 'device:manage', '扫描与维护移动设备'),
    ('mobile_automation:app:list', '查看移动应用', 'app:list', '查看移动应用配置'),
    ('mobile_automation:app:manage', '管理移动应用', 'app:manage', '维护移动应用配置'),
    ('mobile_automation:run', '执行移动自动化', 'run', '创建移动自动化执行'),
    ('mobile_automation:list', '查看移动执行', 'list', '查看移动自动化执行列表'),
    ('mobile_automation:detail', '查看移动执行详情', 'detail', '查看移动自动化执行详情与产物'),
    ('mobile_automation:cancel', '取消移动执行', 'cancel', '取消移动自动化执行')
) AS item(code, name, action, description)
WHERE NOT EXISTS (SELECT 1 FROM sys_permission p WHERE p.code = item.code);

INSERT INTO sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete)
SELECT 0, '移动自动化', 'mobile_automation', 1, '/mobile-automation', '', 'el-icon-mobile-phone', 'mobile_automation:list', 90, 1, 1, 0
WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE code = 'mobile_automation');

INSERT INTO sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete)
SELECT parent.id, item.name, item.code, 2, item.path, item.component, item.icon, item.permission_code, item.sort, 1, 1, 0
FROM sys_menu parent
CROSS JOIN (VALUES
    ('移动设备', 'mobile_device', '/mobile-automation/devices', 'MobileAutomation/DeviceList', 'el-icon-mobile-phone', 'mobile_automation:device:list', 1),
    ('应用配置', 'mobile_app', '/mobile-automation/apps', 'MobileAutomation/AppList', 'el-icon-setting', 'mobile_automation:app:list', 2),
    ('发起执行', 'mobile_run', '/mobile-automation/run', 'MobileAutomation/ExecutionCreate', 'el-icon-video-play', 'mobile_automation:run', 3),
    ('执行记录', 'mobile_execution', '/mobile-automation/executions', 'MobileAutomation/ExecutionList', 'el-icon-tickets', 'mobile_automation:list', 4)
) AS item(name, code, path, component, icon, permission_code, sort)
WHERE parent.code = 'mobile_automation'
  AND NOT EXISTS (SELECT 1 FROM sys_menu child WHERE child.code = item.code);

COMMIT;
