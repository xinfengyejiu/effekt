-- 添加文档源模块的权限和菜单

BEGIN;

-- 1. 添加文档源相关权限
INSERT INTO public.sys_permission (code, name, module, action, description, status, is_delete, created_time, updated_time) VALUES
('document:list', '文档源列表', 'document', 'list', '查看文档源列表', 1, 0, NOW(), NOW()),
('document:detail', '文档源详情', 'document', 'detail', '查看文档源详情', 1, 0, NOW(), NOW()),
('document:create', '文档源创建', 'document', 'create', '创建文档源', 1, 0, NOW(), NOW()),
('document:update', '文档源更新', 'document', 'update', '更新文档源', 1, 0, NOW(), NOW()),
('document:delete', '文档源删除', 'document', 'delete', '删除文档源', 1, 0, NOW(), NOW()),
('document:generate', '文档源生成用例', 'document', 'generate', '根据文档生成测试用例', 1, 0, NOW(), NOW()),
('document:import', '文档源导入用例', 'document', 'import', '导入生成的测试用例', 1, 0, NOW(), NOW())
ON CONFLICT (code) DO UPDATE SET name=EXCLUDED.name, description=EXCLUDED.description;

-- 2. 添加文档源菜单（作为测试用例的子菜单）
-- 先查找测试用例菜单的ID
WITH case_menu AS (
    SELECT id FROM public.sys_menu WHERE code = 'case' AND is_delete = 0
)
INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT id, '文档源管理', 'document', 2, '/document', 'document/index', 'file-text', 'document:list', 10, 1, 1, 0, NOW(), NOW()
FROM case_menu
ON CONFLICT (code) DO UPDATE SET name=EXCLUDED.name, path=EXCLUDED.path, component=EXCLUDED.component;

COMMIT;
