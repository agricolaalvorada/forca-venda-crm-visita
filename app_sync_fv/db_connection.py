# app_sync_fv/db_connection.py
import os
import logging
from dataclasses import dataclass
from typing import Optional

import pyodbc
from dotenv import load_dotenv

# garante que o .env seja carregado
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


@dataclass
class DBConfig:
    """
    Configuração de conexão com o SQL Server (DW).
    Lê as variáveis do .env:

    DB_HOST, DB_PORT, DB_NAME,
    AUTH_METHOD (sql/windows),
    DB_USER, DB_PASSWORD,
    DB_DRIVER, DB_TIMEOUT
    """
    host: str
    port: int
    name: str
    auth_method: str  # 'sql' ou 'windows'
    user: Optional[str]
    password: Optional[str]
    driver: str
    timeout: int

    @classmethod
    def from_env(cls) -> "DBConfig":
        host = os.getenv("DB_HOST")
        port_str = os.getenv("DB_PORT", "1433")
        name = os.getenv("DB_NAME")
        auth_method = os.getenv("AUTH_METHOD", "sql").lower()
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
        timeout_str = os.getenv("DB_TIMEOUT", "30")

        if not host:
            raise RuntimeError("DB_HOST não configurado no .env")
        if not name:
            raise RuntimeError("DB_NAME não configurado no .env")

        try:
            port = int(port_str)
        except ValueError:
            raise RuntimeError(f"DB_PORT inválido: {port_str!r}")

        try:
            timeout = int(timeout_str)
        except ValueError:
            raise RuntimeError(f"DB_TIMEOUT inválido: {timeout_str!r}")

        if auth_method not in ("sql", "windows"):
            raise RuntimeError(f"AUTH_METHOD inválido: {auth_method!r} (use 'sql' ou 'windows')")

        return cls(
            host=host,
            port=port,
            name=name,
            auth_method=auth_method,
            user=user,
            password=password,
            driver=driver,
            timeout=timeout,
        )


class SQLServerConnector:
    """
    Responsável por montar a connection string e abrir a conexão pyodbc.
    """

    def __init__(self, config: DBConfig) -> None:
        self.config = config

    def get_connection(self) -> pyodbc.Connection:
        # garante { } em torno do nome do driver
        driver = self.config.driver
        if not driver.startswith("{"):
            driver = "{" + driver + "}"
        if not driver.endswith("}"):
            driver = driver + "}"

        base = (
            f"DRIVER={driver};"
            f"SERVER={self.config.host},{self.config.port};"
            f"DATABASE={self.config.name};"
            f"TrustServerCertificate=Yes;"
            f"Connection Timeout={self.config.timeout};"
        )

        if self.config.auth_method == "windows":
            conn_str = base + "Trusted_Connection=Yes;"
        else:
            if not self.config.user or not self.config.password:
                raise RuntimeError(
                    "DB_USER/DB_PASSWORD não configurados para AUTH_METHOD=sql."
                )
            conn_str = base + f"UID={self.config.user};PWD={self.config.password};"

        logging.info(
            "Conectando ao SQL Server %s:%s / DB=%s (auth=%s)...",
            self.config.host,
            self.config.port,
            self.config.name,
            self.config.auth_method,
        )
        return pyodbc.connect(conn_str)
