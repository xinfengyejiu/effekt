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

SPARKATP_DB_PASSWORD = os.environ.get('SPARKATP_DB_PASSWORD', '')
sparkatp_sql_uri = os.environ.get(
    'SPARKATP_SQL_URI',
    f'postgresql+psycopg2://postgres:{urlquote(SPARKATP_DB_PASSWORD)}@xxx:xxx/test'
)
EXECUTE_DB_CONFIG = {
    'ZHYY': {
        'st': {
            'host': os.environ.get('ZHYY_ST_DB_HOST', '124.220.32.45'),
            'port': int(os.environ.get('ZHYY_ST_DB_PORT', '18666')),
            'user': os.environ.get('ZHYY_ST_DB_USER', 'postgres'),
            'password': os.environ.get('ZHYY_ST_DB_PASSWORD', ''),
            'database': os.environ.get('ZHYY_ST_DB_NAME', 'smart_management_st')
        },
        'dev': {
            'host': os.environ.get('ZHYY_DEV_DB_HOST', '124.220.32.45'),
            'port': int(os.environ.get('ZHYY_DEV_DB_PORT', '18566')),
            'user': os.environ.get('ZHYY_DEV_DB_USER', 'postgres'),
            'password': os.environ.get('ZHYY_DEV_DB_PASSWORD', ''),
            'database': os.environ.get('ZHYY_DEV_DB_NAME', 'smart_management_st')
        },
        'pre': {
            'host': os.environ.get('ZHYY_PRE_DB_HOST', '8.137.12.32'),
            'port': int(os.environ.get('ZHYY_PRE_DB_PORT', '8096')),
            'user': os.environ.get('ZHYY_PRE_DB_USER', 'sm_test_user'),
            'password': os.environ.get('ZHYY_PRE_DB_PASSWORD', ''),
            'database': os.environ.get('ZHYY_PRE_DB_NAME', 'smart_management_pre')
        }
    },
    'DLZ': {
        'st': {
            'host': os.environ.get('DLZ_ST_DB_HOST', '124.220.32.45'),
            'port': int(os.environ.get('DLZ_ST_DB_PORT', '18666')),
            'user': os.environ.get('DLZ_ST_DB_USER', 'joyhub'),
            'password': os.environ.get('DLZ_ST_DB_PASSWORD', ''),
            'database': os.environ.get('DLZ_ST_DB_NAME', 'joyhub_website_st')
        }
    }
}

USE_TEAM = ["ZHYY", "DLZ", "JOYHUB", "OA", "APP"]

# dev环境请求user_info
# STRESS_URI = 'http://stress-api.qa.huohua.cn'
# prod环境请求user_info
# STRESS_URI = 'http://stress-api.bg.huohua.cn'
STRESS_URI = 'https://qe.bg.huohua.cn'
# STRESS_URI = ' http://xxxx:xxxx/api'
# dev环境 qe domain
# QE_DOMAIN = 'http://qe.qa.huohua.cn'
# prod环境 qe domain
QE_DOMAIN = 'https://qe.bg.huohua.cn'

PASSWORD = quote(os.environ.get('APP_PASSWORD', ''))
REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:7379/15')

JENKINS_BASE_URL = os.environ.get('JENKINS_BASE_URL', 'http://xxxx:xxxx/')
JENKINS_USER = os.environ.get('JENKINS_USER', 'jenkins')
JENKINS_TOKEN = os.environ.get('JENKINS_TOKEN', 'jenkins')
JENKINS_DEFAULT_JOB = os.environ.get('JENKINS_DEFAULT_JOB', 'pytest-auto-runner')
AUTOMATION_CALLBACK_SECRET = os.environ.get('AUTOMATION_CALLBACK_SECRET', '')
PLATFORM_BASE_URL = os.environ.get('PLATFORM_BASE_URL', 'http://127.0.0.1:5010/it/api')
