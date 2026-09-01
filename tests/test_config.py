"""Testes do carregamento de configuração."""

import pytest

from src.utils.config import carregar_config


def test_config_ausente_da_mensagem_util(tmp_path):
    with pytest.raises(FileNotFoundError, match="config.yaml"):
        carregar_config(tmp_path / "nao_existe.yaml")


def test_config_sem_raiz_preenchida(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("corpus:\n  raiz: MUDE_AQUI\n", encoding="utf-8")
    with pytest.raises(ValueError, match="corpus.raiz"):
        carregar_config(p)
