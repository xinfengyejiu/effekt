# encoding: UTF-8
from sqlalchemy import BigInteger, Column, Integer, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class ChatIssueImport(Base):
    __tablename__ = 'chat_issue_import'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_no = Column(String(64), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    source_type = Column(String(32), nullable=False, default='paste')
    raw_text = Column(Text)
    product_id = Column(BigInteger)
    product_name = Column(String(128))
    project_id = Column(BigInteger, nullable=False)
    project_name = Column(String(128))
    status = Column(String(32), nullable=False, default='draft')
    day_label = Column(String(64))
    created_by = Column(BigInteger)
    meta = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    is_delete = Column(Integer, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class ChatIssueItem(Base):
    __tablename__ = 'chat_issue_item'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    import_id = Column(BigInteger, nullable=False)
    sort_no = Column(Integer, nullable=False, default=0)
    title = Column(String(500), nullable=False)
    detail = Column(Text)
    suggest_type = Column(String(32), nullable=False, default='bug')
    severity = Column(Integer, default=2)
    item_status = Column(String(32), nullable=False, default='parsed')
    ai_analysis = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    linked_bug_id = Column(BigInteger)
    linked_case_id = Column(BigInteger)
    source_ref = Column(String(128))
    created_by = Column(BigInteger)
    is_delete = Column(Integer, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))
