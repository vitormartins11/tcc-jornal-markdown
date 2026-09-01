"""
Avaliação de estrutura de jornal convertido para Markdown.

Adapta as três modificações do Markdown TEDS (Tan et al. 2025)
mas opera sobre matérias em vez de tabelas.

Matéria = bloco com cabeçalho (h1, h2, h3, ...) seguido de corpo de texto.
"""

import re
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from rapidfuzz.distance import Levenshtein
from scipy.optimize import linear_sum_assignment


@dataclass
class Materia:
    """Representa uma matéria extraída de Markdown."""
    id: int
    inicio: int
    fim: int
    nivel_heading: int  # 1=h1, 2=h2, ...
    titulo: str
    n_paragrafos: int
    n_tokens_aprox: int


def extrair_materias(markdown: str) -> List[Materia]:
    """
    Extrai matérias de Markdown de jornal.

    Heurística: uma matéria começa em um heading (# ## ### ...)
    e vai até o próximo heading de mesmo nível ou de nível superior.
    """
    linhas = markdown.split('\n')
    materias = []

    i = 0
    id_mat = 0

    while i < len(linhas):
        linha = linhas[i]

        # Detectar heading
        m = re.match(r'^(#{1,6})\s+(.+)$', linha)
        if m:
            nivel = len(m.group(1))
            titulo = m.group(2).strip()
            inicio = i

            # Encontrar fim da matéria: próximo heading de nível <= ou fim
            j = i + 1
            while j < len(linhas):
                proxima = linhas[j]
                m_prox = re.match(r'^(#{1,6})\s+', proxima)
                if m_prox and len(m_prox.group(1)) <= nivel:
                    break
                j += 1

            # Contar parágrafos e tokens do corpo
            corpo = '\n'.join(linhas[i+1:j])
            paragrafos = [p for p in corpo.split('\n\n') if p.strip()]
            tokens = len(corpo.split())

            materias.append(Materia(
                id=id_mat,
                inicio=inicio,
                fim=j,
                nivel_heading=nivel,
                titulo=titulo,
                n_paragrafos=len(paragrafos),
                n_tokens_aprox=tokens
            ))
            id_mat += 1

            i = j
        else:
            i += 1

    return materias


def similaridade_titulo(t1: str, t2: str, limiar: float = 0.75) -> bool:
    """Verifica se dois títulos são similares."""
    t1_norm = t1.lower()
    t2_norm = t2.lower()

    sim = Levenshtein.normalized_similarity(t1_norm, t2_norm)
    return sim >= limiar


def fusao_difusa_materias(materias: List[Materia]) -> List[List[Materia]]:
    """
    Agrupa matérias fragmentadas (continuação entre colunas).

    Heurística: se duas matérias consecutivas têm títulos similares
    e estão no mesmo nível de heading, são a mesma matéria.
    """
    if not materias:
        return []

    usado = [False] * len(materias)
    grupos = []

    for i, m in enumerate(materias):
        if usado[i]:
            continue

        grupo = [m]
        usado[i] = True

        # Procurar continuação (próxima matéria com título similar)
        for j in range(i + 1, len(materias)):
            if usado[j]:
                continue

            m_prox = materias[j]

            # Mesmo nível e título similar?
            if (m_prox.nivel_heading == grupo[-1].nivel_heading and
                similaridade_titulo(grupo[-1].titulo, m_prox.titulo)):
                grupo.append(m_prox)
                usado[j] = True

        grupos.append(grupo)

    return grupos


def distancia_edicao_materia(m1: Materia, m2: Materia) -> float:
    """
    Distância de edição normalizada entre duas matérias.

    Considera: nível de heading, tamanho do corpo, similitude do título.
    """
    # Diferença de tamanho (número de tokens)
    delta_tokens = abs(m1.n_tokens_aprox - m2.n_tokens_aprox)
    max_tokens = max(m1.n_tokens_aprox, m2.n_tokens_aprox, 1)

    # Diferença de nível
    delta_nivel = abs(m1.nivel_heading - m2.nivel_heading)

    # Diferença de título
    sim_titulo = Levenshtein.normalized_similarity(
        m1.titulo.lower(),
        m2.titulo.lower()
    )
    dist_titulo = 1 - sim_titulo

    # Média ponderada
    return (0.5 * (delta_tokens / max_tokens) +
            0.2 * delta_nivel +
            0.3 * dist_titulo)


def pareamento_otimo_materias(grupos_pred: List[List[Materia]],
                              grupos_ref: List[List[Materia]]) -> Tuple[float, dict]:
    """
    Pareamento ótimo entre matérias preditas e referência.
    """
    n_pred = len(grupos_pred)
    n_ref = len(grupos_ref)

    if n_pred == 0 or n_ref == 0:
        return 0.0, {}

    custo = np.zeros((n_pred, n_ref))

    for i, grupo_pred in enumerate(grupos_pred):
        m_pred = grupo_pred[0]
        for j, grupo_ref in enumerate(grupos_ref):
            m_ref = grupo_ref[0]
            custo[i, j] = distancia_edicao_materia(m_pred, m_ref)

    linha_ind, col_ind = linear_sum_assignment(custo)

    similaridades = 1 - custo[linha_ind, col_ind]
    score = float(np.mean(similaridades)) if len(similaridades) > 0 else 0.0

    pareamentos = {int(i): int(j) for i, j in zip(linha_ind, col_ind)}

    return score, pareamentos


def estrutura_jornal_score(pred: str, ref: str) -> float:
    """
    Score de fidelidade estrutural de jornal em Markdown.

    Avalia: hierarquia de títulos, segmentação de matérias, continuidade.

    Returns: valor entre 0 e 1.
    """
    materias_pred = extrair_materias(pred)
    materias_ref = extrair_materias(ref)

    grupos_pred = fusao_difusa_materias(materias_pred)
    grupos_ref = fusao_difusa_materias(materias_ref)

    score, _ = pareamento_otimo_materias(grupos_pred, grupos_ref)

    return score


if __name__ == "__main__":
    md = """
# Manchete

Parágrafo da manchete.

## Intertítulo

Mais conteúdo.
"""

    materias = extrair_materias(md)
    print(f"Matérias extraídas: {len(materias)}")
    for m in materias:
        print(f"  - {m.titulo} (nível {m.nivel_heading}, {m.n_paragrafos} parágrafos)")

    score = estrutura_jornal_score(md, md)
    print(f"\nScore (idêntico): {score:.3f}")
