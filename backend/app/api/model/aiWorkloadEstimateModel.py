# encoding: UTF-8
from sqlalchemy import BigInteger, Column, Integer, Numeric, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class AiWorkloadEstimate(Base):
    __tablename__ = 'ai_workload_estimate'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    estimate_no = Column(String(64), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    product_id = Column(BigInteger, nullable=False)
    product_name = Column(String(128))
    project_id = Column(BigInteger, nullable=False)
    project_name = Column(String(128))
    owner_id = Column(BigInteger)
    owner_name = Column(String(128))
    document_ids = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    reference_document_ids = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    prd_snapshot = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    reference_summary = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    result_summary = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    raw_ai_output = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    failure_reason = Column(Text)
    complexity_level = Column(String(32))
    confidence = Column(String(32))
    total_function_points = Column(Integer, default=0)
    total_case_count = Column(Integer, default=0)
    case_design_hours = Column(Numeric(10, 2), default=0)
    qa_execution_hours = Column(Numeric(10, 2), default=0)
    total_effort_hours = Column(Numeric(10, 2), default=0)
    estimated_tokens = Column(BigInteger, default=0)
    status = Column(String(32), nullable=False, default='draft')
    created_by = Column(BigInteger)
    assigned_by = Column(BigInteger)
    assigned_time = Column(TIMESTAMP)
    confirmed_by = Column(BigInteger)
    confirmed_time = Column(TIMESTAMP)
    confirm_info = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    is_delete = Column(Integer, nullable=False, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class AiWorkloadEstimateModule(Base):
    __tablename__ = 'ai_workload_estimate_module'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    estimate_id = Column(BigInteger, nullable=False)
    module_name = Column(String(128), nullable=False)
    description = Column(Text)
    complexity_level = Column(String(32))
    function_point_count = Column(Integer, default=0)
    case_count = Column(Integer, default=0)
    case_design_hours = Column(Numeric(10, 2), default=0)
    qa_execution_hours = Column(Numeric(10, 2), default=0)
    total_hours = Column(Numeric(10, 2), default=0)
    risk_summary = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    sort_order = Column(Integer, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class AiWorkloadEstimateFunction(Base):
    __tablename__ = 'ai_workload_estimate_function'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    estimate_id = Column(BigInteger, nullable=False)
    module_id = Column(BigInteger)
    module_name = Column(String(128))
    function_name = Column(String(255), nullable=False)
    description = Column(Text)
    test_scope = Column(Text)
    positive_case_count = Column(Integer, default=0)
    negative_case_count = Column(Integer, default=0)
    boundary_case_count = Column(Integer, default=0)
    permission_case_count = Column(Integer, default=0)
    integration_case_count = Column(Integer, default=0)
    case_count = Column(Integer, default=0)
    complexity_reason = Column(Text)
    case_design_hours = Column(Numeric(10, 2), default=0)
    qa_execution_hours = Column(Numeric(10, 2), default=0)
    total_hours = Column(Numeric(10, 2), default=0)
    estimated_tokens = Column(BigInteger, default=0)
    risk_level = Column(String(32))
    sort_order = Column(Integer, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))
