-- 隐藏「数据库造数」菜单（幂等）
BEGIN;
UPDATE sys_menu
SET visible = 0, status = 0
WHERE code = 'data_builder_manage';
COMMIT;
