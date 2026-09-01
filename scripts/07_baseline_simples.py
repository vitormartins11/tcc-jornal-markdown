#!/usr/bin/env python3
"""
Baseline simples usando PyMuPDF.

Extrai texto estruturado de PDFs e compara com gabarito.
Não precisa de Docling/Marker — usa só PyMuPDF que já está instalado.
"""

import csv
import sys
from pathlib import Path

import pymupdf as fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.metricas.avaliador import Avaliador
from src.utils.config import RAIZ_PROJETO, carregar_config


def extrair_texto_estruturado(pdf_path: Path) -> str:
    """
    Extrai texto de PDF com tentativa de manter estrutura.
    """
    try:
        with fitz.open(pdf_path) as doc:
            blocos = []
            for page in doc:
                texto = page.get_text('text')
                if texto.strip():
                    blocos.append(texto)

            return '\n\n'.join(blocos)
    except Exception as e:
        print(f"Erro ao ler {pdf_path}: {e}")
        return ""


def baseline_pymupdf(corpus_raiz: Path, indices_csv: Path, saida_csv: Path):
    """
    Avalia baseline: PyMuPDF extraction vs. gabarito.
    """

    av = Avaliador()

    # Carregar gabarito
    gabarito_dir = RAIZ_PROJETO / 'data' / 'processed'
    gabaritos = {f.stem.replace('.pagina1', ''): f.read_text(encoding='utf-8')
                 for f in gabarito_dir.glob('*.md')}

    print(f"Gabaritos carregados: {len(gabaritos)}")

    # Carregar índice
    with open(indices_csv, encoding='utf-8-sig') as f:
        indice = list(csv.DictReader(f))

    print(f"Avaliando {len(indice)} arquivos...\n")

    resultados = []

    for i, row in enumerate(indice, 1):
        arquivo = row['arquivo'].replace('.txt', '.pdf')
        nome_base = arquivo.replace('.pdf', '')

        # Encontrar PDF
        pdfs = list(corpus_raiz.rglob(arquivo))
        if not pdfs:
            continue

        pdf_path = pdfs[0]

        # Extrair com PyMuPDF
        texto_extraido = extrair_texto_estruturado(pdf_path)

        # Buscar gabarito
        if nome_base not in gabaritos:
            continue

        gabarito = gabaritos[nome_base]

        # Avaliar
        resultado = av.avaliar(texto_extraido, gabarito)

        # Coletar métricas
        resultados.append({
            'arquivo': arquivo,
            'cer': round(resultado['texto']['cer'], 3),
            'wer': round(resultado['texto']['wer'], 3),
            'f1_tokens': round(resultado['texto']['f1_tokens'], 3),
            'estrutura_score': round(resultado['estrutura']['estrutura_score'], 3),
            'markdown_valido': str(resultado['integridade']['markdown_valido']),
        })

        if (i % 50) == 0:
            print(f"  [{i:3d}/{len(indice)}] processados")

    # Salvar
    if not resultados:
        print("Nenhum resultado para salvar!")
        return

    saida_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(saida_csv, 'w', encoding='utf-8-sig', newline='') as f:
        fieldnames = list(resultados[0].keys())
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(resultados)

    # Resumo
    print(f"\n{'='*60}")
    print(f"BASELINE — PyMuPDF Extraction")
    print(f"{'='*60}")
    print(f"Total avaliado: {len(resultados)}")

    if resultados:
        cer_med = sum(float(r['cer']) for r in resultados) / len(resultados)
        f1_med = sum(float(r['f1_tokens']) for r in resultados) / len(resultados)
        est_med = sum(float(r['estrutura_score']) for r in resultados) / len(resultados)

        print(f"  CER médio: {cer_med:.3f}")
        print(f"  F1 tokens médio: {f1_med:.3f}")
        print(f"  Estrutura score médio: {est_med:.3f}")

    print(f"\nRelatório: {saida_csv}")

if __name__ == "__main__":
    cfg = carregar_config()
    corpus_raiz = Path(cfg['corpus']['raiz'])

    indices_dev = RAIZ_PROJETO / 'data' / 'interim' / 'indice_desenvolvimento.csv'
    saida_csv = RAIZ_PROJETO / 'relatorios' / 'baseline_pymupdf.csv'

    print("=" * 60)
    print("BASELINE 1 — PyMuPDF Extraction")
    print("=" * 60)
    print()

    baseline_pymupdf(corpus_raiz, indices_dev, saida_csv)
