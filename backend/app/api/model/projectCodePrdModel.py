# encoding: UTF-8
from sqlalchemy import BigInteger, Column, Integer, SmallInteger, String, Text, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class ProjectCodePrdConfig(Base):
    __tablename__ = 'project_code_prd_config'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    project_id = Column(BigInteger, nullable=False, comment='项目id')
    repo_url = Column(String(512), nullable=False, comment='Git仓库地址')
    default_branch = Column(String(128), comment='默认分支')
    model_config = Column(JSONB, server_default=text("'{}'::jsonb"), comment='模型扩展配置')
    is_delete = Column(Integer, default=0, comment='0：未删除；1：已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class ProjectCodePrdRecord(Base):
    __tablename__ = 'project_code_prd_record'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    project_id = Column(BigInteger, nullable=False, comment='项目id')
    config_id = Column(BigInteger, comment='配置id')
    repo_url = Column(String(512), nullable=False, comment='Git仓库地址')
    branch = Column(String(128), nullable=False, comment='Git分支')
    title = Column(String(256), comment='PRD标题')
    status = Column(SmallInteger, default=0, comment='0:待生成 1:生成中 2:成功 3:失败')
    prd_markdown = Column(Text, comment='PRD Markdown内容')
    summary = Column(Text, comment='代码库分析摘要')
    error_message = Column(Text, comment='错误信息')
    created_by = Column(BigInteger, comment='创建人')
    is_delete = Column(Integer, default=0, comment='0：未删除；1：已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')
