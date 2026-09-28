# encoding: utf-8
from pathlib import Path
from urllib.parse import unquote, urlparse
import sys

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from const import sparkatp_sql_uri

SQL = ROOT / 'resources' / 'sql' / 'chat_issue_import_pgsql.sql'


def main():
    uri = sparkatp_sql_uri.replace('postgresql+psycopg2://', 'postgresql://', 1)
    p = urlparse(uri)
    conn = psycopg2.connect(
        host=p.hostname,
        port=p.port or 5432,
        dbname=(p.path or '/').lstrip('/') or 'test',
        user=unquote(p.username or ''),
        password=unquote(p.password or ''),
    )
    try:
        with conn.cursor() as cur:
            cur.execute(SQL.read_text(encoding='utf-8'))
            conn.commit()
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name LIKE 'chat_issue%' ORDER BY 1"
            )
            print('tables:', [r[0] for r in cur.fetchall()])
            cur.execute("SELECT code FROM sys_permission WHERE module='chat_issue' ORDER BY 1")
            print('perms:', [r[0] for r in cur.fetchall()])
            cur.execute("SELECT code, path, sort FROM sys_menu WHERE code LIKE 'chat_issue%' ORDER BY 1")
            print('menus:', cur.fetchall())
        print('migration ok')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
