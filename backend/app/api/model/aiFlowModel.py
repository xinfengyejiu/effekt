from sqlalchemy import BigInteger, Column, Integer, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class AiSkillFlow(Base):
    __tablename__ = 'ai_skill_flow'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    product_id = Column(BigInteger, comment='产品id')
    product_name = Column(String(128), comment='产品名称')
    project_id = Column(BigInteger, nullable=False, comment='项目id')
    project_name = Column(String(128), comment='项目名称')
    name = Column(String(128), nullable=False, comment='流程名称')
    flow_code = Column(String(64), nullable=False, unique=True, comment='流程编码')
    description = Column(Text, comment='描述')
    trigger_type = Column(String(64), nullable=False, default='manual', comment='触发类型')
    flow_definition = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='流程定义')
    input_schema = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='输入Schema')
    output_schema = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='输出Schema')
    status = Column(Integer, nullable=False, default=3, comment='1启用 2停用 3草稿')
    created_by = Column(BigInteger, comment='创建人')
    is_delete = Column(Integer, nullable=False, default=0, comment='0未删除 1已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class AiSkillFlowExecution(Base):
    __tablename__ = 'ai_skill_flow_execution'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    flow_id = Column(BigInteger, nullable=False, comment='流程id')
    ai_task_id = Column(BigInteger, comment='AI任务id')
    status = Column(String(32), nullable=False, default='pending', comment='状态')
    input_payload = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='输入')
    node_results = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"), comment='节点结果')
    output_payload = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='输出')
    error_message = Column(Text, comment='错误')
    duration_seconds = Column(Integer, comment='耗时')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')
