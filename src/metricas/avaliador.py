"""
Framework de avaliação em camadas para jornal convertido em Markdown.
"""

import re
from typing import Dict

from jiwer import cer, wer
from rapidfuzz.distance import Levenshtein
from collections import Counter

from src.metricas.estrutura_jornal import estrutura_jornal_score

def normalizar_texto(texto: str) -> str:
    """Remove Markdown, normaliza espaço."""
    # Remover imagens e links
    texto = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', texto)
    texto = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', texto)

    # Remover headings
    texto = re.sub(r'^\s{0,3}#{1,6}\s+', '', texto, flags=re.MULTILINE)

    # Remover separadores
    texto = re.sub(r'^\s*[-*_]{3,}\s*$', '', texto, flags=re.MULTILINE)

    # Remover ênfase
    texto = texto.replace('**', '').replace('__', '').replace('*', ' ')
    texto = texto.replace('`', '')

    # Normalizar espaço
    texto = re.sub(r'\s+', ' ', texto).strip()

    return texto.lower()


def metricas_texto(pred: str, ref: str) -> Dict:
    """
    Avalia fidelidade textual.

    Métricas:
    - CER: Character Error Rate (Levenshtein em nível de caractere)
    - WER: Word Error Rate
    - F1_tokens: F1 de tokens, insensível a ordem
    """
    pred_norm = normalizar_texto(pred)
    ref_norm = normalizar_texto(ref)

    # CER
    cer_score = Levenshtein.distance(ref_norm, pred_norm) / max(len(ref_norm), 1)

    # WER
    ref_palavras = ref_norm.split()
    pred_palavras = pred_norm.split()
    wer_score = Levenshtein.distance(ref_palavras, pred_palavras) / max(len(ref_palavras), 1)

    # F1 de tokens
    ref_toks = Counter(re.findall(r'\w+', ref_norm))
    pred_toks = Counter(re.findall(r'\w+', pred_norm))

    inter = sum((ref_toks & pred_toks).values())
    prec = inter / max(sum(pred_toks.values()), 1)
    rec = inter / max(sum(ref_toks.values()), 1)
    f1_tokens = 2 * prec * rec / max(prec + rec, 1e-9)

    return {
        'cer': cer_score,
        'wer': wer_score,
        'f1_tokens': f1_tokens
    }


def metricas_estrutura(pred: str, ref: str) -> Dict:
    """
    Avalia fidelidade estrutural.

    Métricas:
    - estrutura_score: adaptação do Markdown TEDS para jornal
    - n_headings_pred, n_headings_ref: contagem por nível
    """
    score = estrutura_jornal_score(pred, ref)

    # Contar headings por nível
    def contar_headings(md):
        contas = {i: 0 for i in range(1, 7)}
        for linha in md.split('\n'):
            m = re.match(r'^(#{1,6})\s+', linha)
            if m:
                nivel = len(m.group(1))
                contas[nivel] += 1
        return contas

    h_pred = contar_headings(pred)
    h_ref = contar_headings(ref)

    return {
        'estrutura_score': score,
        'headings_pred': h_pred,
        'headings_ref': h_ref
    }


def metricas_integridade(pred: str) -> Dict:
    """
    Avalia integridade técnica do Markdown.

    Métricas:
    - markdown_valido: sintaxe básica OK?
    - repeticao_loop: detecção de loop de repetição
    """
    # Markdown válido: verificar balanceamento de heading, etc
    valido = True
    problemas = []

    # Verificar se há loop de repetição (mesmo texto >= 3 vezes)
    for match in re.finditer(r'(.{10,100})\1{2,}', pred):
        problemas.append('loop_de_repeticao')
        valido = False

    return {
        'markdown_valido': valido,
        'repeticao_detectada': len(problemas) > 0,
        'problemas': problemas
    }


class Avaliador:
    """
    Avaliador de Markdown de jornal em quatro camadas.
    """

    def avaliar(self, pred: str, ref: str) -> Dict:
        """
        Avalia predição contra referência em todas as camadas.

        Returns: dicionário com todas as métricas.
        """
        resultado = {
            'texto': metricas_texto(pred, ref),
            'estrutura': metricas_estrutura(pred, ref),
            'integridade': metricas_integridade(pred)
        }

        return resultado

    def resumo(self, resultado: Dict) -> str:
        """Resumo legível das métricas."""
        linhas = [
            "=== AVALIAÇÃO DE MARKDOWN DE JORNAL ===",
            "",
            "TEXTO:",
            f"  CER: {resultado['texto']['cer']:.3f}",
            f"  WER: {resultado['texto']['wer']:.3f}",
            f"  F1 tokens: {resultado['texto']['f1_tokens']:.3f}",
            "",
            "ESTRUTURA:",
            f"  Score: {resultado['estrutura']['estrutura_score']:.3f}",
            f"  H1: {resultado['estrutura']['headings_pred'][1]} (ref: {resultado['estrutura']['headings_ref'][1]})",
            f"  H2: {resultado['estrutura']['headings_pred'][2]} (ref: {resultado['estrutura']['headings_ref'][2]})",
            "",
            "INTEGRIDADE:",
            f"  Markdown válido: {resultado['integridade']['markdown_valido']}",
            f"  Repetição detectada: {resultado['integridade']['repeticao_detectada']}",
        ]

        return '\n'.join(linhas)


if __name__ == "__main__":
    md = """
# Manchete Principal

Este é o corpo da manchete com alguns parágrafos.

## Intertítulo

Mais conteúdo aqui.
"""

    av = Avaliador()
    resultado = av.avaliar(md, md)
    print(av.resumo(resultado))
