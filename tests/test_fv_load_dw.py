import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app_sync_fv.config import AppConfig
from app_sync_fv.graphql_client import GraphQLClient
from app_sync_fv.fv_service import FVService
from app_sync_fv.db_connection import DBConfig, SQLServerConnector
from app_sync_fv.fv_schema import FVSchemaManager
from app_sync_fv.fv_repository import FVRepositoryDW


def main():
    # AWS / GraphQL
    app_cfg = AppConfig.from_env()
    client = GraphQLClient(app_cfg)
    service = FVService(client, batch_size=app_cfg.batch_size)

    # DW
    db_cfg = DBConfig.from_env()
    connector = SQLServerConnector(db_cfg)

    # Garante tabelas FV
    schema_manager = FVSchemaManager(connector)
    schema_manager.ensure_all_tables()

    # Extrai da AWS
    tipos = service.get_tipos_servico()
    visitas = service.get_registros_visita()
    anexos = service.get_registros_visita_anexos()
    servicos = service.get_registros_visita_servicos()

    print("Vai carregar no DW:")
    print(" - Tipos:", len(tipos))
    print(" - Visitas:", len(visitas))
    print(" - Anexos:", len(anexos))
    print(" - Serviços:", len(servicos))

    # Carrega no DW (TRUNCATE + INSERT)
    repo = FVRepositoryDW(connector)
    repo.load_tipos_servico(tipos)
    repo.load_registros_visita(visitas)
    repo.load_registros_visita_anexos(anexos)
    repo.load_registros_visita_servicos(servicos)

    print("Carga FV concluída no DW_ALVORADA.")


if __name__ == "__main__":
    main()
