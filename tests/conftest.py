"""Apoio comum aos testes."""
import pytest

import config
from casos import Caso
from config import ConfigGeracao, Servico

VARIAVEIS = ("OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_TIMEOUT")


@pytest.fixture(autouse=True)
def ambiente_isolado(monkeypatch, request):
    """Cada teste começa sem variáveis do usuário (os reais usam o ambiente verdadeiro)."""
    if request.node.get_closest_marker("real"):
        return
    for nome in VARIAVEIS:
        monkeypatch.delenv(nome, raising=False)
    # Sem isto, um .env real do usuário seria lido e os testes fariam chamadas pagas.
    monkeypatch.setattr(config, "load_dotenv", lambda *a, **k: False)


@pytest.fixture
def servico():
    return Servico(chave="sk-chave-de-teste")


@pytest.fixture
def config_a():
    return ConfigGeracao(nome="A", formato="livre")


@pytest.fixture
def config_b():
    return ConfigGeracao(nome="B", formato="json")


@pytest.fixture
def caso():
    return Caso("T1", "resposta", "Qual a média mínima?", "7,0 (Art. 99).", "Art. 99, II")
