# encoding: UTF-8
from sqlalchemy import BigInteger, Column, Integer, SmallInteger, String, TIMESTAMP, Text, text
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class DocumentSource(Base):
    __tablename__ = 'document_source'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    product_id = Column(BigInteger, nullable=False, comment='产品ID')
    project_id = Column(BigInteger, nullable=False, comment='项目ID')
    type = Column(SmallInteger, default=1, comment='类型：1-PDF文件，2-飞书链接，3-Excel文件(xlsx/xls)，4-Markdown文件(md/markdown)')
    source = Column(String(512), nullable=False, comment='文件路径或飞书链接')
    content = Column(Text, comment='解析后的文本内容（缓存）')
    version = Column(Integer, default=1, comment='版本号')
    status = Column(SmallInteger, default=0, comment='状态：0-待解析，1-已解析，2-已生成用例')
    ai_model = Column(String(64), comment='使用的AI模型')
    created_by = Column(BigInteger, comment='创建人ID')
    is_delete = Column(Integer, default=0, comment='0：未删除；1：已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), comment='更新时间')
