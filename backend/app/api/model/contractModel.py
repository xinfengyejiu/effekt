# encoding: UTF-8
"""契约测试 ORM 模型。"""
from sqlalchemy import BigInteger, Column, Integer, SmallInteger, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class ContractSuite(Base):
    """契约套件。"""
    __tablename__ = 'contract_suite'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    product_id = Column(BigInteger, nullable=False, comment='产品id')
    project_id = Column(BigInteger, nullable=False, comment='项目id')
    name = Column(String(128), nullable=False, comment='套件名称')
    description = Column(Text, comment='描述')
    source_type = Column(String(32), nullable=False, default='mock_document', comment='mock_document/openapi_upload')
    mock_document_id = Column(BigInteger, comment='关联Mock文档')
    openapi_content = Column(Text, comment='上传的OpenAPI原文')
    base_url = Column(String(512), nullable=False, comment='环境根地址')
    default_headers = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='默认请求头')
    notify_type = Column(String(128), comment='通知渠道')
    notify_webhook = Column(String(512), comment='Webhook地址')
    schedule_type = Column(String(32), nullable=False, default='manual', comment='cron/interval/manual')
    cron_expression = Column(String(128), comment='Cron表达式')
    interval_seconds = Column(Integer, comment='间隔秒数')
    enabled = Column(SmallInteger, nullable=False, default=1, comment='是否启用')
    last_run_at = Column(TIMESTAMP, comment='最近执行时间')
    created_by = Column(BigInteger, comment='创建人')
    is_delete = Column(Integer, nullable=False, default=0, comment='软删')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_time = Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'),
        server_onupdate=text('CURRENT_TIMESTAMP'), comment='更新时间'
    )


class ContractSuiteItem(Base):
    """套件内接口项。"""
    __tablename__ = 'contract_suite_item'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    suite_id = Column(BigInteger, nullable=False, comment='套件id')
    mock_interface_id = Column(BigInteger, comment='来源Mock接口')
    name = Column(String(255), nullable=False, comment='接口名')
    method = Column(String(16), nullable=False, comment='HTTP方法')
    path = Column(String(512), nullable=False, comment='路径模板')
    path_params = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='路径参数')
    query_params = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='Query参数')
    body_template = Column(JSONB, comment='请求体')
    response_schema = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='响应契约Schema')
    timeout_seconds = Column(Integer, nullable=False, default=30, comment='超时秒')
    enabled = Column(SmallInteger, nullable=False, default=1, comment='是否启用')
    sort_order = Column(Integer, nullable=False, default=0, comment='排序')
    is_delete = Column(Integer, nullable=False, default=0, comment='软删')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_time = Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'),
        server_onupdate=text('CURRENT_TIMESTAMP'), comment='更新时间'
    )


class ContractRun(Base):
    """一次契约执行。"""
    __tablename__ = 'contract_run'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    run_no = Column(String(64), nullable=False, unique=True, comment='执行编号')
    suite_id = Column(BigInteger, nullable=False, comment='套件id')
    project_id = Column(BigInteger, nullable=False, comment='项目id')
    trigger_type = Column(String(32), nullable=False, default='manual', comment='manual/scheduled/api')
    status = Column(SmallInteger, nullable=False, default=0, comment='0待执行1执行中2完成3失败')
    total_count = Column(Integer, nullable=False, default=0, comment='接口总数')
    pass_count = Column(Integer, nullable=False, default=0, comment='无漂移')
    drift_count = Column(Integer, nullable=False, default=0, comment='有漂移')
    error_count = Column(Integer, nullable=False, default=0, comment='请求错误')
    breaking_count = Column(Integer, nullable=False, default=0, comment='breaking条数')
    trigger_by = Column(BigInteger, comment='触发人')
    start_time = Column(TIMESTAMP, comment='开始时间')
    end_time = Column(TIMESTAMP, comment='结束时间')
    duration_ms = Column(Integer, comment='耗时毫秒')
    summary = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='汇总扩展')
    notify_status = Column(SmallInteger, nullable=False, default=0, comment='0未通知1成功2失败')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_time = Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'),
        server_onupdate=text('CURRENT_TIMESTAMP'), comment='更新时间'
    )


class ContractRunItem(Base):
    """单接口执行结果。"""
    __tablename__ = 'contract_run_item'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    run_id = Column(BigInteger, nullable=False, comment='执行id')
    suite_item_id = Column(BigInteger, comment='套件项id')
    name = Column(String(255), comment='接口名')
    method = Column(String(16), nullable=False, comment='HTTP方法')
    path = Column(String(512), nullable=False, comment='实际请求路径')
    http_status = Column(Integer, comment='HTTP状态码')
    result_status = Column(String(32), nullable=False, default='pending', comment='pass/drift/error')
    max_severity = Column(String(16), comment='breaking/compatible/info')
    duration_ms = Column(Integer, comment='耗时毫秒')
    response_excerpt = Column(Text, comment='响应截断')
    error_message = Column(Text, comment='错误信息')
    ai_analysis = Column(JSONB, comment='AI漂移分析')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')


class ContractFinding(Base):
    """漂移明细。"""
    __tablename__ = 'contract_finding'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    run_id = Column(BigInteger, nullable=False, comment='执行id')
    run_item_id = Column(BigInteger, nullable=False, comment='执行项id')
    json_path = Column(String(512), nullable=False, comment='JSON路径')
    severity = Column(String(16), nullable=False, comment='breaking/compatible/info')
    drift_type = Column(String(64), nullable=False, comment='漂移类型')
    expected = Column(Text, comment='期望')
    actual = Column(Text, comment='实际')
    message = Column(Text, nullable=False, comment='说明')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
