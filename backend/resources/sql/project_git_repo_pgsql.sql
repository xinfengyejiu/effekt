-- Multi git repos per project (idempotent).

BEGIN;

CREATE TABLE IF NOT EXISTS public.project_git_repo (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    name VARCHAR(128) NOT NULL DEFAULT '',
    repo_url VARCHAR(512) NOT NULL,
    default_branch VARCHAR(128) NOT NULL DEFAULT 'master',
    role_tag VARCHAR(64) NOT NULL DEFAULT 'backend',
    is_primary SMALLINT NOT NULL DEFAULT 0,
    sort_no INTEGER NOT NULL DEFAULT 0,
    enabled SMALLINT NOT NULL DEFAULT 1,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.project_git_repo IS '项目代码仓库（支持多仓库：微服务/前后端分离）';
COMMENT ON COLUMN public.project_git_repo.role_tag IS 'backend/frontend/service/other';
COMMENT ON COLUMN public.project_git_repo.is_primary IS '1=主仓，兼容代码转PRD默认仓';

CREATE INDEX IF NOT EXISTS idx_project_git_repo_project
ON public.project_git_repo(project_id, enabled, sort_no)
WHERE is_delete = 0;

-- Migrate legacy single config into project_git_repo once
INSERT INTO public.project_git_repo (
    project_id, name, repo_url, default_branch, role_tag, is_primary, sort_no, enabled, is_delete, created_time, updated_time
)
SELECT
    c.project_id,
    '默认仓库',
    c.repo_url,
    COALESCE(NULLIF(TRIM(c.default_branch), ''), 'master'),
    'backend',
    1,
    0,
    1,
    0,
    COALESCE(c.created_time, NOW()),
    COALESCE(c.updated_time, NOW())
FROM public.project_code_prd_config c
WHERE c.is_delete = 0
  AND COALESCE(TRIM(c.repo_url), '') <> ''
  AND NOT EXISTS (
      SELECT 1 FROM public.project_git_repo r
      WHERE r.project_id = c.project_id AND r.is_delete = 0
  );

COMMIT;
