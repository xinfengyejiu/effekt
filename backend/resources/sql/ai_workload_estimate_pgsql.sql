-- AI workload estimate tables.
-- PostgreSQL, idempotent.

BEGIN;

CREATE TABLE IF NOT EXISTS public.ai_workload_estimate (
    id BIGSERIAL PRIMARY KEY,
    estimate_no VARCHAR(64) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    product_id BIGINT NOT NULL,
    product_name VARCHAR(128),
    project_id BIGINT NOT NULL,
    project_name VARCHAR(128),
    owner_id BIGINT,
    owner_name VARCHAR(128),
    document_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    reference_document_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    prd_snapshot JSONB NOT NULL DEFAULT '[]'::jsonb,
    reference_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    raw_ai_output JSONB NOT NULL DEFAULT '{}'::jsonb,
    failure_reason TEXT,
    complexity_level VARCHAR(32),
    confidence VARCHAR(32),
    total_function_points INTEGER DEFAULT 0,
    total_case_count INTEGER DEFAULT 0,
    case_design_hours NUMERIC(10,2) DEFAULT 0,
    qa_execution_hours NUMERIC(10,2) DEFAULT 0,
    total_effort_hours NUMERIC(10,2) DEFAULT 0,
    estimated_tokens BIGINT DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    created_by BIGINT,
    assigned_by BIGINT,
    assigned_time TIMESTAMP,
    confirmed_by BIGINT,
    confirmed_time TIMESTAMP,
    confirm_info JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.ai_workload_estimate IS 'AI工作量预估主表';
COMMENT ON COLUMN public.ai_workload_estimate.id IS '主键ID';
COMMENT ON COLUMN public.ai_workload_estimate.estimate_no IS '预估编号';
COMMENT ON COLUMN public.ai_workload_estimate.title IS '预估标题';
COMMENT ON COLUMN public.ai_workload_estimate.product_id IS '产品ID';
COMMENT ON COLUMN public.ai_workload_estimate.product_name IS '产品名称';
COMMENT ON COLUMN public.ai_workload_estimate.project_id IS '项目ID';
COMMENT ON COLUMN public.ai_workload_estimate.project_name IS '项目名称';
COMMENT ON COLUMN public.ai_workload_estimate.owner_id IS '负责人用户ID';
COMMENT ON COLUMN public.ai_workload_estimate.owner_name IS '负责人姓名';
COMMENT ON COLUMN public.ai_workload_estimate.document_ids IS '本次参与预估的PRD文档ID';
COMMENT ON COLUMN public.ai_workload_estimate.reference_document_ids IS '同产品历史参考文档ID';
COMMENT ON COLUMN public.ai_workload_estimate.prd_snapshot IS '本次PRD快照';
COMMENT ON COLUMN public.ai_workload_estimate.reference_summary IS '历史复杂度参考摘要';
COMMENT ON COLUMN public.ai_workload_estimate.result_summary IS '预估结果摘要';
COMMENT ON COLUMN public.ai_workload_estimate.raw_ai_output IS 'AI原始输出JSON';
COMMENT ON COLUMN public.ai_workload_estimate.failure_reason IS '失败原因';
COMMENT ON COLUMN public.ai_workload_estimate.complexity_level IS '整体复杂度等级';
COMMENT ON COLUMN public.ai_workload_estimate.confidence IS '预估置信度';
COMMENT ON COLUMN public.ai_workload_estimate.total_function_points IS '功能点总数';
COMMENT ON COLUMN public.ai_workload_estimate.total_case_count IS '预估用例总数';
COMMENT ON COLUMN public.ai_workload_estimate.case_design_hours IS '用例设计预估工时';
COMMENT ON COLUMN public.ai_workload_estimate.qa_execution_hours IS 'QA执行预估工时';
COMMENT ON COLUMN public.ai_workload_estimate.total_effort_hours IS '总预估工时';
COMMENT ON COLUMN public.ai_workload_estimate.estimated_tokens IS '预估Token消耗';
COMMENT ON COLUMN public.ai_workload_estimate.status IS '状态：draft/pending/running/completed/failed/confirmed';
COMMENT ON COLUMN public.ai_workload_estimate.created_by IS '创建人用户ID';
COMMENT ON COLUMN public.ai_workload_estimate.assigned_by IS '分配人用户ID';
COMMENT ON COLUMN public.ai_workload_estimate.assigned_time IS '分配时间';
COMMENT ON COLUMN public.ai_workload_estimate.confirmed_by IS '确认人用户ID';
COMMENT ON COLUMN public.ai_workload_estimate.confirmed_time IS '确认时间';
COMMENT ON COLUMN public.ai_workload_estimate.confirm_info IS '人工确认信息';
COMMENT ON COLUMN public.ai_workload_estimate.is_delete IS '删除标识：0未删除，1已删除';
COMMENT ON COLUMN public.ai_workload_estimate.created_time IS '创建时间';
COMMENT ON COLUMN public.ai_workload_estimate.updated_time IS '更新时间';

CREATE TABLE IF NOT EXISTS public.ai_workload_estimate_module (
    id BIGSERIAL PRIMARY KEY,
    estimate_id BIGINT NOT NULL,
    module_name VARCHAR(128) NOT NULL,
    description TEXT,
    complexity_level VARCHAR(32),
    function_point_count INTEGER DEFAULT 0,
    case_count INTEGER DEFAULT 0,
    case_design_hours NUMERIC(10,2) DEFAULT 0,
    qa_execution_hours NUMERIC(10,2) DEFAULT 0,
    total_hours NUMERIC(10,2) DEFAULT 0,
    risk_summary JSONB NOT NULL DEFAULT '[]'::jsonb,
    sort_order INTEGER DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.ai_workload_estimate_module IS 'AI工作量预估模块明细';
COMMENT ON COLUMN public.ai_workload_estimate_module.id IS '主键ID';
COMMENT ON COLUMN public.ai_workload_estimate_module.estimate_id IS '预估任务ID';
COMMENT ON COLUMN public.ai_workload_estimate_module.module_name IS '模块名称';
COMMENT ON COLUMN public.ai_workload_estimate_module.description IS '模块说明';
COMMENT ON COLUMN public.ai_workload_estimate_module.complexity_level IS '模块复杂度等级';
COMMENT ON COLUMN public.ai_workload_estimate_module.function_point_count IS '模块功能点数量';
COMMENT ON COLUMN public.ai_workload_estimate_module.case_count IS '模块预估用例数量';
COMMENT ON COLUMN public.ai_workload_estimate_module.case_design_hours IS '模块用例设计预估工时';
COMMENT ON COLUMN public.ai_workload_estimate_module.qa_execution_hours IS '模块QA执行预估工时';
COMMENT ON COLUMN public.ai_workload_estimate_module.total_hours IS '模块总预估工时';
COMMENT ON COLUMN public.ai_workload_estimate_module.risk_summary IS '模块风险摘要';
COMMENT ON COLUMN public.ai_workload_estimate_module.sort_order IS '排序号';
COMMENT ON COLUMN public.ai_workload_estimate_module.created_time IS '创建时间';
COMMENT ON COLUMN public.ai_workload_estimate_module.updated_time IS '更新时间';

CREATE TABLE IF NOT EXISTS public.ai_workload_estimate_function (
    id BIGSERIAL PRIMARY KEY,
    estimate_id BIGINT NOT NULL,
    module_id BIGINT,
    module_name VARCHAR(128),
    function_name VARCHAR(255) NOT NULL,
    description TEXT,
    test_scope TEXT,
    positive_case_count INTEGER DEFAULT 0,
    negative_case_count INTEGER DEFAULT 0,
    boundary_case_count INTEGER DEFAULT 0,
    permission_case_count INTEGER DEFAULT 0,
    integration_case_count INTEGER DEFAULT 0,
    case_count INTEGER DEFAULT 0,
    complexity_reason TEXT,
    case_design_hours NUMERIC(10,2) DEFAULT 0,
    qa_execution_hours NUMERIC(10,2) DEFAULT 0,
    total_hours NUMERIC(10,2) DEFAULT 0,
    estimated_tokens BIGINT DEFAULT 0,
    risk_level VARCHAR(32),
    sort_order INTEGER DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.ai_workload_estimate_function IS 'AI工作量预估功能点明细';
COMMENT ON COLUMN public.ai_workload_estimate_function.id IS '主键ID';
COMMENT ON COLUMN public.ai_workload_estimate_function.estimate_id IS '预估任务ID';
COMMENT ON COLUMN public.ai_workload_estimate_function.module_id IS '模块明细ID';
COMMENT ON COLUMN public.ai_workload_estimate_function.module_name IS '模块名称';
COMMENT ON COLUMN public.ai_workload_estimate_function.function_name IS '功能点名称';
COMMENT ON COLUMN public.ai_workload_estimate_function.description IS '功能点说明';
COMMENT ON COLUMN public.ai_workload_estimate_function.test_scope IS '测试范围';
COMMENT ON COLUMN public.ai_workload_estimate_function.positive_case_count IS '正向用例数量';
COMMENT ON COLUMN public.ai_workload_estimate_function.negative_case_count IS '反向用例数量';
COMMENT ON COLUMN public.ai_workload_estimate_function.boundary_case_count IS '边界用例数量';
COMMENT ON COLUMN public.ai_workload_estimate_function.permission_case_count IS '权限用例数量';
COMMENT ON COLUMN public.ai_workload_estimate_function.integration_case_count IS '集成用例数量';
COMMENT ON COLUMN public.ai_workload_estimate_function.case_count IS '功能点预估用例总数';
COMMENT ON COLUMN public.ai_workload_estimate_function.complexity_reason IS '复杂度判断原因';
COMMENT ON COLUMN public.ai_workload_estimate_function.case_design_hours IS '功能点用例设计预估工时';
COMMENT ON COLUMN public.ai_workload_estimate_function.qa_execution_hours IS '功能点QA执行预估工时';
COMMENT ON COLUMN public.ai_workload_estimate_function.total_hours IS '功能点总预估工时';
COMMENT ON COLUMN public.ai_workload_estimate_function.estimated_tokens IS '功能点预估Token消耗';
COMMENT ON COLUMN public.ai_workload_estimate_function.risk_level IS '风险等级';
COMMENT ON COLUMN public.ai_workload_estimate_function.sort_order IS '排序号';
COMMENT ON COLUMN public.ai_workload_estimate_function.created_time IS '创建时间';
COMMENT ON COLUMN public.ai_workload_estimate_function.updated_time IS '更新时间';

CREATE INDEX IF NOT EXISTS idx_ai_workload_estimate_no
ON public.ai_workload_estimate(estimate_no)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_ai_workload_estimate_product
ON public.ai_workload_estimate(product_id)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_ai_workload_estimate_project
ON public.ai_workload_estimate(project_id)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_ai_workload_estimate_owner
ON public.ai_workload_estimate(owner_id)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_ai_workload_estimate_status
ON public.ai_workload_estimate(status)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_ai_workload_estimate_complexity
ON public.ai_workload_estimate(complexity_level)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_ai_workload_estimate_created_time
ON public.ai_workload_estimate(created_time DESC);

CREATE INDEX IF NOT EXISTS idx_ai_workload_estimate_module_estimate
ON public.ai_workload_estimate_module(estimate_id, sort_order);

CREATE INDEX IF NOT EXISTS idx_ai_workload_estimate_function_estimate
ON public.ai_workload_estimate_function(estimate_id, sort_order);

CREATE INDEX IF NOT EXISTS idx_ai_workload_estimate_function_module
ON public.ai_workload_estimate_function(module_id);

COMMIT;
