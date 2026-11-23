"""Testes REAIS: chamam a API da OpenAI. Não rodam por padrão.

Uso: python -m pytest -m real   (precisa de OPENAI_API_KEY válida e crédito na conta)
Fazem 2 chamadas: o mesmo caso nas configurações A e B.
"""
import pytest

from casos import carregar_casos
from config import carregar_configuracoes, carregar_servico, escolher_configs
from executor import executar

pytestmark = pytest.mark.real


def test_mesmo_caso_nas_configuracoes_a_e_b():
    dados, todas = carregar_configuracoes()
    servico = carregar_servico(dados)
    caso = carregar_casos()[0]
    registros = executar([caso], escolher_configs(todas, ["A", "B"]), servico)
    assert [r["configuracao"] for r in registros] == ["A", "B"]
    for r in registros:
        assert r["erro"] == "", r["erro"]
        assert r["resposta"] and float(r["latencia_s"]) > 0
