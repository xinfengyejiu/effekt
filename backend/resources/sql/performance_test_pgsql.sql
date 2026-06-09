-- 性能测试模块建表脚本（PostgreSQL）

BEGIN;

CREATE OR REPLACE FUNCTION public.set_updated_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_time = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS public.performance_scenario (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    code VARCHAR(64) NOT NULL,
    description TEXT NULL,
    project_id BIGINT NULL,
    product_id BIGINT NULL,
    env_code VARCHAR(32) NULL,
    status SMALLINT NOT NULL DEFAULT 1,
    owner_id BIGINT NULL,
    created_by BIGINT NULL,
    is_delete INTEGER NOT NULL DEFAULT 0,
    ext JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_performance_scenario_code UNIQUE (code)
);

COMMENT ON TABLE public.performance_scenario IS '性能测试场景表';
COMMENT ON COLUMN public.performance_scenario.name IS '场景名称';
COMMENT ON COLUMN public.performance_scenario.code IS '场景编码';
COMMENT ON COLUMN public.performance_scenario.description IS '场景描述';
COMMENT ON COLUMN public.performance_scenario.project_id IS '项目ID';
COMMENT ON COLUMN public.performance_scenario.product_id IS '产品ID';
COMMENT ON COLUMN public.performance_scenario.env_code IS '默认环境编码';
COMMENT ON COLUMN public.performance_scenario.status IS '状态：0-禁用，1-启用，2-草稿，3-归档';
COMMENT ON COLUMN public.performance_scenario.owner_id IS '负责人用户ID';
COMMENT ON COLUMN public.performance_scenario.created_by IS '创建人用户ID';
COMMENT ON COLUMN public.performance_scenario.is_delete IS '0-未删除，1-已删除';
COMMENT ON COLUMN public.performance_scenario.ext IS '扩展字段';

CREATE TABLE IF NOT EXISTS public.performance_script (
    id BIGSERIAL PRIMARY KEY,
    scenario_id BIGINT NOT NULL,
    name VARCHAR(128) NOT NULL,
    tool_type VARCHAR(32) NOT NULL,
    description TEXT NULL,
    current_version_id BIGINT NULL,
    status SMALLINT NOT NULL DEFAULT 1,
    created_by BIGINT NULL,
    is_delete INTEGER NOT NULL DEFAULT 0,
    ext JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.performance_script IS '性能测试脚本资产表';
COMMENT ON COLUMN public.performance_script.scenario_id IS '性能场景ID';
COMMENT ON COLUMN public.performance_script.name IS '脚本名称';
COMMENT ON COLUMN public.performance_script.tool_type IS '工具类型：jmeter/k6/locust';
COMMENT ON COLUMN public.performance_script.current_version_id IS '当前脚本版本ID';
COMMENT ON COLUMN public.performance_script.status IS '状态：0-禁用，1-启用，2-草稿';

CREATE TABLE IF NOT EXISTS public.performance_script_version (
    id BIGSERIAL PRIMARY KEY,
    script_id BIGINT NOT NULL,
    version VARCHAR(64) NOT NULL,
    package_path VARCHAR(512) NOT NULL,
    main_file VARCHAR(255) NULL,
    manifest_path VARCHAR(512) NULL,
    checksum VARCHAR(128) NULL,
    file_size BIGINT NULL,
    generator_type VARCHAR(32) NOT NULL DEFAULT 'upload',
    ai_prompt TEXT NULL,
    structure_plan_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by BIGINT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_performance_script_version UNIQUE (script_id, version)
);

COMMENT ON TABLE public.performance_script_version IS '性能测试脚本版本表';
COMMENT ON COLUMN public.performance_script_version.generator_type IS '生成来源：upload/ai_generated/manual';
COMMENT ON COLUMN public.performance_script_version.structure_plan_json IS 'AI结构化压测方案或脚本清单';

CREATE TABLE IF NOT EXISTS public.performance_execution_config (
    id BIGSERIAL PRIMARY KEY,
    scenario_id BIGINT NOT NULL,
    script_id BIGINT NULL,
    script_version_id BIGINT NULL,
    name VARCHAR(128) NOT NULL,
    env_code VARCHAR(32) NULL,
    base_url VARCHAR(512) NULL,
    concurrent_users INTEGER NULL,
    duration_seconds INTEGER NULL,
    ramp_up_seconds INTEGER NULL,
    test_machine_id BIGINT NULL,
    headers_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    variables_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    parameter_files_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    tool_options_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by BIGINT NULL,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.performance_execution_config IS '性能测试执行配置表';
COMMENT ON COLUMN public.performance_execution_config.headers_json IS '请求头配置JSON';
COMMENT ON COLUMN public.performance_execution_config.variables_json IS '变量配置JSON';
COMMENT ON COLUMN public.performance_execution_config.parameter_files_json IS '参数文件配置JSON数组';
COMMENT ON COLUMN public.performance_execution_config.tool_options_json IS 'JMeter/k6/Locust 工具扩展参数JSON';

CREATE TABLE IF NOT EXISTS public.performance_execution_run (
    id BIGSERIAL PRIMARY KEY,
    run_no VARCHAR(64) NOT NULL,
    scenario_id BIGINT NOT NULL,
    script_id BIGINT NULL,
    script_version_id BIGINT NULL,
    execution_config_id BIGINT NULL,
    tool_type VARCHAR(32) NOT NULL,
    env_code VARCHAR(32) NULL,
    test_machine_id BIGINT NULL,
    jenkins_job_name VARCHAR(128) NULL,
    jenkins_queue_id BIGINT NULL,
    jenkins_build_number BIGINT NULL,
    jenkins_build_url VARCHAR(512) NULL,
    console_url VARCHAR(512) NULL,
    status SMALLINT NOT NULL DEFAULT 0,
    start_time TIMESTAMP NULL,
    end_time TIMESTAMP NULL,
    duration_seconds INTEGER NULL,
    trigger_type VARCHAR(32) NOT NULL DEFAULT 'manual',
    trigger_by BIGINT NULL,
    callback_token VARCHAR(128) NULL,
    error_message TEXT NULL,
    ext JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_performance_execution_run_no UNIQUE (run_no)
);

COMMENT ON TABLE public.performance_execution_run IS '性能测试执行记录表';
COMMENT ON COLUMN public.performance_execution_run.status IS '状态：0-待触发，1-触发中，2-排队中，3-执行中，4-成功，5-失败，6-已取消，7-超时，8-解析失败';
COMMENT ON COLUMN public.performance_execution_run.trigger_type IS '触发类型：manual/jenkins/api/schedule';

CREATE TABLE IF NOT EXISTS public.performance_metric (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL,
    scenario_id BIGINT NOT NULL,
    metric_name VARCHAR(128) NOT NULL,
    metric_value NUMERIC(20, 6) NULL,
    metric_unit VARCHAR(32) NULL,
    metric_source VARCHAR(64) NULL,
    tags_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    metric_time TIMESTAMP NULL,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.performance_metric IS '性能测试统一指标表';
COMMENT ON COLUMN public.performance_metric.metric_name IS '指标名称，如 p95/tps/errorRate/loadGeneratorCpuUsage';
COMMENT ON COLUMN public.performance_metric.metric_source IS '指标来源：jmeter/k6/locust/jenkins_agent/prometheus/apm/slow_sql/log/trace';
COMMENT ON COLUMN public.performance_metric.tags_json IS '指标标签JSON';
COMMENT ON COLUMN public.performance_metric.metric_time IS '指标采样时间';

CREATE TABLE IF NOT EXISTS public.performance_baseline (
    id BIGSERIAL PRIMARY KEY,
    scenario_id BIGINT NOT NULL,
    script_id BIGINT NULL,
    script_version_id BIGINT NULL,
    run_id BIGINT NOT NULL,
    tool_type VARCHAR(32) NOT NULL,
    env_code VARCHAR(32) NULL,
    config_hash VARCHAR(128) NULL,
    name VARCHAR(128) NOT NULL,
    status SMALLINT NOT NULL DEFAULT 1,
    baseline_metrics_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by BIGINT NULL,
    effective_time TIMESTAMP NULL,
    remark TEXT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.performance_baseline IS '性能测试基线表';
COMMENT ON COLUMN public.performance_baseline.status IS '状态：0-废弃，1-生效，2-草稿，3-历史';
COMMENT ON COLUMN public.performance_baseline.baseline_metrics_json IS '基线指标快照JSON';

CREATE TABLE IF NOT EXISTS public.performance_gate_rule (
    id BIGSERIAL PRIMARY KEY,
    scenario_id BIGINT NULL,
    name VARCHAR(128) NOT NULL,
    metric_name VARCHAR(128) NOT NULL,
    operator VARCHAR(16) NOT NULL,
    threshold_value NUMERIC(20, 6) NULL,
    threshold_unit VARCHAR(32) NULL,
    compare_type VARCHAR(32) NOT NULL DEFAULT 'absolute',
    severity VARCHAR(32) NOT NULL DEFAULT 'failed',
    enabled SMALLINT NOT NULL DEFAULT 1,
    created_by BIGINT NULL,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.performance_gate_rule IS '性能测试门禁规则表';
COMMENT ON COLUMN public.performance_gate_rule.compare_type IS '比较类型：absolute/baseline_ratio/baseline_delta';
COMMENT ON COLUMN public.performance_gate_rule.severity IS '严重级别：warning/failed';
COMMENT ON COLUMN public.performance_gate_rule.enabled IS '是否启用：1-启用，0-禁用';

CREATE TABLE IF NOT EXISTS public.performance_gate_result (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL,
    rule_id BIGINT NULL,
    metric_name VARCHAR(128) NOT NULL,
    actual_value NUMERIC(20, 6) NULL,
    threshold_value NUMERIC(20, 6) NULL,
    baseline_value NUMERIC(20, 6) NULL,
    compare_result VARCHAR(64) NULL,
    status VARCHAR(32) NOT NULL,
    message TEXT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.performance_gate_result IS '性能测试门禁结果表';
COMMENT ON COLUMN public.performance_gate_result.status IS '结果：passed/warning/failed';
COMMENT ON COLUMN public.performance_gate_result.compare_result IS '比较结果表达，如 +37.8%';

CREATE TABLE IF NOT EXISTS public.performance_report (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL,
    scenario_id BIGINT NOT NULL,
    summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    metrics_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    gate_result_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    native_report_url VARCHAR(512) NULL,
    unified_report_path VARCHAR(512) NULL,
    raw_result_url VARCHAR(512) NULL,
    log_url VARCHAR(512) NULL,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_performance_report_run UNIQUE (run_id)
);

COMMENT ON TABLE public.performance_report IS '性能测试报告表';

CREATE TABLE IF NOT EXISTS public.performance_ai_analysis (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL,
    scenario_id BIGINT NOT NULL,
    analysis_status VARCHAR(32) NOT NULL DEFAULT 'pending',
    conclusion TEXT NULL,
    conclusion_type VARCHAR(64) NULL,
    confidence VARCHAR(32) NULL,
    evidence_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    suggestion_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    prompt TEXT NULL,
    model_name VARCHAR(128) NULL,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.performance_ai_analysis IS '性能测试AI分析表';
COMMENT ON COLUMN public.performance_ai_analysis.conclusion_type IS '结论类型：明确异常/可能瓶颈/建议复测/需补充监控';
COMMENT ON COLUMN public.performance_ai_analysis.confidence IS '置信度：high/medium/low';

CREATE TABLE IF NOT EXISTS public.performance_test_machine (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    jenkins_agent_name VARCHAR(128) NULL,
    jenkins_label VARCHAR(128) NOT NULL,
    os_type VARCHAR(64) NULL,
    host VARCHAR(128) NULL,
    ip VARCHAR(64) NULL,
    supported_tools_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    tool_versions_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    work_dir VARCHAR(512) NULL,
    max_concurrent_tasks INTEGER NOT NULL DEFAULT 1,
    current_running_tasks INTEGER NOT NULL DEFAULT 0,
    cpu_cores INTEGER NULL,
    memory_gb NUMERIC(10, 2) NULL,
    status SMALLINT NOT NULL DEFAULT 1,
    tags_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    env_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    remark TEXT NULL,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.performance_test_machine IS '性能测试测试机资源池表';
COMMENT ON COLUMN public.performance_test_machine.status IS '状态：0-离线，1-在线，2-忙碌，3-禁用，4-异常';
COMMENT ON COLUMN public.performance_test_machine.supported_tools_json IS '支持工具数组，如 ["jmeter","k6","locust"]';
COMMENT ON COLUMN public.performance_test_machine.env_json IS '环境变量配置JSON';

CREATE TABLE IF NOT EXISTS public.performance_monitor_source (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    source_type VARCHAR(64) NOT NULL,
    env_code VARCHAR(32) NULL,
    endpoint VARCHAR(512) NULL,
    auth_config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    query_config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    enabled SMALLINT NOT NULL DEFAULT 1,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.performance_monitor_source IS '性能测试监控源配置表';
COMMENT ON COLUMN public.performance_monitor_source.source_type IS '监控源类型：jenkins_agent/prometheus/apm/slow_sql/log/trace';
COMMENT ON COLUMN public.performance_monitor_source.auth_config_json IS '鉴权配置JSON';
COMMENT ON COLUMN public.performance_monitor_source.query_config_json IS '查询配置JSON';

ALTER TABLE public.performance_scenario
    ADD COLUMN IF NOT EXISTS name VARCHAR(128),
    ADD COLUMN IF NOT EXISTS code VARCHAR(64),
    ADD COLUMN IF NOT EXISTS description TEXT,
    ADD COLUMN IF NOT EXISTS project_id BIGINT,
    ADD COLUMN IF NOT EXISTS product_id BIGINT,
    ADD COLUMN IF NOT EXISTS env_code VARCHAR(32),
    ADD COLUMN IF NOT EXISTS status SMALLINT NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS owner_id BIGINT,
    ADD COLUMN IF NOT EXISTS created_by BIGINT,
    ADD COLUMN IF NOT EXISTS is_delete INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS ext JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE public.performance_script
    ADD COLUMN IF NOT EXISTS scenario_id BIGINT,
    ADD COLUMN IF NOT EXISTS name VARCHAR(128),
    ADD COLUMN IF NOT EXISTS tool_type VARCHAR(32),
    ADD COLUMN IF NOT EXISTS description TEXT,
    ADD COLUMN IF NOT EXISTS current_version_id BIGINT,
    ADD COLUMN IF NOT EXISTS status SMALLINT NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS created_by BIGINT,
    ADD COLUMN IF NOT EXISTS is_delete INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS ext JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE public.performance_script_version
    ADD COLUMN IF NOT EXISTS script_id BIGINT,
    ADD COLUMN IF NOT EXISTS version VARCHAR(64),
    ADD COLUMN IF NOT EXISTS package_path VARCHAR(512),
    ADD COLUMN IF NOT EXISTS main_file VARCHAR(255),
    ADD COLUMN IF NOT EXISTS manifest_path VARCHAR(512),
    ADD COLUMN IF NOT EXISTS checksum VARCHAR(128),
    ADD COLUMN IF NOT EXISTS file_size BIGINT,
    ADD COLUMN IF NOT EXISTS generator_type VARCHAR(32) NOT NULL DEFAULT 'upload',
    ADD COLUMN IF NOT EXISTS ai_prompt TEXT,
    ADD COLUMN IF NOT EXISTS structure_plan_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS created_by BIGINT,
    ADD COLUMN IF NOT EXISTS created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE public.performance_execution_config
    ADD COLUMN IF NOT EXISTS scenario_id BIGINT,
    ADD COLUMN IF NOT EXISTS script_id BIGINT,
    ADD COLUMN IF NOT EXISTS script_version_id BIGINT,
    ADD COLUMN IF NOT EXISTS name VARCHAR(128),
    ADD COLUMN IF NOT EXISTS env_code VARCHAR(32),
    ADD COLUMN IF NOT EXISTS base_url VARCHAR(512),
    ADD COLUMN IF NOT EXISTS concurrent_users INTEGER,
    ADD COLUMN IF NOT EXISTS duration_seconds INTEGER,
    ADD COLUMN IF NOT EXISTS ramp_up_seconds INTEGER,
    ADD COLUMN IF NOT EXISTS test_machine_id BIGINT,
    ADD COLUMN IF NOT EXISTS headers_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS variables_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS parameter_files_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS tool_options_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS created_by BIGINT,
    ADD COLUMN IF NOT EXISTS is_delete INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE public.performance_execution_run
    ADD COLUMN IF NOT EXISTS run_no VARCHAR(64),
    ADD COLUMN IF NOT EXISTS scenario_id BIGINT,
    ADD COLUMN IF NOT EXISTS script_id BIGINT,
    ADD COLUMN IF NOT EXISTS script_version_id BIGINT,
    ADD COLUMN IF NOT EXISTS execution_config_id BIGINT,
    ADD COLUMN IF NOT EXISTS tool_type VARCHAR(32),
    ADD COLUMN IF NOT EXISTS env_code VARCHAR(32),
    ADD COLUMN IF NOT EXISTS test_machine_id BIGINT,
    ADD COLUMN IF NOT EXISTS jenkins_job_name VARCHAR(128),
    ADD COLUMN IF NOT EXISTS jenkins_queue_id BIGINT,
    ADD COLUMN IF NOT EXISTS jenkins_build_number BIGINT,
    ADD COLUMN IF NOT EXISTS jenkins_build_url VARCHAR(512),
    ADD COLUMN IF NOT EXISTS console_url VARCHAR(512),
    ADD COLUMN IF NOT EXISTS status SMALLINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS start_time TIMESTAMP,
    ADD COLUMN IF NOT EXISTS end_time TIMESTAMP,
    ADD COLUMN IF NOT EXISTS duration_seconds INTEGER,
    ADD COLUMN IF NOT EXISTS trigger_type VARCHAR(32) NOT NULL DEFAULT 'manual',
    ADD COLUMN IF NOT EXISTS trigger_by BIGINT,
    ADD COLUMN IF NOT EXISTS callback_token VARCHAR(128),
    ADD COLUMN IF NOT EXISTS error_message TEXT,
    ADD COLUMN IF NOT EXISTS ext JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE public.performance_metric
    ADD COLUMN IF NOT EXISTS run_id BIGINT,
    ADD COLUMN IF NOT EXISTS scenario_id BIGINT,
    ADD COLUMN IF NOT EXISTS metric_name VARCHAR(128),
    ADD COLUMN IF NOT EXISTS metric_value NUMERIC(20, 6),
    ADD COLUMN IF NOT EXISTS metric_unit VARCHAR(32),
    ADD COLUMN IF NOT EXISTS metric_source VARCHAR(64),
    ADD COLUMN IF NOT EXISTS tags_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS metric_time TIMESTAMP,
    ADD COLUMN IF NOT EXISTS created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE public.performance_baseline
    ADD COLUMN IF NOT EXISTS scenario_id BIGINT,
    ADD COLUMN IF NOT EXISTS script_id BIGINT,
    ADD COLUMN IF NOT EXISTS script_version_id BIGINT,
    ADD COLUMN IF NOT EXISTS run_id BIGINT,
    ADD COLUMN IF NOT EXISTS tool_type VARCHAR(32),
    ADD COLUMN IF NOT EXISTS env_code VARCHAR(32),
    ADD COLUMN IF NOT EXISTS config_hash VARCHAR(128),
    ADD COLUMN IF NOT EXISTS name VARCHAR(128),
    ADD COLUMN IF NOT EXISTS status SMALLINT NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS baseline_metrics_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS created_by BIGINT,
    ADD COLUMN IF NOT EXISTS effective_time TIMESTAMP,
    ADD COLUMN IF NOT EXISTS remark TEXT,
    ADD COLUMN IF NOT EXISTS created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE public.performance_gate_rule
    ADD COLUMN IF NOT EXISTS scenario_id BIGINT,
    ADD COLUMN IF NOT EXISTS name VARCHAR(128),
    ADD COLUMN IF NOT EXISTS metric_name VARCHAR(128),
    ADD COLUMN IF NOT EXISTS operator VARCHAR(16),
    ADD COLUMN IF NOT EXISTS threshold_value NUMERIC(20, 6),
    ADD COLUMN IF NOT EXISTS threshold_unit VARCHAR(32),
    ADD COLUMN IF NOT EXISTS compare_type VARCHAR(32) NOT NULL DEFAULT 'absolute',
    ADD COLUMN IF NOT EXISTS severity VARCHAR(32) NOT NULL DEFAULT 'failed',
    ADD COLUMN IF NOT EXISTS enabled SMALLINT NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS created_by BIGINT,
    ADD COLUMN IF NOT EXISTS is_delete INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE public.performance_gate_result
    ADD COLUMN IF NOT EXISTS run_id BIGINT,
    ADD COLUMN IF NOT EXISTS rule_id BIGINT,
    ADD COLUMN IF NOT EXISTS metric_name VARCHAR(128),
    ADD COLUMN IF NOT EXISTS actual_value NUMERIC(20, 6),
    ADD COLUMN IF NOT EXISTS threshold_value NUMERIC(20, 6),
    ADD COLUMN IF NOT EXISTS baseline_value NUMERIC(20, 6),
    ADD COLUMN IF NOT EXISTS compare_result VARCHAR(64),
    ADD COLUMN IF NOT EXISTS status VARCHAR(32),
    ADD COLUMN IF NOT EXISTS message TEXT,
    ADD COLUMN IF NOT EXISTS created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE public.performance_report
    ADD COLUMN IF NOT EXISTS run_id BIGINT,
    ADD COLUMN IF NOT EXISTS scenario_id BIGINT,
    ADD COLUMN IF NOT EXISTS summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS metrics_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS gate_result_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS native_report_url VARCHAR(512),
    ADD COLUMN IF NOT EXISTS unified_report_path VARCHAR(512),
    ADD COLUMN IF NOT EXISTS raw_result_url VARCHAR(512),
    ADD COLUMN IF NOT EXISTS log_url VARCHAR(512),
    ADD COLUMN IF NOT EXISTS created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE public.performance_ai_analysis
    ADD COLUMN IF NOT EXISTS run_id BIGINT,
    ADD COLUMN IF NOT EXISTS scenario_id BIGINT,
    ADD COLUMN IF NOT EXISTS analysis_status VARCHAR(32) NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS conclusion TEXT,
    ADD COLUMN IF NOT EXISTS conclusion_type VARCHAR(64),
    ADD COLUMN IF NOT EXISTS confidence VARCHAR(32),
    ADD COLUMN IF NOT EXISTS evidence_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS suggestion_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS prompt TEXT,
    ADD COLUMN IF NOT EXISTS model_name VARCHAR(128),
    ADD COLUMN IF NOT EXISTS created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE public.performance_test_machine
    ADD COLUMN IF NOT EXISTS name VARCHAR(128),
    ADD COLUMN IF NOT EXISTS jenkins_agent_name VARCHAR(128),
    ADD COLUMN IF NOT EXISTS jenkins_label VARCHAR(128),
    ADD COLUMN IF NOT EXISTS os_type VARCHAR(64),
    ADD COLUMN IF NOT EXISTS host VARCHAR(128),
    ADD COLUMN IF NOT EXISTS ip VARCHAR(64),
    ADD COLUMN IF NOT EXISTS supported_tools_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS tool_versions_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS work_dir VARCHAR(512),
    ADD COLUMN IF NOT EXISTS max_concurrent_tasks INTEGER NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS current_running_tasks INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS cpu_cores INTEGER,
    ADD COLUMN IF NOT EXISTS memory_gb NUMERIC(10, 2),
    ADD COLUMN IF NOT EXISTS status SMALLINT NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS tags_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS env_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS remark TEXT,
    ADD COLUMN IF NOT EXISTS is_delete INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE public.performance_monitor_source
    ADD COLUMN IF NOT EXISTS name VARCHAR(128),
    ADD COLUMN IF NOT EXISTS source_type VARCHAR(64),
    ADD COLUMN IF NOT EXISTS env_code VARCHAR(32),
    ADD COLUMN IF NOT EXISTS endpoint VARCHAR(512),
    ADD COLUMN IF NOT EXISTS auth_config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS query_config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS enabled SMALLINT NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS is_delete INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- 字段描述（覆盖新增字段与历史字段，便于维护）
COMMENT ON COLUMN public.performance_scenario.id IS '主键ID';
COMMENT ON COLUMN public.performance_scenario.name IS '场景名称';
COMMENT ON COLUMN public.performance_scenario.code IS '场景编码';
COMMENT ON COLUMN public.performance_scenario.description IS '场景描述';
COMMENT ON COLUMN public.performance_scenario.project_id IS '项目ID';
COMMENT ON COLUMN public.performance_scenario.product_id IS '产品ID';
COMMENT ON COLUMN public.performance_scenario.env_code IS '默认环境编码';
COMMENT ON COLUMN public.performance_scenario.status IS '状态：0-禁用，1-启用，2-草稿，3-归档';
COMMENT ON COLUMN public.performance_scenario.owner_id IS '负责人用户ID';
COMMENT ON COLUMN public.performance_scenario.created_by IS '创建人用户ID';
COMMENT ON COLUMN public.performance_scenario.is_delete IS '软删除标识：0-未删除，1-已删除';
COMMENT ON COLUMN public.performance_scenario.ext IS '扩展字段JSON';
COMMENT ON COLUMN public.performance_scenario.created_time IS '创建时间';
COMMENT ON COLUMN public.performance_scenario.updated_time IS '更新时间';

COMMENT ON COLUMN public.performance_script.id IS '主键ID';
COMMENT ON COLUMN public.performance_script.scenario_id IS '性能场景ID';
COMMENT ON COLUMN public.performance_script.name IS '脚本名称';
COMMENT ON COLUMN public.performance_script.tool_type IS '工具类型：jmeter/k6/locust';
COMMENT ON COLUMN public.performance_script.description IS '脚本描述';
COMMENT ON COLUMN public.performance_script.current_version_id IS '当前脚本版本ID';
COMMENT ON COLUMN public.performance_script.status IS '状态：0-禁用，1-启用，2-草稿';
COMMENT ON COLUMN public.performance_script.created_by IS '创建人用户ID';
COMMENT ON COLUMN public.performance_script.is_delete IS '软删除标识：0-未删除，1-已删除';
COMMENT ON COLUMN public.performance_script.ext IS '扩展字段JSON';
COMMENT ON COLUMN public.performance_script.created_time IS '创建时间';
COMMENT ON COLUMN public.performance_script.updated_time IS '更新时间';

COMMENT ON COLUMN public.performance_script_version.id IS '主键ID';
COMMENT ON COLUMN public.performance_script_version.script_id IS '脚本ID';
COMMENT ON COLUMN public.performance_script_version.version IS '版本号';
COMMENT ON COLUMN public.performance_script_version.package_path IS '脚本包路径';
COMMENT ON COLUMN public.performance_script_version.main_file IS '主文件路径或文件名';
COMMENT ON COLUMN public.performance_script_version.manifest_path IS 'manifest文件路径';
COMMENT ON COLUMN public.performance_script_version.checksum IS '文件校验值';
COMMENT ON COLUMN public.performance_script_version.file_size IS '文件大小（字节）';
COMMENT ON COLUMN public.performance_script_version.generator_type IS '生成来源：upload/ai_generated/manual';
COMMENT ON COLUMN public.performance_script_version.ai_prompt IS 'AI生成提示词';
COMMENT ON COLUMN public.performance_script_version.structure_plan_json IS 'AI结构化压测方案或脚本清单JSON';
COMMENT ON COLUMN public.performance_script_version.created_by IS '创建人用户ID';
COMMENT ON COLUMN public.performance_script_version.created_time IS '创建时间';

COMMENT ON COLUMN public.performance_execution_config.id IS '主键ID';
COMMENT ON COLUMN public.performance_execution_config.scenario_id IS '性能场景ID';
COMMENT ON COLUMN public.performance_execution_config.script_id IS '脚本ID';
COMMENT ON COLUMN public.performance_execution_config.script_version_id IS '脚本版本ID';
COMMENT ON COLUMN public.performance_execution_config.name IS '配置名称';
COMMENT ON COLUMN public.performance_execution_config.env_code IS '环境编码';
COMMENT ON COLUMN public.performance_execution_config.base_url IS '基础URL';
COMMENT ON COLUMN public.performance_execution_config.concurrent_users IS '并发用户数';
COMMENT ON COLUMN public.performance_execution_config.duration_seconds IS '持续时间（秒）';
COMMENT ON COLUMN public.performance_execution_config.ramp_up_seconds IS '加压时间（秒）';
COMMENT ON COLUMN public.performance_execution_config.test_machine_id IS '测试机ID';
COMMENT ON COLUMN public.performance_execution_config.headers_json IS '请求头配置JSON';
COMMENT ON COLUMN public.performance_execution_config.variables_json IS '变量配置JSON';
COMMENT ON COLUMN public.performance_execution_config.parameter_files_json IS '参数文件配置JSON数组';
COMMENT ON COLUMN public.performance_execution_config.tool_options_json IS 'JMeter/k6/Locust工具扩展参数JSON';
COMMENT ON COLUMN public.performance_execution_config.created_by IS '创建人用户ID';
COMMENT ON COLUMN public.performance_execution_config.is_delete IS '软删除标识：0-未删除，1-已删除';
COMMENT ON COLUMN public.performance_execution_config.created_time IS '创建时间';
COMMENT ON COLUMN public.performance_execution_config.updated_time IS '更新时间';

COMMENT ON COLUMN public.performance_execution_run.id IS '主键ID';
COMMENT ON COLUMN public.performance_execution_run.run_no IS '执行编号';
COMMENT ON COLUMN public.performance_execution_run.scenario_id IS '性能场景ID';
COMMENT ON COLUMN public.performance_execution_run.script_id IS '脚本ID';
COMMENT ON COLUMN public.performance_execution_run.script_version_id IS '脚本版本ID';
COMMENT ON COLUMN public.performance_execution_run.execution_config_id IS '执行配置ID';
COMMENT ON COLUMN public.performance_execution_run.tool_type IS '工具类型';
COMMENT ON COLUMN public.performance_execution_run.env_code IS '环境编码';
COMMENT ON COLUMN public.performance_execution_run.test_machine_id IS '测试机ID';
COMMENT ON COLUMN public.performance_execution_run.jenkins_job_name IS 'Jenkins任务名称';
COMMENT ON COLUMN public.performance_execution_run.jenkins_queue_id IS 'Jenkins队列ID';
COMMENT ON COLUMN public.performance_execution_run.jenkins_build_number IS 'Jenkins构建号';
COMMENT ON COLUMN public.performance_execution_run.jenkins_build_url IS 'Jenkins构建地址';
COMMENT ON COLUMN public.performance_execution_run.console_url IS '控制台地址';
COMMENT ON COLUMN public.performance_execution_run.status IS '状态：0-待触发，1-触发中，2-排队中，3-执行中，4-成功，5-失败，6-已取消，7-超时，8-解析失败';
COMMENT ON COLUMN public.performance_execution_run.start_time IS '开始时间';
COMMENT ON COLUMN public.performance_execution_run.end_time IS '结束时间';
COMMENT ON COLUMN public.performance_execution_run.duration_seconds IS '耗时秒数';
COMMENT ON COLUMN public.performance_execution_run.trigger_type IS '触发类型：manual/jenkins/api/schedule';
COMMENT ON COLUMN public.performance_execution_run.trigger_by IS '触发人用户ID';
COMMENT ON COLUMN public.performance_execution_run.callback_token IS '回调Token';
COMMENT ON COLUMN public.performance_execution_run.error_message IS '错误信息';
COMMENT ON COLUMN public.performance_execution_run.ext IS '扩展字段JSON';
COMMENT ON COLUMN public.performance_execution_run.created_time IS '创建时间';
COMMENT ON COLUMN public.performance_execution_run.updated_time IS '更新时间';

COMMENT ON COLUMN public.performance_metric.id IS '主键ID';
COMMENT ON COLUMN public.performance_metric.run_id IS '执行记录ID';
COMMENT ON COLUMN public.performance_metric.scenario_id IS '性能场景ID';
COMMENT ON COLUMN public.performance_metric.metric_name IS '指标名称，如p95/tps/errorRate/loadGeneratorCpuUsage';
COMMENT ON COLUMN public.performance_metric.metric_value IS '指标值';
COMMENT ON COLUMN public.performance_metric.metric_unit IS '指标单位';
COMMENT ON COLUMN public.performance_metric.metric_source IS '指标来源：jmeter/k6/locust/jenkins_agent/prometheus/apm/slow_sql/log/trace';
COMMENT ON COLUMN public.performance_metric.tags_json IS '指标标签JSON';
COMMENT ON COLUMN public.performance_metric.metric_time IS '指标采样时间';
COMMENT ON COLUMN public.performance_metric.created_time IS '创建时间';

COMMENT ON COLUMN public.performance_baseline.id IS '主键ID';
COMMENT ON COLUMN public.performance_baseline.scenario_id IS '性能场景ID';
COMMENT ON COLUMN public.performance_baseline.script_id IS '脚本ID';
COMMENT ON COLUMN public.performance_baseline.script_version_id IS '脚本版本ID';
COMMENT ON COLUMN public.performance_baseline.run_id IS '基线来源执行ID';
COMMENT ON COLUMN public.performance_baseline.tool_type IS '工具类型';
COMMENT ON COLUMN public.performance_baseline.env_code IS '环境编码';
COMMENT ON COLUMN public.performance_baseline.config_hash IS '执行配置Hash';
COMMENT ON COLUMN public.performance_baseline.name IS '基线名称';
COMMENT ON COLUMN public.performance_baseline.status IS '状态：0-废弃，1-生效，2-草稿，3-历史';
COMMENT ON COLUMN public.performance_baseline.baseline_metrics_json IS '基线指标快照JSON';
COMMENT ON COLUMN public.performance_baseline.created_by IS '创建人用户ID';
COMMENT ON COLUMN public.performance_baseline.effective_time IS '生效时间';
COMMENT ON COLUMN public.performance_baseline.remark IS '备注';
COMMENT ON COLUMN public.performance_baseline.created_time IS '创建时间';
COMMENT ON COLUMN public.performance_baseline.updated_time IS '更新时间';

COMMENT ON COLUMN public.performance_gate_rule.id IS '主键ID';
COMMENT ON COLUMN public.performance_gate_rule.scenario_id IS '性能场景ID';
COMMENT ON COLUMN public.performance_gate_rule.name IS '规则名称';
COMMENT ON COLUMN public.performance_gate_rule.metric_name IS '指标名称';
COMMENT ON COLUMN public.performance_gate_rule.operator IS '操作符，如 >、>=、<、<=、=、!=';
COMMENT ON COLUMN public.performance_gate_rule.threshold_value IS '阈值';
COMMENT ON COLUMN public.performance_gate_rule.threshold_unit IS '阈值单位';
COMMENT ON COLUMN public.performance_gate_rule.compare_type IS '比较类型：absolute/baseline_ratio/baseline_delta';
COMMENT ON COLUMN public.performance_gate_rule.severity IS '严重级别：warning/failed';
COMMENT ON COLUMN public.performance_gate_rule.enabled IS '是否启用：1-启用，0-禁用';
COMMENT ON COLUMN public.performance_gate_rule.created_by IS '创建人用户ID';
COMMENT ON COLUMN public.performance_gate_rule.is_delete IS '软删除标识：0-未删除，1-已删除';
COMMENT ON COLUMN public.performance_gate_rule.created_time IS '创建时间';
COMMENT ON COLUMN public.performance_gate_rule.updated_time IS '更新时间';

COMMENT ON COLUMN public.performance_gate_result.id IS '主键ID';
COMMENT ON COLUMN public.performance_gate_result.run_id IS '执行记录ID';
COMMENT ON COLUMN public.performance_gate_result.rule_id IS '规则ID';
COMMENT ON COLUMN public.performance_gate_result.metric_name IS '指标名称';
COMMENT ON COLUMN public.performance_gate_result.actual_value IS '实际值';
COMMENT ON COLUMN public.performance_gate_result.threshold_value IS '阈值';
COMMENT ON COLUMN public.performance_gate_result.baseline_value IS '基线值';
COMMENT ON COLUMN public.performance_gate_result.compare_result IS '比较结果表达，如+37.8%';
COMMENT ON COLUMN public.performance_gate_result.status IS '结果：passed/warning/failed';
COMMENT ON COLUMN public.performance_gate_result.message IS '结果说明';
COMMENT ON COLUMN public.performance_gate_result.created_time IS '创建时间';

COMMENT ON COLUMN public.performance_report.id IS '主键ID';
COMMENT ON COLUMN public.performance_report.run_id IS '执行记录ID';
COMMENT ON COLUMN public.performance_report.scenario_id IS '性能场景ID';
COMMENT ON COLUMN public.performance_report.summary_json IS '报告摘要JSON';
COMMENT ON COLUMN public.performance_report.metrics_json IS '指标JSON';
COMMENT ON COLUMN public.performance_report.gate_result_json IS '门禁结果JSON';
COMMENT ON COLUMN public.performance_report.native_report_url IS '原生报告地址';
COMMENT ON COLUMN public.performance_report.unified_report_path IS '统一报告路径';
COMMENT ON COLUMN public.performance_report.raw_result_url IS '原始结果地址';
COMMENT ON COLUMN public.performance_report.log_url IS '日志地址';
COMMENT ON COLUMN public.performance_report.created_time IS '创建时间';
COMMENT ON COLUMN public.performance_report.updated_time IS '更新时间';

COMMENT ON COLUMN public.performance_ai_analysis.id IS '主键ID';
COMMENT ON COLUMN public.performance_ai_analysis.run_id IS '执行记录ID';
COMMENT ON COLUMN public.performance_ai_analysis.scenario_id IS '性能场景ID';
COMMENT ON COLUMN public.performance_ai_analysis.analysis_status IS '分析状态：pending/running/success/failed';
COMMENT ON COLUMN public.performance_ai_analysis.conclusion IS '分析结论';
COMMENT ON COLUMN public.performance_ai_analysis.conclusion_type IS '结论类型：明确异常/可能瓶颈/建议复测/需补充监控';
COMMENT ON COLUMN public.performance_ai_analysis.confidence IS '置信度：high/medium/low';
COMMENT ON COLUMN public.performance_ai_analysis.evidence_json IS '证据JSON数组';
COMMENT ON COLUMN public.performance_ai_analysis.suggestion_json IS '建议JSON数组';
COMMENT ON COLUMN public.performance_ai_analysis.prompt IS '提示词';
COMMENT ON COLUMN public.performance_ai_analysis.model_name IS '模型名称';
COMMENT ON COLUMN public.performance_ai_analysis.created_time IS '创建时间';
COMMENT ON COLUMN public.performance_ai_analysis.updated_time IS '更新时间';

COMMENT ON COLUMN public.performance_test_machine.id IS '主键ID';
COMMENT ON COLUMN public.performance_test_machine.name IS '测试机名称';
COMMENT ON COLUMN public.performance_test_machine.jenkins_agent_name IS 'Jenkins Agent名称';
COMMENT ON COLUMN public.performance_test_machine.jenkins_label IS 'Jenkins Label';
COMMENT ON COLUMN public.performance_test_machine.os_type IS '操作系统类型';
COMMENT ON COLUMN public.performance_test_machine.host IS '主机名';
COMMENT ON COLUMN public.performance_test_machine.ip IS 'IP地址';
COMMENT ON COLUMN public.performance_test_machine.supported_tools_json IS '支持工具数组，如["jmeter","k6","locust"]';
COMMENT ON COLUMN public.performance_test_machine.tool_versions_json IS '工具版本JSON';
COMMENT ON COLUMN public.performance_test_machine.work_dir IS '工作目录';
COMMENT ON COLUMN public.performance_test_machine.max_concurrent_tasks IS '最大并发任务数';
COMMENT ON COLUMN public.performance_test_machine.current_running_tasks IS '当前运行任务数';
COMMENT ON COLUMN public.performance_test_machine.cpu_cores IS 'CPU核心数';
COMMENT ON COLUMN public.performance_test_machine.memory_gb IS '内存大小（GB）';
COMMENT ON COLUMN public.performance_test_machine.status IS '状态：0-离线，1-在线，2-忙碌，3-禁用，4-异常';
COMMENT ON COLUMN public.performance_test_machine.tags_json IS '标签JSON数组';
COMMENT ON COLUMN public.performance_test_machine.env_json IS '环境变量配置JSON';
COMMENT ON COLUMN public.performance_test_machine.remark IS '备注';
COMMENT ON COLUMN public.performance_test_machine.is_delete IS '软删除标识：0-未删除，1-已删除';
COMMENT ON COLUMN public.performance_test_machine.created_time IS '创建时间';
COMMENT ON COLUMN public.performance_test_machine.updated_time IS '更新时间';

COMMENT ON COLUMN public.performance_monitor_source.id IS '主键ID';
COMMENT ON COLUMN public.performance_monitor_source.name IS '监控源名称';
COMMENT ON COLUMN public.performance_monitor_source.source_type IS '监控源类型：jenkins_agent/prometheus/apm/slow_sql/log/trace';
COMMENT ON COLUMN public.performance_monitor_source.env_code IS '环境编码';
COMMENT ON COLUMN public.performance_monitor_source.endpoint IS '服务地址';
COMMENT ON COLUMN public.performance_monitor_source.auth_config_json IS '鉴权配置JSON';
COMMENT ON COLUMN public.performance_monitor_source.query_config_json IS '查询配置JSON';
COMMENT ON COLUMN public.performance_monitor_source.enabled IS '是否启用：1-启用，0-禁用';
COMMENT ON COLUMN public.performance_monitor_source.is_delete IS '软删除标识：0-未删除，1-已删除';
COMMENT ON COLUMN public.performance_monitor_source.created_time IS '创建时间';
COMMENT ON COLUMN public.performance_monitor_source.updated_time IS '更新时间';

CREATE INDEX IF NOT EXISTS idx_performance_scenario_project ON public.performance_scenario(project_id);
CREATE INDEX IF NOT EXISTS idx_performance_scenario_product ON public.performance_scenario(product_id);
CREATE INDEX IF NOT EXISTS idx_performance_script_scenario ON public.performance_script(scenario_id);
CREATE INDEX IF NOT EXISTS idx_performance_script_tool ON public.performance_script(tool_type);
CREATE INDEX IF NOT EXISTS idx_performance_script_version_script ON public.performance_script_version(script_id);
CREATE INDEX IF NOT EXISTS idx_performance_execution_config_scenario ON public.performance_execution_config(scenario_id);
CREATE INDEX IF NOT EXISTS idx_performance_execution_run_scenario ON public.performance_execution_run(scenario_id);
CREATE INDEX IF NOT EXISTS idx_performance_execution_run_status ON public.performance_execution_run(status);
CREATE INDEX IF NOT EXISTS idx_performance_execution_run_created ON public.performance_execution_run(created_time DESC);
CREATE INDEX IF NOT EXISTS idx_performance_metric_run ON public.performance_metric(run_id);
CREATE INDEX IF NOT EXISTS idx_performance_metric_name ON public.performance_metric(metric_name);
CREATE INDEX IF NOT EXISTS idx_performance_baseline_scenario ON public.performance_baseline(scenario_id);
CREATE INDEX IF NOT EXISTS idx_performance_gate_rule_scenario ON public.performance_gate_rule(scenario_id);
CREATE INDEX IF NOT EXISTS idx_performance_gate_result_run ON public.performance_gate_result(run_id);
CREATE INDEX IF NOT EXISTS idx_performance_test_machine_status ON public.performance_test_machine(status);
CREATE INDEX IF NOT EXISTS idx_performance_monitor_source_type ON public.performance_monitor_source(source_type);

DROP TRIGGER IF EXISTS trg_performance_scenario_updated_time ON public.performance_scenario;
CREATE TRIGGER trg_performance_scenario_updated_time BEFORE UPDATE ON public.performance_scenario FOR EACH ROW EXECUTE FUNCTION public.set_updated_time();
DROP TRIGGER IF EXISTS trg_performance_script_updated_time ON public.performance_script;
CREATE TRIGGER trg_performance_script_updated_time BEFORE UPDATE ON public.performance_script FOR EACH ROW EXECUTE FUNCTION public.set_updated_time();
DROP TRIGGER IF EXISTS trg_performance_execution_config_updated_time ON public.performance_execution_config;
CREATE TRIGGER trg_performance_execution_config_updated_time BEFORE UPDATE ON public.performance_execution_config FOR EACH ROW EXECUTE FUNCTION public.set_updated_time();
DROP TRIGGER IF EXISTS trg_performance_execution_run_updated_time ON public.performance_execution_run;
CREATE TRIGGER trg_performance_execution_run_updated_time BEFORE UPDATE ON public.performance_execution_run FOR EACH ROW EXECUTE FUNCTION public.set_updated_time();
DROP TRIGGER IF EXISTS trg_performance_baseline_updated_time ON public.performance_baseline;
CREATE TRIGGER trg_performance_baseline_updated_time BEFORE UPDATE ON public.performance_baseline FOR EACH ROW EXECUTE FUNCTION public.set_updated_time();
DROP TRIGGER IF EXISTS trg_performance_gate_rule_updated_time ON public.performance_gate_rule;
CREATE TRIGGER trg_performance_gate_rule_updated_time BEFORE UPDATE ON public.performance_gate_rule FOR EACH ROW EXECUTE FUNCTION public.set_updated_time();
DROP TRIGGER IF EXISTS trg_performance_report_updated_time ON public.performance_report;
CREATE TRIGGER trg_performance_report_updated_time BEFORE UPDATE ON public.performance_report FOR EACH ROW EXECUTE FUNCTION public.set_updated_time();
DROP TRIGGER IF EXISTS trg_performance_ai_analysis_updated_time ON public.performance_ai_analysis;
CREATE TRIGGER trg_performance_ai_analysis_updated_time BEFORE UPDATE ON public.performance_ai_analysis FOR EACH ROW EXECUTE FUNCTION public.set_updated_time();
DROP TRIGGER IF EXISTS trg_performance_test_machine_updated_time ON public.performance_test_machine;
CREATE TRIGGER trg_performance_test_machine_updated_time BEFORE UPDATE ON public.performance_test_machine FOR EACH ROW EXECUTE FUNCTION public.set_updated_time();
DROP TRIGGER IF EXISTS trg_performance_monitor_source_updated_time ON public.performance_monitor_source;
CREATE TRIGGER trg_performance_monitor_source_updated_time BEFORE UPDATE ON public.performance_monitor_source FOR EACH ROW EXECUTE FUNCTION public.set_updated_time();

COMMIT;
