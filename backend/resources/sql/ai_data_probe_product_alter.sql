-- Add product scope to ai_data_probe_connection (idempotent).

BEGIN;

ALTER TABLE public.ai_data_probe_connection
    ADD COLUMN IF NOT EXISTS product_id BIGINT;

ALTER TABLE public.ai_data_probe_connection
    ADD COLUMN IF NOT EXISTS product_name VARCHAR(128);

COMMENT ON COLUMN public.ai_data_probe_connection.product_id IS '所属产品';
COMMENT ON COLUMN public.ai_data_probe_connection.product_name IS '产品名称冗余';

CREATE INDEX IF NOT EXISTS idx_ai_data_probe_connection_product
ON public.ai_data_probe_connection(product_id, project_id)
WHERE is_delete = 0;

COMMIT;
