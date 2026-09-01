CREATE TABLE IF NOT EXISTS case_generation_checkpoint (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    document_scope_key VARCHAR(128) NOT NULL,
    document_ids BIGINT[] DEFAULT '{}'::BIGINT[],
    template_key VARCHAR(128) NOT NULL,
    task_key VARCHAR(128) NOT NULL,
    task_index INTEGER NOT NULL,
    chunk_index INTEGER DEFAULT 0,
    chunk_title VARCHAR(512),
    agent_name VARCHAR(255),
    skill_id BIGINT,
    skill_name VARCHAR(255),
    status VARCHAR(32) DEFAULT 'pending',
    imported_count INTEGER DEFAULT 0,
    skipped_count INTEGER DEFAULT 0,
    error_message TEXT,
    generation_id VARCHAR(64),
    created_by BIGINT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_case_generation_checkpoint_scope
    ON case_generation_checkpoint(project_id, document_scope_key, template_key);

CREATE UNIQUE INDEX IF NOT EXISTS uk_case_generation_checkpoint_task
    ON case_generation_checkpoint(project_id, document_scope_key, template_key, task_key);
