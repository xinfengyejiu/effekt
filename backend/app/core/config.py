# encoding: UTF-8
"""
QualiSync 配置中心（开源版本）
所有敏感配置均通过环境变量读取，请在 .env 文件中配置。
参考 .env.example 获取完整的环境变量列表。
"""
import os
import json
from urllib.parse import quote_plus as urlquote
from urllib.parse import quote

# ── 服务地址 ─────────────────────────────────────────────
BE_URL = os.environ.get('BE_URL', '0.0.0.0:5010')
BASEDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = os.path.join(BASEDIR, 'logs')

# ── 业务返回码 ────────────────────────────────────────────
RES_CODE = {
    40001: 'URL不正确，请检查！',
    40002: '不支持该请求方法！',
    40003: '参数有误！',
    40004: 'header错误！',
    40005: 'user_id不能为空!',
    40006: '构建任务遇到问题, 请稍后重试!',
    40007: '获取下拉框列表失败！',
    40008: '获取接口列表失败！',
    40009: '新增场景失败！',
    40010: '更新用例编号失败！',
    40011: '获取场景信息失败！',
    40012: '更新场景失败！',
    40013: 'scene_id不能为空!'
}

# ── 主数据库连接 ────────────────────────────────────────────
# 格式: postgresql+psycopg2://user:password@host:port/dbname
SPARKATP_SQL_URI = os.environ.get('SPARKATP_SQL_URI', '')

# ── 多环境数据库配置 ────────────────────────────────────────
# 支持通过 JSON 环境变量配置
# 示例: EXECUTE_DB_CONFIG_JSON='{"team":{"env":{"host":"","port":5432,"user":"","password":"","database":""}}}'
EXECUTE_DB_CONFIG = {}
_execute_db_json = os.environ.get('EXECUTE_DB_CONFIG_JSON', '')
if _execute_db_json:
    try:
        EXECUTE_DB_CONFIG = json.loads(_execute_db_json)
    except (json.JSONDecodeError, TypeError):
        pass

USE_TEAM = os.environ.get('USE_TEAM', '').split(',') if os.environ.get('USE_TEAM') else []

# ── 外部服务地址 ────────────────────────────────────────────
STRESS_URI = os.environ.get('STRESS_URI', '')
QE_DOMAIN = os.environ.get('QE_DOMAIN', '')

# ── 安全 ───────────────────────────────────────────────────
PASSWORD = os.environ.get('APP_PASSWORD', '')

# ── Redis ─────────────────────────────────────────────────
REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')

# ── Jenkins ───────────────────────────────────────────────
JENKINS_BASE_URL = os.environ.get('JENKINS_BASE_URL', '')
JENKINS_USER = os.environ.get('JENKINS_USER', '')
JENKINS_TOKEN = os.environ.get('JENKINS_TOKEN', '')
JENKINS_DEFAULT_JOB = os.environ.get('JENKINS_DEFAULT_JOB', 'pytest-auto-runner')
PERFORMANCE_JENKINS_JOB = os.environ.get('PERFORMANCE_JENKINS_JOB', 'performance-runner')
PERFORMANCE_JENKINS_VIEW_URL = os.environ.get('PERFORMANCE_JENKINS_VIEW_URL', '')
PRECISE_JENKINS_JOB = os.environ.get('PRECISE_JENKINS_JOB', 'precise-test-runner')
AUTOMATION_CALLBACK_SECRET = os.environ.get('AUTOMATION_CALLBACK_SECRET', '')
PLATFORM_BASE_URL = os.environ.get('PLATFORM_BASE_URL', 'http://127.0.0.1:5010/it/api')

# ── AI 模块配置 ───────────────────────────────────────────
AI_WORKSPACE_ROOTS = [item.strip() for item in os.environ.get('AI_WORKSPACE_ROOTS', '').split(',') if item.strip()]
AI_EXECUTION_LOG_DIR = os.environ.get('AI_EXECUTION_LOG_DIR', os.path.join(LOG_DIR, 'ai_execution'))
AI_DEFAULT_TIMEOUT_SECONDS = int(os.environ.get('AI_DEFAULT_TIMEOUT_SECONDS', '300'))
AI_MAX_OUTPUT_BYTES = int(os.environ.get('AI_MAX_OUTPUT_BYTES', '1048576'))
AI_DENY_COMMAND_KEYWORDS = [
    'format', 'shutdown', 'reboot', 'rm', 'del', 'rmdir', 'rd', 'reg', 'diskpart',
    'cipher', 'net user', 'net localgroup', 'sc delete', 'powershell -enc'
]

# ── 移动自动化 ─────────────────────────────────────────────
MOBILE_AUTOMATION_ROOT = os.environ.get('MOBILE_AUTOMATION_ROOT', os.path.join(BASEDIR, 'mobile-autotest'))
MOBILE_AUTOMATION_PYTHON = os.environ.get('MOBILE_AUTOMATION_PYTHON', 'python3')
MOBILE_AUTOMATION_ARTIFACT_ROOT = os.environ.get(
    'MOBILE_AUTOMATION_ARTIFACT_ROOT', os.path.join(BASEDIR, 'attachment', 'mobile_automation')
)
MOBILE_AUTOMATION_TIMEOUT_SECONDS = int(os.environ.get('MOBILE_AUTOMATION_TIMEOUT_SECONDS', '1800'))
MOBILE_AUTOMATION_MAX_PARALLEL_DEVICES = int(os.environ.get('MOBILE_AUTOMATION_MAX_PARALLEL_DEVICES', '1'))
MOBILE_AUTOMATION_ADB_PATH = os.environ.get('MOBILE_AUTOMATION_ADB_PATH', 'adb')
MOBILE_AUTOMATION_APPIUM_URL = os.environ.get('MOBILE_AUTOMATION_APPIUM_URL', 'http://127.0.0.1:4723')
MOBILE_AUTOMATION_APPIUM_BIN = os.environ.get('MOBILE_AUTOMATION_APPIUM_BIN', 'appium')

# ── 静态文件上传目录 ────────────────────────────────────────
UPLOAD_FOLDER = os.path.join(BASEDIR, 'attachment', 'bug_picture')

# ── 飞书通知 ──────────────────────────────────────────────
FEISHU_WEBHOOK_URL = os.environ.get('FEISHU_WEBHOOK_URL', '')
