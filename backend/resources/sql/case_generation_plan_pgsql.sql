-- 需求→用例两阶段生成计划（大纲 / 预览候选 / 覆盖报告）
-- 亦可由 CaseGenerationPlanService.ensure_table 运行时幂等创建

CREATE TABLE IF NOT EXISTS case_generation_plan (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    document_ids BIGINT[] DEFAULT '{}'::bigint[],
    status VARCHAR(32) DEFAULT 'outline',
    import_mode VARCHAR(16) DEFAULT 'preview',
    outline JSONB DEFAULT '{}'::jsonb,
    candidate_cases JSONB DEFAULT '[]'::jsonb,
    coverage JSONB DEFAULT '{}'::jsonb,
    template JSONB DEFAULT '{}'::jsonb,
    generation_id VARCHAR(64),
    created_by BIGINT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_case_generation_plan_project
    ON case_generation_plan(project_id, status);
