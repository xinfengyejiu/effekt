-- 契约测试 / 接口漂移守护表结构（PostgreSQL，幂等）

BEGIN;

CREATE TABLE IF NOT EXISTS public.contract_suite (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL,
    project_id BIGINT NOT NULL,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    source_type VARCHAR(32) NOT NULL DEFAULT 'mock_document',
    mock_document_id BIGINT,
    openapi_content TEXT,
    base_url VARCHAR(512) NOT NULL,
    default_headers JSONB NOT NULL DEFAULT '{}'::jsonb,
    notify_type VARCHAR(128),
    notify_webhook VARCHAR(512),
    schedule_type VARCHAR(32) NOT NULL DEFAULT 'manual',
    cron_expression VARCHAR(128),
    interval_seconds INT,
    enabled SMALLINT NOT NULL DEFAULT 1,
    last_run_at TIMESTAMP,
    created_by BIGINT,
    is_delete INT NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_contract_suite_project ON public.contract_suite(project_id, is_delete);
CREATE INDEX IF NOT EXISTS idx_contract_suite_enabled ON public.contract_suite(enabled, schedule_type);

CREATE TABLE IF NOT EXISTS public.contract_suite_item (
    id BIGSERIAL PRIMARY KEY,
    suite_id BIGINT NOT NULL,
    mock_interface_id BIGINT,
    name VARCHAR(255) NOT NULL,
    method VARCHAR(16) NOT NULL,
    path VARCHAR(512) NOT NULL,
    path_params JSONB NOT NULL DEFAULT '{}'::jsonb,
    query_params JSONB NOT NULL DEFAULT '{}'::jsonb,
    body_template JSONB,
    response_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    timeout_seconds INT NOT NULL DEFAULT 30,
    enabled SMALLINT NOT NULL DEFAULT 1,
    sort_order INT NOT NULL DEFAULT 0,
    is_delete INT NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_contract_suite_item_suite ON public.contract_suite_item(suite_id, is_delete);

CREATE TABLE IF NOT EXISTS public.contract_run (
    id BIGSERIAL PRIMARY KEY,
    run_no VARCHAR(64) NOT NULL,
    suite_id BIGINT NOT NULL,
    project_id BIGINT NOT NULL,
    trigger_type VARCHAR(32) NOT NULL DEFAULT 'manual',
    status SMALLINT NOT NULL DEFAULT 0,
    total_count INT NOT NULL DEFAULT 0,
    pass_count INT NOT NULL DEFAULT 0,
    drift_count INT NOT NULL DEFAULT 0,
    error_count INT NOT NULL DEFAULT 0,
    breaking_count INT NOT NULL DEFAULT 0,
    trigger_by BIGINT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_ms INT,
    summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    notify_status SMALLINT NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_contract_run_no UNIQUE (run_no)
);

CREATE INDEX IF NOT EXISTS idx_contract_run_suite ON public.contract_run(suite_id, created_time DESC);
CREATE INDEX IF NOT EXISTS idx_contract_run_project ON public.contract_run(project_id, created_time DESC);

CREATE TABLE IF NOT EXISTS public.contract_run_item (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL,
    suite_item_id BIGINT,
    name VARCHAR(255),
    method VARCHAR(16) NOT NULL,
    path VARCHAR(512) NOT NULL,
    http_status INT,
    result_status VARCHAR(32) NOT NULL DEFAULT 'pending',
    max_severity VARCHAR(16),
    duration_ms INT,
    response_excerpt TEXT,
    error_message TEXT,
    ai_analysis JSONB,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_contract_run_item_run ON public.contract_run_item(run_id);

CREATE TABLE IF NOT EXISTS public.contract_finding (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL,
    run_item_id BIGINT NOT NULL,
    json_path VARCHAR(512) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    drift_type VARCHAR(64) NOT NULL,
    expected TEXT,
    actual TEXT,
    message TEXT NOT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_contract_finding_run ON public.contract_finding(run_id);
CREATE INDEX IF NOT EXISTS idx_contract_finding_item ON public.contract_finding(run_item_id);

COMMIT;
