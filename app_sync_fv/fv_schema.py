# app_sync_fv/fv_schema.py
import logging
from typing import Dict

from .db_connection import SQLServerConnector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# DDL das tabelas FV (criadas no banco definido em DB_NAME, ex: DW_ALVORADA)
CREATE_TABLES_DDL: Dict[str, str] = {
    "FV_TIPO_SERVICO_VISITA": """
        CREATE TABLE dbo.FV_TIPO_SERVICO_VISITA (
            id         NVARCHAR(50)  NOT NULL PRIMARY KEY,
            descricao  NVARCHAR(255) NULL,
            DataCarga  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
        );
    """,
    "FV_REGISTRO_VISITA": """
        CREATE TABLE dbo.FV_REGISTRO_VISITA (
            id               NVARCHAR(50)   NOT NULL PRIMARY KEY,
            cod_cliente      NVARCHAR(50)   NULL,
            cod_fazenda      NVARCHAR(50)   NULL,
            cod_cultura      NVARCHAR(50)   NULL,
            cod_safra        NVARCHAR(50)   NULL,
            observacoes      NVARCHAR(MAX)  NULL,
            data_inicio      NVARCHAR(50)   NULL,
            data_fim         NVARCHAR(50)   NULL,
            tipo_atendimento NVARCHAR(100)  NULL,
            email            NVARCHAR(255)  NULL,
            data_hora        NVARCHAR(50)   NULL,
            status           NVARCHAR(50)   NULL,
            centro           NVARCHAR(50)   NULL,
            DataCarga        DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME(),
            bp_solicitante  NVARCHAR(100)   NULL
        );
    """,
    "FV_REGISTRO_VISITA_ANEXOS": """
        CREATE TABLE dbo.FV_REGISTRO_VISITA_ANEXOS (
            id        NVARCHAR(50)   NOT NULL PRIMARY KEY,
            id_visita NVARCHAR(50)   NOT NULL,
            url       NVARCHAR(500)  NULL,
            legenda   NVARCHAR(255)  NULL,
            latitude  NVARCHAR(50)   NULL,
            longitude NVARCHAR(50)   NULL,
            DataCarga DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME()
        );
    """,
    "FV_REGISTRO_VISITA_SERVICOS": """
        CREATE TABLE dbo.FV_REGISTRO_VISITA_SERVICOS (
            id         NVARCHAR(50)   NOT NULL PRIMARY KEY,
            id_visita  NVARCHAR(50)   NOT NULL,
            id_servico NVARCHAR(50)   NOT NULL,
            DataCarga  DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME()
        );
    """,
}


class FVSchemaManager:
    """
    Garante que as tabelas FV existam no DW (DB_NAME do .env, ex: DW_ALVORADA).
    """

    def __init__(self, connector: SQLServerConnector) -> None:
        self.connector = connector

    def table_exists(self, table_name: str, schema: str = "dbo") -> bool:
        query = """
            SELECT 1
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?;
        """
        with self.connector.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, (schema, table_name))
            row = cur.fetchone()
        exists = row is not None
        logging.info("Tabela %s.%s existe? %s", schema, table_name, exists)
        return exists

    def create_table_if_not_exists(self, table_name: str) -> None:
        if table_name not in CREATE_TABLES_DDL:
            raise KeyError(f"DDL não definido para a tabela {table_name}.")

        if self.table_exists(table_name):
            logging.info("Tabela %s já existe. Nenhuma ação necessária.", table_name)
            return

        ddl = CREATE_TABLES_DDL[table_name]
        logging.info("Criando tabela %s...", table_name)
        with self.connector.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(ddl)
            conn.commit()
        logging.info("Tabela %s criada com sucesso.", table_name)

    def ensure_all_tables(self) -> None:
        """
        Garante que TODAS as tabelas FV (FV_*) existam no DW.
        """
        for table_name in CREATE_TABLES_DDL.keys():
            self.create_table_if_not_exists(table_name)
