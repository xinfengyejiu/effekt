-- 精准测试菜单与权限初始化脚本

BEGIN;

INSERT INTO public.sys_permission (code, name, module, action, description, status, is_delete, created_time, updated_time) VALUES
('precise:analysis:list', '精准测试分析列表', 'precise', 'analysis:list', '查看精准测试变更分析列表', 1, 0, NOW(), NOW()),
('precise:analysis:create', '精准测试分析新增', 'precise', 'analysis:create', '创建精准测试变更分析任务', 1, 0, NOW(), NOW()),
('precise:analysis:detail', '精准测试分析详情', 'precise', 'analysis:detail', '查看精准测试变更分析详情', 1, 0, NOW(), NOW()),
('precise:analysis:parse', '精准测试解析Diff', 'precise', 'analysis:parse', '解析Git Diff变更文件和变更行', 1, 0, NOW(), NOW()),
('precise:analysis:ai', '精准测试AI影响分析', 'precise', 'analysis:ai', '生成AI影响分析结论', 1, 0, NOW(), NOW()),
('precise:relation:list', '精准测试关系列表', 'precise', 'relation:list', '查看精准测试关系图谱', 1, 0, NOW(), NOW()),
('precise:relation:create', '精准测试关系新增', 'precise', 'relation:create', '新增精准测试关系', 1, 0, NOW(), NOW()),
('precise:relation:update', '精准测试关系编辑', 'precise', 'relation:update', '编辑精准测试关系', 1, 0, NOW(), NOW()),
('precise:relation:delete', '精准测试关系删除', 'precise', 'relation:delete', '删除精准测试关系', 1, 0, NOW(), NOW()),
('precise:relation:import', '精准测试关系导入', 'precise', 'relation:import', '批量导入精准测试关系', 1, 0, NOW(), NOW()),
('precise:recommend:list', '精准测试推荐列表', 'precise', 'recommend:list', '查看精准回归推荐结果', 1, 0, NOW(), NOW()),
('precise:recommend:create', '精准测试生成推荐', 'precise', 'recommend:create', '生成精准回归推荐结果', 1, 0, NOW(), NOW()),
('precise:recommend:accept', '精准测试采纳推荐', 'precise', 'recommend:accept', '人工确认采纳精准回归推荐', 1, 0, NOW(), NOW()),
('precise:execute:create', '精准测试发起执行', 'precise', 'execute:create', '发起Jenkins精准回归执行', 1, 0, NOW(), NOW()),
('precise:execution:list', '精准测试执行列表', 'precise', 'execution:list', '查看精准测试执行记录', 1, 0, NOW(), NOW()),
('precise:execution:sync', '精准测试同步Jenkins', 'precise', 'execution:sync', '同步精准测试Jenkins执行状态', 1, 0, NOW(), NOW()),
('precise:coverage:upload', '精准测试覆盖率上传', 'precise', 'coverage:upload', '上传JaCoCo XML覆盖率报告', 1, 0, NOW(), NOW()),
('precise:coverage:pull', '精准测试覆盖率拉取', 'precise', 'coverage:pull', '从Jenkins归档产物拉取JaCoCo XML', 1, 0, NOW(), NOW()),
('precise:coverage:detail', '精准测试覆盖率详情', 'precise', 'coverage:detail', '查看覆盖率报告详情', 1, 0, NOW(), NOW()),
('precise:coverage:calculate', '精准测试增量覆盖率计算', 'precise', 'coverage:calculate', '计算JaCoCo增量覆盖率', 1, 0, NOW(), NOW()),
('precise:coverage:ai', '精准测试覆盖率AI风险', 'precise', 'coverage:ai', 'AI分析未覆盖变更代码风险', 1, 0, NOW(), NOW()),
('precise:gate:evaluate', '精准测试门禁评估', 'precise', 'gate:evaluate', '执行精准测试质量门禁评估', 1, 0, NOW(), NOW()),
('precise:gate:result', '精准测试门禁结果', 'precise', 'gate:result', '查看精准测试质量门禁结果', 1, 0, NOW(), NOW())
ON CONFLICT (code) DO UPDATE SET name=EXCLUDED.name, module=EXCLUDED.module, action=EXCLUDED.action, description=EXCLUDED.description, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
VALUES (0, '精准测试', 'precise_test', 1, '/precise', 'precise/index', 'el-icon-aim', 'precise:analysis:list', 21, 1, 1, 0, NOW(), NOW())
ON CONFLICT (code) DO UPDATE SET parent_id=0, name=EXCLUDED.name, type=EXCLUDED.type, path=EXCLUDED.path, component=EXCLUDED.component, icon=EXCLUDED.icon, permission_code=EXCLUDED.permission_code, sort=EXCLUDED.sort, visible=1, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT p.id, v.name, v.code, v.type, v.path, v.component, v.icon, v.permission_code, v.sort, v.visible, 1, 0, NOW(), NOW()
FROM public.sys_menu p
CROSS JOIN (VALUES
    ('变更分析', 'precise_analysis', 2, '/precise/analysis', 'precise/analysis', 'el-icon-document-checked', 'precise:analysis:list', 1, 1),
    ('关系图谱', 'precise_relation', 2, '/precise/relations', 'precise/relations', 'el-icon-share', 'precise:relation:list', 2, 1),
    ('回归推荐', 'precise_recommendation', 2, '/precise/recommendation', 'precise/recommendation', 'el-icon-magic-stick', 'precise:recommend:list', 3, 1),
    ('覆盖率报告', 'precise_coverage', 2, '/precise/coverage', 'precise/coverage', 'el-icon-data-analysis', 'precise:coverage:detail', 4, 1),
    ('质量门禁', 'precise_gate', 2, '/precise/gate', 'precise/gate', 'el-icon-finished', 'precise:gate:result', 5, 1)
) AS v(name, code, type, path, component, icon, permission_code, sort, visible)
WHERE p.code = 'precise_test'
ON CONFLICT (code) DO UPDATE SET parent_id=EXCLUDED.parent_id, name=EXCLUDED.name, type=EXCLUDED.type, path=EXCLUDED.path, component=EXCLUDED.component, icon=EXCLUDED.icon, permission_code=EXCLUDED.permission_code, sort=EXCLUDED.sort, visible=EXCLUDED.visible, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT m.id, v.name, v.code, 3, '', '', '', v.permission_code, v.sort, 1, 1, 0, NOW(), NOW()
FROM public.sys_menu m
CROSS JOIN (VALUES
    ('新增分析', 'precise_analysis_create', 'precise:analysis:create', 1),
    ('查看详情', 'precise_analysis_detail', 'precise:analysis:detail', 2),
    ('解析Diff', 'precise_analysis_parse', 'precise:analysis:parse', 3),
    ('AI影响分析', 'precise_analysis_ai', 'precise:analysis:ai', 4)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'precise_analysis'
ON CONFLICT (code) DO UPDATE SET parent_id=EXCLUDED.parent_id, name=EXCLUDED.name, type=EXCLUDED.type, permission_code=EXCLUDED.permission_code, sort=EXCLUDED.sort, visible=1, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT m.id, v.name, v.code, 3, '', '', '', v.permission_code, v.sort, 1, 1, 0, NOW(), NOW()
FROM public.sys_menu m
CROSS JOIN (VALUES
    ('新增关系', 'precise_relation_create', 'precise:relation:create', 1),
    ('编辑关系', 'precise_relation_update', 'precise:relation:update', 2),
    ('删除关系', 'precise_relation_delete', 'precise:relation:delete', 3),
    ('导入关系', 'precise_relation_import', 'precise:relation:import', 4)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'precise_relation'
ON CONFLICT (code) DO UPDATE SET parent_id=EXCLUDED.parent_id, name=EXCLUDED.name, type=EXCLUDED.type, permission_code=EXCLUDED.permission_code, sort=EXCLUDED.sort, visible=1, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT m.id, v.name, v.code, 3, '', '', '', v.permission_code, v.sort, 1, 1, 0, NOW(), NOW()
FROM public.sys_menu m
CROSS JOIN (VALUES
    ('生成推荐', 'precise_recommend_create', 'precise:recommend:create', 1),
    ('采纳推荐', 'precise_recommend_accept', 'precise:recommend:accept', 2),
    ('发起执行', 'precise_execute_create', 'precise:execute:create', 3),
    ('执行列表', 'precise_execution_list', 'precise:execution:list', 4),
    ('同步Jenkins', 'precise_execution_sync', 'precise:execution:sync', 5)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'precise_recommendation'
ON CONFLICT (code) DO UPDATE SET parent_id=EXCLUDED.parent_id, name=EXCLUDED.name, type=EXCLUDED.type, permission_code=EXCLUDED.permission_code, sort=EXCLUDED.sort, visible=1, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT m.id, v.name, v.code, 3, '', '', '', v.permission_code, v.sort, 1, 1, 0, NOW(), NOW()
FROM public.sys_menu m
CROSS JOIN (VALUES
    ('上传覆盖率', 'precise_coverage_upload', 'precise:coverage:upload', 1),
    ('拉取覆盖率', 'precise_coverage_pull', 'precise:coverage:pull', 2),
    ('计算增量覆盖率', 'precise_coverage_calculate', 'precise:coverage:calculate', 3),
    ('AI风险分析', 'precise_coverage_ai', 'precise:coverage:ai', 4)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'precise_coverage'
ON CONFLICT (code) DO UPDATE SET parent_id=EXCLUDED.parent_id, name=EXCLUDED.name, type=EXCLUDED.type, permission_code=EXCLUDED.permission_code, sort=EXCLUDED.sort, visible=1, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT m.id, v.name, v.code, 3, '', '', '', v.permission_code, v.sort, 1, 1, 0, NOW(), NOW()
FROM public.sys_menu m
CROSS JOIN (VALUES
    ('执行门禁', 'precise_gate_evaluate', 'precise:gate:evaluate', 1),
    ('查看门禁结果', 'precise_gate_result', 'precise:gate:result', 2)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'precise_gate'
ON CONFLICT (code) DO UPDATE SET parent_id=EXCLUDED.parent_id, name=EXCLUDED.name, type=EXCLUDED.type, permission_code=EXCLUDED.permission_code, sort=EXCLUDED.sort, visible=1, status=1, is_delete=0, updated_time=NOW();

INSERT INTO public.sys_role_permission (role_id, permission_id, is_delete, created_time)
SELECT r.id, p.id, 0, NOW()
FROM public.sys_role r
CROSS JOIN public.sys_permission p
WHERE r.status = 1
  AND r.is_delete = 0
  AND p.module = 'precise'
  AND p.is_delete = 0
  AND NOT EXISTS (
      SELECT 1 FROM public.sys_role_permission rp
      WHERE rp.role_id = r.id
        AND rp.permission_id = p.id
        AND rp.is_delete = 0
  );

INSERT INTO public.sys_role_menu (role_id, menu_id, is_delete, created_time)
SELECT r.id, m.id, 0, NOW()
FROM public.sys_role r
CROSS JOIN public.sys_menu m
WHERE r.status = 1
  AND r.is_delete = 0
  AND (m.code = 'precise_test' OR m.code LIKE 'precise_%')
  AND m.is_delete = 0
  AND NOT EXISTS (
      SELECT 1 FROM public.sys_role_menu rm
      WHERE rm.role_id = r.id
        AND rm.menu_id = m.id
        AND rm.is_delete = 0
  );

SELECT setval(pg_get_serial_sequence('public.sys_permission', 'id'), COALESCE((SELECT MAX(id) FROM public.sys_permission), 1));
SELECT setval(pg_get_serial_sequence('public.sys_menu', 'id'), COALESCE((SELECT MAX(id) FROM public.sys_menu), 1));

COMMIT;

