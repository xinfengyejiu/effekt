-- Weak network profile + session (PostgreSQL, idempotent).

BEGIN;

CREATE TABLE IF NOT EXISTS public.weak_network_profile (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT,
    product_name VARCHAR(128),
    project_id BIGINT,
    project_name VARCHAR(128),
    name VARCHAR(128) NOT NULL,
    preset_code VARCHAR(64) NOT NULL DEFAULT 'custom',
    latency_ms INTEGER NOT NULL DEFAULT 0,
    bandwidth_kbps INTEGER NOT NULL DEFAULT 0,
    loss_percent NUMERIC(5,2) NOT NULL DEFAULT 0,
    disconnect_rules JSONB NOT NULL DEFAULT '{}'::jsonb,
    remark TEXT,
    enabled SMALLINT NOT NULL DEFAULT 1,
    is_system SMALLINT NOT NULL DEFAULT 0,
    created_by BIGINT,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.weak_network_profile IS '弱网画像（预设/自定义）';
COMMENT ON COLUMN public.weak_network_profile.preset_code IS 'subway/elevator/poor_wifi/custom';
COMMENT ON COLUMN public.weak_network_profile.bandwidth_kbps IS '0 表示不限速';
COMMENT ON COLUMN public.weak_network_profile.disconnect_rules IS '如 {"cycle_sec":30,"down_sec":5}';

CREATE TABLE IF NOT EXISTS public.weak_network_session (
    id BIGSERIAL PRIMARY KEY,
    session_no VARCHAR(64) NOT NULL UNIQUE,
    profile_id BIGINT NOT NULL,
    profile_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    product_id BIGINT,
    project_id BIGINT,
    device_serial VARCHAR(255),
    proxy_port INTEGER NOT NULL DEFAULT 18888,
    pack_hash VARCHAR(128),
    status VARCHAR(32) NOT NULL DEFAULT 'created',
    expires_at TIMESTAMP,
    created_by BIGINT,
    remark TEXT,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.weak_network_session IS '弱网下载会话（审计；非设备实时态）';

CREATE INDEX IF NOT EXISTS idx_weak_network_profile_scope
ON public.weak_network_profile(product_id, project_id, enabled)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_weak_network_session_created
ON public.weak_network_session(created_time DESC)
WHERE is_delete = 0;

CREATE INDEX IF NOT EXISTS idx_weak_network_session_profile
ON public.weak_network_session(profile_id)
WHERE is_delete = 0;

-- Seed system presets (global scope: product/project null)
INSERT INTO public.weak_network_profile (
    product_id, project_id, name, preset_code, latency_ms, bandwidth_kbps, loss_percent,
    disconnect_rules, remark, enabled, is_system, is_delete, created_time, updated_time
)
SELECT NULL, NULL, v.name, v.preset_code, v.latency_ms, v.bandwidth_kbps, v.loss_percent,
       v.disconnect_rules::jsonb, v.remark, 1, 1, 0, NOW(), NOW()
FROM (VALUES
    ('地铁通勤', 'subway', 800, 300, 3.00, '{}', '高延迟+低带宽+轻丢包'),
    ('电梯断连', 'elevator', 200, 0, 0.00, '{"cycle_sec":30,"down_sec":5}', '周期性短断网'),
    ('差Wi-Fi', 'poor_wifi', 400, 150, 5.00, '{}', '低带宽+抖动丢包')
) AS v(name, preset_code, latency_ms, bandwidth_kbps, loss_percent, disconnect_rules, remark)
WHERE NOT EXISTS (
    SELECT 1 FROM public.weak_network_profile p
    WHERE p.preset_code = v.preset_code AND p.is_system = 1 AND p.is_delete = 0
);

INSERT INTO public.sys_permission (code, name, module, action, description, status, is_delete, created_time, updated_time) VALUES
('weak_network:list', '弱网画像列表', 'weak_network', 'list', '查看弱网画像与会话', 1, 0, NOW(), NOW()),
('weak_network:manage', '弱网画像管理', 'weak_network', 'manage', '创建/编辑弱网画像', 1, 0, NOW(), NOW()),
('weak_network:download', '弱网包下载', 'weak_network', 'download', '创建会话并下载弱网脚本包', 1, 0, NOW(), NOW())
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    module = EXCLUDED.module,
    action = EXCLUDED.action,
    description = EXCLUDED.description,
    status = 1,
    is_delete = 0,
    updated_time = NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT parent.id, '弱网配置', 'weak_network', 2, '/weak-network', 'WeakNetwork/ProfileList', 'el-icon-connection', 'weak_network:list', 50, 1, 1, 0, NOW(), NOW()
FROM public.sys_menu parent
WHERE parent.code = 'mobile_automation' AND parent.is_delete = 0
ON CONFLICT (code) DO UPDATE SET
    parent_id = EXCLUDED.parent_id,
    name = EXCLUDED.name,
    type = EXCLUDED.type,
    path = EXCLUDED.path,
    component = EXCLUDED.component,
    icon = EXCLUDED.icon,
    permission_code = EXCLUDED.permission_code,
    sort = EXCLUDED.sort,
    visible = 1,
    status = 1,
    is_delete = 0,
    updated_time = NOW();

-- Fallback if mobile_automation menu missing: attach to root
INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT 0, '弱网配置', 'weak_network', 2, '/weak-network', 'WeakNetwork/ProfileList', 'el-icon-connection', 'weak_network:list', 95, 1, 1, 0, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM public.sys_menu WHERE code = 'weak_network' AND is_delete = 0);

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT m.id, v.name, v.code, 3, '', '', '', v.permission_code, v.sort, 1, 1, 0, NOW(), NOW()
FROM public.sys_menu m
CROSS JOIN (VALUES
    ('管理', 'weak_network_manage', 'weak_network:manage', 1),
    ('下载', 'weak_network_download', 'weak_network:download', 2)
) AS v(name, code, permission_code, sort)
WHERE m.code = 'weak_network'
ON CONFLICT (code) DO UPDATE SET
    parent_id = EXCLUDED.parent_id,
    name = EXCLUDED.name,
    type = EXCLUDED.type,
    permission_code = EXCLUDED.permission_code,
    sort = EXCLUDED.sort,
    visible = 1,
    status = 1,
    is_delete = 0,
    updated_time = NOW();

INSERT INTO public.sys_role_permission (role_id, permission_id, is_delete, created_time)
SELECT r.id, p.id, 0, NOW()
FROM public.sys_role r
CROSS JOIN public.sys_permission p
WHERE r.status = 1 AND r.is_delete = 0
  AND p.module = 'weak_network' AND p.is_delete = 0
  AND NOT EXISTS (
      SELECT 1 FROM public.sys_role_permission rp
      WHERE rp.role_id = r.id AND rp.permission_id = p.id AND rp.is_delete = 0
  );

INSERT INTO public.sys_role_menu (role_id, menu_id, is_delete, created_time)
SELECT r.id, m.id, 0, NOW()
FROM public.sys_role r
CROSS JOIN public.sys_menu m
WHERE r.status = 1 AND r.is_delete = 0
  AND (m.code = 'weak_network' OR m.code LIKE 'weak_network_%')
  AND m.is_delete = 0
  AND NOT EXISTS (
      SELECT 1 FROM public.sys_role_menu rm
      WHERE rm.role_id = r.id AND rm.menu_id = m.id AND rm.is_delete = 0
  );

SELECT setval(pg_get_serial_sequence('public.sys_permission', 'id'), COALESCE((SELECT MAX(id) FROM public.sys_permission), 1));
SELECT setval(pg_get_serial_sequence('public.sys_menu', 'id'), COALESCE((SELECT MAX(id) FROM public.sys_menu), 1));

COMMIT;
