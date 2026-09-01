-- 智能 Mock 服务表、权限、菜单初始化脚本

BEGIN;

CREATE TABLE IF NOT EXISTS public.mock_document (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL,
    project_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    source VARCHAR(512),
    content TEXT,
    parse_status SMALLINT DEFAULT 0,
    parse_error TEXT,
    interface_count INTEGER DEFAULT 0,
    created_by BIGINT,
    is_delete INTEGER DEFAULT 0,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.mock_interface (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT,
    product_id BIGINT NOT NULL,
    project_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    path VARCHAR(512) NOT NULL,
    method VARCHAR(16) NOT NULL,
    description TEXT,
    headers_schema TEXT,
    query_schema TEXT,
    body_schema TEXT,
    response_schema TEXT,
    raw_schema TEXT,
    path_regex VARCHAR(1024),
    path_params TEXT,
    path_score INTEGER DEFAULT 0,
    status SMALLINT DEFAULT 0,
    created_by BIGINT,
    is_delete INTEGER DEFAULT 0,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.mock_scene (
    id BIGSERIAL PRIMARY KEY,
    interface_id BIGINT NOT NULL,
    scene_name VARCHAR(128) NOT NULL,
    scene_code VARCHAR(64) NOT NULL,
    http_status INTEGER DEFAULT 200,
    delay_ms INTEGER DEFAULT 0,
    request_example TEXT,
    response_template TEXT,
    response_headers TEXT,
    response_rule TEXT,
    match_rule TEXT,
    priority INTEGER DEFAULT 0,
    status SMALLINT DEFAULT 0,
    is_delete INTEGER DEFAULT 0,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.mock_call_log (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    interface_id BIGINT,
    scene_id BIGINT,
    method VARCHAR(16) NOT NULL,
    path VARCHAR(512) NOT NULL,
    request_query TEXT,
    request_body TEXT,
    response_body TEXT,
    http_status INTEGER DEFAULT 200,
    duration_ms INTEGER DEFAULT 0,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.mock_parse_issue (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL,
    issue_type VARCHAR(64) NOT NULL,
    source_fragment TEXT,
    error_message TEXT,
    suggestion TEXT,
    status SMALLINT DEFAULT 0,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mock_document_project ON public.mock_document(project_id, is_delete);
CREATE INDEX IF NOT EXISTS idx_mock_interface_project_method_path ON public.mock_interface(project_id, method, path, status, is_delete);
CREATE INDEX IF NOT EXISTS idx_mock_scene_interface ON public.mock_scene(interface_id, scene_code, status, is_delete);
CREATE INDEX IF NOT EXISTS idx_mock_call_log_project ON public.mock_call_log(project_id, created_time DESC);
CREATE INDEX IF NOT EXISTS idx_mock_parse_issue_document ON public.mock_parse_issue(document_id, status);

INSERT INTO public.sys_permission (code, name, module, action, description, status, is_delete, created_time, updated_time) VALUES
('mock:document:list', 'Mock文档列表', 'mock', 'document:list', '查看Mock文档列表', 1, 0, NOW(), NOW()),
('mock:document:import', 'Mock文档导入', 'mock', 'document:import', '导入接口文档并生成Mock草稿', 1, 0, NOW(), NOW()),
('mock:document:detail', 'Mock文档详情', 'mock', 'document:detail', '查看Mock文档详情', 1, 0, NOW(), NOW()),
('mock:interface:list', 'Mock接口列表', 'mock', 'interface:list', '查看Mock接口列表', 1, 0, NOW(), NOW()),
('mock:interface:detail', 'Mock接口详情', 'mock', 'interface:detail', '查看Mock接口详情', 1, 0, NOW(), NOW()),
('mock:interface:update', 'Mock接口更新', 'mock', 'interface:update', '更新Mock接口', 1, 0, NOW(), NOW()),
('mock:interface:enable', 'Mock接口启用', 'mock', 'interface:enable', '启用Mock接口', 1, 0, NOW(), NOW()),
('mock:interface:disable', 'Mock接口停用', 'mock', 'interface:disable', '停用Mock接口', 1, 0, NOW(), NOW()),
('mock:scene:list', 'Mock场景列表', 'mock', 'scene:list', '查看Mock场景列表', 1, 0, NOW(), NOW()),
('mock:scene:update', 'Mock场景更新', 'mock', 'scene:update', '更新Mock场景', 1, 0, NOW(), NOW()),
('mock:scene:enable', 'Mock场景启用', 'mock', 'scene:enable', '启用Mock场景', 1, 0, NOW(), NOW()),
('mock:scene:disable', 'Mock场景停用', 'mock', 'scene:disable', '停用Mock场景', 1, 0, NOW(), NOW()),
('mock:runtime:access', 'Mock运行访问', 'mock', 'runtime:access', '访问Mock Runtime', 1, 0, NOW(), NOW()),
('mock:log:list', 'Mock日志列表', 'mock', 'log:list', '查看Mock调用日志', 1, 0, NOW(), NOW()),
('mock:parse-issue:list', 'Mock解析问题列表', 'mock', 'parse-issue:list', '查看Mock解析问题', 1, 0, NOW(), NOW())
ON CONFLICT (code) DO UPDATE SET name=EXCLUDED.name, module=EXCLUDED.module, action=EXCLUDED.action, description=EXCLUDED.description, status=EXCLUDED.status, is_delete=0, updated_time=NOW();

INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
VALUES (NULL, 'mock服务', 'mock_service', 1, '/mock', 'mock/index', 'api', 'mock:interface:list', 35, 1, 1, 0, NOW(), NOW())
ON CONFLICT (code) DO UPDATE SET parent_id=NULL, name=EXCLUDED.name, type=EXCLUDED.type, path=EXCLUDED.path, component=EXCLUDED.component, permission_code=EXCLUDED.permission_code, sort=EXCLUDED.sort, visible=1, status=1, is_delete=0, updated_time=NOW();

WITH parent_menu AS (
    SELECT id FROM public.sys_menu WHERE code = 'mock_service' AND is_delete = 0
)
INSERT INTO public.sys_menu (parent_id, name, code, type, path, component, icon, permission_code, sort, visible, status, is_delete, created_time, updated_time)
SELECT id, 'Mock文档', 'mock_document', 2, '/mock/document', 'mock/document/index', 'file-text', 'mock:document:list', 10, 1, 1, 0, NOW(), NOW() FROM parent_menu
UNION ALL
SELECT id, 'Mock接口', 'mock_interface', 2, '/mock/interface', 'mock/interface/index', 'api', 'mock:interface:list', 20, 1, 1, 0, NOW(), NOW() FROM parent_menu
UNION ALL
SELECT id, 'Mock调用日志', 'mock_log', 2, '/mock/log', 'mock/log/index', 'history', 'mock:log:list', 30, 1, 1, 0, NOW(), NOW() FROM parent_menu
ON CONFLICT (code) DO UPDATE SET name=EXCLUDED.name, path=EXCLUDED.path, component=EXCLUDED.component, permission_code=EXCLUDED.permission_code, visible=1, status=1, is_delete=0, updated_time=NOW();

SELECT setval(pg_get_serial_sequence('public.sys_permission', 'id'), COALESCE((SELECT MAX(id) FROM public.sys_permission), 1));
SELECT setval(pg_get_serial_sequence('public.sys_menu', 'id'), COALESCE((SELECT MAX(id) FROM public.sys_menu), 1));

COMMIT;
