# encoding: UTF-8
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import time

from app.core.config import SPARKATP_SQL_URI
from logger import logger

# 全局引擎实例
_engine = None
_session_factory = None

# 重试配置
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY = 1  # 秒


def get_engine():
    """获取数据库引擎（单例模式）"""
    global _engine
    if _engine is None:
        _engine = create_engine(
            SPARKATP_SQL_URI,
            pool_size=10,
            max_overflow=20,
            pool_recycle=120,
            pool_pre_ping=True,
            pool_timeout=15,
            pool_reset_on_return='rollback',
            connect_args={
                'connect_timeout': 5,
                'application_name': 'effekt-interface',
                'options': '-c timezone=Asia/Shanghai',
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 5,
                'keepalives_count': 3
            }
        )
    return _engine


def get_session_factory():
    """获取 session 工厂（单例模式）"""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return _session_factory


def get_db():
    """
    FastAPI 依赖注入：获取数据库 session
    用法: db: Session = Depends(get_db)
    """
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def get_db_context():
    """
    上下文管理器方式获取 session
    用法: with get_db_context() as db:
    """
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()


# 保留原有 SqlSession 类以兼容旧代码
class SqlSession:
    """兼容旧代码的 session 封装类"""
    
    def __init__(self, sql_uri=None):
        self.sql_uri = sql_uri or SPARKATP_SQL_URI
        self._session = self.get_session()

    @staticmethod
    def build_postgres_uri(host, port, user, password, database):
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"

    def get_session(self, retry_count=0):
        try:
            factory = get_session_factory()
            engine = factory.kw['bind']
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            except Exception as e:
                logger.warning(f"连接验证失败，尝试重新获取连接: {e}")
                self._dispose_engine()
                raise
            return factory()
        except Exception as e:
            if retry_count < MAX_RETRY_ATTEMPTS:
                logger.warning(f"获取数据库连接失败，第 {retry_count + 1} 次重试: {e}")
                time.sleep(RETRY_DELAY * (retry_count + 1))
                return self.get_session(retry_count + 1)
            else:
                logger.error(f"获取数据库连接失败，已重试 {MAX_RETRY_ATTEMPTS} 次: {e}")
                raise

    def _dispose_engine(self):
        global _engine, _session_factory
        if _engine is not None:
            try:
                _engine.dispose()
                _engine = None
                _session_factory = None
            except Exception as e:
                logger.warning(f'释放数据库连接池失败: {e}')

    def query(self, *args):
        return self._session.query(*args)

    def add(self, added):
        self._session.add(added)

    def add_all(self, added_list):
        if isinstance(added_list, list):
            self._session.add_all(added_list)
        else:
            logger.warning('只能传递list')

    def flush(self):
        self._session.flush()

    def commit(self):
        try:
            self._session.commit()
        except Exception as e:
            logger.warning(f'提交失败: {e}')
            raise

    def rollback(self):
        try:
            self._session.rollback()
        except Exception as e:
            logger.warning(f'回滚失败: {e}')

    def close(self):
        try:
            self._session.close()
        except Exception as e:
            logger.warning(f'关闭失败: {e}')

    def execute(self, sql):
        return self._session.execute(text(sql))

    def done(self, close=True):
        """执行完插入、删除、修改等操作后执行done"""
        try:
            self.commit()
            if close:
                self.close()
        except Exception as e:
            logger.warning(e)
            try:
                self.rollback()
            except Exception as rollback_err:
                logger.warning(f'事务回滚失败: {rollback_err}')
            return e

    @property
    def session(self):
        return self._session


def to_dict(self):
    """SQLAlchemy model 序列化为 dict"""
    return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}
