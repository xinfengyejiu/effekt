# encoding: UTF-8
"""巡检系统 ORM 模型。"""
from sqlalchemy import BigInteger, Column, Date, Integer, SmallInteger, String, TIMESTAMP, Text, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class InspectionGroup(Base):
    """巡检组（按项目分组；调度与通知挂在组上）。"""
    __tablename__ = 'inspection_group'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    project_id = Column(BigInteger, nullable=False)
    description = Column(Text)
    enabled = Column(SmallInteger, nullable=False, default=1)
    schedule_type = Column(String(32), nullable=False, default='manual')  # cron / interval / manual
    cron_expression = Column(String(128))
    interval_seconds = Column(Integer)
    notify_type = Column(String(128))
    notify_webhook = Column(String(512))
    last_run_at = Column(TIMESTAMP)
    created_by = Column(BigInteger)
    is_delete = Column(Integer, nullable=False, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class InspectionTask(Base):
    """巡检任务。"""
    __tablename__ = 'inspection_task'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, nullable=False)
    project_id = Column(BigInteger, nullable=False)
    name = Column(String(128), nullable=False)
    task_type = Column(String(32), nullable=False)          # auto_case / api / sql / script / mixed
    schedule_type = Column(String(32), nullable=False, default='manual')  # cron / interval / manual
    cron_expression = Column(String(128))
    interval_seconds = Column(Integer)
    env_code = Column(String(32))
    enabled = Column(SmallInteger, nullable=False, default=1)
    notify_type = Column(String(128))                       # wechat_work,dingtalk,feishu
    notify_webhook = Column(String(512))
    notify_config = Column(JSONB, server_default=text("'{}'::jsonb"))
    ext = Column(JSONB, server_default=text("'{}'::jsonb"))
    created_by = Column(BigInteger)
    updated_by = Column(BigInteger)
    is_delete = Column(Integer, nullable=False, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class InspectionItem(Base):
    """巡检项。"""
    __tablename__ = 'inspection_item'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, nullable=False)
    item_type = Column(String(32), nullable=False)          # auto_case / api / sql / script
    name = Column(String(128), nullable=False)
    ref_id = Column(BigInteger)                             # 关联自动化用例 ID（仅 auto_case）
    sort_order = Column(Integer, nullable=False, default=0)
    config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    timeout_seconds = Column(Integer, nullable=False, default=30)
    enabled = Column(SmallInteger, nullable=False, default=1)
    is_delete = Column(Integer, nullable=False, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class InspectionDbConfig(Base):
    """数据库连接配置（SQL 巡检用）。"""
    __tablename__ = 'inspection_db_config'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, nullable=False)
    name = Column(String(128), nullable=False)
    db_type = Column(String(32), nullable=False)            # postgresql / mysql / sqlserver / oracle
    host = Column(String(256), nullable=False)
    port = Column(Integer, nullable=False)
    database_name = Column(String(128), nullable=False)
    username = Column(String(128), nullable=False)
    password = Column(String(256), nullable=False)          # 加密存储
    extra_params = Column(JSONB, server_default=text("'{}'::jsonb"))
    enabled = Column(SmallInteger, nullable=False, default=1)
    is_delete = Column(Integer, nullable=False, default=0)
    created_by = Column(BigInteger)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class InspectionExecution(Base):
    """巡检执行记录（组级执行时 task_id 可为空）。"""
    __tablename__ = 'inspection_execution'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger)  # 组级执行可为空；任务级执行填写
    group_id = Column(BigInteger, nullable=False)
    project_id = Column(BigInteger, nullable=False)
    trigger_type = Column(String(32), nullable=False)       # scheduled / manual
    status = Column(SmallInteger, nullable=False, default=0)  # 0=待执行 1=执行中 2=全部通过 3=部分失败 4=全部失败 5=异常
    total_count = Column(Integer, nullable=False, default=0)
    pass_count = Column(Integer, nullable=False, default=0)
    fail_count = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    duration_ms = Column(BigInteger)
    start_time = Column(TIMESTAMP)
    end_time = Column(TIMESTAMP)
    notify_status = Column(SmallInteger, nullable=False, default=0)  # 0=未通知 1=已通知 2=通知失败
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))


class InspectionExecutionItem(Base):
    """巡检项执行结果。"""
    __tablename__ = 'inspection_execution_item'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    execution_id = Column(BigInteger, nullable=False)
    item_id = Column(BigInteger, nullable=False)
    item_type = Column(String(32), nullable=False)
    status = Column(SmallInteger, nullable=False, default=0)  # 0=待执行 1=执行中 2=通过 3=失败 4=异常
    duration_ms = Column(BigInteger)
    result = Column(JSONB, server_default=text("'{}'::jsonb"))
    error_message = Column(Text)
    start_time = Column(TIMESTAMP)
    end_time = Column(TIMESTAMP)


class InspectionDailySummary(Base):
    """巡检统计快照（按日聚合）。"""
    __tablename__ = 'inspection_daily_summary'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, nullable=False)
    group_id = Column(BigInteger)
    summary_date = Column(Date, nullable=False)
    total_executions = Column(Integer, nullable=False, default=0)
    total_items = Column(Integer, nullable=False, default=0)
    pass_items = Column(Integer, nullable=False, default=0)
    fail_items = Column(Integer, nullable=False, default=0)
    error_items = Column(Integer, nullable=False, default=0)
    avg_duration_ms = Column(BigInteger)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    __table_args__ = (
        UniqueConstraint('project_id', 'group_id', 'summary_date', name='uk_inspection_daily_summary'),
    )
