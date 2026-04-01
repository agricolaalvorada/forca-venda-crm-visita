import os
import sys

# adiciona a pasta raiz (APP_SYNC_FV) ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app_sync_fv.config import AppConfig
from app_sync_fv.graphql_client import GraphQLClient

QUERY_LIST_TIPO_SERVICO_VISITA = """
query listTipoServicoVisita {
  listTipoServicoVisita {
    id
    descricao
  }
}
"""

def main():
    cfg = AppConfig.from_env()
    client = GraphQLClient(cfg)

    data = client.query(QUERY_LIST_TIPO_SERVICO_VISITA)
    tipos = data.get("listTipoServicoVisita") or []

    print("Total de tipos de serviço:", len(tipos))
    if tipos:
        print("Primeiro registro:", tipos[0])

if __name__ == "__main__":
    main()
