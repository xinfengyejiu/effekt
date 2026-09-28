# encoding: UTF-8
from sqlalchemy import BigInteger, Column, Integer, Numeric, SmallInteger, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class WeakNetworkProfile(Base):
    __tablename__ = 'weak_network_profile'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger)
    product_name = Column(String(128))
    project_id = Column(BigInteger)
    project_name = Column(String(128))
    name = Column(String(128), nullable=False)
    preset_code = Column(String(64), nullable=False, default='custom')
    latency_ms = Column(Integer, nullable=False, default=0)
    bandwidth_kbps = Column(Integer, nullable=False, default=0)
    loss_percent = Column(Numeric(5, 2), nullable=False, default=0)
    disconnect_rules = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    remark = Column(Text)
    enabled = Column(SmallInteger, nullable=False, default=1)
    is_system = Column(SmallInteger, nullable=False, default=0)
    created_by = Column(BigInteger)
    is_delete = Column(Integer, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class WeakNetworkSession(Base):
    __tablename__ = 'weak_network_session'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_no = Column(String(64), nullable=False, unique=True)
    profile_id = Column(BigInteger, nullable=False)
    profile_snapshot = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    product_id = Column(BigInteger)
    project_id = Column(BigInteger)
    device_serial = Column(String(255))
    proxy_port = Column(Integer, nullable=False, default=18888)
    pack_hash = Column(String(128))
    status = Column(String(32), nullable=False, default='created')
    expires_at = Column(TIMESTAMP)
    created_by = Column(BigInteger)
    remark = Column(Text)
    is_delete = Column(Integer, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))
