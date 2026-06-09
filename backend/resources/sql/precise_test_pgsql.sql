-- AI 精准测试 + JaCoCo 增量覆盖率

CREATE TABLE IF NOT EXISTS precise_analysis (
    id BIGSERIAL PRIMARY KEY,
    analysis_no VARCHAR(64) NOT NULL,
    product_id BIGINT,
    project_id BIGINT,
    repository_url VARCHAR(512),
    branch_name VARCHAR(128),
    base_commit VARCHAR(128),
    target_commit VARCHAR(128),
    title VARCHAR(255),
    description TEXT,
    diff_summary_json JSONB DEFAULT '{}'::jsonb,
    ai_impact_json JSONB DEFAULT '{}'::jsonb,
    status SMALLINT DEFAULT 1,
    risk_level VARCHAR(32),
    created_by BIGINT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete SMALLINT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_precise_analysis_project ON precise_analysis(project_id, is_delete);
CREATE INDEX IF NOT EXISTS idx_precise_analysis_no ON precise_analysis(analysis_no);
CREATE INDEX IF NOT EXISTS idx_precise_analysis_created ON precise_analysis(created_time);
COMMENT ON TABLE precise_analysis IS '精准测试变更分析主表';
COMMENT ON COLUMN precise_analysis.id IS '主键ID';
COMMENT ON COLUMN precise_analysis.analysis_no IS '分析编号';
COMMENT ON COLUMN precise_analysis.product_id IS '产品ID';
COMMENT ON COLUMN precise_analysis.project_id IS '项目ID';
COMMENT ON COLUMN precise_analysis.repository_url IS 'Git仓库地址';
COMMENT ON COLUMN precise_analysis.branch_name IS '分支名称';
COMMENT ON COLUMN precise_analysis.base_commit IS '对比基线Commit';
COMMENT ON COLUMN precise_analysis.target_commit IS '目标Commit';
COMMENT ON COLUMN precise_analysis.title IS '分析标题';
COMMENT ON COLUMN precise_analysis.description IS '分析说明';
COMMENT ON COLUMN precise_analysis.diff_summary_json IS 'Git Diff解析摘要JSON';
COMMENT ON COLUMN precise_analysis.ai_impact_json IS 'AI影响分析结果JSON';
COMMENT ON COLUMN precise_analysis.status IS '状态：1待解析 2已解析Diff 3AI已分析 4已推荐 5执行中 6已完成 7失败';
COMMENT ON COLUMN precise_analysis.risk_level IS '风险等级：low/medium/high/warning';
COMMENT ON COLUMN precise_analysis.created_by IS '创建人用户ID';
COMMENT ON COLUMN precise_analysis.created_time IS '创建时间';
COMMENT ON COLUMN precise_analysis.updated_time IS '更新时间';
COMMENT ON COLUMN precise_analysis.is_delete IS '软删除标记：0未删除 1已删除';

CREATE TABLE IF NOT EXISTS precise_changed_file (
    id BIGSERIAL PRIMARY KEY,
    analysis_id BIGINT NOT NULL,
    file_path VARCHAR(1024),
    change_type VARCHAR(32),
    changed_lines JSONB DEFAULT '[]'::jsonb,
    added_lines JSONB DEFAULT '[]'::jsonb,
    deleted_lines JSONB DEFAULT '[]'::jsonb,
    code_snippets JSONB DEFAULT '[]'::jsonb,
    ai_summary TEXT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete SMALLINT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_precise_changed_file_analysis ON precise_changed_file(analysis_id, is_delete);
CREATE INDEX IF NOT EXISTS idx_precise_changed_file_path ON precise_changed_file(file_path);
COMMENT ON TABLE precise_changed_file IS '精准测试变更文件明细表';
COMMENT ON COLUMN precise_changed_file.id IS '主键ID';
COMMENT ON COLUMN precise_changed_file.analysis_id IS '变更分析ID';
COMMENT ON COLUMN precise_changed_file.file_path IS '变更文件路径';
COMMENT ON COLUMN precise_changed_file.change_type IS '变更类型：added/modified/deleted/renamed';
COMMENT ON COLUMN precise_changed_file.changed_lines IS '变更行号列表JSON';
COMMENT ON COLUMN precise_changed_file.added_lines IS '新增行号列表JSON';
COMMENT ON COLUMN precise_changed_file.deleted_lines IS '删除行号列表JSON';
COMMENT ON COLUMN precise_changed_file.code_snippets IS '变更代码片段JSON';
COMMENT ON COLUMN precise_changed_file.ai_summary IS 'AI文件变更摘要';
COMMENT ON COLUMN precise_changed_file.created_time IS '创建时间';
COMMENT ON COLUMN precise_changed_file.updated_time IS '更新时间';
COMMENT ON COLUMN precise_changed_file.is_delete IS '软删除标记：0未删除 1已删除';

CREATE TABLE IF NOT EXISTS precise_relation_map (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT,
    project_id BIGINT,
    relation_type VARCHAR(64),
    source_type VARCHAR(64),
    source_key VARCHAR(1024),
    target_type VARCHAR(64),
    target_key VARCHAR(1024),
    weight NUMERIC(10,4) DEFAULT 1,
    confidence NUMERIC(10,4) DEFAULT 1,
    source_origin VARCHAR(64) DEFAULT 'manual',
    status SMALLINT DEFAULT 1,
    created_by BIGINT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete SMALLINT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_precise_relation_project ON precise_relation_map(project_id, relation_type, is_delete);
CREATE INDEX IF NOT EXISTS idx_precise_relation_source ON precise_relation_map(source_type, source_key);
CREATE INDEX IF NOT EXISTS idx_precise_relation_target ON precise_relation_map(target_type, target_key);
COMMENT ON TABLE precise_relation_map IS '精准测试关系图谱表';
COMMENT ON COLUMN precise_relation_map.id IS '主键ID';
COMMENT ON COLUMN precise_relation_map.product_id IS '产品ID';
COMMENT ON COLUMN precise_relation_map.project_id IS '项目ID';
COMMENT ON COLUMN precise_relation_map.relation_type IS '关系类型：file_api/api_module/module_case/case_script等';
COMMENT ON COLUMN precise_relation_map.source_type IS '源节点类型';
COMMENT ON COLUMN precise_relation_map.source_key IS '源节点唯一键';
COMMENT ON COLUMN precise_relation_map.target_type IS '目标节点类型';
COMMENT ON COLUMN precise_relation_map.target_key IS '目标节点唯一键';
COMMENT ON COLUMN precise_relation_map.weight IS '关系权重';
COMMENT ON COLUMN precise_relation_map.confidence IS '关系置信度';
COMMENT ON COLUMN precise_relation_map.source_origin IS '关系来源：manual/ai_suggested/imported/execution_collected';
COMMENT ON COLUMN precise_relation_map.status IS '状态：0禁用 1启用';
COMMENT ON COLUMN precise_relation_map.created_by IS '创建人用户ID';
COMMENT ON COLUMN precise_relation_map.created_time IS '创建时间';
COMMENT ON COLUMN precise_relation_map.updated_time IS '更新时间';
COMMENT ON COLUMN precise_relation_map.is_delete IS '软删除标记：0未删除 1已删除';

CREATE TABLE IF NOT EXISTS precise_recommendation (
    id BIGSERIAL PRIMARY KEY,
    analysis_id BIGINT NOT NULL,
    case_id BIGINT,
    script_id BIGINT,
    module_name VARCHAR(255),
    api_path VARCHAR(512),
    recommend_level VARCHAR(16),
    execute_type VARCHAR(32),
    risk_level VARCHAR(32),
    reason TEXT,
    ai_reason TEXT,
    confidence NUMERIC(10,4),
    accepted SMALLINT DEFAULT 1,
    execution_status SMALLINT DEFAULT 0,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete SMALLINT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_precise_recommendation_analysis ON precise_recommendation(analysis_id, is_delete);
COMMENT ON TABLE precise_recommendation IS '精准测试回归推荐结果表';
COMMENT ON COLUMN precise_recommendation.id IS '主键ID';
COMMENT ON COLUMN precise_recommendation.analysis_id IS '变更分析ID';
COMMENT ON COLUMN precise_recommendation.case_id IS '测试用例ID';
COMMENT ON COLUMN precise_recommendation.script_id IS '自动化脚本ID';
COMMENT ON COLUMN precise_recommendation.module_name IS '模块名称';
COMMENT ON COLUMN precise_recommendation.api_path IS '接口路径';
COMMENT ON COLUMN precise_recommendation.recommend_level IS '推荐等级：P0/P1/P2/P3';
COMMENT ON COLUMN precise_recommendation.execute_type IS '执行类型：auto/manual/api/performance';
COMMENT ON COLUMN precise_recommendation.risk_level IS '风险等级';
COMMENT ON COLUMN precise_recommendation.reason IS '规则推荐原因';
COMMENT ON COLUMN precise_recommendation.ai_reason IS 'AI推荐原因';
COMMENT ON COLUMN precise_recommendation.confidence IS '推荐置信度';
COMMENT ON COLUMN precise_recommendation.accepted IS '是否采纳：0否 1是';
COMMENT ON COLUMN precise_recommendation.execution_status IS '执行状态：0未执行 1执行中 2成功 3失败 4跳过';
COMMENT ON COLUMN precise_recommendation.created_time IS '创建时间';
COMMENT ON COLUMN precise_recommendation.updated_time IS '更新时间';
COMMENT ON COLUMN precise_recommendation.is_delete IS '软删除标记：0未删除 1已删除';

CREATE TABLE IF NOT EXISTS precise_execution (
    id BIGSERIAL PRIMARY KEY,
    analysis_id BIGINT NOT NULL,
    execution_no VARCHAR(64),
    jenkins_job_name VARCHAR(255),
    jenkins_queue_id VARCHAR(128),
    jenkins_build_number VARCHAR(128),
    jenkins_build_url VARCHAR(1024),
    console_url VARCHAR(1024),
    callback_token VARCHAR(128),
    status SMALLINT DEFAULT 1,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    error_message TEXT,
    created_by BIGINT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete SMALLINT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_precise_execution_analysis ON precise_execution(analysis_id, is_delete);
COMMENT ON TABLE precise_execution IS '精准测试Jenkins执行记录表';
COMMENT ON COLUMN precise_execution.id IS '主键ID';
COMMENT ON COLUMN precise_execution.analysis_id IS '变更分析ID';
COMMENT ON COLUMN precise_execution.execution_no IS '执行编号';
COMMENT ON COLUMN precise_execution.jenkins_job_name IS 'Jenkins任务名称';
COMMENT ON COLUMN precise_execution.jenkins_queue_id IS 'Jenkins队列ID';
COMMENT ON COLUMN precise_execution.jenkins_build_number IS 'Jenkins构建号';
COMMENT ON COLUMN precise_execution.jenkins_build_url IS 'Jenkins构建地址';
COMMENT ON COLUMN precise_execution.console_url IS 'Jenkins控制台地址';
COMMENT ON COLUMN precise_execution.callback_token IS '回调校验Token';
COMMENT ON COLUMN precise_execution.status IS '状态：1待触发 2排队中 3执行中 4成功 5失败 6取消';
COMMENT ON COLUMN precise_execution.start_time IS '开始时间';
COMMENT ON COLUMN precise_execution.end_time IS '结束时间';
COMMENT ON COLUMN precise_execution.error_message IS '错误信息';
COMMENT ON COLUMN precise_execution.created_by IS '创建人用户ID';
COMMENT ON COLUMN precise_execution.created_time IS '创建时间';
COMMENT ON COLUMN precise_execution.updated_time IS '更新时间';
COMMENT ON COLUMN precise_execution.is_delete IS '软删除标记：0未删除 1已删除';

CREATE TABLE IF NOT EXISTS precise_coverage_report (
    id BIGSERIAL PRIMARY KEY,
    analysis_id BIGINT NOT NULL,
    execution_id BIGINT,
    report_no VARCHAR(64),
    coverage_type VARCHAR(32),
    tool_type VARCHAR(32),
    artifact_url VARCHAR(1024),
    local_path VARCHAR(1024),
    summary_json JSONB DEFAULT '{}'::jsonb,
    status SMALLINT DEFAULT 1,
    created_by BIGINT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete SMALLINT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_precise_coverage_analysis ON precise_coverage_report(analysis_id, is_delete);
COMMENT ON TABLE precise_coverage_report IS '精准测试覆盖率报告表';
COMMENT ON COLUMN precise_coverage_report.id IS '主键ID';
COMMENT ON COLUMN precise_coverage_report.analysis_id IS '变更分析ID';
COMMENT ON COLUMN precise_coverage_report.execution_id IS '执行记录ID';
COMMENT ON COLUMN precise_coverage_report.report_no IS '覆盖率报告编号';
COMMENT ON COLUMN precise_coverage_report.coverage_type IS '覆盖率类型：incremental/full';
COMMENT ON COLUMN precise_coverage_report.tool_type IS '覆盖率工具类型：jacoco';
COMMENT ON COLUMN precise_coverage_report.artifact_url IS 'Jenkins归档产物地址';
COMMENT ON COLUMN precise_coverage_report.local_path IS '本地覆盖率文件路径';
COMMENT ON COLUMN precise_coverage_report.summary_json IS '覆盖率摘要JSON';
COMMENT ON COLUMN precise_coverage_report.status IS '状态：1解析成功 2解析失败';
COMMENT ON COLUMN precise_coverage_report.created_by IS '创建人用户ID';
COMMENT ON COLUMN precise_coverage_report.created_time IS '创建时间';
COMMENT ON COLUMN precise_coverage_report.updated_time IS '更新时间';
COMMENT ON COLUMN precise_coverage_report.is_delete IS '软删除标记：0未删除 1已删除';

CREATE TABLE IF NOT EXISTS precise_incremental_coverage (
    id BIGSERIAL PRIMARY KEY,
    analysis_id BIGINT NOT NULL,
    coverage_report_id BIGINT NOT NULL,
    file_path VARCHAR(1024),
    changed_line_count INT DEFAULT 0,
    covered_changed_line_count INT DEFAULT 0,
    uncovered_changed_line_count INT DEFAULT 0,
    incremental_line_rate NUMERIC(10,4),
    uncovered_lines JSONB DEFAULT '[]'::jsonb,
    detail_json JSONB DEFAULT '{}'::jsonb,
    ai_risk_json JSONB DEFAULT '{}'::jsonb,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete SMALLINT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_precise_incremental_analysis ON precise_incremental_coverage(analysis_id, is_delete);
CREATE INDEX IF NOT EXISTS idx_precise_incremental_report ON precise_incremental_coverage(coverage_report_id, is_delete);
COMMENT ON TABLE precise_incremental_coverage IS '精准测试增量覆盖率结果表';
COMMENT ON COLUMN precise_incremental_coverage.id IS '主键ID';
COMMENT ON COLUMN precise_incremental_coverage.analysis_id IS '变更分析ID';
COMMENT ON COLUMN precise_incremental_coverage.coverage_report_id IS '覆盖率报告ID';
COMMENT ON COLUMN precise_incremental_coverage.file_path IS '文件路径';
COMMENT ON COLUMN precise_incremental_coverage.changed_line_count IS '变更有效行数';
COMMENT ON COLUMN precise_incremental_coverage.covered_changed_line_count IS '已覆盖变更行数';
COMMENT ON COLUMN precise_incremental_coverage.uncovered_changed_line_count IS '未覆盖变更行数';
COMMENT ON COLUMN precise_incremental_coverage.incremental_line_rate IS '增量行覆盖率';
COMMENT ON COLUMN precise_incremental_coverage.uncovered_lines IS '未覆盖变更行列表JSON';
COMMENT ON COLUMN precise_incremental_coverage.detail_json IS '文件级覆盖率详情JSON';
COMMENT ON COLUMN precise_incremental_coverage.ai_risk_json IS 'AI未覆盖风险分析JSON';
COMMENT ON COLUMN precise_incremental_coverage.created_time IS '创建时间';
COMMENT ON COLUMN precise_incremental_coverage.updated_time IS '更新时间';
COMMENT ON COLUMN precise_incremental_coverage.is_delete IS '软删除标记：0未删除 1已删除';

CREATE TABLE IF NOT EXISTS precise_quality_gate (
    id BIGSERIAL PRIMARY KEY,
    analysis_id BIGINT NOT NULL,
    gate_status VARCHAR(32),
    line_rate_threshold NUMERIC(10,4) DEFAULT 80,
    actual_line_rate NUMERIC(10,4),
    p0_case_pass_rate NUMERIC(10,4),
    p1_case_pass_rate NUMERIC(10,4),
    risk_level VARCHAR(32),
    block_reasons JSONB DEFAULT '[]'::jsonb,
    suggestions JSONB DEFAULT '[]'::jsonb,
    ai_conclusion TEXT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete SMALLINT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_precise_quality_gate_analysis ON precise_quality_gate(analysis_id, is_delete);
COMMENT ON TABLE precise_quality_gate IS '精准测试质量门禁结果表';
COMMENT ON COLUMN precise_quality_gate.id IS '主键ID';
COMMENT ON COLUMN precise_quality_gate.analysis_id IS '变更分析ID';
COMMENT ON COLUMN precise_quality_gate.gate_status IS '门禁状态：passed/warning/blocked';
COMMENT ON COLUMN precise_quality_gate.line_rate_threshold IS '增量覆盖率阈值';
COMMENT ON COLUMN precise_quality_gate.actual_line_rate IS '实际增量覆盖率';
COMMENT ON COLUMN precise_quality_gate.p0_case_pass_rate IS 'P0推荐用例通过率';
COMMENT ON COLUMN precise_quality_gate.p1_case_pass_rate IS 'P1推荐用例通过率';
COMMENT ON COLUMN precise_quality_gate.risk_level IS '综合风险等级';
COMMENT ON COLUMN precise_quality_gate.block_reasons IS '阻断原因JSON';
COMMENT ON COLUMN precise_quality_gate.suggestions IS '处理建议JSON';
COMMENT ON COLUMN precise_quality_gate.ai_conclusion IS 'AI结论';
COMMENT ON COLUMN precise_quality_gate.created_time IS '创建时间';
COMMENT ON COLUMN precise_quality_gate.updated_time IS '更新时间';
COMMENT ON COLUMN precise_quality_gate.is_delete IS '软删除标记：0未删除 1已删除';
