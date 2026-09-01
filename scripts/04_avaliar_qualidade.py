#!/usr/bin/env python3
"""
Avalia a qualidade de cada Markdown extraído usando a métrica da Fase 1.
Gera um relatório mostrando quais arquivos precisam de mais revisão.
"""

import csv
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.metricas.avaliador import Avaliador
from src.utils.config import RAIZ_PROJETO, carregar_config


def avaliar_lote(markdown_dir: Path, output_csv: Path):
    """
    Avalia qualidade de todos os Markdown em um diretório.

    Compara cada arquivo contra si mesmo (identidade) para medir:
    - Integridade do Markdown (loops, sintaxe)
    - Estrutura de headings
    """

    av = Avaliador()
    resultados = []

    md_files = sorted(markdown_dir.glob('*.md'))
    print(f"Avaliando {len(md_files)} arquivos de Markdown...\n")

    for i, md_path in enumerate(md_files, 1):
        # Ler arquivo
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                conteudo = f.read()
        except Exception as e:
            print(f"  [{i:3d}] {md_path.name:30s} ERRO: {e}")
            continue

        # Avaliar (comparar contra si mesmo para validação básica)
        resultado = av.avaliar(conteudo, conteudo)

        # Extrair métricas-chave
        score_estrutura = resultado['estrutura']['estrutura_score']
        markdown_valido = resultado['integridade']['markdown_valido']
        repeticao = resultado['integridade']['repeticao_detectada']
        n_headings = sum(resultado['estrutura']['headings_pred'].values())

        # Score de qualidade (0-1)
        # Bom markdown deve ter: estrutura OK + headings + sem loops
        qualidade = (
            (score_estrutura * 0.5) +  # Estrutura
            (1.0 if markdown_valido else 0.0) * 0.3 +  # Integridade
            (1.0 if n_headings > 0 else 0.0) * 0.2  # Presença de headings
        )

        resultados.append({
            'arquivo': md_path.name,
            'qualidade': round(qualidade, 3),
            'estrutura_score': round(score_estrutura, 3),
            'markdown_valido': markdown_valido,
            'repeticao': repeticao,
            'n_headings': n_headings,
            'tamanho_chars': len(conteudo),
        })

        # Feedback
        status = "✓" if qualidade > 0.7 else "⚠" if qualidade > 0.4 else "✗"
        print(f"  [{i:3d}] {md_path.name:30s} {status} qualidade={qualidade:.3f}")

        if (i % 50) == 0:
            print(f"       ... {i}/{ len(md_files)}")

    # Salvar relatório
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=resultados[0].keys())
        w.writeheader()
        w.writerows(resultados)

    # Resumo
    print(f"\n{'='*60}")
    print(f"RESUMO DE QUALIDADE")
    print(f"{'='*60}")

    qualidades = [r['qualidade'] for r in resultados]
    boas = sum(1 for q in qualidades if q > 0.7)
    medias = sum(1 for q in qualidades if 0.4 < q <= 0.7)
    ruins = sum(1 for q in qualidades if q <= 0.4)

    print(f"Total avaliado: {len(resultados)}")
    print(f"  ✓ Boas (>0.7): {boas} ({100*boas/len(resultados):.1f}%)")
    print(f"  ⚠ Médias (0.4-0.7): {medias} ({100*medias/len(resultados):.1f}%)")
    print(f"  ✗ Ruins (<0.4): {ruins} ({100*ruins/len(resultados):.1f}%)")

    print(f"\nRelatório salvo em: {output_csv}")

    # Listar arquivos ruins para revisão prioritária
    ruins_files = sorted([r for r in resultados if r['qualidade'] <= 0.4],
                         key=lambda x: x['qualidade'])

    if ruins_files:
        print(f"\n⚠ Arquivos que precisam revisão prioritária ({len(ruins_files)}):")
        for r in ruins_files[:20]:  # Top 20
            print(f"   {r['arquivo']:30s} qualidade={r['qualidade']:.3f}")
        if len(ruins_files) > 20:
            print(f"   ... e mais {len(ruins_files) - 20}")

    return resultados


if __name__ == "__main__":
    cfg = carregar_config()

    markdown_dir = RAIZ_PROJETO / 'data' / 'interim' / 'markdown_bruto'
    output_csv = RAIZ_PROJETO / 'relatorios' / 'qualidade_markdown.csv'

    print("=" * 60)
    print("AVALIAÇÃO DE QUALIDADE — 350 PÁGINAS")
    print("=" * 60)
    print()

    avaliar_lote(markdown_dir, output_csv)
