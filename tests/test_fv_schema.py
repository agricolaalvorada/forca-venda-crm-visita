import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app_sync_fv.db_connection import DBConfig, SQLServerConnector
from app_sync_fv.fv_schema import FVSchemaManager


def main():
    cfg = DBConfig.from_env()
    connector = SQLServerConnector(cfg)
    schema_manager = FVSchemaManager(connector)

    schema_manager.ensure_all_tables()
    print("Tabelas FV garantidas no DW.")


if __name__ == "__main__":
    main()
