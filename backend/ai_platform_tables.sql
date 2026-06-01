-- AI 测试中枢基础表与权限初始化

CREATE TABLE IF NOT EXISTS ai_agent (
    id BIGSERIAL PRIMARY KEY,
    agent_code VARCHAR(64) NOT NULL UNIQUE,
    product_id BIGINT,
    product_name VARCHAR(128),
    project_id BIGINT,
    project_name VARCHAR(128),
    name VARCHAR(128) NOT NULL,
    agent_type INTEGER NOT NULL DEFAULT 1,
    entrypoint VARCHAR(256) NOT NULL,
    version VARCHAR(64),
    description TEXT,
    capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,
    supported_tasks JSONB NOT NULL DEFAULT '[]'::jsonb,
    permission_policy JSONB NOT NULL DEFAULT '{}'::jsonb,
    workspace_policy JSONB NOT NULL DEFAULT '{}'::jsonb,
    timeout_seconds INTEGER NOT NULL DEFAULT 300,
    max_concurrency INTEGER NOT NULL DEFAULT 1,
    cost_policy JSONB NOT NULL DEFAULT '{}'::jsonb,
    status INTEGER NOT NULL DEFAULT 1,
    created_by BIGINT,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_agent_execution (
    id BIGSERIAL PRIMARY KEY,
    execution_no VARCHAR(64) NOT NULL UNIQUE,
    agent_id BIGINT NOT NULL,
    project_id BIGINT NOT NULL,
    workspace_path VARCHAR(512) NOT NULL,
    task_type VARCHAR(64),
    input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    command_snapshot TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    stdout_path VARCHAR(512),
    stderr_path VARCHAR(512),
    result_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT,
    duration_seconds INTEGER,
    cost_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    trigger_by BIGINT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_tool (
    id BIGSERIAL PRIMARY KEY,
    tool_code VARCHAR(64) NOT NULL UNIQUE,
    product_id BIGINT,
    product_name VARCHAR(128),
    project_id BIGINT,
    project_name VARCHAR(128),
    name VARCHAR(128) NOT NULL,
    tool_type VARCHAR(64) NOT NULL,
    command_template TEXT NOT NULL,
    input_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    artifact_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    parser_type VARCHAR(64),
    parser_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    env_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    timeout_seconds INTEGER NOT NULL DEFAULT 300,
    status INTEGER NOT NULL DEFAULT 1,
    created_by BIGINT,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_tool_execution (
    id BIGSERIAL PRIMARY KEY,
    execution_no VARCHAR(64) NOT NULL UNIQUE,
    tool_id BIGINT NOT NULL,
    project_id BIGINT NOT NULL,
    ai_task_id BIGINT,
    workspace_path VARCHAR(512) NOT NULL,
    input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    command_snapshot TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    result_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    artifact_paths JSONB NOT NULL DEFAULT '[]'::jsonb,
    stdout_path VARCHAR(512),
    stderr_path VARCHAR(512),
    duration_seconds INTEGER,
    error_message TEXT,
    trigger_by BIGINT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_mcp_connector (
    id BIGSERIAL PRIMARY KEY,
    connector_code VARCHAR(64) NOT NULL UNIQUE,
    product_id BIGINT,
    product_name VARCHAR(128),
    project_id BIGINT,
    project_name VARCHAR(128),
    name VARCHAR(128) NOT NULL,
    connector_type VARCHAR(64) NOT NULL,
    endpoint VARCHAR(512),
    auth_type VARCHAR(32) NOT NULL DEFAULT 'none',
    auth_ref VARCHAR(256),
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,
    status INTEGER NOT NULL DEFAULT 1,
    created_by BIGINT,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_mcp_call_log (
    id BIGSERIAL PRIMARY KEY,
    connector_id BIGINT NOT NULL,
    project_id BIGINT,
    operation VARCHAR(128) NOT NULL,
    request_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    response_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(32) NOT NULL DEFAULT 'success',
    error_message TEXT,
    duration_ms INTEGER,
    created_by BIGINT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_skill_flow (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT,
    product_name VARCHAR(128),
    project_id BIGINT NOT NULL,
    project_name VARCHAR(128),
    name VARCHAR(128) NOT NULL,
    flow_code VARCHAR(64) NOT NULL UNIQUE,
    description TEXT,
    trigger_type VARCHAR(64) NOT NULL DEFAULT 'manual',
    flow_definition JSONB NOT NULL DEFAULT '{}'::jsonb,
    input_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    status INTEGER NOT NULL DEFAULT 3,
    created_by BIGINT,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_skill_flow_execution (
    id BIGSERIAL PRIMARY KEY,
    flow_id BIGINT NOT NULL,
    ai_task_id BIGINT,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    node_results JSONB NOT NULL DEFAULT '[]'::jsonb,
    output_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT,
    duration_seconds INTEGER,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_test_task (
    id BIGSERIAL PRIMARY KEY,
    task_no VARCHAR(64) NOT NULL UNIQUE,
    product_id BIGINT,
    product_name VARCHAR(128),
    project_id BIGINT NOT NULL,
    project_name VARCHAR(128),
    task_type VARCHAR(64) NOT NULL,
    source_type VARCHAR(64),
    source_id BIGINT,
    source_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    risk_level VARCHAR(16),
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    recommended_tests JSONB NOT NULL DEFAULT '[]'::jsonb,
    selected_agents JSONB NOT NULL DEFAULT '[]'::jsonb,
    selected_tools JSONB NOT NULL DEFAULT '[]'::jsonb,
    selected_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    result_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    report_id BIGINT,
    created_by BIGINT,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_test_task_step (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    step_order INTEGER NOT NULL DEFAULT 1,
    step_type VARCHAR(64) NOT NULL,
    ref_type VARCHAR(64),
    ref_id BIGINT,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_quality_report (
    id BIGSERIAL PRIMARY KEY,
    report_no VARCHAR(64) NOT NULL UNIQUE,
    product_id BIGINT,
    product_name VARCHAR(128),
    project_id BIGINT NOT NULL,
    project_name VARCHAR(128),
    task_id BIGINT,
    report_type VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    risk_level VARCHAR(16),
    summary TEXT,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    findings JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommendations JSONB NOT NULL DEFAULT '[]'::jsonb,
    markdown_content TEXT,
    html_content TEXT,
    created_by BIGINT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE ai_agent IS 'AI Agent 注册表，维护可调用智能体的基础信息、能力和运行策略';
COMMENT ON COLUMN ai_agent.id IS '主键ID';
COMMENT ON COLUMN ai_agent.agent_code IS 'Agent唯一编码';
COMMENT ON COLUMN ai_agent.name IS 'Agent名称';
COMMENT ON COLUMN ai_agent.agent_type IS 'Agent类型：1本地命令，2远程服务，3平台内置';
COMMENT ON COLUMN ai_agent.entrypoint IS 'Agent入口地址或启动命令';
COMMENT ON COLUMN ai_agent.version IS 'Agent版本号';
COMMENT ON COLUMN ai_agent.description IS 'Agent描述';
COMMENT ON COLUMN ai_agent.capabilities IS '能力标签列表';
COMMENT ON COLUMN ai_agent.supported_tasks IS '支持的任务类型列表';
COMMENT ON COLUMN ai_agent.permission_policy IS '权限控制策略';
COMMENT ON COLUMN ai_agent.workspace_policy IS '工作空间访问策略';
COMMENT ON COLUMN ai_agent.timeout_seconds IS '默认执行超时时间，单位秒';
COMMENT ON COLUMN ai_agent.max_concurrency IS '最大并发执行数';
COMMENT ON COLUMN ai_agent.cost_policy IS '成本控制策略';
COMMENT ON COLUMN ai_agent.status IS '状态：1启用，2停用';
COMMENT ON COLUMN ai_agent.created_by IS '创建人用户ID';
COMMENT ON COLUMN ai_agent.is_delete IS '是否删除：0否，1是';
COMMENT ON COLUMN ai_agent.created_time IS '创建时间';
COMMENT ON COLUMN ai_agent.updated_time IS '更新时间';

COMMENT ON TABLE ai_agent_execution IS 'AI Agent 执行记录表，记录每次智能体调用过程与结果';
COMMENT ON COLUMN ai_agent_execution.id IS '主键ID';
COMMENT ON COLUMN ai_agent_execution.execution_no IS '执行流水号';
COMMENT ON COLUMN ai_agent_execution.agent_id IS 'Agent ID';
COMMENT ON COLUMN ai_agent_execution.project_id IS '项目ID';
COMMENT ON COLUMN ai_agent_execution.workspace_path IS '执行工作空间路径';
COMMENT ON COLUMN ai_agent_execution.task_type IS '任务类型';
COMMENT ON COLUMN ai_agent_execution.input_payload IS '输入参数快照';
COMMENT ON COLUMN ai_agent_execution.command_snapshot IS '实际执行命令快照';
COMMENT ON COLUMN ai_agent_execution.status IS '执行状态：pending/running/success/failed/canceled';
COMMENT ON COLUMN ai_agent_execution.stdout_path IS '标准输出日志路径';
COMMENT ON COLUMN ai_agent_execution.stderr_path IS '标准错误日志路径';
COMMENT ON COLUMN ai_agent_execution.result_payload IS '执行结果数据';
COMMENT ON COLUMN ai_agent_execution.error_message IS '错误信息';
COMMENT ON COLUMN ai_agent_execution.duration_seconds IS '执行耗时，单位秒';
COMMENT ON COLUMN ai_agent_execution.cost_summary IS '成本统计信息';
COMMENT ON COLUMN ai_agent_execution.trigger_by IS '触发人用户ID';
COMMENT ON COLUMN ai_agent_execution.created_time IS '创建时间';
COMMENT ON COLUMN ai_agent_execution.updated_time IS '更新时间';

COMMENT ON TABLE ai_tool IS 'AI 工具注册表，维护可被 AI 任务调用的命令行工具或平台工具';
COMMENT ON COLUMN ai_tool.id IS '主键ID';
COMMENT ON COLUMN ai_tool.tool_code IS '工具唯一编码';
COMMENT ON COLUMN ai_tool.name IS '工具名称';
COMMENT ON COLUMN ai_tool.tool_type IS '工具类型';
COMMENT ON COLUMN ai_tool.command_template IS '命令模板';
COMMENT ON COLUMN ai_tool.input_schema IS '输入参数JSON Schema';
COMMENT ON COLUMN ai_tool.output_schema IS '输出结果JSON Schema';
COMMENT ON COLUMN ai_tool.artifact_schema IS '产物JSON Schema';
COMMENT ON COLUMN ai_tool.parser_type IS '输出解析器类型';
COMMENT ON COLUMN ai_tool.parser_config IS '输出解析器配置';
COMMENT ON COLUMN ai_tool.env_schema IS '环境变量JSON Schema';
COMMENT ON COLUMN ai_tool.timeout_seconds IS '默认执行超时时间，单位秒';
COMMENT ON COLUMN ai_tool.status IS '状态：1启用，2停用';
COMMENT ON COLUMN ai_tool.created_by IS '创建人用户ID';
COMMENT ON COLUMN ai_tool.is_delete IS '是否删除：0否，1是';
COMMENT ON COLUMN ai_tool.created_time IS '创建时间';
COMMENT ON COLUMN ai_tool.updated_time IS '更新时间';

COMMENT ON TABLE ai_tool_execution IS 'AI 工具执行记录表，记录工具调用参数、日志、产物和结果';
COMMENT ON COLUMN ai_tool_execution.id IS '主键ID';
COMMENT ON COLUMN ai_tool_execution.execution_no IS '执行流水号';
COMMENT ON COLUMN ai_tool_execution.tool_id IS '工具ID';
COMMENT ON COLUMN ai_tool_execution.project_id IS '项目ID';
COMMENT ON COLUMN ai_tool_execution.ai_task_id IS '关联AI任务ID';
COMMENT ON COLUMN ai_tool_execution.workspace_path IS '执行工作空间路径';
COMMENT ON COLUMN ai_tool_execution.input_payload IS '输入参数快照';
COMMENT ON COLUMN ai_tool_execution.command_snapshot IS '实际执行命令快照';
COMMENT ON COLUMN ai_tool_execution.status IS '执行状态：pending/running/success/failed/canceled';
COMMENT ON COLUMN ai_tool_execution.result_summary IS '执行结果摘要';
COMMENT ON COLUMN ai_tool_execution.artifact_paths IS '产物文件路径列表';
COMMENT ON COLUMN ai_tool_execution.stdout_path IS '标准输出日志路径';
COMMENT ON COLUMN ai_tool_execution.stderr_path IS '标准错误日志路径';
COMMENT ON COLUMN ai_tool_execution.duration_seconds IS '执行耗时，单位秒';
COMMENT ON COLUMN ai_tool_execution.error_message IS '错误信息';
COMMENT ON COLUMN ai_tool_execution.trigger_by IS '触发人用户ID';
COMMENT ON COLUMN ai_tool_execution.created_time IS '创建时间';
COMMENT ON COLUMN ai_tool_execution.updated_time IS '更新时间';

COMMENT ON TABLE ai_mcp_connector IS 'MCP 连接器表，维护外部上下文服务或工具服务连接配置';
COMMENT ON COLUMN ai_mcp_connector.id IS '主键ID';
COMMENT ON COLUMN ai_mcp_connector.connector_code IS '连接器唯一编码';
COMMENT ON COLUMN ai_mcp_connector.name IS '连接器名称';
COMMENT ON COLUMN ai_mcp_connector.connector_type IS '连接器类型';
COMMENT ON COLUMN ai_mcp_connector.endpoint IS '服务地址或入口';
COMMENT ON COLUMN ai_mcp_connector.auth_type IS '认证方式：none/token/basic/oauth等';
COMMENT ON COLUMN ai_mcp_connector.auth_ref IS '认证配置引用，不直接存储密钥';
COMMENT ON COLUMN ai_mcp_connector.config IS '连接器扩展配置';
COMMENT ON COLUMN ai_mcp_connector.capabilities IS '连接器能力列表';
COMMENT ON COLUMN ai_mcp_connector.status IS '状态：1启用，2停用';
COMMENT ON COLUMN ai_mcp_connector.created_by IS '创建人用户ID';
COMMENT ON COLUMN ai_mcp_connector.is_delete IS '是否删除：0否，1是';
COMMENT ON COLUMN ai_mcp_connector.created_time IS '创建时间';
COMMENT ON COLUMN ai_mcp_connector.updated_time IS '更新时间';

COMMENT ON TABLE ai_mcp_call_log IS 'MCP 调用日志表，记录连接器调用请求、响应摘要和耗时';
COMMENT ON COLUMN ai_mcp_call_log.id IS '主键ID';
COMMENT ON COLUMN ai_mcp_call_log.connector_id IS '连接器ID';
COMMENT ON COLUMN ai_mcp_call_log.project_id IS '项目ID';
COMMENT ON COLUMN ai_mcp_call_log.operation IS '调用操作名称';
COMMENT ON COLUMN ai_mcp_call_log.request_snapshot IS '请求参数快照';
COMMENT ON COLUMN ai_mcp_call_log.response_summary IS '响应摘要';
COMMENT ON COLUMN ai_mcp_call_log.status IS '调用状态：success/failed';
COMMENT ON COLUMN ai_mcp_call_log.error_message IS '错误信息';
COMMENT ON COLUMN ai_mcp_call_log.duration_ms IS '调用耗时，单位毫秒';
COMMENT ON COLUMN ai_mcp_call_log.created_by IS '调用人用户ID';
COMMENT ON COLUMN ai_mcp_call_log.created_time IS '创建时间';

COMMENT ON TABLE ai_skill_flow IS 'AI 技能流程定义表，维护多 Agent、多工具编排流程';
COMMENT ON COLUMN ai_skill_flow.id IS '主键ID';
COMMENT ON COLUMN ai_skill_flow.project_id IS '项目ID';
COMMENT ON COLUMN ai_skill_flow.name IS '流程名称';
COMMENT ON COLUMN ai_skill_flow.flow_code IS '流程唯一编码';
COMMENT ON COLUMN ai_skill_flow.description IS '流程描述';
COMMENT ON COLUMN ai_skill_flow.trigger_type IS '触发类型：manual/webhook/schedule等';
COMMENT ON COLUMN ai_skill_flow.flow_definition IS '流程编排定义';
COMMENT ON COLUMN ai_skill_flow.input_schema IS '流程输入JSON Schema';
COMMENT ON COLUMN ai_skill_flow.output_schema IS '流程输出JSON Schema';
COMMENT ON COLUMN ai_skill_flow.status IS '状态：1启用，2停用，3草稿';
COMMENT ON COLUMN ai_skill_flow.created_by IS '创建人用户ID';
COMMENT ON COLUMN ai_skill_flow.is_delete IS '是否删除：0否，1是';
COMMENT ON COLUMN ai_skill_flow.created_time IS '创建时间';
COMMENT ON COLUMN ai_skill_flow.updated_time IS '更新时间';

COMMENT ON TABLE ai_skill_flow_execution IS 'AI 技能流程执行记录表，记录流程节点结果和整体输出';
COMMENT ON COLUMN ai_skill_flow_execution.id IS '主键ID';
COMMENT ON COLUMN ai_skill_flow_execution.flow_id IS '流程ID';
COMMENT ON COLUMN ai_skill_flow_execution.ai_task_id IS '关联AI任务ID';
COMMENT ON COLUMN ai_skill_flow_execution.status IS '执行状态：pending/running/success/failed/canceled';
COMMENT ON COLUMN ai_skill_flow_execution.input_payload IS '流程输入参数';
COMMENT ON COLUMN ai_skill_flow_execution.node_results IS '节点执行结果列表';
COMMENT ON COLUMN ai_skill_flow_execution.output_payload IS '流程输出结果';
COMMENT ON COLUMN ai_skill_flow_execution.error_message IS '错误信息';
COMMENT ON COLUMN ai_skill_flow_execution.duration_seconds IS '执行耗时，单位秒';
COMMENT ON COLUMN ai_skill_flow_execution.created_time IS '创建时间';
COMMENT ON COLUMN ai_skill_flow_execution.updated_time IS '更新时间';

COMMENT ON TABLE ai_test_task IS 'AI 测试任务表，承载需求分析、用例生成、自动执行和质量评估等任务';
COMMENT ON COLUMN ai_test_task.id IS '主键ID';
COMMENT ON COLUMN ai_test_task.task_no IS '任务编号';
COMMENT ON COLUMN ai_test_task.project_id IS '项目ID';
COMMENT ON COLUMN ai_test_task.task_type IS '任务类型';
COMMENT ON COLUMN ai_test_task.source_type IS '来源类型：requirement/bug/api/case/manual等';
COMMENT ON COLUMN ai_test_task.source_id IS '来源业务ID';
COMMENT ON COLUMN ai_test_task.source_payload IS '来源数据快照';
COMMENT ON COLUMN ai_test_task.risk_level IS '风险级别：low/medium/high/critical';
COMMENT ON COLUMN ai_test_task.status IS '任务状态：pending/running/success/failed/canceled';
COMMENT ON COLUMN ai_test_task.recommended_tests IS '推荐测试项列表';
COMMENT ON COLUMN ai_test_task.selected_agents IS '选中的Agent列表';
COMMENT ON COLUMN ai_test_task.selected_tools IS '选中的工具列表';
COMMENT ON COLUMN ai_test_task.selected_skills IS '选中的技能流程列表';
COMMENT ON COLUMN ai_test_task.result_summary IS '任务结果摘要';
COMMENT ON COLUMN ai_test_task.report_id IS '关联质量报告ID';
COMMENT ON COLUMN ai_test_task.created_by IS '创建人用户ID';
COMMENT ON COLUMN ai_test_task.is_delete IS '是否删除：0否，1是';
COMMENT ON COLUMN ai_test_task.created_time IS '创建时间';
COMMENT ON COLUMN ai_test_task.updated_time IS '更新时间';

COMMENT ON TABLE ai_test_task_step IS 'AI 测试任务步骤表，记录任务内每个执行步骤的状态和输入输出';
COMMENT ON COLUMN ai_test_task_step.id IS '主键ID';
COMMENT ON COLUMN ai_test_task_step.task_id IS 'AI任务ID';
COMMENT ON COLUMN ai_test_task_step.step_order IS '步骤顺序';
COMMENT ON COLUMN ai_test_task_step.step_type IS '步骤类型';
COMMENT ON COLUMN ai_test_task_step.ref_type IS '引用对象类型：agent/tool/flow等';
COMMENT ON COLUMN ai_test_task_step.ref_id IS '引用对象ID';
COMMENT ON COLUMN ai_test_task_step.status IS '步骤状态：pending/running/success/failed/canceled';
COMMENT ON COLUMN ai_test_task_step.input_payload IS '步骤输入参数';
COMMENT ON COLUMN ai_test_task_step.output_payload IS '步骤输出结果';
COMMENT ON COLUMN ai_test_task_step.error_message IS '错误信息';
COMMENT ON COLUMN ai_test_task_step.start_time IS '开始时间';
COMMENT ON COLUMN ai_test_task_step.end_time IS '结束时间';
COMMENT ON COLUMN ai_test_task_step.duration_seconds IS '执行耗时，单位秒';
COMMENT ON COLUMN ai_test_task_step.created_time IS '创建时间';
COMMENT ON COLUMN ai_test_task_step.updated_time IS '更新时间';

COMMENT ON TABLE ai_quality_report IS 'AI 质量报告表，保存 AI 测试任务生成的质量分析报告';
COMMENT ON COLUMN ai_quality_report.id IS '主键ID';
COMMENT ON COLUMN ai_quality_report.report_no IS '报告编号';
COMMENT ON COLUMN ai_quality_report.project_id IS '项目ID';
COMMENT ON COLUMN ai_quality_report.task_id IS '关联AI任务ID';
COMMENT ON COLUMN ai_quality_report.report_type IS '报告类型';
COMMENT ON COLUMN ai_quality_report.title IS '报告标题';
COMMENT ON COLUMN ai_quality_report.risk_level IS '风险级别：low/medium/high/critical';
COMMENT ON COLUMN ai_quality_report.summary IS '报告摘要';
COMMENT ON COLUMN ai_quality_report.metrics IS '质量指标数据';
COMMENT ON COLUMN ai_quality_report.findings IS '问题发现列表';
COMMENT ON COLUMN ai_quality_report.recommendations IS '改进建议列表';
COMMENT ON COLUMN ai_quality_report.markdown_content IS 'Markdown格式报告内容';
COMMENT ON COLUMN ai_quality_report.html_content IS 'HTML格式报告内容';
COMMENT ON COLUMN ai_quality_report.created_by IS '创建人用户ID';
COMMENT ON COLUMN ai_quality_report.created_time IS '创建时间';

CREATE INDEX IF NOT EXISTS idx_ai_agent_status ON ai_agent(status, is_delete);
CREATE INDEX IF NOT EXISTS idx_ai_agent_execution_agent ON ai_agent_execution(agent_id, status);
CREATE INDEX IF NOT EXISTS idx_ai_tool_status ON ai_tool(status, is_delete);
CREATE INDEX IF NOT EXISTS idx_ai_tool_execution_tool ON ai_tool_execution(tool_id, status);
CREATE INDEX IF NOT EXISTS idx_ai_task_project ON ai_test_task(project_id, task_type, status, is_delete);
CREATE INDEX IF NOT EXISTS idx_ai_report_project ON ai_quality_report(project_id, report_type);

INSERT INTO permission (code, name, module, action, description, status, is_delete)
SELECT p.code, p.name, p.module, p.action, p.description, 1, 0
FROM (VALUES
    ('ai_agent:list', 'Agent列表', 'ai_agent', 'list', '查看Agent列表'),
    ('ai_agent:create', 'Agent创建', 'ai_agent', 'create', '创建Agent'),
    ('ai_agent:update', 'Agent更新', 'ai_agent', 'update', '更新Agent'),
    ('ai_agent:delete', 'Agent删除', 'ai_agent', 'delete', '删除Agent'),
    ('ai_agent:execute', 'Agent执行', 'ai_agent', 'execute', '执行Agent'),
    ('ai_agent:detail', 'Agent详情', 'ai_agent', 'detail', '查看Agent详情'),
    ('ai_tool:list', '工具列表', 'ai_tool', 'list', '查看工具列表'),
    ('ai_tool:create', '工具创建', 'ai_tool', 'create', '创建工具'),
    ('ai_tool:update', '工具更新', 'ai_tool', 'update', '更新工具'),
    ('ai_tool:delete', '工具删除', 'ai_tool', 'delete', '删除工具'),
    ('ai_tool:execute', '工具执行', 'ai_tool', 'execute', '执行工具'),
    ('ai_tool:detail', '工具详情', 'ai_tool', 'detail', '查看工具详情'),
    ('ai_mcp:list', 'MCP列表', 'ai_mcp', 'list', '查看MCP列表'),
    ('ai_mcp:create', 'MCP创建', 'ai_mcp', 'create', '创建MCP连接'),
    ('ai_mcp:update', 'MCP更新', 'ai_mcp', 'update', '更新MCP连接'),
    ('ai_mcp:delete', 'MCP删除', 'ai_mcp', 'delete', '删除MCP连接'),
    ('ai_mcp:call', 'MCP调用', 'ai_mcp', 'call', '调用MCP连接'),
    ('ai_mcp:detail', 'MCP详情', 'ai_mcp', 'detail', '查看MCP详情'),
    ('ai_flow:list', 'AI流程列表', 'ai_flow', 'list', '查看AI流程列表'),
    ('ai_flow:create', 'AI流程创建', 'ai_flow', 'create', '创建AI流程'),
    ('ai_flow:update', 'AI流程更新', 'ai_flow', 'update', '更新AI流程'),
    ('ai_flow:delete', 'AI流程删除', 'ai_flow', 'delete', '删除AI流程'),
    ('ai_flow:execute', 'AI流程执行', 'ai_flow', 'execute', '执行AI流程'),
    ('ai_flow:detail', 'AI流程详情', 'ai_flow', 'detail', '查看AI流程详情'),
    ('ai_task:list', 'AI任务列表', 'ai_task', 'list', '查看AI任务列表'),
    ('ai_task:create', 'AI任务创建', 'ai_task', 'create', '创建AI任务'),
    ('ai_task:execute', 'AI任务执行', 'ai_task', 'execute', '执行AI任务'),
    ('ai_task:detail', 'AI任务详情', 'ai_task', 'detail', '查看AI任务详情'),
    ('ai_task:cancel', 'AI任务取消', 'ai_task', 'cancel', '取消AI任务'),
    ('ai_report:list', 'AI报告列表', 'ai_report', 'list', '查看AI报告列表'),
    ('ai_report:create', 'AI报告创建', 'ai_report', 'create', '创建AI报告'),
    ('ai_report:detail', 'AI报告详情', 'ai_report', 'detail', '查看AI报告详情'),
    ('ai_report:export', 'AI报告导出', 'ai_report', 'export', '导出AI报告')
) AS p(code, name, module, action, description)
WHERE NOT EXISTS (SELECT 1 FROM permission WHERE permission.code = p.code);

INSERT INTO menu (name, code, type, path, component, icon, permission_code, parent_id, sort, visible, status, is_delete)
SELECT 'AI测试中枢', 'ai_testing_center', 2, '/test-platform/ai-platform', 'TestPlatform/AI/AiPlatform', 'el-icon-cpu', 'ai_task:list', 0, 20, 1, 1, 0
WHERE NOT EXISTS (SELECT 1 FROM menu WHERE code = 'ai_testing_center');

UPDATE menu
SET type = 2,
    path = '/test-platform/ai-platform',
    component = 'TestPlatform/AI/AiPlatform',
    icon = 'el-icon-cpu',
    permission_code = 'ai_task:list',
    visible = 1,
    status = 1,
    is_delete = 0
WHERE code = 'ai_testing_center';

UPDATE menu
SET visible = 0
WHERE code IN ('ai_agent_center', 'ai_tool_market', 'ai_mcp_center', 'ai_flow_canvas', 'ai_task_center', 'ai_report_center');

INSERT INTO role_permission (role_id, permission_id, is_delete)
SELECT r.id, p.id, 0
FROM role r
JOIN permission p ON p.code LIKE 'ai_%' AND p.is_delete = 0
WHERE r.is_delete = 0
  AND (r.is_system = 1 OR r.code IN ('admin', 'administrator', 'super_admin'))
  AND NOT EXISTS (
    SELECT 1 FROM role_permission rp
    WHERE rp.role_id = r.id AND rp.permission_id = p.id AND rp.is_delete = 0
  );

COMMIT;
