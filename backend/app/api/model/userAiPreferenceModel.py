# encoding: UTF-8
from sqlalchemy import BigInteger, Column, Integer, Numeric, String, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class UserAiPreference(Base):
    __tablename__ = 'user_ai_preference'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    provider = Column(String(64), nullable=False, default='')
    model = Column(String(128), nullable=False, default='')
    api_base = Column(String(512))
    api_key = Column(String(512))
    use_custom = Column(Integer, nullable=False, default=0)
    temperature = Column(Numeric(4, 2))
    max_tokens = Column(Integer)
    extra = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    is_delete = Column(Integer, nullable=False, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))
