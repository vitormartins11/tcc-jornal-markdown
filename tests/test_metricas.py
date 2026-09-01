import pytest
from src.metricas.markdown_teds import (
    extrair_tabelas, fusao_difusa, markdown_teds,
    similaridade_cabecalho, distancia_edicao_tabela, Tabela
)


def test_extrair_tabelas_simples():
    md = """
| A | B |
|---|---|
| 1 | 2 |
"""
    tabelas = extrair_tabelas(md)
    assert len(tabelas) == 1
    assert tabelas[0].colunas == 2


def test_extrair_tabelas_multiplas():
    md = """
| A | B |
|---|---|
| 1 | 2 |

Texto no meio.

| X | Y | Z |
|---|---|---|
| a | b | c |
"""
    tabelas = extrair_tabelas(md)
    assert len(tabelas) == 2
    assert tabelas[1].colunas == 3


def test_similaridade_cabecalho_identico():
    assert similaridade_cabecalho("| Coluna A |", "| Coluna A |") == True


def test_similaridade_cabecalho_diferente():
    assert similaridade_cabecalho("| Coluna A |", "| Coluna X |", limiar=0.9) == False


def test_markdown_teds_identico():
    md = """
| A | B |
|---|---|
| 1 | 2 |
| 3 | 4 |
"""
    score = markdown_teds(md, md)
    assert score > 0.9, f"Score foi {score}, esperado > 0.9"


def test_markdown_teds_vazio():
    score = markdown_teds("sem tabelas", "sem tabelas")
    assert score == 0.0, "Nenhuma tabela, score deveria ser 0"


def test_markdown_teds_tabelas_diferentes():
    md_ref = """
| A | B |
|---|---|
| 1 | 2 |
"""

    md_pred = """
| X | Y |
|---|---|
| 9 | 8 |
"""

    score = markdown_teds(md_pred, md_ref)
    assert 0 <= score <= 1, f"Score fora de [0, 1]: {score}"
