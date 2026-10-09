-- AI 场景造数：扩展 data_builder（PostgreSQL，幂等）

BEGIN;

ALTER TABLE public.data_builder
    ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE public.data_builder
    ADD COLUMN IF NOT EXISTS source VARCHAR(32) NOT NULL DEFAULT 'manual';

ALTER TABLE public.data_builder
    ADD COLUMN IF NOT EXISTS scene_key VARCHAR(128);

COMMENT ON COLUMN public.data_builder.tags IS '场景标签 JSON 数组';
COMMENT ON COLUMN public.data_builder.source IS 'manual/ai/saved_from_task';
COMMENT ON COLUMN public.data_builder.scene_key IS '可选场景键，便于深链';

CREATE INDEX IF NOT EXISTS idx_data_builder_scene_key
    ON public.data_builder(project_id, scene_key)
    WHERE is_delete = 0;

COMMIT;
