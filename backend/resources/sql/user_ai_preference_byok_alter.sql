-- Extend user_ai_preference with BYOK fields (idempotent).

BEGIN;

ALTER TABLE public.user_ai_preference
    ADD COLUMN IF NOT EXISTS api_base VARCHAR(512);

ALTER TABLE public.user_ai_preference
    ADD COLUMN IF NOT EXISTS api_key VARCHAR(512);

ALTER TABLE public.user_ai_preference
    ADD COLUMN IF NOT EXISTS use_custom SMALLINT NOT NULL DEFAULT 0;

COMMENT ON COLUMN public.user_ai_preference.api_base IS '用户自定义 API Base URL';
COMMENT ON COLUMN public.user_ai_preference.api_key IS '用户自定义 API Key（仅本人可见，接口回显脱敏）';
COMMENT ON COLUMN public.user_ai_preference.use_custom IS '1=使用个人供应商配置；0=仅切换模型名走平台密钥';

COMMIT;
