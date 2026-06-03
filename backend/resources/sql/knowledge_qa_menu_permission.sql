-- 需求问答菜单与权限初始化脚本

BEGIN;

INSERT INTO public.permission (code, name, module, action, description, status, is_delete, created_time, updated_time) VALUES
('knowledge:list', '需求问答列表', 'knowledge', 'list', '查看需求问答文档列表', 1, 0, NOW(), NOW()),
('knowledge:upload', '需求问答上传', 'knowledge', 'upload', '上传需求问答知识库文件', 1, 0, NOW(), NOW()),
('knowledge:parse', '需求问答解析', 'knowledge', 'parse', '解析需求文档为知识库分片', 1, 0, NOW(), NOW()),
('knowledge:search', '需求问答检索', 'knowledge', 'search', '执行本地知识库检索', 1, 0, NOW(), NOW()),
('knowledge:chat', '需求问答对话', 'knowledge', 'chat', '执行知识库大模型问答', 1, 0, NOW(), NOW()),
('knowledge:setting', '需求问答模型设置', 'knowledge', 'setting', '维护知识库问答模型设置', 1, 0, NOW(), NOW()),
('knowledge:delete', '需求问答删除', 'knowledge', 'delete', '删除需求问答文档或会话', 1, 0, NOW(), NOW())
ON CONFLICT (code) DO UPDATE SET name=EXCLUDED.name, module=EXCLUDED.module, action=EXCLUDED.action, description=EXCLUDED.description, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
VALUES (NULL, '需求问答', 'requirement_qa', 1, '/requirement-qa', 'requirement-qa/index', 'el-icon-chat-dot-round', 'knowledge:list', 38, 1, 1, 0, NOW(), NOW())
ON CONFLICT (code) DO UPDATE SET parent_id=NULL, name=EXCLUDED.name, type=EXCLUDED.type, path=EXCLUDED.path, component=EXCLUDED.component, icon=EXCLUDED.icon, permission_code=EXCLUDED.permission_code, sort=EXCLUDED.sort, visible=1, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.role_permission (role_id, permission_id, is_delete, created_time)
SELECT r.id, p.id, 0, NOW()
FROM public.role r
CROSS JOIN public.permission p
WHERE r.status = 1
  AND r.is_delete = 0
  AND p.code IN ('knowledge:list', 'knowledge:upload', 'knowledge:parse', 'knowledge:search', 'knowledge:chat', 'knowledge:setting', 'knowledge:delete')
  AND p.is_delete = 0
  AND NOT EXISTS (
      SELECT 1 FROM public.role_permission rp
      WHERE rp.role_id = r.id
        AND rp.permission_id = p.id
        AND rp.is_delete = 0
  );

INSERT INTO public.role_menu (role_id, menu_id, is_delete, created_time)
SELECT r.id, m.id, 0, NOW()
FROM public.role r
CROSS JOIN public.menu m
WHERE r.status = 1
  AND r.is_delete = 0
  AND m.code = 'requirement_qa'
  AND m.is_delete = 0
  AND NOT EXISTS (
      SELECT 1 FROM public.role_menu rm
      WHERE rm.role_id = r.id
        AND rm.menu_id = m.id
        AND rm.is_delete = 0
  );

SELECT setval(pg_get_serial_sequence('public.permission', 'id'), COALESCE((SELECT MAX(id) FROM public.permission), 1));
SELECT setval(pg_get_serial_sequence('public.menu', 'id'), COALESCE((SELECT MAX(id) FROM public.menu), 1));

COMMIT;
