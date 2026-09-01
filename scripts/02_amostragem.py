#!/usr/bin/env python3
"""
Amostragem estratificada do corpus.
"""

import csv
import random
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.config import RAIZ_PROJETO, carregar_config


def amostragem_estratificada(config: dict, n_dev: int = 350, n_teste: int = 120):
    """Seleciona páginas para desenvolvimento e teste."""

    inv_path = RAIZ_PROJETO / config['saida']['relatorios'] / 'inventario.csv'
    with open(inv_path, encoding='utf-8-sig') as f:
        inventario = list(csv.DictReader(f))

    print(f"Total de páginas no corpus: {len(inventario)}")

    por_edicao = defaultdict(list)
    for row in inventario:
        ed = row['pasta_edicao']
        por_edicao[ed].append(row)

    print(f"Total de edições: {len(por_edicao)}")

    edicoes_ordenadas = sorted(por_edicao.keys())
    edicoes_teste = set(edicoes_ordenadas[-2:])

    print(f"Edições reservadas para teste: {sorted(edicoes_teste)}")

    paginas_teste = []
    for ed in edicoes_teste:
        paginas_teste.extend(por_edicao[ed])

    paginas_dev_candidatas = []
    for ed in edicoes_ordenadas:
        if ed not in edicoes_teste:
            paginas_dev_candidatas.extend(por_edicao[ed])

    por_tipo = defaultdict(list)
    for row in paginas_dev_candidatas:
        tipo = row['tipo_pagina']
        por_tipo[tipo].append(row)

    print(f"\nDistribuição de tipos (dev candidatas):")
    for tipo, pages in sorted(por_tipo.items()):
        print(f"  {tipo}: {len(pages)}")

    random.seed(42)
    paginas_dev = []
    for tipo, pages in por_tipo.items():
        n_tipo = max(1, int(len(pages) / len(paginas_dev_candidatas) * n_dev))
        amostra = random.sample(pages, min(n_tipo, len(pages)))
        paginas_dev.extend(amostra)

    if len(paginas_dev) < n_dev:
        faltam = n_dev - len(paginas_dev)
        restantes = [p for p in paginas_dev_candidatas if p not in paginas_dev]
        paginas_dev.extend(random.sample(restantes, min(faltam, len(restantes))))

    paginas_dev = paginas_dev[:n_dev]
    paginas_teste = paginas_teste[:n_teste]

    print(f"\nAmostra final:")
    print(f"  Desenvolvimento: {len(paginas_dev)} páginas")
    print(f"  Teste: {len(paginas_teste)} páginas")

    saida_dir = RAIZ_PROJETO / 'data' / 'interim'
    saida_dir.mkdir(parents=True, exist_ok=True)

    with open(saida_dir / 'indice_desenvolvimento.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=paginas_dev[0].keys())
        w.writeheader()
        w.writerows(paginas_dev)

    with open(saida_dir / 'indice_teste.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=paginas_teste[0].keys())
        w.writeheader()
        w.writerows(paginas_teste)

    print(f"\nIndices salvos em:")
    print(f"  {saida_dir / 'indice_desenvolvimento.csv'}")
    print(f"  {saida_dir / 'indice_teste.csv'}")


if __name__ == "__main__":
    cfg = carregar_config()
    amostragem_estratificada(cfg, n_dev=350, n_teste=120)
