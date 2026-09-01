-- 巡检系统权限与菜单初始化（PostgreSQL，幂等执行）

BEGIN;

-- 1. 插入权限
INSERT INTO sys_permission (code, name, module, action, description, status, is_delete)
SELECT item.code, item.name, 'inspection', item.action, item.description, 1, 0
FROM (VALUES
    ('inspection:group:list', '查看巡检组', 'group:list', '查看巡检组列表'),
    ('inspection:group:manage', '管理巡检组', 'group:manage', '创建/编辑/删除巡检组'),
    ('inspection:task:list', '查看巡检任务', 'task:list', '查看巡检任务列表'),
    ('inspection:task:manage', '管理巡检任务', 'task:manage', '创建/编辑/删除巡检任务'),
    ('inspection:task:execute', '执行巡检任务', 'task:execute', '手动触发巡检任务执行'),
    ('inspection:dbconfig:list', '查看数据库连接', 'dbconfig:list', '查看数据库连接配置'),
    ('inspection:dbconfig:manage', '管理数据库连接', 'dbconfig:manage', '创建/编辑/删除数据库连接'),
    ('inspection:execution:list', '查看执行记录', 'execution:list', '查看巡检执行记录'),
    ('inspection:execution:detail', '查看执行详情', 'execution:detail', '查看巡检执行详情'),
    ('inspection:report', '查看巡检报告', 'report', '查看巡检统计报表')
) AS item(code, name, action, description)
WHERE NOT EXISTS (SELECT 1 FROM sys_permission p WHERE p.code = item.code);

-- 2. 插入一级菜单（目录）
INSERT INTO sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete)
SELECT 0, '巡检管理', 'inspection', 1, '/inspection', '', 'el-icon-monitor', 'inspection:group:list', 95, 1, 1, 0
WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE code = 'inspection');

-- 3. 插入二级菜单
INSERT INTO sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete)
SELECT parent.id, item.name, item.code, 2, item.path, item.component, item.icon, item.permission_code, item.sort, 1, 1, 0
FROM sys_menu parent
CROSS JOIN (VALUES
    ('巡检概览', 'inspection_dashboard', '/inspection/dashboard', 'Inspection/Dashboard', 'el-icon-data-analysis', 'inspection:report', 1),
    ('定时任务', 'inspection_task', '/inspection/tasks', 'Inspection/TaskWorkspace', 'el-icon-tickets', 'inspection:task:list', 2),
    ('数据库连接', 'inspection_dbconfig', '/inspection/db-configs', 'Inspection/DbConfigList', 'el-icon-connection', 'inspection:dbconfig:list', 3),
    ('执行记录', 'inspection_execution', '/inspection/executions', 'Inspection/ExecutionList', 'el-icon-document', 'inspection:execution:list', 4),
    ('巡检报告', 'inspection_report', '/inspection/reports', 'Inspection/Report', 'el-icon-pie-chart', 'inspection:report', 5)
) AS item(name, code, path, component, icon, permission_code, sort)
WHERE parent.code = 'inspection'
  AND NOT EXISTS (SELECT 1 FROM sys_menu child WHERE child.code = item.code);

-- 3.1 收敛旧菜单：巡检组并入定时任务
UPDATE sys_menu
SET name = '定时任务',
    path = '/inspection/tasks',
    component = 'Inspection/TaskWorkspace',
    sort = 2,
    visible = 1
WHERE code = 'inspection_task';

UPDATE sys_menu
SET visible = 0,
    status = 0
WHERE code = 'inspection_group';

-- 4. 给所有启用角色授予巡检权限（否则接口会 403）
INSERT INTO sys_role_permission (role_id, permission_id, is_delete, created_time)
SELECT r.id, p.id, 0, NOW()
FROM sys_role r
CROSS JOIN sys_permission p
WHERE r.status = 1
  AND r.is_delete = 0
  AND p.is_delete = 0
  AND p.code LIKE 'inspection:%'
  AND NOT EXISTS (
      SELECT 1 FROM sys_role_permission rp
      WHERE rp.role_id = r.id
        AND rp.permission_id = p.id
        AND rp.is_delete = 0
  );

-- 5. 给所有启用角色挂上巡检菜单
INSERT INTO sys_role_menu (role_id, menu_id, is_delete, created_time)
SELECT r.id, m.id, 0, NOW()
FROM sys_role r
CROSS JOIN sys_menu m
WHERE r.status = 1
  AND r.is_delete = 0
  AND m.is_delete = 0
  AND (m.code = 'inspection' OR m.code LIKE 'inspection_%')
  AND NOT EXISTS (
      SELECT 1 FROM sys_role_menu rm
      WHERE rm.role_id = r.id
        AND rm.menu_id = m.id
        AND rm.is_delete = 0
  );

COMMIT;
