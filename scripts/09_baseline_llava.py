#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script 09 (v2): Baseline VLM com LLaVA-1.5-7B (Phase 3)

Objetivo:
  - Extrair Markdown de PDFs usando LLaVA Vision
  - Comparar com gabaritos manuais
  - Calcular TEDS score (estrutura)
  - Gerar relatório de baseline

Uso:
  python scripts/09_baseline_llava.py

Requisitos:
  - pip install torch torchvision torchaudio transformers pillow
  - ~16GB RAM (modelo 7B)
  - GPU opcional (mas CPU funciona, mais lento)
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
import re
import warnings

warnings.filterwarnings('ignore')

# Verificar dependências
try:
    from pdf2image import convert_from_path
    from PIL import Image
    from transformers import AutoProcessor, LlavaForConditionalGeneration
    import torch
except ImportError as e:
    print(f"❌ Erro: Faltam dependências!")
    print(f"   Execute: pip install pdf2image pillow torch transformers")
    sys.exit(1)

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
TEST_IMAGES = DATA_PROCESSED / "test" / "images"
TEST_ANNOT = DATA_PROCESSED / "test" / "annotations"
RESULTADOS = PROJECT_ROOT / "resultados"

# Criar diretório de resultados
RESULTADOS.mkdir(exist_ok=True)

# Verificar GPU
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🖥️  Usando device: {DEVICE.upper()}")

# Modelo LLaVA
MODEL_ID = "llava-hf/llava-1.5-7b-hf"

print("⏳ Carregando modelo LLaVA (primeira vez leva alguns minutos)...")
try:
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = LlavaForConditionalGeneration.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        device_map=DEVICE,
        low_cpu_mem_usage=True
    )
    print("✓ Modelo carregado com sucesso!")
except Exception as e:
    print(f"❌ Erro ao carregar modelo: {e}")
    sys.exit(1)

# ============================================================================
# FUNÇÕES
# ============================================================================

def pdf_para_imagem(pdf_path, max_pages=1):
    """Converter PDF para imagem (primeira página)"""
    try:
        images = convert_from_path(pdf_path, first_page=1, last_page=max_pages, dpi=150)
        return images[0] if images else None
    except Exception as e:
        print(f"  ❌ Erro ao converter PDF: {e}")
        return None

def extrair_markdown_com_llava(imagem):
    """
    Usar LLaVA para extrair Markdown de imagem

    Retorna:
      str: Markdown extraído
    """
    try:
        # Preparar input
        prompt = """Analise esta página de jornal e extraia o conteúdo em Markdown estruturado.

IMPORTANTE:
1. Use hierarquia de títulos:
   # = Chapéu (seção/categoria)
   ## = Manchete (título principal)
   ### = Olho/Subtítulo
   #### = Intertítulo
   ##### = Legenda

2. Separe as matérias claramente com quebras de linha.

3. Mantenha a ordem de leitura (esquerda para direita, cima para baixo).

4. Preserve a formatação quando relevante (negrito, itálico).

5. Se houver imagens/figuras, indique com [Figura: descrição breve]

Retorne APENAS o Markdown, sem comentários adicionais:"""

        inputs = processor(prompt, imagem, return_tensors='pt').to(DEVICE)

        # Se estiver em GPU e usando float16, converter inputs
        if DEVICE == "cuda":
            inputs = {k: v.half() if v.dtype == torch.float32 else v for k, v in inputs.items()}

        # Gerar
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=1024,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )

        # Decodificar
        generated_text = processor.decode(output[0], skip_special_tokens=True)

        # Extrair apenas a parte após o prompt
        if prompt in generated_text:
            markdown = generated_text.split(prompt)[-1].strip()
        else:
            markdown = generated_text

        return markdown

    except Exception as e:
        print(f"  ❌ Erro ao processar com LLaVA: {e}")
        return None

def carregar_gabarito(md_path):
    """Carregar gabarito manual em Markdown"""
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"  ❌ Erro ao carregar gabarito: {e}")
        return None

def contar_headings(markdown_text):
    """Contar headings por nível no Markdown"""
    if not markdown_text:
        return {}

    counts = {}
    for line in markdown_text.split('\n'):
        match = re.match(r'^(#+)', line)
        if match:
            level = len(match.group(1))
            counts[level] = counts.get(level, 0) + 1

    return counts

def calcular_estrutura_score(extracted, gabarito):
    """
    Calcular score de estrutura (simplificado)

    Compara:
    - Número de headings por nível
    - Comprimento do texto
    """
    if not extracted or not gabarito:
        return 0.0

    headings_ext = contar_headings(extracted)
    headings_gab = contar_headings(gabarito)

    # Score baseado em proximidade de headings
    total_levels = set(headings_ext.keys()) | set(headings_gab.keys())

    if not total_levels:
        # Nenhum heading em nenhum - comparar por comprimento
        ratio = min(len(extracted), len(gabarito)) / max(len(extracted), len(gabarito))
        return ratio

    scores = []
    for level in total_levels:
        ext_count = headings_ext.get(level, 0)
        gab_count = headings_gab.get(level, 0)

        if gab_count == 0:
            score = 0.0 if ext_count > 0 else 1.0
        else:
            score = min(ext_count, gab_count) / max(ext_count, gab_count)

        scores.append(score)

    return sum(scores) / len(scores) if scores else 0.0

def processar_pagina(pdf_path, md_path, nome_pagina):
    """Processar uma página: extrair + comparar"""
    print(f"\n  📄 Processando: {nome_pagina}")

    # 1. Converter PDF para imagem
    print(f"     → Convertendo PDF para imagem...")
    imagem = pdf_para_imagem(pdf_path)

    if imagem is None:
        print(f"     ❌ Falha na conversão")
        return None

    print(f"     ✓ Imagem pronta ({imagem.size})")

    # 2. Extrair com LLaVA
    print(f"     → Processando com LLaVA...")
    extracted_md = extrair_markdown_com_llava(imagem)

    if not extracted_md:
        print(f"     ❌ Falha na extração")
        return None

    print(f"     ✓ Extração realizada ({len(extracted_md)} chars)")

    # 3. Carregar gabarito
    gabarito_md = carregar_gabarito(md_path)
    if not gabarito_md:
        print(f"     ❌ Gabarito não encontrado")
        return None

    # 4. Calcular score
    estrutura_score = calcular_estrutura_score(extracted_md, gabarito_md)

    # 5. Estatísticas
    headings_ext = contar_headings(extracted_md)
    headings_gab = contar_headings(gabarito_md)

    resultado = {
        'nome_pagina': nome_pagina,
        'pdf_path': str(pdf_path),
        'md_path': str(md_path),
        'extracted_markdown': extracted_md,
        'gabarito_markdown': gabarito_md,
        'estrutura_score': estrutura_score,
        'headings_extracted': headings_ext,
        'headings_gabarito': headings_gab,
        'tamanho_extracted': len(extracted_md),
        'tamanho_gabarito': len(gabarito_md),
        'timestamp': datetime.now().isoformat()
    }

    print(f"     ✓ Score de estrutura: {estrutura_score:.2%}")

    return resultado

def main():
    print("=" * 80)
    print("FASE 3: BASELINE VLM COM LLaVA-1.5-7B")
    print("=" * 80)

    # 1. Listar páginas de teste
    print("\n1️⃣  Carregando páginas de teste...")

    pdf_files = sorted(list(TEST_IMAGES.glob("*.pdf")))

    if not pdf_files:
        print("❌ Nenhum PDF encontrado em test set!")
        return

    print(f"✓ {len(pdf_files)} PDFs encontrados")

    # 2. Processar (apenas 5 primeiras para teste)
    print("\n2️⃣  Processando páginas...")

    n_samples = min(5, len(pdf_files))  # Apenas 5 para teste
    print(f"   Processando {n_samples} amostras (para teste)")

    resultados = []

    for i, pdf_path in enumerate(pdf_files[:n_samples], 1):
        nome_pagina = pdf_path.stem
        md_path = TEST_ANNOT / f"{nome_pagina}.md"

        print(f"\n[{i}/{n_samples}]", end="")

        if not md_path.exists():
            print(f"  ⚠️  Gabarito não encontrado para {nome_pagina}")
            continue

        resultado = processar_pagina(pdf_path, md_path, nome_pagina)
        if resultado:
            resultados.append(resultado)

    if not resultados:
        print("❌ Nenhuma página foi processada com sucesso!")
        return

    # 3. Gerar relatório
    print("\n\n3️⃣  Gerando relatórios...")

    # Calcular médias
    scores = [r['estrutura_score'] for r in resultados]
    media_score = sum(scores) / len(scores) if scores else 0.0

    # Salvar resultados detalhados
    resultados_path = RESULTADOS / "baseline_llava_detalhado.json"
    with open(resultados_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Resultados detalhados salvos")

    # Salvar resumo
    resumo = {
        'data': datetime.now().isoformat(),
        'modelo': 'LLaVA-1.5-7B',
        'device': DEVICE,
        'amostras_processadas': len(resultados),
        'estrutura_score_media': media_score,
        'estrutura_score_min': min(scores),
        'estrutura_score_max': max(scores),
        'resultados_por_pagina': [
            {
                'nome_pagina': r['nome_pagina'],
                'estrutura_score': r['estrutura_score'],
                'tamanho_extracted': r['tamanho_extracted'],
                'tamanho_gabarito': r['tamanho_gabarito']
            }
            for r in resultados
        ]
    }

    resumo_path = RESULTADOS / "baseline_llava_resumo.json"
    with open(resumo_path, 'w', encoding='utf-8') as f:
        json.dump(resumo, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Resumo salvo")

    # Salvar relatório de texto
    relatorio_path = RESULTADOS / "baseline_llava.txt"
    with open(relatorio_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("FASE 3: BASELINE VLM COM LLaVA-1.5-7B\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Modelo: LLaVA-1.5-7B\n")
        f.write(f"Device: {DEVICE.upper()}\n")
        f.write(f"Amostras: {len(resultados)}\n\n")

        f.write("RESULTADOS AGREGADOS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Estrutura Score (Médio): {media_score:.2%}\n")
        f.write(f"Estrutura Score (Mín):   {min(scores):.2%}\n")
        f.write(f"Estrutura Score (Máx):   {max(scores):.2%}\n\n")

        f.write("RESULTADOS POR PÁGINA\n")
        f.write("-" * 80 + "\n")
        for r in resultados:
            f.write(f"{r['nome_pagina']}: {r['estrutura_score']:.2%}\n")
            f.write(f"  Headings (Extraído): {r['headings_extracted']}\n")
            f.write(f"  Headings (Gabarito): {r['headings_gabarito']}\n")
            f.write(f"  Tamanho: {r['tamanho_extracted']} chars (extraído) vs {r['tamanho_gabarito']} chars (gabarito)\n\n")

        f.write("\nPRÓXIMOS PASSOS\n")
        f.write("-" * 80 + "\n")
        f.write("1. Analisar erros e padrões de falha\n")
        f.write("2. Ajustar prompt para melhorar estrutura\n")
        f.write("3. Testar em mais amostras (50-100 páginas)\n")
        f.write("4. Preparar dataset para fine-tuning de Qwen2.5-VL-7B\n")

    print(f"  ✓ Relatório salvo")

    # 4. Resumo
    print("\n" + "=" * 80)
    print("✅ BASELINE LLAVA COMPLETO!")
    print("=" * 80)
    print(f"\n📊 RESULTADOS:")
    print(f"   Amostras processadas: {len(resultados)}")
    print(f"   Estrutura Score (médio): {media_score:.2%}")
    print(f"   Range: {min(scores):.2%} - {max(scores):.2%}")
    print(f"\n📁 Relatórios em: {RESULTADOS}")
    print(f"\n📝 Próximo passo: Analisar resultados e ajustar prompt")

if __name__ == "__main__":
    main()
