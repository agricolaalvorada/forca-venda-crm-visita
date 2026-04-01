# app_sync_fv/fv_repository.py
from __future__ import annotations

import logging
from typing import List, Dict, Any

from .db_connection import SQLServerConnector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


class FVRepositoryDW:
    """
    Responsável por carregar os dados da FV nas tabelas do DW:
    - sempre faz TRUNCATE antes de inserir (carga full).
    """

    def __init__(self, connector: SQLServerConnector) -> None:
        self.connector = connector

    # ---------------- helpers internos ----------------

    def _truncate_table(self, table_name: str) -> None:
        logging.info("TRUNCATE TABLE %s ...", table_name)
        with self.connector.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"TRUNCATE TABLE {table_name};")
            conn.commit()
        logging.info("TRUNCATE TABLE %s concluído.", table_name)

    def _bulk_insert(self, sql: str, rows: List[tuple]) -> None:
        if not rows:
            logging.info("Nenhuma linha para inserir. SQL: %s", sql.strip())
            return

        logging.info("Inserindo %d linhas...", len(rows))
        with self.connector.get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.fast_executemany = True
            except Exception:
                pass
            cur.executemany(sql, rows)
            conn.commit()
        logging.info("Insert concluído (%d linhas).", len(rows))

    # ---------------- cargas públicas ----------------

    def load_tipos_servico(self, tipos: List[Dict[str, Any]]) -> None:
        table = "dbo.FV_TIPO_SERVICO_VISITA"
        self._truncate_table(table)

        sql = f"""
            INSERT INTO {table} (id, descricao)
            VALUES (?, ?);
        """

        rows: List[tuple] = []
        for t in tipos:
            rows.append((
                t.get("id"),
                t.get("descricao"),
            ))

        self._bulk_insert(sql, rows)

    def load_registros_visita(self, visitas: List[Dict[str, Any]]) -> None:
        table = "dbo.FV_REGISTRO_VISITA"
        self._truncate_table(table)

        sql = f"""
            INSERT INTO {table} (
                id,
                cod_cliente,
                cod_fazenda,
                cod_cultura,
                cod_safra,
                observacoes,
                data_inicio,
                data_fim,
                tipo_atendimento,
                email,
                data_hora,
                status,
                centro,
                bp_solicitante
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        rows: List[tuple] = []
        for v in visitas:
            rows.append((
                v.get("id"),
                v.get("cod_cliente"),
                v.get("cod_fazenda"),
                v.get("cod_cultura"),
                v.get("cod_safra"),
                v.get("observacoes"),
                v.get("data_inicio"),
                v.get("data_fim"),
                v.get("tipo_atendimento"),
                v.get("email"),
                v.get("data_hora"),
                v.get("status"),
                v.get("centro"),
                v.get("bp_solicitante"),  # <-- CORRIGIDO (antes faltava)
            ))

        self._bulk_insert(sql, rows)

    def load_registros_visita_anexos(self, anexos: List[Dict[str, Any]]) -> None:
        table = "dbo.FV_REGISTRO_VISITA_ANEXOS"
        self._truncate_table(table)

        sql = f"""
            INSERT INTO {table} (
                id,
                id_visita,
                url,
                legenda,
                latitude,
                longitude
            )
            VALUES (?, ?, ?, ?, ?, ?);
        """

        rows: List[tuple] = []
        for a in anexos:
            rows.append((
                a.get("id"),
                a.get("id_visita"),
                a.get("url"),
                a.get("legenda"),
                a.get("latitude"),
                a.get("longitude"),
            ))

        self._bulk_insert(sql, rows)

    def load_registros_visita_servicos(self, servicos: List[Dict[str, Any]]) -> None:
        table = "dbo.FV_REGISTRO_VISITA_SERVICOS"
        self._truncate_table(table)

        sql = f"""
            INSERT INTO {table} (
                id,
                id_visita,
                id_servico
            )
            VALUES (?, ?, ?);
        """

        rows: List[tuple] = []
        for s in servicos:
            rows.append((
                s.get("id"),
                s.get("id_visita"),
                s.get("id_servico"),
            ))

        self._bulk_insert(sql, rows)
