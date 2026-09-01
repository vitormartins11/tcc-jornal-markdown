"""
Markdown Tree-Edit-Distance Score (Markdown TEDS).

Adaptado de Tan et al. (2025) para avaliar fidelidade estrutural
de Markdown convertido a partir de documentos.

Este módulo implementa as três modificações ao TEDS padrão:
1. Isolamento da estrutura de tabela
2. Fusão difusa de tabelas fragmentadas
3. Pareamento ótimo com algoritmo húngaro
"""

import re
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from scipy.optimize import linear_sum_assignment


@dataclass
class Tabela:
    """Representa uma tabela extraída de Markdown."""
    id: int
    inicio: int
    fim: int
    linhas: int
    colunas: int
    cabecalho: str

    def tamanho(self) -> int:
        return self.linhas * self.colunas


def extrair_tabelas(markdown: str) -> List[Tabela]:
    """
    Extrai tabelas de um string Markdown.

    Padrão: linhas começando com |, com cabeçalho e separador

    Returns:
        Lista de Tabela ordenadas por posição no texto.
    """
    linhas = markdown.split('\n')
    tabelas = []
    em_tabela = False
    inicio_tabela = None
    id_tabela = 0

    for i, linha in enumerate(linhas):
        eh_linha_tabela = linha.strip().startswith('|')

        if eh_linha_tabela and not em_tabela:
            # Começar tabela
            em_tabela = True
            inicio_tabela = i
        elif not eh_linha_tabela and em_tabela:
            # Terminar tabela
            em_tabela = False
            if inicio_tabela is not None:
                # Extrair metadados da tabela
                linhas_tabela = linhas[inicio_tabela:i]
                n_linhas = len([l for l in linhas_tabela if l.strip().startswith('|') and '-' not in l])
                # Contar células da primeira linha
                primeira = linhas_tabela[0]
                n_colunas = len([c for c in primeira.split('|')[1:-1]])

                cabecalho_preview = primeira[:60]

                tabelas.append(Tabela(
                    id=id_tabela,
                    inicio=inicio_tabela,
                    fim=i,
                    linhas=n_linhas,
                    colunas=n_colunas,
                    cabecalho=cabecalho_preview
                ))
                id_tabela += 1
                inicio_tabela = None

    if em_tabela and inicio_tabela is not None:
        linhas_tabela = linhas[inicio_tabela:]
        n_linhas = len([l for l in linhas_tabela if l.strip().startswith('|') and '-' not in l])
        primeira = linhas_tabela[0]
        n_colunas = len([c for c in primeira.split('|')[1:-1]])
        cabecalho_preview = primeira[:60]

        tabelas.append(Tabela(
            id=id_tabela,
            inicio=inicio_tabela,
            fim=len(linhas),
            linhas=n_linhas,
            colunas=n_colunas,
            cabecalho=cabecalho_preview
        ))

    return tabelas


def similaridade_cabecalho(c1: str, c2: str, limiar: float = 0.8) -> bool:
    """
    Verifica se dois cabeçalhos são textualmente similares.

    Usada na fusão difusa para detectar tabelas fragmentadas
    que representam a mesma tabela lógica.
    """
    from rapidfuzz.distance import Levenshtein

    # Normalizar
    c1_norm = c1.lower().replace('|', '').replace('-', '').strip()
    c2_norm = c2.lower().replace('|', '').replace('-', '').strip()

    if not c1_norm or not c2_norm:
        return False

    dist = Levenshtein.normalized_similarity(c1_norm, c2_norm)
    return dist >= limiar


def fusao_difusa(tabelas: List[Tabela]) -> List[List[Tabela]]:
    """
    Agrupa tabelas fragmentadas que representam a mesma tabela lógica.

    Retorna lista de grupos, onde cada grupo é uma lista de tabelas.
    Se a tabela não tem vizinha similar, fica sozinha no grupo.
    """
    if not tabelas:
        return []

    usado = [False] * len(tabelas)
    grupos = []

    for i, t in enumerate(tabelas):
        if usado[i]:
            continue

        grupo = [t]
        usado[i] = True

        # Procurar vizinhas similares (consecutivas e com cabeçalho próximo)
        for j in range(i + 1, len(tabelas)):
            if usado[j]:
                continue

            t_prox = tabelas[j]

            # Vizinha consecutiva? (sem tabelas entre elas)
            se_consecutiva = (t_prox.inicio == grupo[-1].fim or
                            t_prox.inicio == grupo[-1].fim + 1)

            if se_consecutiva and similaridade_cabecalho(grupo[-1].cabecalho, t_prox.cabecalho):
                grupo.append(t_prox)
                usado[j] = True

        grupos.append(grupo)

    return grupos


def distancia_edicao_tabela(t1: Tabela, t2: Tabela) -> float:
    """
    Distância de edição normalizada entre duas tabelas.

    Leva em conta diferença em linhas, colunas e cabeçalho.
    Valor entre 0 (idênticas) e 1 (completamente diferentes).
    """
    # Diferença em tamanho
    delta_linhas = abs(t1.linhas - t2.linhas)
    delta_colunas = abs(t1.colunas - t2.colunas)

    tamanho_max = max(t1.tamanho(), t2.tamanho())
    if tamanho_max == 0:
        delta_tamanho = 0
    else:
        delta_tamanho = (delta_linhas + delta_colunas) / tamanho_max

    # Diferença em cabeçalho
    from rapidfuzz.distance import Levenshtein
    dist_cabecalho = 1 - Levenshtein.normalized_similarity(
        t1.cabecalho.lower(),
        t2.cabecalho.lower()
    )

    # Média ponderada
    return 0.7 * delta_tamanho + 0.3 * dist_cabecalho


def pareamento_otimo(grupos_pred: List[List[Tabela]],
                     grupos_ref: List[List[Tabela]]) -> Tuple[float, dict]:
    """
    Pareamento ótimo entre tabelas preditas e referência usando algoritmo húngaro.

    Returns:
        (score: similaridade média do melhor pareamento,
         pareamentos: dicionário {índice_pred -> índice_ref})
    """
    n_pred = len(grupos_pred)
    n_ref = len(grupos_ref)

    if n_pred == 0 or n_ref == 0:
        return 0.0, {}

    # Matriz de custos (distância)
    custo = np.zeros((n_pred, n_ref))

    for i, grupo_pred in enumerate(grupos_pred):
        # Usar primeira tabela do grupo como representante
        t_pred = grupo_pred[0]

        for j, grupo_ref in enumerate(grupos_ref):
            t_ref = grupo_ref[0]
            custo[i, j] = distancia_edicao_tabela(t_pred, t_ref)

    # Algoritmo húngaro minimiza custo
    linha_ind, col_ind = linear_sum_assignment(custo)

    # Converter em similaridade
    similaridades = 1 - custo[linha_ind, col_ind]
    score = float(np.mean(similaridades)) if len(similaridades) > 0 else 0.0

    pareamentos = {int(i): int(j) for i, j in zip(linha_ind, col_ind)}

    return score, pareamentos


def markdown_teds(pred: str, ref: str) -> float:
    """
    Markdown TEDS Score: similaridade estrutural de Markdown.

    Implementa as três modificações ao TEDS:
    1. Isolamento de tabelas
    2. Fusão difusa de tabelas fragmentadas
    3. Pareamento ótimo com algoritmo húngaro

    Args:
        pred: Markdown predito
        ref: Markdown referência (gabarito)

    Returns:
        Score entre 0 (completamente diferente) e 1 (idêntico).
        Considera principalmente a estrutura de tabelas.
    """
    # Extrair tabelas
    tabelas_pred = extrair_tabelas(pred)
    tabelas_ref = extrair_tabelas(ref)

    # Fusão difusa
    grupos_pred = fusao_difusa(tabelas_pred)
    grupos_ref = fusao_difusa(tabelas_ref)

    # Pareamento ótimo
    score, _ = pareamento_otimo(grupos_pred, grupos_ref)

    return score


if __name__ == "__main__":
    # Teste rápido
    markdown_ref = """
| Coluna A | Coluna B |
|---|---|
| Valor 1 | Valor 2 |
| Valor 3 | Valor 4 |
"""

    markdown_pred = """
| Coluna A | Coluna B |
|---|---|
| Valor 1 | Valor 2 |
| Valor 3 | Valor 4 |
"""

    score = markdown_teds(markdown_pred, markdown_ref)
    print(f"Score: {score:.3f}")
