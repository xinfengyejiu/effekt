BEGIN;

CREATE TABLE IF NOT EXISTS public.project_code_prd_config (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    repo_url VARCHAR(512) NOT NULL,
    default_branch VARCHAR(128),
    model_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.project_code_prd_config IS '项目代码转PRD配置';
COMMENT ON COLUMN public.project_code_prd_config.project_id IS '项目ID';
COMMENT ON COLUMN public.project_code_prd_config.repo_url IS 'Git仓库地址';
COMMENT ON COLUMN public.project_code_prd_config.default_branch IS '默认分支';
COMMENT ON COLUMN public.project_code_prd_config.model_config IS '大模型扩展配置';

CREATE UNIQUE INDEX IF NOT EXISTS uk_project_code_prd_config_project ON public.project_code_prd_config(project_id, is_delete);
CREATE INDEX IF NOT EXISTS idx_project_code_prd_config_project_id ON public.project_code_prd_config(project_id);

CREATE TABLE IF NOT EXISTS public.project_code_prd_record (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    config_id BIGINT,
    repo_url VARCHAR(512) NOT NULL,
    branch VARCHAR(128) NOT NULL,
    title VARCHAR(256),
    status SMALLINT NOT NULL DEFAULT 0,
    prd_markdown TEXT,
    summary TEXT,
    error_message TEXT,
    created_by BIGINT,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.project_code_prd_record IS '项目代码转PRD生成记录';
COMMENT ON COLUMN public.project_code_prd_record.status IS '0:待生成 1:生成中 2:成功 3:失败';
COMMENT ON COLUMN public.project_code_prd_record.prd_markdown IS 'PRD Markdown内容，包含流程图或时序图';

CREATE INDEX IF NOT EXISTS idx_project_code_prd_record_project_id ON public.project_code_prd_record(project_id);
CREATE INDEX IF NOT EXISTS idx_project_code_prd_record_config_id ON public.project_code_prd_record(config_id);
CREATE INDEX IF NOT EXISTS idx_project_code_prd_record_status ON public.project_code_prd_record(status);

COMMIT;
