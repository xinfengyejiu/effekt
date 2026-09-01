from sqlalchemy import BigInteger, Column, Integer, SmallInteger, String, TIMESTAMP, text
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class User(Base):
    __tablename__ = 'sys_user'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    username = Column(String(64), unique=True, nullable=False, comment='登录用户名')
    real_name = Column(String(64), comment='真实姓名')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    mobile = Column(String(32), comment='手机号')
    email = Column(String(128), comment='邮箱')
    avatar = Column(String(255), comment='头像地址')
    status = Column(SmallInteger, default=1, comment='1:启用 0:禁用')
    last_login_time = Column(TIMESTAMP, nullable=True, comment='最后登录时间')
    created_by = Column(BigInteger, comment='创建人')
    is_delete = Column(Integer, default=0, comment='0：未删除；1：已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class UserRole(Base):
    __tablename__ = 'sys_user_role'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    user_id = Column(BigInteger, nullable=False, comment='用户id')
    role_id = Column(BigInteger, nullable=False, comment='角色id')
    is_delete = Column(Integer, default=0, comment='0：未删除；1：已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
