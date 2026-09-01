-- AI test review assistant tables.

CREATE TABLE IF NOT EXISTS public.ai_test_review (
    id BIGSERIAL PRIMARY KEY,
    review_no VARCHAR(64) NOT NULL UNIQUE,
    product_id BIGINT,
    product_name VARCHAR(128),
    project_id BIGINT NOT NULL,
    project_name VARCHAR(128),
    review_type VARCHAR(64) NOT NULL,
    source_type VARCHAR(64) NOT NULL DEFAULT 'manual',
    source_id BIGINT,
    title VARCHAR(255) NOT NULL,
    input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    context_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    risk_level VARCHAR(32),
    score INTEGER,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_by BIGINT,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.ai_test_review_finding (
    id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL,
    finding_type VARCHAR(64) NOT NULL DEFAULT 'risk',
    risk_level VARCHAR(32),
    module_name VARCHAR(255),
    api_path VARCHAR(512),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    suggestion TEXT,
    evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(32) NOT NULL DEFAULT 'open',
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS public.ai_test_review_case_suggestion (
    id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL,
    finding_id BIGINT,
    module_name VARCHAR(255),
    case_title VARCHAR(255) NOT NULL,
    preconditions TEXT,
    steps TEXT,
    expected_results TEXT,
    priority SMALLINT DEFAULT 2,
    case_type SMALLINT DEFAULT 1,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    matched_case_id BIGINT,
    action_status VARCHAR(32) NOT NULL DEFAULT 'pending',
    created_case_id BIGINT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_ai_test_review_project ON public.ai_test_review(project_id, review_type, status, is_delete);
CREATE INDEX IF NOT EXISTS idx_ai_test_review_source ON public.ai_test_review(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_ai_test_review_created ON public.ai_test_review(created_time);
CREATE INDEX IF NOT EXISTS idx_ai_test_review_finding_review ON public.ai_test_review_finding(review_id, status, is_delete);
CREATE INDEX IF NOT EXISTS idx_ai_test_review_case_review ON public.ai_test_review_case_suggestion(review_id, action_status, is_delete);

COMMENT ON TABLE public.ai_test_review IS 'AI测试评审主表';
COMMENT ON TABLE public.ai_test_review_finding IS 'AI测试评审风险发现表';
COMMENT ON TABLE public.ai_test_review_case_suggestion IS 'AI测试评审建议用例表';
