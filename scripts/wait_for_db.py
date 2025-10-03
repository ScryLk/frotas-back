import os
import time
import sys

try:
    import pymysql  # type: ignore
except Exception as e:
    print("PyMySQL não está instalado dentro da imagem.", file=sys.stderr)
    raise

HOST = os.getenv("DB_HOST", "127.0.0.1")
PORT = int(os.getenv("DB_PORT", "3306"))
USER = os.getenv("DB_USER", "root")
PASSWORD = os.getenv("DB_PASSWORD", "root")
DBNAME = os.getenv("DB_NAME", "frotas")
TIMEOUT = int(os.getenv("DB_WAIT_TIMEOUT", "60"))

start = time.time()
last_log = 0.0

while True:
    try:
        conn = pymysql.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database=DBNAME,
            connect_timeout=5,
            read_timeout=5,
            write_timeout=5,
        )
        conn.close()
        print("Banco de dados está pronto.")
        break
    except Exception as e:
        now = time.time()
        if now - last_log > 5:
            print(f"Aguardando DB em {HOST}:{PORT}... ({e})")
            last_log = now
        if now - start > TIMEOUT:
            raise RuntimeError(f"Timeout aguardando DB em {HOST}:{PORT}") from e
        time.sleep(2)
