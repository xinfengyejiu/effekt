# encoding: UTF-8
from sqlalchemy import BigInteger, Column, Integer, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class WeakNetworkAiTask(Base):
    __tablename__ = 'weak_network_ai_task'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_no = Column(String(64), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    brief = Column(Text)
    product_id = Column(BigInteger)
    product_name = Column(String(128))
    project_id = Column(BigInteger)
    project_name = Column(String(128))
    status = Column(String(32), nullable=False, default='draft')
    recommended_profiles = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    selected_profile_ids = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    weak_network_session_ids = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    created_by = Column(BigInteger)
    remark = Column(Text)
    is_delete = Column(Integer, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class WeakNetworkAiCheckpoint(Base):
    __tablename__ = 'weak_network_ai_checkpoint'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, nullable=False)
    sort_no = Column(Integer, nullable=False, default=0)
    title = Column(String(500), nullable=False)
    expect_text = Column(Text)
    profile_preset = Column(String(64))
    status = Column(String(32), nullable=False, default='pending')
    last_verdict = Column(String(32))
    last_observation = Column(Text)
    is_delete = Column(Integer, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class WeakNetworkAiEvidence(Base):
    __tablename__ = 'weak_network_ai_evidence'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, nullable=False)
    checkpoint_id = Column(BigInteger)
    file_path = Column(String(512))
    note = Column(Text)
    mobile_execution_id = Column(BigInteger)
    created_by = Column(BigInteger)
    is_delete = Column(Integer, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class WeakNetworkAiFinding(Base):
    __tablename__ = 'weak_network_ai_finding'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, nullable=False)
    checkpoint_id = Column(BigInteger)
    title = Column(String(500), nullable=False)
    detail = Column(Text)
    status = Column(String(32), nullable=False, default='open')
    linked_bug_id = Column(BigInteger)
    ai_payload = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    is_delete = Column(Integer, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))
