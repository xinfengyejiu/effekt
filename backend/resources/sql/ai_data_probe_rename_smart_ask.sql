-- Rename display text: 对号查数 -> 智能问数 (keep permission/menu codes unchanged).

UPDATE public.sys_menu
SET name = 'AI智能问数',
    updated_time = NOW()
WHERE code = 'ai_data_probe'
  AND is_delete = 0;

UPDATE public.sys_permission
SET name = REPLACE(name, '对号查数', '智能问数'),
    description = REPLACE(COALESCE(description, ''), '对号查数', '智能问数'),
    updated_time = NOW()
WHERE module = 'ai_data_probe'
  AND is_delete = 0;
