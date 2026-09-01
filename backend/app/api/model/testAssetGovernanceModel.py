# encoding: UTF-8
from sqlalchemy import BigInteger, Column, Integer, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class TestAssetScan(Base):
    __tablename__ = 'test_asset_scan'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    scan_no = Column(String(64), nullable=False, unique=True)
    product_id = Column(BigInteger)
    product_name = Column(String(128))
    project_id = Column(BigInteger, nullable=False)
    project_name = Column(String(128))
    title = Column(String(255), nullable=False)
    scan_type = Column(String(64), nullable=False, default='full')
    options_json = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    summary_json = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    health_score = Column(Integer)
    status = Column(String(32), nullable=False, default='pending')
    error_message = Column(Text)
    created_by = Column(BigInteger)
    started_time = Column(TIMESTAMP)
    finished_time = Column(TIMESTAMP)
    is_delete = Column(Integer, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class TestAssetIssue(Base):
    __tablename__ = 'test_asset_issue'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    scan_id = Column(BigInteger, nullable=False)
    product_id = Column(BigInteger)
    project_id = Column(BigInteger, nullable=False)
    module_id = Column(BigInteger)
    module_name = Column(String(128))
    issue_type = Column(String(64), nullable=False)
    severity = Column(String(32), nullable=False, default='medium')
    title = Column(String(255), nullable=False)
    description = Column(Text)
    evidence_json = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    suggestion_json = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    related_case_ids = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    action_status = Column(String(32), nullable=False, default='open')
    assigned_to = Column(BigInteger)
    resolved_by = Column(BigInteger)
    resolved_time = Column(TIMESTAMP)
    is_delete = Column(Integer, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class TestAssetAction(Base):
    __tablename__ = 'test_asset_action'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    issue_id = Column(BigInteger, nullable=False)
    action_type = Column(String(64), nullable=False)
    action_payload = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    result_payload = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    status = Column(String(32), nullable=False, default='success')
    error_message = Column(Text)
    created_by = Column(BigInteger)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))
