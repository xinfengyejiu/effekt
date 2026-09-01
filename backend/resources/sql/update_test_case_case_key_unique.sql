-- 调整 test_case 用例编号唯一约束
-- 仅约束未删除用例，允许软删除后的 case_key 被重新生成和使用。

BEGIN;

ALTER TABLE public.test_case
    DROP CONSTRAINT IF EXISTS uk_test_case_project_case_key;

DROP INDEX IF EXISTS public.uk_test_case_project_case_key;
DROP INDEX IF EXISTS public.uk_test_case_project_case_key_active;

CREATE UNIQUE INDEX uk_test_case_project_case_key_active
    ON public.test_case(project_id, case_key)
    WHERE is_delete = 0;

COMMIT;
