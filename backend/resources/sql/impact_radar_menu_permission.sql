-- 变更影响雷达权限与菜单（PostgreSQL，幂等）

BEGIN;

INSERT INTO sys_permission (code, name, module, action, description, status, is_delete)
SELECT item.code, item.name, 'precise', item.action, item.description, 1, 0
FROM (VALUES
    ('precise:radar:run', '变更影响雷达执行', 'radar:run', '创建并执行变更影响雷达分析'),
    ('precise:radar:list', '变更影响雷达查看', 'radar:list', '查看雷达列表与详情')
) AS item(code, name, action, description)
WHERE NOT EXISTS (SELECT 1 FROM sys_permission p WHERE p.code = item.code);

INSERT INTO sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete)
SELECT parent.id, '变更影响雷达', 'precise_radar', 2, '/precise/radar', 'PreciseTest/RadarList', 'el-icon-aim', 'precise:radar:list', 6, 1, 1, 0
FROM sys_menu parent
WHERE parent.code = 'precise_test'
  AND NOT EXISTS (SELECT 1 FROM sys_menu child WHERE child.code = 'precise_radar');

INSERT INTO sys_role_permission (role_id, permission_id, is_delete, created_time)
SELECT r.id, p.id, 0, NOW()
FROM sys_role r
CROSS JOIN sys_permission p
WHERE r.status = 1
  AND r.is_delete = 0
  AND p.is_delete = 0
  AND p.code LIKE 'precise:radar:%'
  AND NOT EXISTS (
      SELECT 1 FROM sys_role_permission rp
      WHERE rp.role_id = r.id
        AND rp.permission_id = p.id
        AND rp.is_delete = 0
  );

INSERT INTO sys_role_menu (role_id, menu_id, is_delete, created_time)
SELECT r.id, m.id, 0, NOW()
FROM sys_role r
CROSS JOIN sys_menu m
WHERE r.status = 1
  AND r.is_delete = 0
  AND m.is_delete = 0
  AND m.code = 'precise_radar'
  AND NOT EXISTS (
      SELECT 1 FROM sys_role_menu rm
      WHERE rm.role_id = r.id
        AND rm.menu_id = m.id
        AND rm.is_delete = 0
  );

COMMIT;
