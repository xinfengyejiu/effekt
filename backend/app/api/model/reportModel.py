from sqlalchemy import BigInteger, Column, SmallInteger, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class Report(Base):
    __tablename__ = 'report'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    plan_id = Column(BigInteger, nullable=True, comment='计划id')
    project_id = Column(BigInteger, nullable=False, comment='项目id')
    product_id = Column(BigInteger, nullable=False, comment='产品id')

    name = Column(String(128), nullable=False, comment='报告名称')
    report_type = Column(SmallInteger, default=1, comment='1:实时报告 2:归档报告')
    summary = Column(JSONB, comment='统计数据')
    content = Column(Text, comment='HTML内容')
    file_url = Column(String(512), comment='文件地址')
    generated_by = Column(BigInteger, comment='生成人')
    generated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='生成时间')


class DefectSync(Base):
    __tablename__ = 'defect_sync'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    project_id = Column(BigInteger, nullable=False, comment='项目id')
    external_id = Column(String(64), nullable=False, comment='外部缺陷id')
    external_system = Column(String(32), comment='外部系统')
    plan_case_id = Column(BigInteger, comment='计划用例id')
    status = Column(String(32), comment='外部状态')
    last_sync_time = Column(TIMESTAMP, comment='最后同步时间')
