from sqlalchemy import BigInteger, Column, Integer, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class AiTestTask(Base):
    __tablename__ = 'ai_test_task'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    task_no = Column(String(64), nullable=False, unique=True, comment='任务编号')
    product_id = Column(BigInteger, comment='产品id')
    product_name = Column(String(128), comment='产品名称')
    project_id = Column(BigInteger, nullable=False, comment='项目id')
    project_name = Column(String(128), comment='项目名称')
    task_type = Column(String(64), nullable=False, comment='任务类型')
    source_type = Column(String(64), comment='来源类型')
    source_id = Column(BigInteger, comment='来源id')
    source_payload = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='来源输入')
    risk_level = Column(String(16), comment='风险等级')
    status = Column(String(32), nullable=False, default='pending', comment='状态')
    recommended_tests = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"), comment='推荐测试')
    selected_agents = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"), comment='选择Agent')
    selected_tools = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"), comment='选择工具')
    selected_skills = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"), comment='选择Skill')
    result_summary = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='结果摘要')
    report_id = Column(BigInteger, comment='报告id')
    created_by = Column(BigInteger, comment='创建人')
    is_delete = Column(Integer, nullable=False, default=0, comment='0未删除 1已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class AiTestTaskStep(Base):
    __tablename__ = 'ai_test_task_step'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    task_id = Column(BigInteger, nullable=False, comment='AI任务id')
    step_order = Column(Integer, nullable=False, default=1, comment='步骤顺序')
    step_type = Column(String(64), nullable=False, comment='步骤类型')
    ref_type = Column(String(64), comment='关联类型')
    ref_id = Column(BigInteger, comment='关联id')
    status = Column(String(32), nullable=False, default='pending', comment='状态')
    input_payload = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='输入')
    output_payload = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='输出')
    error_message = Column(Text, comment='错误')
    start_time = Column(TIMESTAMP, comment='开始时间')
    end_time = Column(TIMESTAMP, comment='结束时间')
    duration_seconds = Column(Integer, comment='耗时')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')
