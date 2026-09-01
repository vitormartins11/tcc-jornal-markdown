#!/usr/bin/env python3
"""
Passo 1 — Inventário e higiene do corpus (Fase 0.4 do plano).

Lê o caminho do corpus de config/config.yaml, varre todas as páginas e grava
três arquivos em relatorios/:

    inventario.csv           uma linha por página
    inventario_edicoes.csv   uma linha por edição
    anomalias.txt            o que precisa da sua atenção

Rode assim, a partir da raiz do projeto:

    python scripts/01_inventario.py

Leia anomalias.txt antes de qualquer processamento em lote.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.inventario.inventario import varrer  # noqa: E402
from src.utils.config import RAIZ_PROJETO, carregar_config  # noqa: E402


def main() -> None:
    cfg = carregar_config()
    raiz_corpus = Path(cfg["corpus"]["raiz"])
    saida = RAIZ_PROJETO / cfg["saida"]["relatorios"]

    print(f"Corpus : {raiz_corpus}")
    print(f"Saída  : {saida}")
    print("Varrendo... (alguns minutos para milhares de PDFs)\n")

    varrer(raiz_corpus, saida)


if __name__ == "__main__":
    main()
