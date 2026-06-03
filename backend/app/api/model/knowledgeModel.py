# encoding: UTF-8
from sqlalchemy import BigInteger, Column, Integer, Numeric, SmallInteger, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class KnowledgeChunk(Base):
    __tablename__ = 'knowledge_chunk'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    document_id = Column(BigInteger, nullable=False, comment='文档ID')
    product_id = Column(BigInteger, nullable=False, comment='产品ID')
    project_id = Column(BigInteger, nullable=False, comment='项目ID')
    chunk_no = Column(Integer, nullable=False, comment='分片序号')
    title = Column(String(255), comment='分片标题')
    content = Column(Text, nullable=False, comment='分片内容')
    summary = Column(Text, comment='摘要')
    keywords = Column(JSONB, server_default=text("'[]'::jsonb"), comment='关键词')
    embedding = Column(JSONB, server_default=text("'[]'::jsonb"), comment='文本向量，优先由Embedding模型生成')
    embedding_model = Column(String(128), comment='向量模型名称')
    token_count = Column(Integer, default=0, comment='估算Token数')
    status = Column(SmallInteger, default=1, comment='1有效 0禁用')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), comment='更新时间')
    is_delete = Column(Integer, default=0, comment='0未删除 1已删除')


class KnowledgeChatSession(Base):
    __tablename__ = 'knowledge_chat_session'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    product_id = Column(BigInteger, nullable=False, comment='产品ID')
    project_id = Column(BigInteger, nullable=False, comment='项目ID')
    title = Column(String(255), comment='会话标题')
    created_by = Column(BigInteger, comment='创建人')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), comment='更新时间')
    is_delete = Column(Integer, default=0, comment='0未删除 1已删除')


class KnowledgeChatMessage(Base):
    __tablename__ = 'knowledge_chat_message'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    session_id = Column(BigInteger, nullable=False, comment='会话ID')
    role = Column(String(20), nullable=False, comment='user/assistant/system')
    content = Column(Text, nullable=False, comment='消息内容')
    mode = Column(String(32), comment='local/llm/hybrid')
    evidence = Column(JSONB, server_default=text("'[]'::jsonb"), comment='引用证据')
    model_config = Column(JSONB, server_default=text("'{}'::jsonb"), comment='模型配置快照')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    is_delete = Column(Integer, default=0, comment='0未删除 1已删除')


class KnowledgeModelSetting(Base):
    __tablename__ = 'knowledge_model_setting'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    scope_type = Column(String(20), nullable=False, default='global', comment='global/product/project')
    scope_id = Column(BigInteger, nullable=False, default=0, comment='作用域ID')
    provider = Column(String(32), default='custom', comment='模型供应商')
    api_base = Column(String(512), comment='API Base')
    model = Column(String(128), comment='模型名称')
    embedding_model = Column(String(128), comment='向量模型名称')
    temperature = Column(Numeric(4, 2), default=0.30, comment='温度')
    max_tokens = Column(Integer, default=2048, comment='最大输出Token')
    top_k = Column(Integer, default=5, comment='检索数量')
    score_threshold = Column(Numeric(5, 4), default=0, comment='分数阈值')
    use_env_key = Column(SmallInteger, default=1, comment='是否使用环境变量Key')
    api_key_ref = Column(String(128), comment='Key引用')
    status = Column(SmallInteger, default=1, comment='状态')
    created_by = Column(BigInteger, comment='创建人')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), comment='更新时间')
    is_delete = Column(Integer, default=0, comment='0未删除 1已删除')
