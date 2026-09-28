# encoding: UTF-8
"""对话式质量助手 ORM 模型。"""
from sqlalchemy import BigInteger, Column, Integer, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class QaAssistantSession(Base):
    """质量助手会话。"""
    __tablename__ = 'qa_assistant_session'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    session_no = Column(String(64), nullable=False, unique=True, comment='会话编号')
    user_id = Column(BigInteger, nullable=False, comment='用户')
    product_id = Column(BigInteger, comment='产品')
    project_id = Column(BigInteger, comment='项目')
    title = Column(String(255), comment='标题')
    context = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='多轮槽位')
    is_delete = Column(Integer, nullable=False, default=0, comment='软删')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_time = Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'),
        server_onupdate=text('CURRENT_TIMESTAMP'), comment='更新时间'
    )


class QaAssistantMessage(Base):
    """质量助手消息。"""
    __tablename__ = 'qa_assistant_message'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    session_id = Column(BigInteger, nullable=False, comment='会话id')
    role = Column(String(16), nullable=False, comment='user/assistant/system')
    content = Column(Text, nullable=False, comment='展示文本')
    intent = Column(String(64), comment='意图')
    tool_trace = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"), comment='工具调用审计')
    answer_payload = Column(JSONB, comment='完整回答协议')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
