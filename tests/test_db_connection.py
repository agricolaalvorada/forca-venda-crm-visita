import os
import sys

# adiciona a pasta raiz ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app_sync_fv.db_connection import DBConfig, SQLServerConnector


def main():
    cfg = DBConfig.from_env()
    connector = SQLServerConnector(cfg)

    with connector.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT TOP 1 name FROM sys.tables;")
        row = cur.fetchone()
        print("Conexão OK. Primeiro objeto em sys.tables:", row[0] if row else "nenhuma tabela")


if __name__ == "__main__":
    main()
