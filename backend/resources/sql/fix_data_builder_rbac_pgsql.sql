-- 造数工厂 / 数据库造数：补齐权限并赋给常用角色（幂等）
BEGIN;

INSERT INTO sys_permission (code, name, module, action, description, status, is_delete)
SELECT 'data_builder:list', '造数器列表', 'data_builder', 'list', '查看造数器列表', 1, 0
WHERE NOT EXISTS (SELECT 1 FROM sys_permission WHERE code = 'data_builder:list');

INSERT INTO sys_permission (code, name, module, action, description, status, is_delete)
SELECT 'data_builder:detail', '造数器详情', 'data_builder', 'detail', '查看造数器详情', 1, 0
WHERE NOT EXISTS (SELECT 1 FROM sys_permission WHERE code = 'data_builder:detail');

INSERT INTO sys_permission (code, name, module, action, description, status, is_delete)
SELECT 'data_builder:create', '创建造数器', 'data_builder', 'create', '创建造数器/场景', 1, 0
WHERE NOT EXISTS (SELECT 1 FROM sys_permission WHERE code = 'data_builder:create');

INSERT INTO sys_permission (code, name, module, action, description, status, is_delete)
SELECT 'data_builder:update', '更新造数器', 'data_builder', 'update', '更新造数器/场景', 1, 0
WHERE NOT EXISTS (SELECT 1 FROM sys_permission WHERE code = 'data_builder:update');

INSERT INTO sys_permission (code, name, module, action, description, status, is_delete)
SELECT 'data_builder:delete', '删除造数器', 'data_builder', 'delete', '删除造数器/场景', 1, 0
WHERE NOT EXISTS (SELECT 1 FROM sys_permission WHERE code = 'data_builder:delete');

INSERT INTO sys_permission (code, name, module, action, description, status, is_delete)
SELECT 'data_builder:execute', '执行造数器', 'data_builder', 'execute', '执行造数场景', 1, 0
WHERE NOT EXISTS (SELECT 1 FROM sys_permission WHERE code = 'data_builder:execute');

INSERT INTO sys_permission (code, name, module, action, description, status, is_delete)
SELECT 'data_builder:*', '造数器全部权限', 'data_builder', '*', '造数器模块全部权限', 1, 0
WHERE NOT EXISTS (SELECT 1 FROM sys_permission WHERE code = 'data_builder:*');

INSERT INTO sys_permission (code, name, module, action, description, status, is_delete)
SELECT 'data_task:status', '造数任务状态', 'data_task', 'status', '查看造数任务状态/列表', 1, 0
WHERE NOT EXISTS (SELECT 1 FROM sys_permission WHERE code = 'data_task:status');

INSERT INTO sys_permission (code, name, module, action, description, status, is_delete)
SELECT 'data_task:*', '造数任务全部权限', 'data_task', '*', '造数任务模块全部权限', 1, 0
WHERE NOT EXISTS (SELECT 1 FROM sys_permission WHERE code = 'data_task:*');

-- 菜单权限码对齐接口
UPDATE sys_menu
SET permission_code = 'data_builder:*'
WHERE code IN ('data_factory_manage', 'data_builder_manage')
  AND (permission_code IS NULL OR permission_code = '' OR permission_code = 'db-builder:*');

UPDATE sys_menu
SET permission_code = 'data_tools:*'
WHERE code = 'data_tools'
  AND (permission_code IS NULL OR permission_code = '');

INSERT INTO sys_permission (code, name, module, action, description, status, is_delete)
SELECT 'data_tools:*', '造数工具全部权限', 'data_tools', '*', '造数工具目录权限', 1, 0
WHERE NOT EXISTS (SELECT 1 FROM sys_permission WHERE code = 'data_tools:*');

-- 赋给 admin / data_manager / test_manager / ui_manager
INSERT INTO sys_role_permission (role_id, permission_id, is_delete)
SELECT r.id, p.id, 0
FROM sys_role r
CROSS JOIN sys_permission p
WHERE r.code IN ('admin', 'data_manager', 'test_manager', 'ui_manager')
  AND r.is_delete = 0
  AND p.is_delete = 0
  AND p.code IN (
    'data_builder:*',
    'data_builder:list',
    'data_builder:detail',
    'data_builder:create',
    'data_builder:update',
    'data_builder:delete',
    'data_builder:execute',
    'data_task:*',
    'data_task:status',
    'data_tools:*'
  )
  AND NOT EXISTS (
    SELECT 1 FROM sys_role_permission rp
    WHERE rp.role_id = r.id AND rp.permission_id = p.id AND COALESCE(rp.is_delete, 0) = 0
  );

COMMIT;
