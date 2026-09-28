-- 变更影响雷达 / Git 行级血缘（PostgreSQL，幂等）

BEGIN;

ALTER TABLE public.precise_analysis
    ADD COLUMN IF NOT EXISTS source_type VARCHAR(32);

ALTER TABLE public.precise_analysis
    ADD COLUMN IF NOT EXISTS source_ref VARCHAR(1024);

ALTER TABLE public.precise_analysis
    ADD COLUMN IF NOT EXISTS commit_id VARCHAR(128);

ALTER TABLE public.precise_analysis
    ADD COLUMN IF NOT EXISTS must_test_assets JSONB NOT NULL DEFAULT '{}'::jsonb;

COMMENT ON COLUMN public.precise_analysis.source_type IS 'manual_commit/git_url/mr_url/radar';
COMMENT ON COLUMN public.precise_analysis.source_ref IS '原始 Git URL 或外部单号';
COMMENT ON COLUMN public.precise_analysis.commit_id IS '解析出的目标 commit';
COMMENT ON COLUMN public.precise_analysis.must_test_assets IS '契约/巡检等深链资产 JSON';

CREATE TABLE IF NOT EXISTS public.precise_lineage_item (
    id BIGSERIAL PRIMARY KEY,
    analysis_id BIGINT NOT NULL,
    file_path VARCHAR(1024) NOT NULL,
    modified_row TEXT NOT NULL,
    row_kind VARCHAR(32) NOT NULL DEFAULT 'deleted',
    histories JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_delete SMALLINT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_precise_lineage_analysis
    ON public.precise_lineage_item(analysis_id, is_delete);

COMMENT ON TABLE public.precise_lineage_item IS '变更行级 Git pickaxe 血缘';
COMMENT ON COLUMN public.precise_lineage_item.modified_row IS '用于 git log -S 的有效代码行/锚定行';
COMMENT ON COLUMN public.precise_lineage_item.row_kind IS 'deleted/context_for_add';
COMMENT ON COLUMN public.precise_lineage_item.histories IS '历史提交列表 JSON';

COMMIT;
