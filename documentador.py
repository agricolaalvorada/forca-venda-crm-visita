import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Set, TextIO, Dict, Any
from dataclasses import dataclass, field


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@dataclass(slots=True)
class ConsolidatorConfig:
    """Configurações de infraestrutura e limites (Sharding & Filtering)."""

    target_dir: Path
    output_base_name: str
    max_file_size_kb: int = 500
    max_chunk_size_mb: int = 3
    allowed_extensions: Set[str] = field(
        default_factory=lambda: {".py", ".sql", ".md", ".yaml", ".yml"}
    )
    ignore_dirs: Set[str] = field(
        default_factory=lambda: {
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            ".idea",
            "data",
            "logs",
            "assets",
            "node_modules",
        }
    )
    ignore_files: Set[str] = field(
        default_factory=lambda: {"build_context.py", "poetry.lock", "requirements.txt"}
    )

    def __post_init__(self) -> None:
        self.target_dir = Path(self.target_dir).resolve()
        self.allowed_extensions = {ext.lower() for ext in self.allowed_extensions}

        if self.max_file_size_kb <= 0:
            raise ValueError("max_file_size_kb deve ser maior que zero.")

        if self.max_chunk_size_mb <= 0:
            raise ValueError("max_chunk_size_mb deve ser maior que zero.")


class ProjectConsolidator:
    def __init__(self, config: ConsolidatorConfig):
        self.config = config
        self.target_dir = config.target_dir

        self.files_processed = 0
        self.files_skipped_size = 0
        self.files_skipped_invalid = 0
        self.files_failed = 0
        self.shards_created = 0
        
        self._architecture_tree_cache = ""

    def _is_ignored_path(self, path: Path) -> bool:
        return any(part in self.config.ignore_dirs for part in path.parts)

    def _get_valid_files(self) -> List[Path]:
        """Varre o diretório uma única vez aplicando todos os filtros."""
        valid_files: List[Path] = []
        max_bytes = self.config.max_file_size_kb * 1024

        for file_path in self.target_dir.rglob("*"):
            if self._is_ignored_path(file_path):
                continue

            if not file_path.is_file():
                continue

            if file_path.name in self.config.ignore_files:
                self.files_skipped_invalid += 1
                continue

            if file_path.suffix.lower() not in self.config.allowed_extensions:
                self.files_skipped_invalid += 1
                continue

            try:
                file_size = file_path.stat().st_size
            except OSError as exc:
                logging.warning("Falha ao obter tamanho do arquivo %s: %s", file_path, exc)
                self.files_failed += 1
                continue

            if file_size > max_bytes:
                logging.warning(
                    "Ignorado por tamanho (%.1f KB): %s",
                    file_size / 1024,
                    file_path.relative_to(self.target_dir),
                )
                self.files_skipped_size += 1
                continue

            valid_files.append(file_path)

        # Ordenação global para garantir determinismo
        return sorted(valid_files, key=lambda p: str(p.relative_to(self.target_dir)).lower())

    def _build_tree_from_paths(self, paths: List[Path]) -> str:
        """Constrói a representação visual da árvore em memória a partir da lista já filtrada, eliminando I/O."""
        tree_dict: Dict[str, Any] = {}
        
        # Constrói o dicionário aninhado representando a estrutura
        for p in paths:
            rel_path = p.relative_to(self.target_dir)
            current_level = tree_dict
            for part in rel_path.parts:
                current_level = current_level.setdefault(part, {})

        def render_node(node: Dict[str, Any], prefix: str = "") -> List[str]:
            lines = []
            keys = sorted(node.keys(), key=lambda k: (bool(node[k]), k.lower())) # Arquivos primeiro, pastas depois
            
            for index, key in enumerate(keys):
                connector = "└── " if index == len(keys) - 1 else "├── "
                lines.append(f"{prefix}{connector}{key}\n")
                
                if node[key]:  # Se tem filhos (é um diretório)
                    extension_prefix = "    " if index == len(keys) - 1 else "│   "
                    lines.extend(render_node(node[key], prefix + extension_prefix))
                    
            return lines

        return "".join(render_node(tree_dict))

    def _generate_metadata_header(self, chunk_index: int) -> str:
        """Cria o cabeçalho base para os metadados do shard."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"{'=' * 80}\n"
            f"ARTEFATO DE CONTEXTO DO PROJETO - PARTE {chunk_index}\n"
            f"Gerado em: {timestamp}\n"
            f"Diretório Alvo: {self.target_dir}\n"
            f"{'=' * 80}\n\n"
        )

    def _get_chunk_filename(self, index: int) -> Path:
        """Gera o nome do arquivo particionado na estrutura correta."""
        base_path = Path(self.config.output_base_name)

        if not base_path.is_absolute():
            base_path = self.target_dir / base_path

        base_path.parent.mkdir(parents=True, exist_ok=True)

        return base_path.with_name(f"{base_path.stem}_pt{index}{base_path.suffix}")

    @staticmethod
    def _get_text_size_bytes(text: str) -> int:
        """Calcula o footprint real do texto em bytes UTF-8."""
        return len(text.encode("utf-8"))

    def _build_file_block(self, file_path: Path) -> str:
        """Gera o bloco formatado do conteúdo do arquivo."""
        relative_path = file_path.relative_to(self.target_dir)
        content = file_path.read_text(encoding="utf-8", errors="replace")

        return (
            f"\n{'#' * 80}\n"
            f"### ARQUIVO: {relative_path} ###\n"
            f"{'#' * 80}\n\n"
            f"{content}\n\n"
        )

    def _open_new_shard(self, chunk_index: int) -> tuple[TextIO, Path, int]:
        """Abre um novo shard e injeta obrigatoriamente a árvore de arquitetura."""
        shard_path = self._get_chunk_filename(chunk_index)
        shard_file = open(shard_path, "w", encoding="utf-8")

        # 1. Escreve Header
        header = self._generate_metadata_header(chunk_index)
        shard_file.write(header)
        shard_size = self._get_text_size_bytes(header)

        # 2. Injeta a Árvore de Arquitetura em TODO shard para manter contexto espacial
        tree_header = (
            "=== ÁRVORE DE ARQUITETURA (ARQUIVOS PROCESSADOS) ===\n"
            f"{self._architecture_tree_cache}"
            f"{'=' * 80}\n\n"
        )
        shard_file.write(tree_header)
        shard_size += self._get_text_size_bytes(tree_header)

        self.shards_created += 1

        return shard_file, shard_path, shard_size

    def run(self) -> None:
        """Executa a extração, gera a topologia e orquestra o sharding."""
        if not self.target_dir.exists():
            raise FileNotFoundError(f"Diretório alvo não encontrado: {self.target_dir}")

        if not self.target_dir.is_dir():
            raise NotADirectoryError(f"O caminho informado não é um diretório: {self.target_dir}")

        logging.info("Iniciando varredura e consolidação em: %s", self.target_dir)

        # Single-pass de I/O para identificar os arquivos válidos
        files_to_process = self._get_valid_files()

        if not files_to_process:
            logging.warning("Nenhum arquivo válido encontrado na topologia.")
            return

        # Gera a árvore visual estritamente baseada no que foi validado
        self._architecture_tree_cache = self._build_tree_from_paths(files_to_process)

        max_chunk_bytes = self.config.max_chunk_size_mb * 1024 * 1024
        chunk_index = 1

        out_file, current_file_path, current_chunk_size = self._open_new_shard(chunk_index)

        try:
            for file_path in files_to_process:
                try:
                    block = self._build_file_block(file_path)
                    block_bytes = self._get_text_size_bytes(block)

                    # Verifica se o bloco atual estoura o limite do shard
                    if current_chunk_size + block_bytes > max_chunk_bytes and current_chunk_size > 0:
                        out_file.close()
                        logging.info(
                            "Shard finalizado: %s (%.2f MB)",
                            current_file_path.name,
                            current_chunk_size / (1024 * 1024),
                        )

                        chunk_index += 1
                        out_file, current_file_path, current_chunk_size = self._open_new_shard(chunk_index)

                    out_file.write(block)
                    current_chunk_size += block_bytes
                    self.files_processed += 1

                except Exception as exc:
                    self.files_failed += 1
                    logging.error("Falha ao ler/processar %s: %s", file_path, exc)

        finally:
            out_file.close()

        logging.info(
            "Shard finalizado: %s (%.2f MB)",
            current_file_path.name,
            current_chunk_size / (1024 * 1024),
        )
        
        logging.info("--- Resumo da Consolidação ---")
        logging.info("Arquivos processados: %d", self.files_processed)
        logging.info("Arquivos ignorados (tamanho): %d", self.files_skipped_size)
        logging.info("Arquivos ignorados (filtro): %d", self.files_skipped_invalid)
        logging.info("Arquivos com falha de leitura: %d", self.files_failed)
        logging.info("Total de shards gerados: %d", self.shards_created)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ETL de repositório com sharding para LLM.")
    parser.add_argument(
        "-t",
        "--target",
        type=str,
        default=".",
        help="Diretório alvo do projeto.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="contexto_projeto.txt",
        help="Nome base do arquivo gerado.",
    )
    parser.add_argument(
        "--max-file-kb",
        type=int,
        default=500,
        help="Tamanho máximo por arquivo individual em KB.",
    )
    parser.add_argument(
        "--max-chunk-mb",
        type=int,
        default=3,
        help="Tamanho máximo de cada shard em MB.",
    )
    return parser


def main() -> None:
    setup_logging()

    parser = build_parser()
    args = parser.parse_args()

    config = ConsolidatorConfig(
        target_dir=Path(args.target),
        output_base_name=args.output,
        max_file_size_kb=args.max_file_kb,
        max_chunk_size_mb=args.max_chunk_mb,
    )

    app = ProjectConsolidator(config)
    app.run()


if __name__ == "__main__":
    main()