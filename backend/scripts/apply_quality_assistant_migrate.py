# encoding: utf-8
"""Apply quality assistant SQL migrations using project DB settings."""
from pathlib import Path
from urllib.parse import unquote, urlparse

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / 'resources' / 'sql' / 'quality_assistant_pgsql.sql',
    ROOT / 'resources' / 'sql' / 'quality_assistant_menu_permission.sql',
]


def _conn_kwargs():
    import sys
    sys.path.insert(0, str(ROOT))
    from const import sparkatp_sql_uri
    uri = sparkatp_sql_uri.replace('postgresql+psycopg2://', 'postgresql://', 1)
    parsed = urlparse(uri)
    return {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'dbname': (parsed.path or '/test').lstrip('/') or 'test',
        'user': unquote(parsed.username or 'postgres'),
        'password': unquote(parsed.password or ''),
    }


def main():
    conn = psycopg2.connect(**_conn_kwargs())
    try:
        with conn.cursor() as cur:
            for path in FILES:
                cur.execute(path.read_text(encoding='utf-8'))
                conn.commit()
                print('applied', path.name)
            cur.execute(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema='public' AND table_name LIKE 'qa_assistant_%'
                ORDER BY 1
                """
            )
            print('tables:', [r[0] for r in cur.fetchall()])
            cur.execute("SELECT code FROM sys_permission WHERE code LIKE 'qa:assistant:%' ORDER BY 1")
            print('perms:', [r[0] for r in cur.fetchall()])
        print('migration ok')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
