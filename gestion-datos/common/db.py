import os
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor


@contextmanager
def cursor():
    """Conexión + cursor con commit/rollback automático (la transacción incluye el log)."""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "db"), port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "personas_db"),
        user=os.getenv("DB_USER", "app"), password=os.getenv("DB_PASSWORD", "app_pass"),
    )
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def registrar_log(cur, tipo: str, documento: str, usuario: str, detalle: str = ""):
    cur.execute(
        "INSERT INTO logs (tipo_transaccion, documento, usuario, detalle) VALUES (%s,%s,%s,%s)",
        (tipo, documento, usuario, detalle),
    )
