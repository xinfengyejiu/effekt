# encoding: UTF-8
import os
from urllib.parse import quote_plus as urlquote
from urllib.parse import quote

# dev环境
# BE_URL = '127.0.0.1:6080'
# online环境
BE_URL = '0.0.0.0:5010'

BASEDIR = os.path.dirname(os.path.abspath(__file__))
# PROJDIR = os.path.dirname(BASEDIR)
LOG_DIR = os.path.join(BASEDIR, 'logs')

# 返回码
RES_CODE = {
    40001: 'URL不正确，请检查！',
    40002: '不支持该请求方法！',
    40003: '参数有误！',
    40004: 'header错误！',
    40005: 'user_id不能为空! ',
    40006: '构建任务遇到问题, 请稍后重试! ',
    40007: '获取下拉框列表失败！',
    40008: '获取接口列表失败！',
    40009: '新增场景失败！',
    40010: '更新用例编号失败！',
    40011: '获取场景信息失败！',
    40012: '更新场景失败！',
    40013: 'scene_id不能为空!'
}

sparkatp_sql_uri = f'postgresql+psycopg2://postgres:{urlquote("f267abd8-7005-472f-8cef-c1738c691c6c")}@39.170.26.156:8366/test'
# sparkatp_sql_uri = f'postgresql+psycopg2://postgres:{urlquote("difyai123456")}@39.170.26.156:8366/test-platform-prod'
EXECUTE_DB_CONFIG = {
    'ZHYY': {
        'st': {
            'host': '124.220.32.45',
            'port': 18666,
            'user': 'postgres',
            'password': '89c75b17-1738-4b7d-b651-4c65a5a662ab',
            'database': 'smart_management_st'
        },
        'dev': {
            'host': '124.220.32.45',
            'port': 18566,
            'user': 'postgres',
            'password': 'f267abd8-7005-472f-8cef-c1738c691c6c',
            'database': 'smart_management_st'
        },
        'pre': {
            'host': '8.137.12.32',
            'port': 8096,
            'user': 'sm_test_user',
            'password': 'Test@736141',
            'database': 'smart_management_pre'
        }
    },
    'DLZ': {
        'st': {
            'host': '124.220.32.45',
            'port': 18666,
            'user': 'joyhub',
            'password': 'e364be29-6089-4610-97d5-0037a28d0703',
            'database': 'joyhub_website_st'
        }
    }
}
# MySQL 数据库（保留原配置供参考）
# sparkatp_sql_uri = 'mysql+pymysql://qa-dev:jaeg3SCQt0@mysql.qa.huohua.cn/sparkatp?charset=utf8mb4'
# password = urlquote("peppa@test")

USE_TEAM = ["ZHYY", "DLZ", "JOYHUB", "OA", "APP"]

# dev环境请求user_info
# STRESS_URI = 'http://stress-api.qa.huohua.cn'
# prod环境请求user_info
# STRESS_URI = 'http://stress-api.bg.huohua.cn'
STRESS_URI = 'https://qe.bg.huohua.cn'
# STRESS_URI = ' http://172.19.24.100:5012/api'
# dev环境 qe domain
# QE_DOMAIN = 'http://qe.qa.huohua.cn'
# prod环境 qe domain
QE_DOMAIN = 'https://qe.bg.huohua.cn'

PASSWORD = quote('AcUVeRb8lN')
REDIS_URL = 'redis://127.0.0.1:7379/15'
# REDIS_URL = 'redis://39.170.26.156:7378/15'

JENKINS_BASE_URL = os.environ.get('JENKINS_BASE_URL', 'http://39.170.26.156:8256/')
JENKINS_USER = os.environ.get('JENKINS_USER', 'jenkins')
JENKINS_TOKEN = os.environ.get('JENKINS_TOKEN', 'jenkins')
JENKINS_DEFAULT_JOB = os.environ.get('JENKINS_DEFAULT_JOB', 'pytest-auto-runner')
AUTOMATION_CALLBACK_SECRET = os.environ.get('AUTOMATION_CALLBACK_SECRET', '')
PLATFORM_BASE_URL = os.environ.get('PLATFORM_BASE_URL', 'http://127.0.0.1:5010/it/api')

AI_WORKSPACE_ROOTS = [item.strip() for item in os.environ.get('AI_WORKSPACE_ROOTS', 'D:\\zhyy,D:\\AIcoding').split(',') if item.strip()]
AI_EXECUTION_LOG_DIR = os.environ.get('AI_EXECUTION_LOG_DIR', os.path.join(LOG_DIR, 'ai_execution'))
AI_DEFAULT_TIMEOUT_SECONDS = int(os.environ.get('AI_DEFAULT_TIMEOUT_SECONDS', '300'))
AI_MAX_OUTPUT_BYTES = int(os.environ.get('AI_MAX_OUTPUT_BYTES', '1048576'))
AI_DENY_COMMAND_KEYWORDS = [
    'format', 'shutdown', 'reboot', 'rm', 'del', 'rmdir', 'rd', 'reg', 'diskpart',
    'cipher', 'net user', 'net localgroup', 'sc delete', 'powershell -enc'
]
