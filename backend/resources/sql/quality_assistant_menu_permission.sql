-- 对话式质量助手权限初始化（PostgreSQL，幂等）
-- 入口为全局悬浮助手，不强制挂左侧菜单；权限供接口鉴权与角色分配。

BEGIN;

INSERT INTO sys_permission (code, name, module, action, description, status, is_delete)
SELECT item.code, item.name, 'qa_assistant', item.action, item.description, 1, 0
FROM (VALUES
    ('qa:assistant:chat', '质量助手对话', 'chat', '使用对话式质量助手问答'),
    ('qa:assistant:action', '质量助手动作', 'action', '从助手触发受限写操作（如跑契约套件）')
) AS item(code, name, action, description)
WHERE NOT EXISTS (SELECT 1 FROM sys_permission p WHERE p.code = item.code);

INSERT INTO sys_role_permission (role_id, permission_id, is_delete, created_time)
SELECT r.id, p.id, 0, NOW()
FROM sys_role r
CROSS JOIN sys_permission p
WHERE r.status = 1
  AND r.is_delete = 0
  AND p.is_delete = 0
  AND p.code LIKE 'qa:assistant:%'
  AND NOT EXISTS (
      SELECT 1 FROM sys_role_permission rp
      WHERE rp.role_id = r.id
        AND rp.permission_id = p.id
        AND rp.is_delete = 0
  );

COMMIT;
