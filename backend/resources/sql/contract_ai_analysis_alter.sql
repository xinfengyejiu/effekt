-- 契约 AI 分析字段（幂等）
ALTER TABLE public.contract_run_item
    ADD COLUMN IF NOT EXISTS ai_analysis JSONB;

COMMENT ON COLUMN public.contract_run_item.ai_analysis IS 'AI漂移分析';
