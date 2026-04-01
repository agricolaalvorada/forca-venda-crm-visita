import logging
import sys
from datetime import datetime
from pathlib import Path

from app_sync_fv.config import AppConfig
from app_sync_fv.graphql_client import GraphQLClient
from app_sync_fv.fv_service import FVService
from app_sync_fv.db_connection import DBConfig, SQLServerConnector
from app_sync_fv.fv_schema import FVSchemaManager
from app_sync_fv.fv_repository import FVRepositoryDW


def setup_logging() -> Path:
    """
    Configura logging para console + arquivo em ./logs.
    Retorna o caminho completo do arquivo de log criado.
    """
    base_dir = Path(__file__).resolve().parent
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_file = logs_dir / f"app_sync_fv_{datetime.now():%Y%m%d_%H%M%S}.log"

    # logger raiz
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # remove handlers antigos (se houver)
    for h in list(logger.handlers):
        logger.removeHandler(h)

    # Formato para o ARQUIVO (mais completo)
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    # Formato para o CONSOLE (mais visual)
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)-15s | %(message)s",
        "%H:%M:%S",
    )

    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Handler para arquivo
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return log_file


def main() -> None:
    log_file = setup_logging()
    logger = logging.getLogger("APP_SYNC_FV")

    logger.info("")
    logger.info("====================================================================")
    logger.info("🚀 INÍCIO da carga FV (AWS AppSync ➜ DW_ALVORADA)")
    logger.info("📄 Log em arquivo: %s", log_file)
    logger.info("====================================================================")

    try:
        # ---------- Configurações ----------
        logger.info("")
        logger.info("🔧 [CONFIG] Carregando configurações (.env)...")
        app_cfg = AppConfig.from_env()
        db_cfg = DBConfig.from_env()
        logger.info("🔧 [CONFIG] Configurações carregadas com sucesso.")

        # ---------- Conexões / serviços ----------
        logger.info("")
        logger.info("☁️ [AWS] Criando cliente GraphQL (AppSync)...")
        client = GraphQLClient(app_cfg)

        logger.info("🗄️ [DW] Criando conector SQL Server (DW_ALVORADA)...")
        connector = SQLServerConnector(db_cfg)

        logger.info("🧩 [SERVIÇOS] Instanciando FVService (AWS) e FVRepositoryDW (DW)...")
        service = FVService(client, batch_size=app_cfg.batch_size)
        schema_manager = FVSchemaManager(connector)
        repo = FVRepositoryDW(connector)

        # ---------- Garantir tabelas ----------
        logger.info("")
        logger.info("📐 [SCHEMA] Verificando/criando tabelas FV no DW...")
        schema_manager.ensure_all_tables()
        logger.info("📐 [SCHEMA] Tabelas FV prontas no DW_ALVORADA.")

        # ---------- Extração da AWS ----------
        logger.info("")
        logger.info("☁️ [AWS] Buscando dados na AWS AppSync (tipos, visitas, anexos, serviços)...")

        tipos = service.get_tipos_servico()
        visitas = service.get_registros_visita()
        anexos = service.get_registros_visita_anexos()
        servicos = service.get_registros_visita_servicos()

        logger.info(
            "☁️ [AWS] Dados obtidos: tipos=%d | visitas=%d | anexos=%d | serviços=%d",
            len(tipos),
            len(visitas),
            len(anexos),
            len(servicos),
        )

        # ---------- Carga no DW (TRUNCATE + INSERT) ----------
        logger.info("")
        logger.info("📥 [DW] Iniciando carga no DW_ALVORADA (TRUNCATE + INSERT)...")

        logger.info("📥 [DW] Carregando tabela dbo.FV_TIPO_SERVICO_VISITA...")
        repo.load_tipos_servico(tipos)

        logger.info("📥 [DW] Carregando tabela dbo.FV_REGISTRO_VISITA...")
        repo.load_registros_visita(visitas)

        logger.info("📥 [DW] Carregando tabela dbo.FV_REGISTRO_VISITA_ANEXOS...")
        repo.load_registros_visita_anexos(anexos)

        logger.info("📥 [DW] Carregando tabela dbo.FV_REGISTRO_VISITA_SERVICOS...")
        repo.load_registros_visita_servicos(servicos)

        logger.info("")
        logger.info("✅ Carga FV concluída com sucesso no DW_ALVORADA.")
        logger.info("====================================================================")
        logger.info("🏁 FIM da execução sem erros.")
        logger.info("====================================================================")

    except Exception as e:
        logger.exception("❌ ERRO durante a execução da carga FV: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
