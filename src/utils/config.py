"""Carregamento da configuração do projeto."""

from pathlib import Path

import yaml

RAIZ_PROJETO = Path(__file__).resolve().parents[2]


def carregar_config(caminho: Path | str | None = None) -> dict:
    """
    Lê config/config.yaml. Falha com mensagem útil se ele não existir ainda.
    """
    caminho = Path(caminho) if caminho else RAIZ_PROJETO / "config" / "config.yaml"

    if not caminho.exists():
        exemplo = RAIZ_PROJETO / "config" / "config.example.yaml"
        raise FileNotFoundError(
            f"Configuração não encontrada em {caminho}.\n"
            f"Copie {exemplo.name} para config.yaml e ajuste o caminho do corpus."
        )

    with open(caminho, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    raiz_corpus = cfg.get("corpus", {}).get("raiz", "")
    if not raiz_corpus or raiz_corpus == "MUDE_AQUI":
        raise ValueError(
            "Defina corpus.raiz em config/config.yaml antes de rodar os scripts."
        )
    if not Path(raiz_corpus).is_dir():
        raise FileNotFoundError(f"corpus.raiz não existe: {raiz_corpus}")

    return cfg
