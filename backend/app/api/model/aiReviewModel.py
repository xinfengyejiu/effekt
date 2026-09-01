# encoding: UTF-8
from sqlalchemy import BigInteger, Column, Integer, SmallInteger, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class AiTestReview(Base):
    __tablename__ = 'ai_test_review'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    review_no = Column(String(64), nullable=False, unique=True)
    product_id = Column(BigInteger)
    product_name = Column(String(128))
    project_id = Column(BigInteger, nullable=False)
    project_name = Column(String(128))
    review_type = Column(String(64), nullable=False)
    source_type = Column(String(64), nullable=False, default='manual')
    source_id = Column(BigInteger)
    title = Column(String(255), nullable=False)
    input_payload = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    context_payload = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    result_summary = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    risk_level = Column(String(32))
    score = Column(Integer)
    status = Column(String(32), nullable=False, default='pending')
    error_message = Column(Text)
    created_by = Column(BigInteger)
    is_delete = Column(Integer, nullable=False, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class AiTestReviewFinding(Base):
    __tablename__ = 'ai_test_review_finding'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    review_id = Column(BigInteger, nullable=False)
    finding_type = Column(String(64), nullable=False, default='risk')
    risk_level = Column(String(32))
    module_name = Column(String(255))
    api_path = Column(String(512))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    suggestion = Column(Text)
    evidence_json = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    status = Column(String(32), nullable=False, default='open')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))
    is_delete = Column(Integer, nullable=False, default=0)


class AiTestReviewCaseSuggestion(Base):
    __tablename__ = 'ai_test_review_case_suggestion'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    review_id = Column(BigInteger, nullable=False)
    finding_id = Column(BigInteger)
    module_name = Column(String(255))
    case_title = Column(String(255), nullable=False)
    preconditions = Column(Text)
    steps = Column(Text)
    expected_results = Column(Text)
    priority = Column(SmallInteger, default=2)
    case_type = Column(SmallInteger, default=1)
    tags = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    matched_case_id = Column(BigInteger)
    action_status = Column(String(32), nullable=False, default='pending')
    created_case_id = Column(BigInteger)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))
    is_delete = Column(Integer, nullable=False, default=0)
