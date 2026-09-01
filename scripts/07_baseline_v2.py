#!/usr/bin/env python3
"""
Baseline simples v2 — sem complicações.
"""

import csv
import sys
from pathlib import Path

import pymupdf as fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.metricas.avaliador import Avaliador
from src.utils.config import RAIZ_PROJETO


def extrair_texto(pdf_path: Path) -> str:
    """Extrai texto de PDF."""
    try:
        with fitz.open(pdf_path) as doc:
            blocos = []
            for page in doc:
                texto = page.get_text('text')
                if texto.strip():
                    blocos.append(texto)
            return '\n\n'.join(blocos)
    except:
        return ""


if __name__ == "__main__":
    # Caminhos
    corpus_raiz = Path("D:/Dataset jornais/PDFS DC ANO 2025")
    gabarito_dir = RAIZ_PROJETO / 'data' / 'processed'
    saida_csv = RAIZ_PROJETO / 'relatorios' / 'baseline_pymupdf.csv'

    print("=" * 60)
    print("BASELINE — PyMuPDF vs Gabarito")
    print("=" * 60)
    print()

    # Listar gabaritos
    gabarito_files = list(gabarito_dir.glob('*.md'))
    print(f"Gabaritos encontrados: {len(gabarito_files)}\n")

    av = Avaliador()
    resultados = []
    processados = 0
    nao_encontrados = 0

    for i, gab_path in enumerate(sorted(gabarito_files)[:100], 1):  # Primeiros 100 para teste
        # Nome do arquivo — gabarito vem como "DA01P01.pdf.md"
        nome_gab = gab_path.stem  # Remove .md → "DA01P01.pdf"

        # Procurar PDF correspondente
        # Se gabarito é "DA01P01.pdf", procurar "DA01P01.pdf"
        nome_pdf = nome_gab.replace('.pdf', '') + '.pdf'  # "DA01P01.pdf" → "DA01P01.pdf"

        pdf_paths = list(corpus_raiz.rglob(nome_pdf))
        if not pdf_paths:
            nao_encontrados += 1
            continue

        pdf_path = pdf_paths[0]

        # Extrair
        texto = extrair_texto(pdf_path)
        gabarito = gab_path.read_text(encoding='utf-8')

        if not texto or not gabarito:
            continue

        # Avaliar
        res = av.avaliar(texto, gabarito)

        resultados.append({
            'arquivo': nome_pdf,
            'cer': round(res['texto']['cer'], 3),
            'f1_tokens': round(res['texto']['f1_tokens'], 3),
            'estrutura': round(res['estrutura']['estrutura_score'], 3),
        })

        processados += 1

        if (processados % 20) == 0:
            print(f"  [{processados:3d}] processados, {nao_encontrados} não encontrados")

    # Salvar
    saida_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(saida_csv, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['arquivo', 'cer', 'f1_tokens', 'estrutura'])
        w.writeheader()
        w.writerows(resultados)

    # Resumo
    print(f"\n{'='*60}")
    print(f"RESULTADO")
    print(f"{'='*60}")
    print(f"Total avaliado: {len(resultados)}")
    print(f"Não encontrados: {nao_encontrados}")

    if resultados:
        cer = sum(float(r['cer']) for r in resultados) / len(resultados)
        f1 = sum(float(r['f1_tokens']) for r in resultados) / len(resultados)
        est = sum(float(r['estrutura']) for r in resultados) / len(resultados)

        print(f"\nMédias:")
        print(f"  CER médio: {cer:.3f}")
        print(f"  F1 tokens: {f1:.3f}")
        print(f"  Estrutura: {est:.3f}")

    print(f"\nSalvo em: {saida_csv}")
