-- 对话式质量助手表结构（PostgreSQL，幂等）

BEGIN;

CREATE TABLE IF NOT EXISTS public.qa_assistant_session (
    id BIGSERIAL PRIMARY KEY,
    session_no VARCHAR(64) NOT NULL,
    user_id BIGINT NOT NULL,
    product_id BIGINT,
    project_id BIGINT,
    title VARCHAR(255),
    context JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_delete INT NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_qa_assistant_session_no UNIQUE (session_no)
);

CREATE INDEX IF NOT EXISTS idx_qa_assistant_session_user
    ON public.qa_assistant_session(user_id, is_delete, updated_time DESC);
CREATE INDEX IF NOT EXISTS idx_qa_assistant_session_project
    ON public.qa_assistant_session(project_id, is_delete);

CREATE TABLE IF NOT EXISTS public.qa_assistant_message (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    intent VARCHAR(64),
    tool_trace JSONB NOT NULL DEFAULT '[]'::jsonb,
    answer_payload JSONB,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qa_assistant_message_session
    ON public.qa_assistant_message(session_id, id ASC);

COMMIT;
