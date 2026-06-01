from sqlalchemy import BigInteger, Column, Integer, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class AiAgent(Base):
    __tablename__ = 'ai_agent'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    agent_code = Column(String(64), nullable=False, unique=True, comment='Agent唯一编码')
    product_id = Column(BigInteger, comment='产品id')
    product_name = Column(String(128), comment='产品名称')
    project_id = Column(BigInteger, comment='项目id')
    project_name = Column(String(128), comment='项目名称')
    name = Column(String(128), nullable=False, comment='Agent名称')
    agent_type = Column(Integer, nullable=False, default=1, comment='1 coding 2 qa 3 security 4 report 5 ops')
    entrypoint = Column(String(256), nullable=False, comment='执行入口')
    version = Column(String(64), comment='版本')
    description = Column(Text, comment='描述')
    capabilities = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"), comment='能力')
    supported_tasks = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"), comment='支持任务')
    permission_policy = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='权限策略')
    workspace_policy = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='工作区策略')
    timeout_seconds = Column(Integer, nullable=False, default=300, comment='超时时间')
    max_concurrency = Column(Integer, nullable=False, default=1, comment='最大并发')
    cost_policy = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='成本策略')
    status = Column(Integer, nullable=False, default=1, comment='1启用 2停用 3草稿')
    created_by = Column(BigInteger, comment='创建人')
    is_delete = Column(Integer, nullable=False, default=0, comment='0未删除 1已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class AiAgentExecution(Base):
    __tablename__ = 'ai_agent_execution'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    execution_no = Column(String(64), nullable=False, unique=True, comment='执行编号')
    agent_id = Column(BigInteger, nullable=False, comment='Agent id')
    project_id = Column(BigInteger, nullable=False, comment='项目id')
    workspace_path = Column(String(512), nullable=False, comment='工作区')
    task_type = Column(String(64), comment='任务类型')
    input_payload = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='输入')
    command_snapshot = Column(Text, comment='命令快照')
    status = Column(String(32), nullable=False, default='pending', comment='状态')
    stdout_path = Column(String(512), comment='stdout日志')
    stderr_path = Column(String(512), comment='stderr日志')
    result_payload = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='结果')
    error_message = Column(Text, comment='错误')
    duration_seconds = Column(Integer, comment='耗时')
    cost_summary = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='成本')
    trigger_by = Column(BigInteger, comment='触发人')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')
