# encoding: UTF-8
from sqlalchemy import BigInteger, Column, Integer, SmallInteger, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class MobileExecutionConfig(Base):
    __tablename__ = 'mobile_execution_config'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    project_id = Column(BigInteger, nullable=False)
    mobile_app_id = Column(BigInteger, nullable=False)
    device_serial = Column(String(255), nullable=False)
    env_code = Column(String(32), nullable=False)
    script_selector = Column(String(512), nullable=False)
    remark = Column(Text)
    enabled = Column(SmallInteger, nullable=False, default=1)
    created_by = Column(BigInteger)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class MobileExecutionConfigCase(Base):
    __tablename__ = 'mobile_execution_config_case'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    config_id = Column(BigInteger, nullable=False)
    case_id = Column(BigInteger, nullable=False)
    run_order = Column(Integer, nullable=False, default=0)


class MobileDevice(Base):
    __tablename__ = 'mobile_device'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    serial_no = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(128))
    device_group = Column(String(128))
    remark = Column(Text)
    brand = Column(String(128))
    model = Column(String(255))
    android_version = Column(String(64))
    sdk_version = Column(String(32))
    screen_width = Column(Integer)
    screen_height = Column(Integer)
    density = Column(String(64))
    adb_status = Column(String(32), nullable=False, default='unknown')
    usage_status = Column(String(32), nullable=False, default='idle')
    last_seen_time = Column(TIMESTAMP)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class MobileApp(Base):
    __tablename__ = 'mobile_app'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, nullable=False)
    name = Column(String(128), nullable=False)
    package_name = Column(String(255), nullable=False)
    launch_activity = Column(String(255))
    app_type = Column(String(32), nullable=False, default='android')
    apk_path = Column(String(512))
    version_name = Column(String(64))
    version_code = Column(String(64))
    default_capabilities = Column(JSONB, server_default=text("'{}'::jsonb"))
    install_before_run = Column(SmallInteger, nullable=False, default=0)
    clear_data_before_run = Column(SmallInteger, nullable=False, default=0)
    enabled = Column(SmallInteger, nullable=False, default=1)
    created_by = Column(BigInteger)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class MobileExecutionStep(Base):
    __tablename__ = 'mobile_execution_step'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    execution_id = Column(BigInteger, nullable=False)
    execution_case_id = Column(BigInteger)
    step_no = Column(Integer, nullable=False)
    instruction = Column(Text)
    action_type = Column(String(32))
    action_payload = Column(JSONB, server_default=text("'{}'::jsonb"))
    locator_strategy = Column(String(32))
    target_element = Column(JSONB, server_default=text("'{}'::jsonb"))
    page_snapshot = Column(JSONB, server_default=text("'{}'::jsonb"))
    before_screenshot_artifact_id = Column(BigInteger)
    after_screenshot_artifact_id = Column(BigInteger)
    ui_xml_artifact_id = Column(BigInteger)
    status = Column(String(32), nullable=False, default='pending')
    duration_ms = Column(Integer)
    error_message = Column(Text)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))


class MobileArtifact(Base):
    __tablename__ = 'mobile_artifact'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    execution_id = Column(BigInteger, nullable=False)
    execution_case_id = Column(BigInteger)
    step_id = Column(BigInteger)
    artifact_type = Column(String(64), nullable=False)
    relative_path = Column(String(1024), nullable=False)
    content_type = Column(String(128))
    size_bytes = Column(BigInteger)
    checksum = Column(String(128))
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
