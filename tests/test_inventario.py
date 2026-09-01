"""Testes das funções puras do inventário."""

from src.inventario.inventario import (
    classificar_pagina,
    parse_pasta_edicao,
    parse_pasta_mes,
    sem_acento,
)


def test_sem_acento():
    assert sem_acento("EDIÇÃO") == "EDICAO"


def test_parse_pasta_mes():
    assert parse_pasta_mes("04 - ABRIL DE 2025") == (4, 4, 2025)
    assert parse_pasta_mes("05 - JUNHO DE 2025")[1:] == (6, 2025)  # prefixo errado
    assert parse_pasta_mes("docling")[1] is None


def test_parse_pasta_edicao():
    assert parse_pasta_edicao("EDIÇÃO DE 17-01-2025") == ("2025-01-17", False)
    assert parse_pasta_edicao("EDIÇÃO DE 05 A 07-04-2025") == ("2025-04-05", True)
    assert parse_pasta_edicao("qualquer coisa") == (None, None)


def test_classificar_pagina():
    assert classificar_pagina(9000, 2, "CAPA.pdf", 6000, 11000) == "capa"
    assert classificar_pagina(20000, 1, "DA17P15.pdf", 6000, 11000) == "densa"
    assert classificar_pagina(5000, 1, "DA17P02.pdf", 6000, 11000) == "leve"
    assert classificar_pagina(100, 3, "DA17P09.pdf", 6000, 11000) == "predominantemente_visual"
