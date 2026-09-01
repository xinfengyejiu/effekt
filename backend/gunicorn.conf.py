# encoding: UTF-8
"""
Gunicorn 配置文件（FastAPI + Uvicorn Worker）
"""
import os

# 从环境变量获取绑定地址，默认 0.0.0.0:5010
bind = os.environ.get('BE_URL', '0.0.0.0:5010')

# Worker 配置
workers = 2  # 建议: CPU核心数 * 2 + 1
worker_class = 'uvicorn.workers.UvicornWorker'

# 超时配置
timeout = 300  # 每个请求的最大处理时间

# 日志配置
loglevel = 'info'
accesslog = '-'  # 输出到标准输出
errorlog = '-'   # 输出到标准错误

# 进程配置
daemon = False  # 容器内前台运行
pidfile = 'logs/gunicorn.pid'

# 预加载应用
preload_app = True
