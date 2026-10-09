-- Per-user AI model preference (idempotent).

BEGIN;

CREATE TABLE IF NOT EXISTS public.user_ai_preference (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    provider VARCHAR(64) NOT NULL DEFAULT '',
    model VARCHAR(128) NOT NULL DEFAULT '',
    api_base VARCHAR(512),
    api_key VARCHAR(512),
    use_custom SMALLINT NOT NULL DEFAULT 0,
    temperature NUMERIC(4,2),
    max_tokens INTEGER,
    extra JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.user_ai_preference IS '用户个人中心-AI模型偏好';

CREATE UNIQUE INDEX IF NOT EXISTS uk_user_ai_preference_user
ON public.user_ai_preference(user_id)
WHERE is_delete = 0;

COMMIT;
