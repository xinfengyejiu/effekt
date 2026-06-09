from sqlalchemy import BigInteger, Column, Integer, Numeric, SmallInteger, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class PerformanceScenario(Base):
    __tablename__ = 'performance_scenario'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    name = Column(String(128), nullable=False, comment='场景名称')
    code = Column(String(64), nullable=False, unique=True, comment='场景编码')
    description = Column(Text, comment='场景描述')
    project_id = Column(BigInteger, comment='项目ID')
    product_id = Column(BigInteger, comment='产品ID')
    env_code = Column(String(32), comment='默认环境编码')
    status = Column(SmallInteger, nullable=False, default=1, comment='0-禁用 1-启用 2-草稿 3-归档')
    owner_id = Column(BigInteger, comment='负责人用户ID')
    created_by = Column(BigInteger, comment='创建人用户ID')
    is_delete = Column(Integer, nullable=False, default=0, comment='0-未删除 1-已删除')
    ext = Column(JSONB, server_default=text("'{}'::jsonb"), comment='扩展字段')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class PerformanceScript(Base):
    __tablename__ = 'performance_script'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    scenario_id = Column(BigInteger, nullable=False, comment='性能场景ID')
    name = Column(String(128), nullable=False, comment='脚本名称')
    tool_type = Column(String(32), nullable=False, comment='工具类型：jmeter/k6/locust')
    description = Column(Text, comment='脚本描述')
    current_version_id = Column(BigInteger, comment='当前脚本版本ID')
    status = Column(SmallInteger, nullable=False, default=1, comment='0-禁用 1-启用 2-草稿')
    created_by = Column(BigInteger, comment='创建人用户ID')
    is_delete = Column(Integer, nullable=False, default=0, comment='0-未删除 1-已删除')
    ext = Column(JSONB, server_default=text("'{}'::jsonb"), comment='扩展字段')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class PerformanceScriptVersion(Base):
    __tablename__ = 'performance_script_version'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    script_id = Column(BigInteger, nullable=False, comment='脚本ID')
    version = Column(String(64), nullable=False, comment='版本号')
    package_path = Column(String(512), nullable=False, comment='脚本包路径')
    main_file = Column(String(255), comment='主文件')
    manifest_path = Column(String(512), comment='manifest路径')
    checksum = Column(String(128), comment='文件校验值')
    file_size = Column(BigInteger, comment='文件大小')
    generator_type = Column(String(32), nullable=False, default='upload', comment='upload/ai_generated/manual')
    ai_prompt = Column(Text, comment='AI生成提示词')
    structure_plan_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='结构化压测方案')
    created_by = Column(BigInteger, comment='创建人用户ID')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')


class PerformanceExecutionConfig(Base):
    __tablename__ = 'performance_execution_config'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    scenario_id = Column(BigInteger, nullable=False, comment='性能场景ID')
    script_id = Column(BigInteger, comment='脚本ID')
    script_version_id = Column(BigInteger, comment='脚本版本ID')
    name = Column(String(128), nullable=False, comment='配置名称')
    env_code = Column(String(32), comment='环境编码')
    base_url = Column(String(512), comment='基础URL')
    concurrent_users = Column(Integer, comment='并发用户数')
    duration_seconds = Column(Integer, comment='持续时间秒')
    ramp_up_seconds = Column(Integer, comment='加压时间秒')
    test_machine_id = Column(BigInteger, comment='测试机ID')
    headers_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='Header配置')
    variables_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='变量配置')
    parameter_files_json = Column(JSONB, server_default=text("'[]'::jsonb"), comment='参数文件配置')
    tool_options_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='工具扩展参数')
    created_by = Column(BigInteger, comment='创建人用户ID')
    is_delete = Column(Integer, nullable=False, default=0, comment='0-未删除 1-已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class PerformanceExecutionRun(Base):
    __tablename__ = 'performance_execution_run'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    run_no = Column(String(64), nullable=False, unique=True, comment='执行编号')
    scenario_id = Column(BigInteger, nullable=False, comment='性能场景ID')
    script_id = Column(BigInteger, comment='脚本ID')
    script_version_id = Column(BigInteger, comment='脚本版本ID')
    execution_config_id = Column(BigInteger, comment='执行配置ID')
    tool_type = Column(String(32), nullable=False, comment='工具类型')
    env_code = Column(String(32), comment='环境编码')
    test_machine_id = Column(BigInteger, comment='测试机ID')
    jenkins_job_name = Column(String(128), comment='Jenkins任务名称')
    jenkins_queue_id = Column(BigInteger, comment='Jenkins队列ID')
    jenkins_build_number = Column(BigInteger, comment='Jenkins构建号')
    jenkins_build_url = Column(String(512), comment='Jenkins构建地址')
    console_url = Column(String(512), comment='控制台地址')
    status = Column(SmallInteger, nullable=False, default=0, comment='0-待触发 1-触发中 2-排队中 3-执行中 4-成功 5-失败 6-已取消 7-超时 8-解析失败')
    start_time = Column(TIMESTAMP, comment='开始时间')
    end_time = Column(TIMESTAMP, comment='结束时间')
    duration_seconds = Column(Integer, comment='耗时秒数')
    trigger_type = Column(String(32), nullable=False, default='manual', comment='触发类型')
    trigger_by = Column(BigInteger, comment='触发人')
    callback_token = Column(String(128), comment='回调token')
    error_message = Column(Text, comment='错误信息')
    ext = Column(JSONB, server_default=text("'{}'::jsonb"), comment='扩展字段')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class PerformanceMetric(Base):
    __tablename__ = 'performance_metric'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    run_id = Column(BigInteger, nullable=False, comment='执行记录ID')
    scenario_id = Column(BigInteger, nullable=False, comment='性能场景ID')
    metric_name = Column(String(128), nullable=False, comment='指标名称')
    metric_value = Column(Numeric(20, 6), comment='指标值')
    metric_unit = Column(String(32), comment='指标单位')
    metric_source = Column(String(64), comment='指标来源')
    tags_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='标签JSON')
    metric_time = Column(TIMESTAMP, comment='采样时间')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')


class PerformanceBaseline(Base):
    __tablename__ = 'performance_baseline'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    scenario_id = Column(BigInteger, nullable=False, comment='性能场景ID')
    script_id = Column(BigInteger, comment='脚本ID')
    script_version_id = Column(BigInteger, comment='脚本版本ID')
    run_id = Column(BigInteger, nullable=False, comment='基线来源执行ID')
    tool_type = Column(String(32), nullable=False, comment='工具类型')
    env_code = Column(String(32), comment='环境编码')
    config_hash = Column(String(128), comment='执行配置hash')
    name = Column(String(128), nullable=False, comment='基线名称')
    status = Column(SmallInteger, nullable=False, default=1, comment='0-废弃 1-生效 2-草稿 3-历史')
    baseline_metrics_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='基线指标快照')
    created_by = Column(BigInteger, comment='创建人')
    effective_time = Column(TIMESTAMP, comment='生效时间')
    remark = Column(Text, comment='备注')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class PerformanceGateRule(Base):
    __tablename__ = 'performance_gate_rule'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    scenario_id = Column(BigInteger, comment='性能场景ID')
    name = Column(String(128), nullable=False, comment='规则名称')
    metric_name = Column(String(128), nullable=False, comment='指标名称')
    operator = Column(String(16), nullable=False, comment='操作符')
    threshold_value = Column(Numeric(20, 6), comment='阈值')
    threshold_unit = Column(String(32), comment='阈值单位')
    compare_type = Column(String(32), nullable=False, default='absolute', comment='absolute/baseline_ratio/baseline_delta')
    severity = Column(String(32), nullable=False, default='failed', comment='warning/failed')
    enabled = Column(SmallInteger, nullable=False, default=1, comment='是否启用')
    created_by = Column(BigInteger, comment='创建人')
    is_delete = Column(Integer, nullable=False, default=0, comment='0-未删除 1-已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class PerformanceGateResult(Base):
    __tablename__ = 'performance_gate_result'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    run_id = Column(BigInteger, nullable=False, comment='执行记录ID')
    rule_id = Column(BigInteger, comment='规则ID')
    metric_name = Column(String(128), nullable=False, comment='指标名称')
    actual_value = Column(Numeric(20, 6), comment='实际值')
    threshold_value = Column(Numeric(20, 6), comment='阈值')
    baseline_value = Column(Numeric(20, 6), comment='基线值')
    compare_result = Column(String(64), comment='比较结果')
    status = Column(String(32), nullable=False, comment='passed/warning/failed')
    message = Column(Text, comment='结果说明')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')


class PerformanceReport(Base):
    __tablename__ = 'performance_report'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    run_id = Column(BigInteger, nullable=False, unique=True, comment='执行记录ID')
    scenario_id = Column(BigInteger, nullable=False, comment='性能场景ID')
    summary_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='报告摘要')
    metrics_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='指标JSON')
    gate_result_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='门禁结果JSON')
    native_report_url = Column(String(512), comment='原生报告地址')
    unified_report_path = Column(String(512), comment='统一报告路径')
    raw_result_url = Column(String(512), comment='原始结果地址')
    log_url = Column(String(512), comment='日志地址')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class PerformanceAiAnalysis(Base):
    __tablename__ = 'performance_ai_analysis'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    run_id = Column(BigInteger, nullable=False, comment='执行记录ID')
    scenario_id = Column(BigInteger, nullable=False, comment='性能场景ID')
    analysis_status = Column(String(32), nullable=False, default='pending', comment='分析状态')
    conclusion = Column(Text, comment='结论')
    conclusion_type = Column(String(64), comment='结论类型')
    confidence = Column(String(32), comment='置信度')
    evidence_json = Column(JSONB, server_default=text("'[]'::jsonb"), comment='证据JSON')
    suggestion_json = Column(JSONB, server_default=text("'[]'::jsonb"), comment='建议JSON')
    prompt = Column(Text, comment='提示词')
    model_name = Column(String(128), comment='模型名称')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class PerformanceTestMachine(Base):
    __tablename__ = 'performance_test_machine'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    name = Column(String(128), nullable=False, comment='测试机名称')
    jenkins_agent_name = Column(String(128), comment='Jenkins Agent名称')
    jenkins_label = Column(String(128), nullable=False, comment='Jenkins Label')
    os_type = Column(String(64), comment='操作系统')
    host = Column(String(128), comment='主机名')
    ip = Column(String(64), comment='IP地址')
    supported_tools_json = Column(JSONB, server_default=text("'[]'::jsonb"), comment='支持工具')
    tool_versions_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='工具版本')
    work_dir = Column(String(512), comment='工作目录')
    max_concurrent_tasks = Column(Integer, nullable=False, default=1, comment='最大并发任务数')
    current_running_tasks = Column(Integer, nullable=False, default=0, comment='当前运行任务数')
    cpu_cores = Column(Integer, comment='CPU核心数')
    memory_gb = Column(Numeric(10, 2), comment='内存GB')
    status = Column(SmallInteger, nullable=False, default=1, comment='0-离线 1-在线 2-忙碌 3-禁用 4-异常')
    tags_json = Column(JSONB, server_default=text("'[]'::jsonb"), comment='标签')
    env_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='环境变量')
    remark = Column(Text, comment='备注')
    is_delete = Column(Integer, nullable=False, default=0, comment='0-未删除 1-已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class PerformanceMonitorSource(Base):
    __tablename__ = 'performance_monitor_source'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    name = Column(String(128), nullable=False, comment='监控源名称')
    source_type = Column(String(64), nullable=False, comment='监控源类型')
    env_code = Column(String(32), comment='环境编码')
    endpoint = Column(String(512), comment='服务地址')
    auth_config_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='鉴权配置')
    query_config_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='查询配置')
    enabled = Column(SmallInteger, nullable=False, default=1, comment='是否启用')
    is_delete = Column(Integer, nullable=False, default=0, comment='0-未删除 1-已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')
