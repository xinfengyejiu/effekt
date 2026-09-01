-- Rename system management tables to sys_* names.
-- PostgreSQL, idempotent.

DO $$
BEGIN
    IF to_regclass('public.sys_user') IS NULL AND to_regclass('public.user') IS NOT NULL THEN
        ALTER TABLE public."user" RENAME TO sys_user;
    END IF;

    IF to_regclass('public.sys_user_role') IS NULL AND to_regclass('public.user_role') IS NOT NULL THEN
        ALTER TABLE public.user_role RENAME TO sys_user_role;
    END IF;

    IF to_regclass('public.sys_role') IS NULL AND to_regclass('public.role') IS NOT NULL THEN
        ALTER TABLE public.role RENAME TO sys_role;
    END IF;

    IF to_regclass('public.sys_permission') IS NULL AND to_regclass('public.permission') IS NOT NULL THEN
        ALTER TABLE public.permission RENAME TO sys_permission;
    END IF;

    IF to_regclass('public.sys_role_permission') IS NULL AND to_regclass('public.role_permission') IS NOT NULL THEN
        ALTER TABLE public.role_permission RENAME TO sys_role_permission;
    END IF;

    IF to_regclass('public.sys_menu') IS NULL AND to_regclass('public.menu') IS NOT NULL THEN
        ALTER TABLE public.menu RENAME TO sys_menu;
    END IF;

    IF to_regclass('public.sys_role_menu') IS NULL AND to_regclass('public.role_menu') IS NOT NULL THEN
        ALTER TABLE public.role_menu RENAME TO sys_role_menu;
    END IF;
END $$;

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'sys_user',
      'sys_user_role',
      'sys_role',
      'sys_permission',
      'sys_role_permission',
      'sys_menu',
      'sys_role_menu'
  )
ORDER BY table_name;
