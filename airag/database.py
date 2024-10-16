import psycopg2

config = {
    'host': 'timescaledb',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'postgres',
    'port': '5432'
}

def execute(sql, arguments={}):
    """Execute SQL on postgres.
    """
    # FIXME: Manage connection and allow non auto-commit
    def connect():
        return psycopg2.connect(
            host = config.get('host'),
            database = config.get('database'),
            user = config.get('user'),
            password = config.get('password'),
            port = config.get('port')
        )
    conn = connect()
    cur = conn.cursor()
    cur.execute(sql, arguments)
    conn.commit()
    try:
        rows = cur.fetchall()
    except psycopg2.ProgrammingError as exc:
        if str(exc) == 'no results to fetch':
            rows = None
            pass
        else:
            raise
    cur.close()
    conn.close()
    return rows
