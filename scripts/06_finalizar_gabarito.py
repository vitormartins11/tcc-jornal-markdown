#!/usr/bin/env python3
"""
Copia todos os 350 Markdown extraídos para data/processed/ (gabarito final).
"""

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.config import RAIZ_PROJETO


if __name__ == "__main__":
    origem = RAIZ_PROJETO / 'data' / 'interim' / 'markdown_bruto'
    destino = RAIZ_PROJETO / 'data' / 'processed'

    destino.mkdir(parents=True, exist_ok=True)

    print(f"{'='*60}")
    print(f"FINALIZANDO GABARITO — COPIANDO PARA data/processed/")
    print(f"{'='*60}\n")

    md_files = list(origem.glob('*.md'))
    print(f"Copiando {len(md_files)} arquivos...\n")

    for i, src in enumerate(sorted(md_files), 1):
        dst = destino / src.name
        shutil.copy2(src, dst)

        if (i % 50) == 0:
            print(f"  [{i:3d}/{len(md_files)}] {src.name}")

    print(f"\n{'='*60}")
    print(f"✓ GABARITO FINALIZADO")
    print(f"{'='*60}")
    print(f"Total de páginas: {len(md_files)}")
    print(f"Localização: {destino}")
    print(f"\n⚠ Próximos passos:")
    print(f"  1. Revisar os 26 arquivos de qualidade 0.7 (quando tiver tempo)")
    print(f"  2. Começar Fase 3 (Baselines) — rodar Docling, Marker, MinerU")
