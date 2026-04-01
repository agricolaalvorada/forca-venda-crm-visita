import os
import sys

# adiciona a pasta raiz (APP_SYNC_FV) ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app_sync_fv.config import AppConfig
from app_sync_fv.graphql_client import GraphQLClient
from app_sync_fv.fv_service import FVService


def main():
    cfg = AppConfig.from_env()
    client = GraphQLClient(cfg)
    service = FVService(client, batch_size=cfg.batch_size)

    tipos = service.get_tipos_servico()
    visitas = service.get_registros_visita()
    anexos = service.get_registros_visita_anexos()
    servicos = service.get_registros_visita_servicos()

    print("Tipos de serviço:", len(tipos))
    print("Visitas:", len(visitas))
    print("Anexos:", len(anexos))
    print("Serviços:", len(servicos))

    if visitas:
        print("\nPrimeira visita:")
        print(visitas[0])


if __name__ == "__main__":
    main()
