#!/usr/bin/env python3
"""
Lista os arquivos que precisam revisão, ordenados por prioridade.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.config import RAIZ_PROJETO


if __name__ == "__main__":
    cfg = RAIZ_PROJETO / 'relatorios' / 'qualidade_markdown.csv'

    with open(cfg, encoding='utf-8-sig') as f:
        dados = list(csv.DictReader(f))

    # Filtrar: apenas os que precisam revisão (qualidade <= 0.7)
    para_revisar = [d for d in dados if float(d['qualidade']) <= 0.7]

    # Ordenar por qualidade (piores primeiro)
    para_revisar.sort(key=lambda x: float(x['qualidade']))

    print(f"{'='*70}")
    print(f"ARQUIVOS PARA REVISÃO PRIORITÁRIA")
    print(f"{'='*70}")
    print(f"Total: {len(para_revisar)} arquivos\n")

    print(f"{'Arquivo':<35} {'Qualidade':<12} {'Headings':<10}")
    print(f"{'-'*70}")

    for d in para_revisar:
        print(f"{d['arquivo']:<35} {d['qualidade']:<12} {d['n_headings']:<10}")

    print(f"\n{'='*70}")
    print(f"Pasta para revisar: data/interim/markdown_bruto/")
    print(f"{'='*70}")
