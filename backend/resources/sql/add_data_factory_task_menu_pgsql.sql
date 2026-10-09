-- 造数工具：左侧菜单增加「造数结果历史」（幂等）
BEGIN;

INSERT INTO sys_menu (
  parent_id, name, code, type, path, component, icon, permission_code,
  sort, visible, status, is_delete
)
SELECT
  m.id,
  '造数结果历史',
  'data_factory_task_history',
  2,
  '/data-tools/factory/task',
  'data-tools/factory/task',
  'el-icon-document',
  'data_task:status',
  30,
  1,
  1,
  0
FROM sys_menu m
WHERE m.code = 'data_tools'
  AND NOT EXISTS (
    SELECT 1 FROM sys_menu WHERE code = 'data_factory_task_history'
  );

-- 已存在则校正路径与展示名
UPDATE sys_menu
SET
  name = '造数结果历史',
  path = '/data-tools/factory/task',
  permission_code = COALESCE(NULLIF(permission_code, ''), 'data_task:status'),
  visible = 1,
  status = 1,
  is_delete = 0,
  sort = COALESCE(sort, 30)
WHERE code = 'data_factory_task_history';

-- 赋给已有造数工厂菜单的角色
INSERT INTO sys_role_menu (role_id, menu_id, is_delete)
SELECT rm.role_id, hist.id, 0
FROM sys_role_menu rm
JOIN sys_menu factory ON factory.id = rm.menu_id AND factory.code = 'data_factory_manage'
JOIN sys_menu hist ON hist.code = 'data_factory_task_history'
WHERE COALESCE(rm.is_delete, 0) = 0
  AND NOT EXISTS (
    SELECT 1 FROM sys_role_menu x
    WHERE x.role_id = rm.role_id
      AND x.menu_id = hist.id
      AND COALESCE(x.is_delete, 0) = 0
  );

COMMIT;
