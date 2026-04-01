# app_sync_fv/fv_service.py
import logging
from typing import Dict, Any, List

from .graphql_client import GraphQLClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ---------- Queries GraphQL ----------

QUERY_LIST_TIPO_SERVICO_VISITA = """
query listTipoServicoVisita {
  listTipoServicoVisita {
    id
    descricao
  }
}
"""

QUERY_LIST_REGISTRO_VISITA_PAGINADA = """
query listRegistroVisitaPaginada($skip: Int, $take: Int) {
  listRegistroVisitaPaginada(skip: $skip, take: $take) {
    id
    cod_cliente
    cod_fazenda
    cod_cultura
    cod_safra
    observacoes
    data_inicio
    data_fim
    tipo_atendimento
    email
    data_hora
    status
    centro
    bp_solicitante
  }
}
"""

QUERY_LIST_REGISTRO_VISITA_ANEXOS_PAGINADA = """
query listRegistroVisitaAnexosPaginada($skip: Int, $take: Int) {
  listRegistroVisitaAnexosPaginada(skip: $skip, take: $take) {
    id
    id_visita
    url
    legenda
    latitude
    longitude
  }
}
"""

QUERY_LIST_REGISTRO_VISITA_SERVICOS_PAGINADA = """
query listRegistroVisitaServicosPaginada($skip: Int, $take: Int) {
  listRegistroVisitaServicosPaginada(skip: $skip, take: $take) {
    id
    id_visita
    id_servico
  }
}
"""


class FVService:
    """
    Serviço de domínio da FV:
    - chama todas as queries GraphQL
    - faz paginação skip/take onde precisa
    """

    def __init__(self, client: GraphQLClient, batch_size: int = 500) -> None:
        self.client = client
        self.batch_size = batch_size

    # ---------- helper interno de paginação ----------

    def _fetch_all_paged(self, query: str, root_field: str) -> List[Dict[str, Any]]:
        """
        Faz paginação usando skip/take:
        - take = batch_size fixo
        - skip = 0, batch_size, 2*batch_size, ...
        Para quando o batch vier vazio ou com menos registros que batch_size.
        """
        all_rows: List[Dict[str, Any]] = []
        skip = 0

        while True:
            variables = {"skip": skip, "take": self.batch_size}
            logging.info(
                "Buscando %s: skip=%s, take=%s",
                root_field,
                skip,
                self.batch_size,
            )
            data = self.client.query(query, variables)
            batch = data.get(root_field) or []
            qtd = len(batch)
            logging.info("Batch retornado: %d linhas", qtd)

            if not batch:
                break

            all_rows.extend(batch)

            if qtd < self.batch_size:
                # última página
                break

            skip += self.batch_size

        logging.info("Total de linhas em %s: %d", root_field, len(all_rows))
        return all_rows

    # ---------- métodos públicos ----------

    def get_tipos_servico(self) -> List[Dict[str, Any]]:
        logging.info("Buscando tipos de serviço (listTipoServicoVisita)...")
        data = self.client.query(QUERY_LIST_TIPO_SERVICO_VISITA)
        rows = data.get("listTipoServicoVisita") or []
        logging.info("Total de tipos de serviço: %d", len(rows))
        return rows

    def get_registros_visita(self) -> List[Dict[str, Any]]:
        return self._fetch_all_paged(
            QUERY_LIST_REGISTRO_VISITA_PAGINADA,
            "listRegistroVisitaPaginada",
        )

    def get_registros_visita_anexos(self) -> List[Dict[str, Any]]:
        return self._fetch_all_paged(
            QUERY_LIST_REGISTRO_VISITA_ANEXOS_PAGINADA,
            "listRegistroVisitaAnexosPaginada",
        )

    def get_registros_visita_servicos(self) -> List[Dict[str, Any]]:
        return self._fetch_all_paged(
            QUERY_LIST_REGISTRO_VISITA_SERVICOS_PAGINADA,
            "listRegistroVisitaServicosPaginada",
        )
