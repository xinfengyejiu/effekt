from sqlalchemy import BigInteger, Column, Integer, SmallInteger, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class DataBuilder(Base):
    __tablename__ = 'data_builder'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    project_id = Column(BigInteger, nullable=False, comment='项目id')
    name = Column(String(128), nullable=False, comment='造数器名称')
    description = Column(Text, comment='描述')
    builder_type = Column(SmallInteger, default=1, comment='1:流程编排 2:SQL 3:脚本')
    definition = Column(JSONB, nullable=False, comment='构造定义')
    input_schema = Column(JSONB, comment='输入定义')
    output_example = Column(JSONB, comment='输出示例')
    tags = Column(JSONB, server_default=text("'[]'::jsonb"), comment='场景标签 JSON 数组')
    source = Column(String(32), default='manual', comment='manual/ai/saved_from_task')
    scene_key = Column(String(128), comment='可选场景键')
    created_by = Column(BigInteger, comment='创建人')
    is_delete = Column(Integer, default=0, comment='0：未删除；1：已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class DataTask(Base):
    __tablename__ = 'data_task'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    builder_id = Column(BigInteger, nullable=False, comment='造数器id')
    project_id = Column(BigInteger, nullable=False, comment='项目id')
    params = Column(JSONB, comment='任务参数')
    status = Column(SmallInteger, default=0, comment='0:等待 1:执行中 2:成功 3:失败')
    result_data = Column(JSONB, comment='生成数据')
    error_message = Column(Text, comment='错误信息')
    created_by = Column(BigInteger, comment='创建人')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    completed_time = Column(TIMESTAMP, nullable=True, comment='完成时间')
