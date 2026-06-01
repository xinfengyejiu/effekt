from sqlalchemy import BigInteger, Column, Integer, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class AiTool(Base):
    __tablename__ = 'ai_tool'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    tool_code = Column(String(64), nullable=False, unique=True, comment='工具唯一编码')
    product_id = Column(BigInteger, comment='产品id')
    product_name = Column(String(128), comment='产品名称')
    project_id = Column(BigInteger, comment='项目id')
    project_name = Column(String(128), comment='项目名称')
    name = Column(String(128), nullable=False, comment='工具名称')
    tool_type = Column(String(64), nullable=False, comment='工具类型')
    command_template = Column(Text, nullable=False, comment='命令模板')
    input_schema = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='输入Schema')
    output_schema = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='输出Schema')
    artifact_schema = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='产物Schema')
    parser_type = Column(String(64), comment='解析类型')
    parser_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='解析配置')
    env_schema = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='环境Schema')
    timeout_seconds = Column(Integer, nullable=False, default=300, comment='超时时间')
    status = Column(Integer, nullable=False, default=1, comment='1启用 2停用 3草稿')
    created_by = Column(BigInteger, comment='创建人')
    is_delete = Column(Integer, nullable=False, default=0, comment='0未删除 1已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class AiToolExecution(Base):
    __tablename__ = 'ai_tool_execution'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    execution_no = Column(String(64), nullable=False, unique=True, comment='执行编号')
    tool_id = Column(BigInteger, nullable=False, comment='工具id')
    project_id = Column(BigInteger, nullable=False, comment='项目id')
    ai_task_id = Column(BigInteger, comment='AI任务id')
    workspace_path = Column(String(512), nullable=False, comment='工作区')
    input_payload = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='输入')
    command_snapshot = Column(Text, comment='命令快照')
    status = Column(String(32), nullable=False, default='pending', comment='状态')
    result_summary = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='结果摘要')
    artifact_paths = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"), comment='产物路径')
    stdout_path = Column(String(512), comment='stdout日志')
    stderr_path = Column(String(512), comment='stderr日志')
    duration_seconds = Column(Integer, comment='耗时')
    error_message = Column(Text, comment='错误')
    trigger_by = Column(BigInteger, comment='触发人')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')
