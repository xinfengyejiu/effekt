from sqlalchemy import BigInteger, Column, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class AiQualityReport(Base):
    __tablename__ = 'ai_quality_report'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    report_no = Column(String(64), nullable=False, unique=True, comment='报告编号')
    product_id = Column(BigInteger, comment='产品id')
    product_name = Column(String(128), comment='产品名称')
    project_id = Column(BigInteger, nullable=False, comment='项目id')
    project_name = Column(String(128), comment='项目名称')
    task_id = Column(BigInteger, comment='AI任务id')
    report_type = Column(String(64), nullable=False, comment='报告类型')
    title = Column(String(255), nullable=False, comment='标题')
    risk_level = Column(String(16), comment='风险等级')
    summary = Column(Text, comment='摘要')
    metrics = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='指标')
    findings = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"), comment='发现')
    recommendations = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"), comment='建议')
    markdown_content = Column(Text, comment='Markdown内容')
    html_content = Column(Text, comment='HTML内容')
    created_by = Column(BigInteger, comment='创建人')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
