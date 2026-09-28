# encoding: UTF-8
"""效能平台模块目录：质量助手全平台导航与能力分层。"""

# capability:
#   navigate — 可深链跳转
#   query    — 可只读汇总（Tool 查库）
#   action   — 可受限写操作（需二次确认）

PLATFORM_MODULES = [
    {
        'key': 'home',
        'name': '首页',
        'keywords': ['首页', '工作台', 'effekt'],
        'route': '/effekt',
        'capability': ['navigate'],
        'group': '基础',
    },
    {
        'key': 'product',
        'name': '产品管理',
        'keywords': ['产品', '产品管理'],
        'route': '/test-platform/product',
        'capability': ['navigate'],
        'group': '基础配置',
    },
    {
        'key': 'project',
        'name': '项目管理',
        'keywords': ['项目', '项目管理'],
        'route': '/test-platform/project',
        'capability': ['navigate'],
        'group': '基础配置',
    },
    {
        'key': 'case',
        'name': '用例管理',
        'keywords': ['用例', '测试用例', '用例管理', 'case'],
        'route': '/test-platform/case',
        'capability': ['navigate', 'query'],
        'group': '用例周期',
    },
    {
        'key': 'plan',
        'name': '测试计划',
        'keywords': ['计划', '测试计划', '执行计划'],
        'route': '/test-platform/plan',
        'capability': ['navigate', 'query'],
        'group': '用例周期',
    },
    {
        'key': 'report',
        'name': '测试报告',
        'keywords': ['报告', '测试报告'],
        'route': '/test-platform/report',
        'capability': ['navigate', 'query'],
        'group': '用例周期',
    },
    {
        'key': 'bug',
        'name': 'Bug 管理',
        'keywords': ['bug', '缺陷', '问题单', 'bug管理'],
        'route': '/bug/list',
        'capability': ['navigate', 'query'],
        'group': '用例周期',
    },
    {
        'key': 'requirement_qa',
        'name': '需求问答',
        'keywords': ['需求问答', '需求', 'prd问答'],
        'route': '/requirement-qa',
        'capability': ['navigate'],
        'group': '用例周期',
    },
    {
        'key': 'ai_platform',
        'name': 'AI 测试中枢',
        'keywords': ['ai中枢', 'ai测试中枢', '测试中枢', 'ai agent'],
        'route': '/test-platform/ai-platform',
        'capability': ['navigate'],
        'group': 'AI质量助手',
    },
    {
        'key': 'ai_review',
        'name': 'AI 测试评审',
        'keywords': ['ai评审', '测试评审', '用例评审'],
        'route': '/ai-review',
        'capability': ['navigate'],
        'group': 'AI质量助手',
    },
    {
        'key': 'ai_workload',
        'name': 'AI 工作量预估',
        'keywords': ['工作量', '工作量预估', 'ai预估'],
        'route': '/ai-workload-estimate',
        'capability': ['navigate'],
        'group': 'AI质量助手',
    },
    {
        'key': 'test_asset',
        'name': '测试资产治理',
        'keywords': ['测试资产', '资产治理'],
        'route': '/test-asset-governance',
        'capability': ['navigate'],
        'group': 'AI质量助手',
    },
    {
        'key': 'precise',
        'name': '精准测试',
        'keywords': ['精准测试', '精准', '覆盖率', '门禁'],
        'route': '/precise/analysis',
        'capability': ['navigate'],
        'group': 'AI质量助手',
    },
    {
        'key': 'impact_radar',
        'name': '变更影响雷达',
        'keywords': ['变更影响雷达', '影响雷达', 'git追溯', 'commit链接', '变更追溯', '行级血缘', '必测清单'],
        'route': '/precise/radar',
        'capability': ['navigate'],
        'group': 'AI质量助手',
    },
    {
        'key': 'skill_rules',
        'name': '业务技能规则',
        'keywords': ['技能规则', 'skill', '业务规则'],
        'route': '/test-platform/skill-rules',
        'capability': ['navigate'],
        'group': 'AI质量助手',
    },
    {
        'key': 'contract',
        'name': '契约守护',
        'keywords': ['契约', '契约测试', '接口漂移', 'breaking', 'openapi'],
        'route': '/contract/suites',
        'capability': ['navigate', 'query', 'action'],
        'group': '测试支撑工具',
    },
    {
        'key': 'inspection',
        'name': '巡检管理',
        'keywords': ['巡检', '巡检管理', '巡检失败'],
        'route': '/inspection/dashboard',
        'capability': ['navigate', 'query'],
        'group': '测试支撑工具',
    },
    {
        'key': 'performance',
        'name': '性能测试',
        'keywords': ['性能', '压测', '性能测试', '性能报告'],
        'route': '/performance/scenarios',
        'capability': ['navigate', 'query'],
        'group': '测试支撑工具',
    },
    {
        'key': 'mobile',
        'name': '移动自动化',
        'keywords': ['移动', '移动自动化', 'app自动化', '设备'],
        'route': '/mobile-automation/devices',
        'capability': ['navigate', 'query'],
        'group': '测试支撑工具',
    },
    {
        'key': 'mock',
        'name': 'Mock 服务',
        'keywords': ['mock', 'mock服务', '接口mock'],
        'route': '/mock/document',
        'capability': ['navigate'],
        'group': '测试支撑工具',
    },
    {
        'key': 'data_factory',
        'name': '造数工厂',
        'keywords': ['造数', '造数工厂', '数据工厂', '造数工具', '数据库造数', 'db造数', '对话造数'],
        'route': '/data-tools/factory',
        'capability': ['navigate'],
        'group': '测试支撑工具',
    },
    {
        'key': 'data_factory_task_history',
        'name': '造数结果历史',
        'keywords': ['造数历史', '造数结果', '造数任务', '任务历史'],
        'route': '/data-tools/factory/task',
        'capability': ['navigate'],
        'group': '测试支撑工具',
    },
    {
        'key': 'system_user',
        'name': '用户管理',
        'keywords': ['用户管理', '账号'],
        'route': '/system/user',
        'capability': ['navigate'],
        'group': '系统管理',
    },
    {
        'key': 'system_role',
        'name': '角色管理',
        'keywords': ['角色', '角色管理'],
        'route': '/system/role',
        'capability': ['navigate'],
        'group': '系统管理',
    },
    {
        'key': 'system_menu',
        'name': '菜单管理',
        'keywords': ['菜单', '菜单管理'],
        'route': '/system/menu',
        'capability': ['navigate'],
        'group': '系统管理',
    },
    {
        'key': 'system_permission',
        'name': '权限管理',
        'keywords': ['权限', '权限管理'],
        'route': '/system/permission',
        'capability': ['navigate'],
        'group': '系统管理',
    },
]


def match_module(text):
    """按关键词匹配平台模块（长词优先）。"""
    raw = (text or '').strip().lower()
    if not raw:
        return None
    ranked = []
    for mod in PLATFORM_MODULES:
        for kw in mod.get('keywords') or []:
            k = kw.lower()
            if k and k in raw:
                ranked.append((len(k), mod))
                break
    if not ranked:
        return None
    ranked.sort(key=lambda x: -x[0])
    return ranked[0][1]


def list_modules_by_group():
    groups = {}
    for mod in PLATFORM_MODULES:
        groups.setdefault(mod.get('group') or '其它', []).append(mod)
    return groups


def module_route(mod, project_id=None, product_id=None):
    route = mod.get('route') or '/effekt'
    if not project_id and not product_id:
        return route
    sep = '&' if '?' in route else '?'
    parts = []
    if project_id not in (None, ''):
        # 各页参数风格不完全统一：计划用 projectId，契约多用 project_id
        if route.startswith('/test-platform/') or route.startswith('/bug'):
            parts.append('projectId={}'.format(project_id))
        else:
            parts.append('project_id={}'.format(project_id))
    if product_id not in (None, '') and route.startswith('/test-platform/'):
        parts.append('productId={}'.format(product_id))
    if not parts:
        return route
    return route + sep + '&'.join(parts)
