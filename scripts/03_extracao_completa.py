#!/usr/bin/env python3
"""
Extração completa em TODAS as 350 páginas de desenvolvimento.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.gabarito.extrator_automatico import extrair_lote
from src.utils.config import RAIZ_PROJETO, carregar_config


if __name__ == "__main__":
    cfg = carregar_config()
    corpus_raiz = Path(cfg['corpus']['raiz'])

    # Extrair TODAS as 350 páginas de desenvolvimento
    indices_dev = RAIZ_PROJETO / 'data' / 'interim' / 'indice_desenvolvimento.csv'
    saida_dir = RAIZ_PROJETO / 'data' / 'interim' / 'markdown_bruto'

    print("=" * 60)
    print("EXTRAÇÃO COMPLETA — 350 PÁGINAS DE DESENVOLVIMENTO")
    print("=" * 60)
    print()

    extrair_lote(corpus_raiz, indices_dev, saida_dir, max_arquivos=None)
