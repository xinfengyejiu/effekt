-- Android 移动自动化首期建表脚本（PostgreSQL）
-- 仅新增移动自动化表，不修改既有 Jenkins 自动化表。

BEGIN;

CREATE TABLE IF NOT EXISTS public.mobile_execution_config (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    project_id BIGINT NOT NULL,
    mobile_app_id BIGINT NOT NULL,
    device_serial VARCHAR(255) NOT NULL,
    env_code VARCHAR(32) NOT NULL,
    script_selector VARCHAR(512) NOT NULL,
    remark TEXT,
    enabled SMALLINT NOT NULL DEFAULT 1,
    created_by BIGINT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.mobile_execution_config_case (
    id BIGSERIAL PRIMARY KEY,
    config_id BIGINT NOT NULL,
    case_id BIGINT NOT NULL,
    run_order INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT uk_mobile_execution_config_case UNIQUE (config_id, case_id)
);

CREATE INDEX IF NOT EXISTS idx_mobile_execution_config_project ON public.mobile_execution_config(project_id, enabled);

CREATE TABLE IF NOT EXISTS public.mobile_device (
    id BIGSERIAL PRIMARY KEY,
    serial_no VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(128),
    device_group VARCHAR(128),
    remark TEXT,
    brand VARCHAR(128),
    model VARCHAR(255),
    android_version VARCHAR(64),
    sdk_version VARCHAR(32),
    screen_width INTEGER,
    screen_height INTEGER,
    density VARCHAR(64),
    adb_status VARCHAR(32) NOT NULL DEFAULT 'unknown',
    usage_status VARCHAR(32) NOT NULL DEFAULT 'idle',
    last_seen_time TIMESTAMP NULL,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.mobile_app (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    name VARCHAR(128) NOT NULL,
    package_name VARCHAR(255) NOT NULL,
    launch_activity VARCHAR(255),
    app_type VARCHAR(32) NOT NULL DEFAULT 'android',
    apk_path VARCHAR(512),
    version_name VARCHAR(64),
    version_code VARCHAR(64),
    default_capabilities JSONB NOT NULL DEFAULT '{}'::jsonb,
    install_before_run SMALLINT NOT NULL DEFAULT 0,
    clear_data_before_run SMALLINT NOT NULL DEFAULT 0,
    enabled SMALLINT NOT NULL DEFAULT 1,
    created_by BIGINT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_mobile_app_project_name UNIQUE (project_id, name)
);

CREATE TABLE IF NOT EXISTS public.mobile_execution_step (
    id BIGSERIAL PRIMARY KEY,
    execution_id BIGINT NOT NULL,
    execution_case_id BIGINT NULL,
    step_no INTEGER NOT NULL,
    instruction TEXT,
    action_type VARCHAR(32),
    action_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    locator_strategy VARCHAR(32),
    target_element JSONB NOT NULL DEFAULT '{}'::jsonb,
    page_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    before_screenshot_artifact_id BIGINT NULL,
    after_screenshot_artifact_id BIGINT NULL,
    ui_xml_artifact_id BIGINT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    duration_ms INTEGER NULL,
    error_message TEXT,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_mobile_execution_step UNIQUE (execution_id, execution_case_id, step_no)
);

CREATE TABLE IF NOT EXISTS public.mobile_artifact (
    id BIGSERIAL PRIMARY KEY,
    execution_id BIGINT NOT NULL,
    execution_case_id BIGINT NULL,
    step_id BIGINT NULL,
    artifact_type VARCHAR(64) NOT NULL,
    relative_path VARCHAR(1024) NOT NULL,
    content_type VARCHAR(128),
    size_bytes BIGINT NULL,
    checksum VARCHAR(128),
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mobile_device_status ON public.mobile_device(adb_status, usage_status);
CREATE INDEX IF NOT EXISTS idx_mobile_app_project ON public.mobile_app(project_id, enabled);
CREATE INDEX IF NOT EXISTS idx_mobile_step_execution ON public.mobile_execution_step(execution_id, execution_case_id, step_no);
CREATE INDEX IF NOT EXISTS idx_mobile_artifact_execution ON public.mobile_artifact(execution_id, execution_case_id, artifact_type);

CREATE OR REPLACE FUNCTION public.set_mobile_automation_updated_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_time = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_mobile_device_updated_time ON public.mobile_device;
CREATE TRIGGER trg_mobile_device_updated_time BEFORE UPDATE ON public.mobile_device
FOR EACH ROW EXECUTE FUNCTION public.set_mobile_automation_updated_time();

DROP TRIGGER IF EXISTS trg_mobile_app_updated_time ON public.mobile_app;
CREATE TRIGGER trg_mobile_app_updated_time BEFORE UPDATE ON public.mobile_app
FOR EACH ROW EXECUTE FUNCTION public.set_mobile_automation_updated_time();

DROP TRIGGER IF EXISTS trg_mobile_execution_step_updated_time ON public.mobile_execution_step;
CREATE TRIGGER trg_mobile_execution_step_updated_time BEFORE UPDATE ON public.mobile_execution_step
FOR EACH ROW EXECUTE FUNCTION public.set_mobile_automation_updated_time();

COMMIT;
