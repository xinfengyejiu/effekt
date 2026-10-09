# encoding: UTF-8
from sqlalchemy import BigInteger, Column, Integer, SmallInteger, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class AiDataProbeConnection(Base):
    __tablename__ = 'ai_data_probe_connection'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    db_type = Column(String(32), nullable=False, default='postgresql')
    host = Column(String(256), nullable=False)
    port = Column(Integer, nullable=False)
    database_name = Column(String(128), nullable=False)
    username = Column(String(128), nullable=False)
    password = Column(String(512), nullable=False, default='')
    product_id = Column(BigInteger)
    product_name = Column(String(128))
    project_id = Column(BigInteger)
    project_name = Column(String(128))
    env = Column(String(64), nullable=False, default='test')
    remark = Column(Text)
    enabled = Column(SmallInteger, nullable=False, default=1)
    created_by = Column(BigInteger)
    is_delete = Column(Integer, nullable=False, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class AiDataProbeSession(Base):
    __tablename__ = 'ai_data_probe_session'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_no = Column(String(64), nullable=False, unique=True)
    connection_id = Column(BigInteger, nullable=False)
    project_id = Column(BigInteger)
    title = Column(String(255), nullable=False, default='')
    status = Column(String(32), nullable=False, default='active')
    created_by = Column(BigInteger)
    meta = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    is_delete = Column(Integer, nullable=False, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class AiDataProbeMessage(Base):
    __tablename__ = 'ai_data_probe_message'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, nullable=False)
    role = Column(String(32), nullable=False)
    content = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_by = Column(BigInteger)
    is_delete = Column(Integer, nullable=False, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))


class AiDataProbeAudit(Base):
    __tablename__ = 'ai_data_probe_audit'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger)
    connection_id = Column(BigInteger)
    sql_text = Column(Text)
    sql_hash = Column(String(64))
    row_count = Column(Integer, nullable=False, default=0)
    latency_ms = Column(Integer)
    success = Column(SmallInteger, nullable=False, default=0)
    error_message = Column(Text)
    created_by = Column(BigInteger)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
