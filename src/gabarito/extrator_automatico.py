#!/usr/bin/env python3
"""
Extração semi-automática de estrutura do PDF nativo.

Usa os metadados tipográficos do PDF (font, tamanho, peso) para
inferir a hierarquia de headings. A saída é um Markdown bruto
que será revisado manualmente.
"""

import csv
from pathlib import Path
from typing import List, Dict

import pymupdf as fitz


def extrair_spans_tipograficos(pdf_path: Path) -> List[Dict]:
    """
    Extrai spans (trechos de texto) com metadados tipográficos.

    Returns:
        Lista de dicts com: {'texto', 'tamanho', 'peso', 'font', 'x0', 'y0'}
    """
    spans = []

    try:
        with fitz.open(pdf_path) as doc:
            for page_num, page in enumerate(doc):
                dicts = page.get_text('dict')

                for bloco in dicts.get('blocks', []):
                    if bloco.get('type') != 0:
                        continue

                    for linha in bloco.get('lines', []):
                        for span in linha.get('spans', []):
                            spans.append({
                                'page': page_num,
                                'texto': span.get('text', ''),
                                'tamanho': round(span.get('size', 0), 1),
                                'peso': 'bold' if span.get('flags', 0) & 16 else 'normal',
                                'font': span.get('font', 'unknown'),
                                'x0': round(span.get('origin', [0, 0])[0], 1),
                                'y0': round(span.get('origin', [0, 0])[1], 1),
                            })
    except Exception as e:
        print(f"Erro ao ler {pdf_path}: {e}")
        return []

    return spans


def inferir_nivel_heading(tamanho: float, peso: str, x0: float, tamanhos_unicos: List[float], posicoes_x: List[float]) -> int:
    """
    Inferir nível de heading baseado em tipografia E posição.

    Critérios:
    1. Tamanho: maior = mais importante
    2. Peso: bold = título
    3. Posição X: alinhado à esquerda (x0 < 50) = título
    4. Comprimento: linhas curtas = mais provável ser título

    Heurística melhorada:
    - Maior tamanho + bold + alinhado à esquerda = ## (manchete)
    - Segundo maior + bold = ### (intertítulo)
    - Tamanho médio + bold = #### (subseção)
    - Resto = parágrafo normal
    """
    if not tamanhos_unicos:
        return 0

    # Critério 1: Tamanho
    eh_tamanho_grande = tamanho >= tamanhos_unicos[0] - 2 if tamanhos_unicos else False
    eh_tamanho_medio = tamanho >= tamanhos_unicos[min(1, len(tamanhos_unicos)-1)] - 1 if len(tamanhos_unicos) > 1 else False

    # Critério 2: Peso
    eh_bold = peso == 'bold'

    # Critério 3: Posição (alinhado à esquerda = x0 < 50)
    eh_alinhado_esquerda = x0 < 50

    # Scoring
    score = 0
    if eh_bold:
        score += 2
    if eh_alinhado_esquerda:
        score += 1
    if eh_tamanho_grande:
        score += 2
    elif eh_tamanho_medio:
        score += 1

    # Decidir nível
    if score >= 4:  # Bold + alinhado + tamanho grande
        return 2  # Manchete (##)
    elif score >= 3:  # Bold + alinhado OU bold + tamanho grande
        return 3  # Intertítulo (###)
    elif score >= 2:  # Bold + algo mais
        return 4  # Subseção (####)

    return 0  # Parágrafo normal

def markdown_from_spans(spans: List[Dict]) -> str:
    """
    Converte spans em Markdown estruturado com melhor detecção de headings.
    """
    if not spans:
        return ""

    tamanhos_todos = sorted(set(s['tamanho'] for s in spans if s['tamanho'] > 0), reverse=True)
    posicoes_x = [s['x0'] for s in spans]

    lines = []
    current_y = None
    current_line = []

    for span in spans:
        y = span['y0']

        if current_y is not None and abs(y - current_y) > 3:
            if current_line:
                texto_linha = ' '.join(s['texto'].strip() for s in current_line if s['texto'].strip())

                if texto_linha:
                    tamanho_med = sum(s['tamanho'] for s in current_line) / len(current_line)
                    peso = 'bold' if any(s['peso'] == 'bold' for s in current_line) else 'normal'
                    x0_med = sum(s['x0'] for s in current_line) / len(current_line)

                    # NOVA FUNÇÃO COM X0
                    nivel = inferir_nivel_heading(tamanho_med, peso, x0_med, tamanhos_todos, posicoes_x)

                    if nivel > 0:
                        lines.append('#' * nivel + ' ' + texto_linha)
                    else:
                        lines.append(texto_linha)

            current_line = []
            current_y = y

        current_line.append(span)
        current_y = y

    if current_line:
        texto_linha = ' '.join(s['texto'].strip() for s in current_line if s['texto'].strip())
        if texto_linha:
            tamanho_med = sum(s['tamanho'] for s in current_line) / len(current_line)
            peso = 'bold' if any(s['peso'] == 'bold' for s in current_line) else 'normal'
            x0_med = sum(s['x0'] for s in current_line) / len(current_line)

            # NOVA FUNÇÃO COM X0
            nivel = inferir_nivel_heading(tamanho_med, peso, x0_med, tamanhos_todos, posicoes_x)

            if nivel > 0:
                lines.append('#' * nivel + ' ' + texto_linha)
            else:
                lines.append(texto_linha)

    markdown = '\n'.join(lines)

    import re
    markdown = re.sub(r'\n(##\s+)', r'\n\n\1', markdown)

    return markdown
def extrair_arquivo(pdf_path: Path, saida_path: Path):
    """Extrai Markdown bruto de um PDF e salva."""
    if not pdf_path.exists():
        print(f"Arquivo não encontrado: {pdf_path}")
        return False

    print(f"Extraindo: {pdf_path.name}", end=" ... ")

    spans = extrair_spans_tipograficos(pdf_path)
    if not spans:
        print("FALHOU (sem conteúdo)")
        return False

    markdown = markdown_from_spans(spans)

    saida_path.parent.mkdir(parents=True, exist_ok=True)
    with open(saida_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"OK ({len(markdown)} chars)")
    return True


def extrair_lote(corpus_raiz: Path, indices_csv: Path, saida_dir: Path, max_arquivos: int = None):
    """
    Extrai todos os PDFs listados em um CSV de índice.
    """
    # Carregar índice
    with open(indices_csv, encoding='utf-8-sig') as f:
        indice = list(csv.DictReader(f))

    if max_arquivos:
        indice = indice[:max_arquivos]

    print(f"Extraindo {len(indice)} arquivos...")

    sucesso = 0
    falha = 0

    for row in indice:
        # Construir caminho do PDF
        pasta_edicao = row['pasta_edicao']
        arquivo_pdf = row['arquivo']

        pdf_path = corpus_raiz / 'PDFS DC ANO 2025' / arquivo_pdf.replace('.txt', '.pdf')

        if not pdf_path.exists():
            # Tentar buscar em qualquer lugar
            pdfs = list(corpus_raiz.rglob(arquivo_pdf.replace('.txt', '.pdf')))
            if pdfs:
                pdf_path = pdfs[0]
            else:
                print(f"  ✗ Não encontrado: {arquivo_pdf}")
                falha += 1
                continue

        # Nome do arquivo de saída
        nome_base = arquivo_pdf.replace('.txt', '')
        md_path = saida_dir / f"{nome_base}.md"

        if extrair_arquivo(pdf_path, md_path):
            sucesso += 1
        else:
            falha += 1

    print(f"\nResumo:")
    print(f"  Sucesso: {sucesso}")
    print(f"  Falha: {falha}")
    print(f"  Salvos em: {saida_dir}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

    from src.utils.config import RAIZ_PROJETO, carregar_config

    cfg = carregar_config()
    corpus_raiz = Path(cfg['corpus']['raiz'])

    # Extrair primeiras 10 páginas de desenvolvimento como teste
    indices_dev = RAIZ_PROJETO / 'data' / 'interim' / 'indice_desenvolvimento.csv'
    saida_dir = RAIZ_PROJETO / 'data' / 'interim' / 'markdown_bruto'

    print("=== Teste de Extração Automática ===\n")
    extrair_lote(corpus_raiz, indices_dev, saida_dir, max_arquivos=10)
