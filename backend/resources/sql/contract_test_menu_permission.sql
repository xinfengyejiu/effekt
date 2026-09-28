-- 契约测试权限与菜单初始化（PostgreSQL，幂等）

BEGIN;

INSERT INTO sys_permission (code, name, module, action, description, status, is_delete)
SELECT item.code, item.name, 'contract', item.action, item.description, 1, 0
FROM (VALUES
    ('contract:suite:list', '查看契约套件', 'suite:list', '查看契约套件列表'),
    ('contract:suite:manage', '管理契约套件', 'suite:manage', '创建/编辑/删除契约套件'),
    ('contract:suite:run', '执行契约套件', 'suite:run', '手动触发契约执行'),
    ('contract:run:list', '查看契约执行', 'run:list', '查看契约执行记录与详情')
) AS item(code, name, action, description)
WHERE NOT EXISTS (SELECT 1 FROM sys_permission p WHERE p.code = item.code);

INSERT INTO sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete)
SELECT 0, '契约守护', 'contract', 1, '/contract', '', 'el-icon-document-checked', 'contract:suite:list', 96, 1, 1, 0
WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE code = 'contract');

INSERT INTO sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete)
SELECT parent.id, item.name, item.code, 2, item.path, item.component, item.icon, item.permission_code, item.sort, 1, 1, 0
FROM sys_menu parent
CROSS JOIN (VALUES
    ('契约套件', 'contract_suites', '/contract/suites', 'Contract/SuiteList', 'el-icon-document-checked', 'contract:suite:list', 1),
    ('执行记录', 'contract_runs', '/contract/runs', 'Contract/RunList', 'el-icon-tickets', 'contract:run:list', 2)
) AS item(name, code, path, component, icon, permission_code, sort)
WHERE parent.code = 'contract'
  AND NOT EXISTS (SELECT 1 FROM sys_menu child WHERE child.code = item.code);

INSERT INTO sys_role_permission (role_id, permission_id, is_delete, created_time)
SELECT r.id, p.id, 0, NOW()
FROM sys_role r
CROSS JOIN sys_permission p
WHERE r.status = 1
  AND r.is_delete = 0
  AND p.is_delete = 0
  AND p.code LIKE 'contract:%'
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
  AND (m.code = 'contract' OR m.code LIKE 'contract_%')
  AND NOT EXISTS (
      SELECT 1 FROM sys_role_menu rm
      WHERE rm.role_id = r.id
        AND rm.menu_id = m.id
        AND rm.is_delete = 0
  );

COMMIT;
