from sqlalchemy import BigInteger, Column, Integer, SmallInteger, String, TIMESTAMP, Text, text
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class Role(Base):
    __tablename__ = 'sys_role'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    code = Column(String(64), unique=True, nullable=False, comment='角色编码')
    name = Column(String(64), nullable=False, comment='角色名称')
    description = Column(Text, comment='角色描述')
    status = Column(SmallInteger, default=1, comment='1:启用 0:禁用')
    is_system = Column(SmallInteger, default=0, comment='是否系统内置角色')
    created_by = Column(BigInteger, comment='创建人')
    is_delete = Column(Integer, default=0, comment='0：未删除；1：已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class Permission(Base):
    __tablename__ = 'sys_permission'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    code = Column(String(128), unique=True, nullable=False, comment='权限编码')
    name = Column(String(128), nullable=False, comment='权限名称')
    module = Column(String(64), comment='所属模块')
    action = Column(String(64), comment='动作')
    description = Column(Text, comment='描述')
    status = Column(SmallInteger, default=1, comment='1:启用 0:禁用')
    is_delete = Column(Integer, default=0, comment='0：未删除；1：已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class RolePermission(Base):
    __tablename__ = 'sys_role_permission'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    role_id = Column(BigInteger, nullable=False, comment='角色id')
    permission_id = Column(BigInteger, nullable=False, comment='权限id')
    is_delete = Column(Integer, default=0, comment='0：未删除；1：已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')


class Menu(Base):
    __tablename__ = 'sys_menu'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    parent_id = Column(BigInteger, default=0, comment='父菜单id')
    name = Column(String(64), nullable=False, comment='菜单名称')
    code = Column(String(64), unique=True, comment='菜单编码')
    type = Column(SmallInteger, default=1, comment='1:目录 2:菜单 3:按钮')
    path = Column(String(255), comment='路由路径')
    component = Column(String(255), comment='前端组件路径')
    icon = Column(String(64), comment='图标')
    permission_code = Column(String(128), comment='对应权限编码')
    sort = Column(Integer, default=0, comment='排序')
    visible = Column(SmallInteger, default=1, comment='1:显示 0:隐藏')
    status = Column(SmallInteger, default=1, comment='1:启用 0:禁用')
    is_delete = Column(Integer, default=0, comment='0：未删除；1：已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), nullable=True, comment='修改时间')


class RoleMenu(Base):
    __tablename__ = 'sys_role_menu'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    role_id = Column(BigInteger, nullable=False, comment='角色id')
    menu_id = Column(BigInteger, nullable=False, comment='菜单id')
    is_delete = Column(Integer, default=0, comment='0：未删除；1：已删除')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间')
