#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script 08: Integrar Dataset Manual (Phase 2)

Objetivo:
  - Varrer todas as edições (Janeiro a Junho 2025)
  - Encontrar pares PDF + MD (.corrigido.md)
  - Copiar para pasta estruturada (train/val/test)
  - Gerar relatório de integração

Uso:
  python scripts/08_integrar_dataset_manual.py
"""

import os
import shutil
from pathlib import Path
from collections import defaultdict
import json
from datetime import datetime

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# MUDE ISSO PARA O CAMINHO DO SEU DATASET
DATASET_SOURCE = r"D:\Dataset jornais\PDFS DC ANO 2025"

# Pasta do seu projeto
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Estrutura de saída
TRAIN_IMAGES = DATA_PROCESSED / "train" / "images"
TRAIN_ANNOT = DATA_PROCESSED / "train" / "annotations"
VAL_IMAGES = DATA_PROCESSED / "val" / "images"
VAL_ANNOT = DATA_PROCESSED / "val" / "annotations"
TEST_IMAGES = DATA_PROCESSED / "test" / "images"
TEST_ANNOT = DATA_PROCESSED / "test" / "annotations"

# ============================================================================
# FUNÇÕES
# ============================================================================

def criar_diretorios():
    """Criar estrutura de diretórios"""
    for path in [TRAIN_IMAGES, TRAIN_ANNOT, VAL_IMAGES, VAL_ANNOT, TEST_IMAGES, TEST_ANNOT]:
        path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Diretório criado/verificado: {path}")

def encontrar_pares_pdf_md(dataset_path):
    """
    Varrer dataset e encontrar pares PDF + MD

    Retorna:
      list: [(pdf_path, md_path, nome_pagina, mes, edicao), ...]
    """
    pares = []
    dataset_path = Path(dataset_path)

    if not dataset_path.exists():
        print(f"❌ Erro: Dataset não encontrado em {dataset_path}")
        return pares

    # Varrer meses
    for mes_dir in sorted(dataset_path.iterdir()):
        if not mes_dir.is_dir():
            continue

        mes = mes_dir.name
        print(f"\n📅 Varrendo: {mes}")

        # Varrer edições
        for edicao_dir in sorted(mes_dir.iterdir()):
            if not edicao_dir.is_dir():
                continue

            edicao = edicao_dir.name

            # Procurar pasta "divididos" (onde estão os .corrigido.md)
            divididos_dir = edicao_dir / "divididos"
            if not divididos_dir.exists():
                # Se não tiver "divididos", tentar direto na edição
                divididos_dir = edicao_dir

            # Encontrar pares
            md_files = list(divididos_dir.glob("*.corrigido.md"))

            for md_path in md_files:
                # Extrair nome base (ex: DA15P01)
                nome_arquivo = md_path.stem  # Remove .corrigido.md
                nome_pagina = nome_arquivo.replace(".corrigido", "")

                # Procurar PDF correspondente
                pdf_path = divididos_dir / f"{nome_pagina}.pdf"

                if not pdf_path.exists():
                    # Tentar em outras variações
                    pdf_candidates = list(divididos_dir.glob(f"{nome_pagina.split('.')[0]}*.pdf"))
                    if pdf_candidates:
                        pdf_path = pdf_candidates[0]
                    else:
                        print(f"  ⚠️  PDF não encontrado para {md_path.name}")
                        continue

                pares.append({
                    'pdf': pdf_path,
                    'md': md_path,
                    'nome_pagina': nome_pagina,
                    'mes': mes,
                    'edicao': edicao
                })
                print(f"  ✓ Par encontrado: {nome_pagina}")

    return pares

def estratificar_dataset(pares, train_ratio=0.68, val_ratio=0.12, test_ratio=0.20):
    """
    Estratificar dataset por edição

    Mantém páginas da mesma edição no mesmo split
    """
    # Agrupar por edição
    por_edicao = defaultdict(list)
    for par in pares:
        chave = (par['mes'], par['edicao'])
        por_edicao[chave].append(par)

    print(f"\n📊 Total de edições: {len(por_edicao)}")
    print(f"   Total de pares: {len(pares)}")

    # Estratificar
    train = []
    val = []
    test = []

    edicoes = sorted(por_edicao.keys())
    n_edicoes = len(edicoes)

    train_split = int(n_edicoes * train_ratio)
    val_split = int(n_edicoes * (train_ratio + val_ratio))

    for i, chave in enumerate(edicoes):
        paginas = por_edicao[chave]
        if i < train_split:
            train.extend(paginas)
        elif i < val_split:
            val.extend(paginas)
        else:
            test.extend(paginas)

    print(f"\n✓ Estratificação:")
    print(f"  Train: {len(train)} pares ({len(train)/len(pares)*100:.1f}%)")
    print(f"  Val:   {len(val)} pares ({len(val)/len(pares)*100:.1f}%)")
    print(f"  Test:  {len(test)} pares ({len(test)/len(pares)*100:.1f}%)")

    return train, val, test

def copiar_pares(pares, dest_images, dest_annot, split_name):
    """Copiar pares PDF + MD para destino"""
    print(f"\n📁 Copiando {split_name}...")

    for i, par in enumerate(pares, 1):
        pdf_src = par['pdf']
        md_src = par['md']

        # Nome destino: DA15P01.pagina1 (sem extensão)
        nome_base = par['nome_pagina']

        pdf_dest = dest_images / f"{nome_base}.pdf"
        md_dest = dest_annot / f"{nome_base}.md"

        try:
            shutil.copy2(pdf_src, pdf_dest)
            shutil.copy2(md_src, md_dest)
            if i % 50 == 0:
                print(f"  ✓ {i}/{len(pares)} pares copiados")
        except Exception as e:
            print(f"  ❌ Erro ao copiar {nome_base}: {e}")

    print(f"  ✓ {len(pares)} pares copiados com sucesso!")

def gerar_relatorio(train, val, test):
    """Gerar relatório de integração"""

    # data_splits.json
    splits_info = {
        'train': len(train),
        'val': len(val),
        'test': len(test),
        'total': len(train) + len(val) + len(test),
        'data_splits': {
            'train': [p['nome_pagina'] for p in train],
            'val': [p['nome_pagina'] for p in val],
            'test': [p['nome_pagina'] for p in test]
        },
        'timestamp': datetime.now().isoformat()
    }

    with open(DATA_PROCESSED / "data_splits.json", 'w', encoding='utf-8') as f:
        json.dump(splits_info, f, indent=2, ensure_ascii=False)

    # dataset_stats.json
    meses = defaultdict(int)
    edicoes = set()

    for par in train + val + test:
        meses[par['mes']] += 1
        edicoes.add((par['mes'], par['edicao']))

    stats = {
        'total_pares': len(train) + len(val) + len(test),
        'meses_unicos': len(meses),
        'edicoes_unicas': len(edicoes),
        'distribuicao_por_mes': dict(sorted(meses.items())),
        'split_ratio': {
            'train': f"{len(train)/(len(train)+len(val)+len(test))*100:.1f}%",
            'val': f"{len(val)/(len(train)+len(val)+len(test))*100:.1f}%",
            'test': f"{len(test)/(len(train)+len(val)+len(test))*100:.1f}%"
        }
    }

    with open(DATA_PROCESSED / "dataset_stats.json", 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    # relatorio_integracao.txt
    with open(PROJECT_ROOT / "relatorios" / "integracao_fase2.txt", 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("FASE 2: INTEGRAÇÃO DE DATASET MANUAL\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Fonte: {DATASET_SOURCE}\n\n")

        f.write("RESUMO\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total de pares: {stats['total_pares']}\n")
        f.write(f"Meses únicos: {stats['meses_unicos']}\n")
        f.write(f"Edições únicas: {stats['edicoes_unicas']}\n\n")

        f.write("DISTRIBUIÇÃO POR SPLIT\n")
        f.write("-" * 80 + "\n")
        f.write(f"Train: {len(train)} pares ({stats['split_ratio']['train']})\n")
        f.write(f"Val:   {len(val)} pares ({stats['split_ratio']['val']})\n")
        f.write(f"Test:  {len(test)} pares ({stats['split_ratio']['test']})\n\n")

        f.write("DISTRIBUIÇÃO POR MÊS\n")
        f.write("-" * 80 + "\n")
        for mes, count in sorted(stats['distribuicao_por_mes'].items()):
            f.write(f"{mes}: {count} pares\n")

    print(f"\n📊 Relatórios gerados:")
    print(f"  ✓ data_splits.json")
    print(f"  ✓ dataset_stats.json")
    print(f"  ✓ integracao_fase2.txt")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("FASE 2: INTEGRAR DATASET MANUAL")
    print("=" * 80)

    # 1. Criar diretórios
    print("\n1️⃣  Criando diretórios...")
    criar_diretorios()

    # 2. Encontrar pares
    print("\n2️⃣  Encontrando pares PDF + MD...")
    pares = encontrar_pares_pdf_md(DATASET_SOURCE)

    if not pares:
        print("❌ Nenhum par encontrado!")
        return

    # 3. Estratificar
    print("\n3️⃣  Estratificando dataset...")
    train, val, test = estratificar_dataset(pares)

    # 4. Copiar
    print("\n4️⃣  Copiando pares...")
    copiar_pares(train, TRAIN_IMAGES, TRAIN_ANNOT, "TRAIN")
    copiar_pares(val, VAL_IMAGES, VAL_ANNOT, "VAL")
    copiar_pares(test, TEST_IMAGES, TEST_ANNOT, "TEST")

    # 5. Gerar relatório
    print("\n5️⃣  Gerando relatórios...")
    gerar_relatorio(train, val, test)

    print("\n" + "=" * 80)
    print("✅ FASE 2 COMPLETA!")
    print("=" * 80)
    print(f"\n📁 Dataset integrado em: {DATA_PROCESSED}")
    print(f"\n📊 Próximo passo: Iniciar Fase 3 (Baseline VLM)")

if __name__ == "__main__":
    main()
