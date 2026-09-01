-- Skills / Business Rules / AI Generation Context 初始化脚本
-- 数据库：PostgreSQL

CREATE TABLE IF NOT EXISTS test_skill (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    module_id BIGINT,
    name VARCHAR(128) NOT NULL,
    code VARCHAR(64) NOT NULL,
    description TEXT,
    trigger_condition TEXT NOT NULL,
    reasoning_path TEXT,
    output_spec TEXT,
    skill_file_path VARCHAR(512),
    skill_type SMALLINT NOT NULL DEFAULT 1,
    risk_level SMALLINT NOT NULL DEFAULT 2,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    status SMALLINT NOT NULL DEFAULT 1,
    owner_id BIGINT,
    created_by BIGINT,
    usage_count INTEGER NOT NULL DEFAULT 0,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE test_skill IS '测试 Skills 表：沉淀面向 AI 用例生成的测试策略、历史缺陷模式、边界场景和测试经验';
COMMENT ON COLUMN test_skill.id IS '主键 ID';
COMMENT ON COLUMN test_skill.project_id IS '所属项目 ID';
COMMENT ON COLUMN test_skill.module_id IS '所属模块 ID，空表示项目级通用 Skill';
COMMENT ON COLUMN test_skill.name IS 'Skill 名称';
COMMENT ON COLUMN test_skill.code IS 'Skill 编码，建议项目内唯一';
COMMENT ON COLUMN test_skill.description IS 'Skill 描述';
COMMENT ON COLUMN test_skill.trigger_condition IS '触发条件，描述什么需求或场景下应该使用该 Skill';
COMMENT ON COLUMN test_skill.reasoning_path IS '推理路径，指导 AI 如何分析需求并设计测试点';
COMMENT ON COLUMN test_skill.output_spec IS '输出规范，指导 AI 必须生成哪些类型或结构的用例';
COMMENT ON COLUMN test_skill.skill_file_path IS 'Skill 文件路径，指向 config/skills 下生成的 SKILL.md';
COMMENT ON COLUMN test_skill.skill_type IS 'Skill 类型：1通用测试策略 2历史缺陷模式 3边界场景 4接口测试 5UI测试 6性能测试 7安全测试 8数据一致性 9并发幂等 99其他';
COMMENT ON COLUMN test_skill.risk_level IS '风险等级：0高风险 1中高风险 2中风险 3低风险';
COMMENT ON COLUMN test_skill.tags IS '标签数组，例如 ["支付","金额","边界"]';
COMMENT ON COLUMN test_skill.status IS '状态：1启用 2停用 3草稿';
COMMENT ON COLUMN test_skill.owner_id IS '负责人用户 ID';
COMMENT ON COLUMN test_skill.created_by IS '创建人用户 ID';
COMMENT ON COLUMN test_skill.usage_count IS '使用次数，后续 PRD 生成用例引用该 Skill 时累加';
COMMENT ON COLUMN test_skill.is_delete IS '软删除标记：0未删除 1已删除';
COMMENT ON COLUMN test_skill.created_time IS '创建时间';
COMMENT ON COLUMN test_skill.updated_time IS '更新时间';

ALTER TABLE test_skill ADD COLUMN IF NOT EXISTS skill_file_path VARCHAR(512);
COMMENT ON COLUMN test_skill.skill_file_path IS 'Skill 文件路径，指向 config/skills 下生成的 SKILL.md';

CREATE UNIQUE INDEX IF NOT EXISTS uk_test_skill_project_code
ON test_skill(project_id, code)
WHERE is_delete = 0;
COMMENT ON INDEX uk_test_skill_project_code IS '同一项目下未删除 Skill 编码唯一';

CREATE INDEX IF NOT EXISTS idx_test_skill_project_module
ON test_skill(project_id, module_id)
WHERE is_delete = 0;
COMMENT ON INDEX idx_test_skill_project_module IS '按项目和模块查询 Skill';

CREATE INDEX IF NOT EXISTS idx_test_skill_status
ON test_skill(status)
WHERE is_delete = 0;
COMMENT ON INDEX idx_test_skill_status IS '按 Skill 状态过滤';

CREATE INDEX IF NOT EXISTS idx_test_skill_type
ON test_skill(skill_type)
WHERE is_delete = 0;
COMMENT ON INDEX idx_test_skill_type IS '按 Skill 类型过滤';

CREATE INDEX IF NOT EXISTS idx_test_skill_risk_level
ON test_skill(risk_level)
WHERE is_delete = 0;
COMMENT ON INDEX idx_test_skill_risk_level IS '按风险等级过滤';

CREATE INDEX IF NOT EXISTS idx_test_skill_created_time
ON test_skill(created_time DESC);
COMMENT ON INDEX idx_test_skill_created_time IS 'Skill 列表按创建时间排序';

CREATE INDEX IF NOT EXISTS idx_test_skill_file_path
ON test_skill(skill_file_path)
WHERE is_delete = 0;
COMMENT ON INDEX idx_test_skill_file_path IS '按 Skill 文件路径查询';

CREATE INDEX IF NOT EXISTS idx_test_skill_tags_gin
ON test_skill USING GIN(tags);
COMMENT ON INDEX idx_test_skill_tags_gin IS 'Skill 标签 JSONB GIN 索引';

CREATE TABLE IF NOT EXISTS test_business_rule (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    module_id BIGINT,
    name VARCHAR(128) NOT NULL,
    rule_code VARCHAR(64),
    rule_content TEXT NOT NULL,
    applicable_scene TEXT,
    example TEXT,
    rule_file_path VARCHAR(512),
    priority SMALLINT NOT NULL DEFAULT 2,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    status SMALLINT NOT NULL DEFAULT 1,
    owner_id BIGINT,
    created_by BIGINT,
    usage_count INTEGER NOT NULL DEFAULT 0,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE test_business_rule IS '业务规则表：沉淀确定性的业务约束、参数校验规则和场景规则';
COMMENT ON COLUMN test_business_rule.id IS '主键 ID';
COMMENT ON COLUMN test_business_rule.project_id IS '所属项目 ID';
COMMENT ON COLUMN test_business_rule.module_id IS '所属模块 ID，空表示项目级通用规则';
COMMENT ON COLUMN test_business_rule.name IS '业务规则名称';
COMMENT ON COLUMN test_business_rule.rule_code IS '业务规则编码，建议项目内唯一，可为空';
COMMENT ON COLUMN test_business_rule.rule_content IS '业务规则内容';
COMMENT ON COLUMN test_business_rule.applicable_scene IS '适用场景';
COMMENT ON COLUMN test_business_rule.example IS '规则示例';
COMMENT ON COLUMN test_business_rule.rule_file_path IS '业务规则文件路径，指向 config/rules 下生成的 RULE.md';
COMMENT ON COLUMN test_business_rule.priority IS '优先级：0高 1中高 2中 3低';

ALTER TABLE test_business_rule ADD COLUMN IF NOT EXISTS rule_file_path VARCHAR(512);
COMMENT ON COLUMN test_business_rule.rule_file_path IS '业务规则文件路径，指向 config/rules 下生成的 RULE.md';
COMMENT ON COLUMN test_business_rule.tags IS '标签数组，例如 ["支付","金额","参数校验"]';
COMMENT ON COLUMN test_business_rule.status IS '状态：1启用 2停用 3草稿';
COMMENT ON COLUMN test_business_rule.owner_id IS '负责人用户 ID';
COMMENT ON COLUMN test_business_rule.created_by IS '创建人用户 ID';
COMMENT ON COLUMN test_business_rule.usage_count IS '使用次数，后续 PRD 生成用例引用该规则时累加';
COMMENT ON COLUMN test_business_rule.is_delete IS '软删除标记：0未删除 1已删除';
COMMENT ON COLUMN test_business_rule.created_time IS '创建时间';
COMMENT ON COLUMN test_business_rule.updated_time IS '更新时间';

CREATE UNIQUE INDEX IF NOT EXISTS uk_test_business_rule_project_code
ON test_business_rule(project_id, rule_code)
WHERE is_delete = 0 AND rule_code IS NOT NULL;
COMMENT ON INDEX uk_test_business_rule_project_code IS '同一项目下未删除业务规则编码唯一，rule_code 为空时不参与唯一约束';

CREATE INDEX IF NOT EXISTS idx_test_business_rule_project_module
ON test_business_rule(project_id, module_id)
WHERE is_delete = 0;
COMMENT ON INDEX idx_test_business_rule_project_module IS '按项目和模块查询业务规则';

CREATE INDEX IF NOT EXISTS idx_test_business_rule_status
ON test_business_rule(status)
WHERE is_delete = 0;
COMMENT ON INDEX idx_test_business_rule_status IS '按业务规则状态过滤';

CREATE INDEX IF NOT EXISTS idx_test_business_rule_priority
ON test_business_rule(priority)
WHERE is_delete = 0;
COMMENT ON INDEX idx_test_business_rule_priority IS '按业务规则优先级过滤';

CREATE INDEX IF NOT EXISTS idx_test_business_rule_created_time
ON test_business_rule(created_time DESC);
COMMENT ON INDEX idx_test_business_rule_created_time IS '业务规则列表按创建时间排序';

CREATE INDEX IF NOT EXISTS idx_test_business_rule_file_path
ON test_business_rule(rule_file_path)
WHERE is_delete = 0;
COMMENT ON INDEX idx_test_business_rule_file_path IS '按业务规则文件路径查询';

CREATE INDEX IF NOT EXISTS idx_test_business_rule_tags_gin
ON test_business_rule USING GIN(tags);
COMMENT ON INDEX idx_test_business_rule_tags_gin IS '业务规则标签 JSONB GIN 索引';

CREATE TABLE IF NOT EXISTS test_ai_generation_context (
    id BIGSERIAL PRIMARY KEY,
    generation_id BIGINT,
    project_id BIGINT NOT NULL,
    module_id BIGINT,
    source_type SMALLINT NOT NULL,
    source_id BIGINT NOT NULL,
    source_name VARCHAR(128),
    match_score INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE test_ai_generation_context IS 'AI 生成上下文引用记录表：记录某次 PRD/AI 生成用例使用了哪些 Skill 或业务规则';
COMMENT ON COLUMN test_ai_generation_context.id IS '主键 ID';
COMMENT ON COLUMN test_ai_generation_context.generation_id IS 'AI 生成任务 ID，兼容现有 PRD 生成功能的任务 ID';
COMMENT ON COLUMN test_ai_generation_context.project_id IS '项目 ID';
COMMENT ON COLUMN test_ai_generation_context.module_id IS '模块 ID';
COMMENT ON COLUMN test_ai_generation_context.source_type IS '来源类型：1 Skill 2业务规则';
COMMENT ON COLUMN test_ai_generation_context.source_id IS '来源 ID，Skill ID 或 Business Rule ID';
COMMENT ON COLUMN test_ai_generation_context.source_name IS '来源名称快照';
COMMENT ON COLUMN test_ai_generation_context.match_score IS '匹配分数';
COMMENT ON COLUMN test_ai_generation_context.created_time IS '创建时间';

CREATE INDEX IF NOT EXISTS idx_test_ai_generation_context_generation
ON test_ai_generation_context(generation_id);
COMMENT ON INDEX idx_test_ai_generation_context_generation IS '按 AI 生成任务 ID 查询上下文引用';

CREATE INDEX IF NOT EXISTS idx_test_ai_generation_context_project_module
ON test_ai_generation_context(project_id, module_id);
COMMENT ON INDEX idx_test_ai_generation_context_project_module IS '按项目和模块查询上下文引用';

CREATE INDEX IF NOT EXISTS idx_test_ai_generation_context_source
ON test_ai_generation_context(source_type, source_id);
COMMENT ON INDEX idx_test_ai_generation_context_source IS '按来源类型和来源 ID 查询上下文引用';

CREATE INDEX IF NOT EXISTS idx_test_ai_generation_context_created_time
ON test_ai_generation_context(created_time DESC);
COMMENT ON INDEX idx_test_ai_generation_context_created_time IS '上下文引用记录按创建时间排序';

CREATE OR REPLACE FUNCTION update_updated_time_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_time = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_test_skill_updated_time ON test_skill;
CREATE TRIGGER trg_test_skill_updated_time
BEFORE UPDATE ON test_skill
FOR EACH ROW
EXECUTE FUNCTION update_updated_time_column();
COMMENT ON TRIGGER trg_test_skill_updated_time ON test_skill IS '自动维护 test_skill.updated_time';

DROP TRIGGER IF EXISTS trg_test_business_rule_updated_time ON test_business_rule;
CREATE TRIGGER trg_test_business_rule_updated_time
BEFORE UPDATE ON test_business_rule
FOR EACH ROW
EXECUTE FUNCTION update_updated_time_column();
COMMENT ON TRIGGER trg_test_business_rule_updated_time ON test_business_rule IS '自动维护 test_business_rule.updated_time';

INSERT INTO sys_permission (code, name, module, action, description, status, is_delete)
VALUES
    ('skill:create', '创建测试Skill', 'skill', 'create', '创建测试 Skills', 1, 0),
    ('skill:update', '更新测试Skill', 'skill', 'update', '更新测试 Skills', 1, 0),
    ('skill:delete', '删除测试Skill', 'skill', 'delete', '软删除测试 Skills', 1, 0),
    ('skill:list', '查询测试Skill列表', 'skill', 'list', '查询测试 Skills 列表', 1, 0),
    ('skill:detail', '查询测试Skill详情', 'skill', 'detail', '查询测试 Skills 详情', 1, 0),
    ('business-rule:create', '创建业务规则', 'business-rule', 'create', '创建业务规则', 1, 0),
    ('business-rule:update', '更新业务规则', 'business-rule', 'update', '更新业务规则', 1, 0),
    ('business-rule:delete', '删除业务规则', 'business-rule', 'delete', '软删除业务规则', 1, 0),
    ('business-rule:list', '查询业务规则列表', 'business-rule', 'list', '查询业务规则列表', 1, 0),
    ('business-rule:detail', '查询业务规则详情', 'business-rule', 'detail', '查询业务规则详情', 1, 0)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    module = EXCLUDED.module,
    action = EXCLUDED.action,
    description = EXCLUDED.description,
    status = 1,
    is_delete = 0,
    updated_time = CURRENT_TIMESTAMP;

-- Skills / Business Rules 菜单初始化
-- 默认挂载到“测试平台(test_platform)”目录下；如果不存在则创建测试平台目录。
INSERT INTO sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete)
VALUES (0, '测试平台', 'test_platform', 1, '/test-platform', 'Layout', 'test', NULL, 2, 1, 1, 0)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    type = EXCLUDED.type,
    path = EXCLUDED.path,
    component = EXCLUDED.component,
    icon = EXCLUDED.icon,
    sort = EXCLUDED.sort,
    visible = 1,
    status = 1,
    is_delete = 0,
    updated_time = CURRENT_TIMESTAMP;

WITH parent_menu AS (
    SELECT id FROM sys_menu WHERE code = 'test_platform' LIMIT 1
)
INSERT INTO sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete)
SELECT id, '测试 Skills', 'skill_manage', 2, '/test-platform/skills', 'test-platform/skills/index', 'skill', 'skill:list', 20, 1, 1, 0 FROM parent_menu
ON CONFLICT (code) DO UPDATE SET
    parent_id = EXCLUDED.parent_id,
    name = EXCLUDED.name,
    type = EXCLUDED.type,
    path = EXCLUDED.path,
    component = EXCLUDED.component,
    icon = EXCLUDED.icon,
    permission_code = EXCLUDED.permission_code,
    sort = EXCLUDED.sort,
    visible = 1,
    status = 1,
    is_delete = 0,
    updated_time = CURRENT_TIMESTAMP;

WITH parent_menu AS (
    SELECT id FROM sys_menu WHERE code = 'test_platform' LIMIT 1
)
INSERT INTO sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete)
SELECT id, '业务规则', 'business_rule_manage', 2, '/test-platform/business-rules', 'test-platform/business-rules/index', 'rule', 'business-rule:list', 21, 1, 1, 0 FROM parent_menu
ON CONFLICT (code) DO UPDATE SET
    parent_id = EXCLUDED.parent_id,
    name = EXCLUDED.name,
    type = EXCLUDED.type,
    path = EXCLUDED.path,
    component = EXCLUDED.component,
    icon = EXCLUDED.icon,
    permission_code = EXCLUDED.permission_code,
    sort = EXCLUDED.sort,
    visible = 1,
    status = 1,
    is_delete = 0,
    updated_time = CURRENT_TIMESTAMP;

WITH parent_menu AS (
    SELECT id FROM sys_menu WHERE code = 'skill_manage' LIMIT 1
)
INSERT INTO sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete)
SELECT id, '新增', 'skill:create', 3, '', '', NULL, 'skill:create', 1, 1, 1, 0 FROM parent_menu
UNION ALL SELECT id, '编辑', 'skill:update', 3, '', '', NULL, 'skill:update', 2, 1, 1, 0 FROM parent_menu
UNION ALL SELECT id, '删除', 'skill:delete', 3, '', '', NULL, 'skill:delete', 3, 1, 1, 0 FROM parent_menu
UNION ALL SELECT id, '列表查询', 'skill:list', 3, '', '', NULL, 'skill:list', 4, 1, 1, 0 FROM parent_menu
UNION ALL SELECT id, '详情', 'skill:detail', 3, '', '', NULL, 'skill:detail', 5, 1, 1, 0 FROM parent_menu
ON CONFLICT (code) DO UPDATE SET
    parent_id = EXCLUDED.parent_id,
    name = EXCLUDED.name,
    type = EXCLUDED.type,
    path = EXCLUDED.path,
    component = EXCLUDED.component,
    permission_code = EXCLUDED.permission_code,
    sort = EXCLUDED.sort,
    visible = 1,
    status = 1,
    is_delete = 0,
    updated_time = CURRENT_TIMESTAMP;

WITH parent_menu AS (
    SELECT id FROM sys_menu WHERE code = 'business_rule_manage' LIMIT 1
)
INSERT INTO sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete)
SELECT id, '新增', 'business-rule:create', 3, '', '', NULL, 'business-rule:create', 1, 1, 1, 0 FROM parent_menu
UNION ALL SELECT id, '编辑', 'business-rule:update', 3, '', '', NULL, 'business-rule:update', 2, 1, 1, 0 FROM parent_menu
UNION ALL SELECT id, '删除', 'business-rule:delete', 3, '', '', NULL, 'business-rule:delete', 3, 1, 1, 0 FROM parent_menu
UNION ALL SELECT id, '列表查询', 'business-rule:list', 3, '', '', NULL, 'business-rule:list', 4, 1, 1, 0 FROM parent_menu
UNION ALL SELECT id, '详情', 'business-rule:detail', 3, '', '', NULL, 'business-rule:detail', 5, 1, 1, 0 FROM parent_menu
ON CONFLICT (code) DO UPDATE SET
    parent_id = EXCLUDED.parent_id,
    name = EXCLUDED.name,
    type = EXCLUDED.type,
    path = EXCLUDED.path,
    component = EXCLUDED.component,
    permission_code = EXCLUDED.permission_code,
    sort = EXCLUDED.sort,
    visible = 1,
    status = 1,
    is_delete = 0,
    updated_time = CURRENT_TIMESTAMP;
