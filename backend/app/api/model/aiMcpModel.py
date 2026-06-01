from sqlalchemy import BigInteger, Column, Integer, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class AiMcpConnector(Base):
    __tablename__ = 'ai_mcp_connector'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    connector_code = Column(String(64), nullable=False, unique=True, comment='连接器编码')
    product_id = Column(BigInteger, comment='产品id')
    product_name = Column(String(128), comment='产品名称')
    project_id = Column(BigInteger, comment='项目id')
    project_name = Column(String(128), comment='项目名称')
    name = Column(String(128), nullable=False, comment='连接器名称')
    connector_type = Column(String(64), nullable=False, comment='连接器类型')
    endpoint = Column(String(512), comment='端点')
    auth_type = Column(String(32), nullable=False, default='none', comment='鉴权类型')
    auth_ref = Column(String(256), comment='密钥引用')
    config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='配置')
    capabilities = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"), comment='能力')
    status = Column(Integer, nullable=False, default=1, comment='1启用 2停用 3草稿')
    created_by = Column(BigInteger, comment='创建人')
    is_delete = Column(Integer, nullable=False, default=0, comment='0未删除 1已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class AiMcpCallLog(Base):
    __tablename__ = 'ai_mcp_call_log'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    connector_id = Column(BigInteger, nullable=False, comment='连接器id')
    project_id = Column(BigInteger, comment='项目id')
    operation = Column(String(128), nullable=False, comment='操作')
    request_snapshot = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='请求快照')
    response_summary = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='响应摘要')
    status = Column(String(32), nullable=False, default='success', comment='状态')
    error_message = Column(Text, comment='错误')
    duration_ms = Column(Integer, comment='耗时毫秒')
    created_by = Column(BigInteger, comment='创建人')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
