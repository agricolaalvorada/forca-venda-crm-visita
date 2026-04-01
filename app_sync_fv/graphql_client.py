# app_sync_fv/graphql_client.py
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests

# Compatibilidade: rodar como pacote (imports relativos) ou como script (imports absolutos)
try:
    from .config import AppConfig  # type: ignore
except Exception:  # pragma: no cover
    from app_sync_fv.config import AppConfig  # type: ignore


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


class GraphQLClient:
    """
    Cliente genérico para chamadas GraphQL no AppSync (AWS).
    - Usa URL e API Key vindas do AppConfig.
    - Expõe BOTH: .query() e .execute() para compatibilidade.
    """

    def __init__(self, config: AppConfig, timeout: int = 60) -> None:
        self.api_url = config.api_url
        self.headers = {
            "x-api-key": config.api_key,
            "Content-Type": "application/json",
        }
        self.timeout = timeout

    def query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Alias compatível com FVService: retorna apenas o dict de 'data'."""
        return self.execute(query=query, variables=variables)

    def execute(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executa uma query/mutation GraphQL e retorna data['data'].
        Lança exceção se houver HTTP error ou GraphQL errors.
        """
        payload = {"query": query, "variables": variables or {}}

        logging.debug("GraphQL request payload: %s", payload)

        resp = requests.post(
            self.api_url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout,
        )
        resp.raise_for_status()

        data = resp.json()

        errors = data.get("errors") or []
        if errors:
            first = errors[0]
            msg = first.get("message") if isinstance(first, dict) else str(first)
            raise RuntimeError(f"GraphQL error: {msg}")

        if "data" not in data:
            raise RuntimeError(f"Resposta GraphQL sem 'data': {data}")

        return data["data"]
