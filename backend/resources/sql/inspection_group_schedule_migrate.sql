-- ============================================================
-- 巡检组级调度/通知字段迁移（PostgreSQL，幂等）
-- 将任务上的 schedule/notify 上收到所属组（同组取第一条非空）
-- ============================================================

BEGIN;

-- 1. inspection_group 增加调度与通知字段
ALTER TABLE public.inspection_group
    ADD COLUMN IF NOT EXISTS schedule_type VARCHAR(32) NOT NULL DEFAULT 'manual';

ALTER TABLE public.inspection_group
    ADD COLUMN IF NOT EXISTS cron_expression VARCHAR(128);

ALTER TABLE public.inspection_group
    ADD COLUMN IF NOT EXISTS interval_seconds INT;

ALTER TABLE public.inspection_group
    ADD COLUMN IF NOT EXISTS notify_type VARCHAR(128);

ALTER TABLE public.inspection_group
    ADD COLUMN IF NOT EXISTS notify_webhook VARCHAR(512);

ALTER TABLE public.inspection_group
    ADD COLUMN IF NOT EXISTS last_run_at TIMESTAMP;

-- 2. 组级执行允许 task_id 为空
ALTER TABLE public.inspection_execution
    ALTER COLUMN task_id DROP NOT NULL;

-- 3. 从任务上收调度/通知到组（仅当组仍为 manual 且无 webhook 时）
UPDATE public.inspection_group g
SET
    schedule_type = COALESCE(t.schedule_type, g.schedule_type),
    cron_expression = COALESCE(t.cron_expression, g.cron_expression),
    interval_seconds = COALESCE(t.interval_seconds, g.interval_seconds),
    notify_type = COALESCE(NULLIF(t.notify_type, ''), g.notify_type),
    notify_webhook = COALESCE(NULLIF(t.notify_webhook, ''), g.notify_webhook)
FROM (
    SELECT DISTINCT ON (group_id)
        group_id,
        schedule_type,
        cron_expression,
        interval_seconds,
        notify_type,
        notify_webhook
    FROM public.inspection_task
    WHERE is_delete = 0
      AND (
          schedule_type IN ('cron', 'interval')
          OR (notify_type IS NOT NULL AND notify_type <> '')
          OR (notify_webhook IS NOT NULL AND notify_webhook <> '')
      )
    ORDER BY group_id,
             CASE WHEN schedule_type IN ('cron', 'interval') THEN 0 ELSE 1 END,
             id ASC
) t
WHERE g.id = t.group_id
  AND g.is_delete = 0
  AND (
      g.schedule_type = 'manual'
      OR g.notify_webhook IS NULL
      OR g.notify_webhook = ''
  );

COMMIT;
