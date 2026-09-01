-- HTML report upload can be associated with product/project only.
ALTER TABLE public.report
    ALTER COLUMN plan_id DROP NOT NULL;
