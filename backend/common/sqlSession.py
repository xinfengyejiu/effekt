# 创建连接相关
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus as urlquote
import time

from const import sparkatp_sql_uri

from logger import logger

_ENGINE_CACHE = {}
_SESSION_FACTORY_CACHE = {}

# 重试配置
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY = 1  # 秒


"""
sql操作：
排序：order_by(ChartsName.column.desc()/asc())
limit: .offset(n)过滤前面n条数据 .limit(n)
count: .count()计数
是否存在：is_exist = session.query(exists().where(Book.id > 10)).scalar()
or: .filter(or_(Chart.column == x, Chart.column > y)).all()
one: .one()只获取一条，如不存在或存在多条都会报错
first: 通过主键获取记录  filter(**).first()
"""


class SqlSession:
    def __init__(self, sql_uri=sparkatp_sql_uri):
        self.sql_uri = sql_uri
        self._session = self.get_session()

    @staticmethod
    def build_postgres_uri(host, port, user, password, database):
        return f"postgresql+psycopg2://{user}:{urlquote(str(password))}@{host}:{port}/{database}"

    def get_session(self, retry_count=0):
        try:
            session_factory = _SESSION_FACTORY_CACHE.get(self.sql_uri)
            if session_factory is None:
                engine = _ENGINE_CACHE.get(self.sql_uri)
                if engine is None:
                    engine = create_engine(
                        self.sql_uri,
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
                    _ENGINE_CACHE[self.sql_uri] = engine
                session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
                _SESSION_FACTORY_CACHE[self.sql_uri] = session_factory
            engine = session_factory.kw['bind']
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            except Exception as e:
                logger.warning(f"连接验证失败，尝试重新获取连接: {e}")
                self._dispose_engine()
                raise

            return session_factory()
        except Exception as e:
            if retry_count < MAX_RETRY_ATTEMPTS:
                logger.warning(f"获取数据库连接失败，第 {retry_count + 1} 次重试: {e}")
                time.sleep(RETRY_DELAY * (retry_count + 1))
                return self.get_session(retry_count + 1)
            else:
                logger.error(f"获取数据库连接失败，已重试 {MAX_RETRY_ATTEMPTS} 次: {e}")
                raise

    def _is_disconnect_error(self, error):
        if isinstance(error, DBAPIError) and getattr(error, 'connection_invalidated', False):
            return True
        message = str(error).lower()
        return any(text in message for text in (
            'server closed the connection unexpectedly',
            'connection already closed',
            'connection not open',
            'terminating connection',
            'could not receive data from server',
            'could not send data to server',
            'software caused connection abort',
            '10053',
            'ssl connection has been closed unexpectedly'
        ))

    def _dispose_engine(self):
        engine = _ENGINE_CACHE.pop(self.sql_uri, None)
        _SESSION_FACTORY_CACHE.pop(self.sql_uri, None)
        if engine is not None:
            try:
                engine.dispose()
            except Exception as e:
                logger.warning(f'释放数据库连接池失败: {e}')

    def _handle_session_error(self, action, error):
        if self._is_disconnect_error(error):
            logger.warning(f'数据库连接在{action}时已断开，清理连接池: {error}')
            self._dispose_engine()
        else:
            logger.warning(f'数据库会话{action}失败: {error}')

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
            self._handle_session_error('提交', e)
            raise

    def rollback(self):
        try:
            self._session.rollback()
        except Exception as e:
            self._handle_session_error('回滚', e)
            if not self._is_disconnect_error(e):
                raise

    def close(self):
        try:
            self._session.close()
        except Exception as e:
            self._handle_session_error('关闭', e)
            if not self._is_disconnect_error(e):
                raise

    def execute(self, sql):
        return self._session.execute(text(sql))

    def done(self, close=True):
        """
        执行完插入、删除、修改等操作后执行done，如报错回滚本次事务的sql操作
        :return:
        """
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
    return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}
