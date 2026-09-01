-- ============================================================
-- 巡检系统数据库表结构
-- ============================================================

BEGIN;

-- 1. 巡检组
CREATE TABLE IF NOT EXISTS public.inspection_group (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    project_id BIGINT NOT NULL,
    description TEXT,
    enabled SMALLINT NOT NULL DEFAULT 1,
    schedule_type VARCHAR(32) NOT NULL DEFAULT 'manual',  -- cron/interval/manual
    cron_expression VARCHAR(128),
    interval_seconds INT,
    notify_type VARCHAR(128),  -- wechat_work,dingtalk,feishu
    notify_webhook VARCHAR(512),
    last_run_at TIMESTAMP,
    created_by BIGINT,
    is_delete INT NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inspection_group_project_id ON public.inspection_group(project_id);
CREATE INDEX IF NOT EXISTS idx_inspection_group_enabled ON public.inspection_group(enabled);

-- 自动更新 updated_time
CREATE OR REPLACE FUNCTION public.set_inspection_group_updated_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_time = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_inspection_group_updated_time
BEFORE UPDATE ON public.inspection_group
FOR EACH ROW EXECUTE FUNCTION public.set_inspection_group_updated_time();

-- 2. 巡检任务
CREATE TABLE IF NOT EXISTS public.inspection_task (
    id BIGSERIAL PRIMARY KEY,
    group_id BIGINT NOT NULL,
    project_id BIGINT NOT NULL,
    name VARCHAR(128) NOT NULL,
    task_type VARCHAR(32) NOT NULL,  -- auto_case/api/sql/script/mixed
    schedule_type VARCHAR(32) NOT NULL DEFAULT 'manual',  -- cron/interval/manual
    cron_expression VARCHAR(128),
    interval_seconds INT,
    env_code VARCHAR(32),
    enabled SMALLINT NOT NULL DEFAULT 1,
    notify_type VARCHAR(128),  -- wechat_work,dingtalk,feishu
    notify_webhook VARCHAR(512),
    notify_config JSONB DEFAULT '{}'::jsonb,
    ext JSONB DEFAULT '{}'::jsonb,
    created_by BIGINT,
    updated_by BIGINT,
    is_delete INT NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inspection_task_group_id ON public.inspection_task(group_id);
CREATE INDEX IF NOT EXISTS idx_inspection_task_project_id ON public.inspection_task(project_id);
CREATE INDEX IF NOT EXISTS idx_inspection_task_enabled ON public.inspection_task(enabled);

CREATE OR REPLACE FUNCTION public.set_inspection_task_updated_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_time = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_inspection_task_updated_time
BEFORE UPDATE ON public.inspection_task
FOR EACH ROW EXECUTE FUNCTION public.set_inspection_task_updated_time();

-- 3. 巡检项
CREATE TABLE IF NOT EXISTS public.inspection_item (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    item_type VARCHAR(32) NOT NULL,  -- auto_case/api/sql/script
    name VARCHAR(128) NOT NULL,
    ref_id BIGINT,  -- 关联的自动化用例 ID (仅 auto_case 类型)
    sort_order INT NOT NULL DEFAULT 0,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    timeout_seconds INT NOT NULL DEFAULT 30,
    enabled SMALLINT NOT NULL DEFAULT 1,
    is_delete INT NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inspection_item_task_id ON public.inspection_item(task_id);
CREATE INDEX IF NOT EXISTS idx_inspection_item_item_type ON public.inspection_item(item_type);

CREATE OR REPLACE FUNCTION public.set_inspection_item_updated_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_time = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_inspection_item_updated_time
BEFORE UPDATE ON public.inspection_item
FOR EACH ROW EXECUTE FUNCTION public.set_inspection_item_updated_time();

-- 4. 数据库连接配置
CREATE TABLE IF NOT EXISTS public.inspection_db_config (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    name VARCHAR(128) NOT NULL,
    db_type VARCHAR(32) NOT NULL,  -- postgresql/mysql/sqlserver/oracle
    host VARCHAR(256) NOT NULL,
    port INT NOT NULL,
    database_name VARCHAR(128) NOT NULL,
    username VARCHAR(128) NOT NULL,
    password VARCHAR(256) NOT NULL,  -- 加密存储
    extra_params JSONB DEFAULT '{}'::jsonb,
    enabled SMALLINT NOT NULL DEFAULT 1,
    is_delete INT NOT NULL DEFAULT 0,
    created_by BIGINT,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inspection_db_config_project_id ON public.inspection_db_config(project_id);

CREATE OR REPLACE FUNCTION public.set_inspection_db_config_updated_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_time = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_inspection_db_config_updated_time
BEFORE UPDATE ON public.inspection_db_config
FOR EACH ROW EXECUTE FUNCTION public.set_inspection_db_config_updated_time();

-- 5. 巡检执行记录
CREATE TABLE IF NOT EXISTS public.inspection_execution (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT,  -- 组级执行可为空
    group_id BIGINT NOT NULL,
    project_id BIGINT NOT NULL,
    trigger_type VARCHAR(32) NOT NULL,  -- scheduled/manual
    status SMALLINT NOT NULL DEFAULT 0,  -- 0=待执行 1=执行中 2=全部通过 3=部分失败 4=全部失败 5=异常
    total_count INT NOT NULL DEFAULT 0,
    pass_count INT NOT NULL DEFAULT 0,
    fail_count INT NOT NULL DEFAULT 0,
    error_count INT NOT NULL DEFAULT 0,
    duration_ms BIGINT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    notify_status SMALLINT NOT NULL DEFAULT 0,  -- 0=未通知 1=已通知 2=通知失败
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inspection_execution_task_id ON public.inspection_execution(task_id);
CREATE INDEX IF NOT EXISTS idx_inspection_execution_group_id ON public.inspection_execution(group_id);
CREATE INDEX IF NOT EXISTS idx_inspection_execution_project_id ON public.inspection_execution(project_id);
CREATE INDEX IF NOT EXISTS idx_inspection_execution_status ON public.inspection_execution(status);
CREATE INDEX IF NOT EXISTS idx_inspection_execution_created_time ON public.inspection_execution(created_time);

-- 6. 巡检项执行结果
CREATE TABLE IF NOT EXISTS public.inspection_execution_item (
    id BIGSERIAL PRIMARY KEY,
    execution_id BIGINT NOT NULL,
    item_id BIGINT NOT NULL,
    item_type VARCHAR(32) NOT NULL,
    status SMALLINT NOT NULL DEFAULT 0,  -- 0=待执行 1=执行中 2=通过 3=失败 4=异常
    duration_ms BIGINT,
    result JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inspection_execution_item_execution_id ON public.inspection_execution_item(execution_id);
CREATE INDEX IF NOT EXISTS idx_inspection_execution_item_item_id ON public.inspection_execution_item(item_id);

-- 7. 巡检统计快照 (按日聚合，可选)
CREATE TABLE IF NOT EXISTS public.inspection_daily_summary (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    group_id BIGINT,
    summary_date DATE NOT NULL,
    total_executions INT NOT NULL DEFAULT 0,
    total_items INT NOT NULL DEFAULT 0,
    pass_items INT NOT NULL DEFAULT 0,
    fail_items INT NOT NULL DEFAULT 0,
    error_items INT NOT NULL DEFAULT 0,
    avg_duration_ms BIGINT,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, group_id, summary_date)
);

CREATE INDEX IF NOT EXISTS idx_inspection_daily_summary_project_id ON public.inspection_daily_summary(project_id);
CREATE INDEX IF NOT EXISTS idx_inspection_daily_summary_summary_date ON public.inspection_daily_summary(summary_date);

COMMIT;
