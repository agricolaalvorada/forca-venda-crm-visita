# config.py
import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Carrega o .env da pasta do projeto
load_dotenv()


@dataclass
class AppConfig:
    """
    Configuração da aplicação para acesso à AWS FV (GraphQL).
    Lê tudo do .env.
    """
    api_url: str
    api_key: str
    batch_size: int = 500

    @classmethod
    def from_env(cls) -> "AppConfig":
        api_url = os.getenv("AWS_FV_GRAPHQL_URL")
        api_key = os.getenv("AWS_FV_API_KEY")
        batch_size_str = os.getenv("FV_BATCH_SIZE", "500")

        if not api_url:
            raise RuntimeError("AWS_FV_GRAPHQL_URL não configurada no .env")

        if not api_key:
            raise RuntimeError("AWS_FV_API_KEY não configurada no .env")

        try:
            batch_size = int(batch_size_str)
        except ValueError:
            raise RuntimeError(f"FV_BATCH_SIZE inválido: {batch_size_str!r}")

        return cls(
            api_url=api_url,
            api_key=api_key,
            batch_size=batch_size,
        )
