"""Configurações de geração e credencial (sem rede)."""
import pytest

from config import (ARQUIVO_PADRAO, carregar_configuracoes, carregar_servico,
                    escolher_configs, montar_config_geracao, validar_chave)
from erros import ErroConfiguracao


def test_arquivo_do_projeto_traz_a_e_b_ativas_e_c_desligada():
    _, configs = carregar_configuracoes(ARQUIVO_PADRAO)
    assert configs["A"].ativa and configs["B"].ativa and not configs["C"].ativa
    assert configs["A"].formato == "livre" and configs["B"].formato == "json"
    assert configs["A"].max_tokens == configs["B"].max_tokens   # só o formato muda
    assert configs["C"].reasoning_effort == "low"


def test_d_difere_da_a_apenas_na_instrucao_de_saida():
    _, configs = carregar_configuracoes(ARQUIVO_PADRAO)
    a, d = configs["A"].parametros(), configs["D"].parametros()
    assert configs["D"].ativa and configs["D"].formato == "conferir"
    assert {k for k in a.keys() | d.keys() if a.get(k) != d.get(k)} == {"formato"}


def test_a_e_b_diferem_apenas_no_formato():
    _, configs = carregar_configuracoes(ARQUIVO_PADRAO)
    a, b = configs["A"].parametros(), configs["B"].parametros()
    diferentes = {k for k in a.keys() | b.keys() if a.get(k) != b.get(k)}
    assert diferentes == {"formato"}


def test_escolher_usa_apenas_ativas_por_padrao():
    _, configs = carregar_configuracoes(ARQUIVO_PADRAO)
    assert [c.nome for c in escolher_configs(configs)] == ["A", "B", "D"]


def test_escolher_aceita_nomes_explicitos():
    _, configs = carregar_configuracoes(ARQUIVO_PADRAO)
    assert [c.nome for c in escolher_configs(configs, ["A", "C"])] == ["A", "C"]


def test_escolher_exige_duas_configuracoes():
    _, configs = carregar_configuracoes(ARQUIVO_PADRAO)
    with pytest.raises(ErroConfiguracao, match="pelo menos duas"):
        escolher_configs(configs, ["A"])


def test_escolher_nome_inexistente():
    _, configs = carregar_configuracoes(ARQUIVO_PADRAO)
    with pytest.raises(ErroConfiguracao, match="inexistente: Z"):
        escolher_configs(configs, ["A", "Z"])


@pytest.mark.parametrize(
    "bruto, mensagem",
    [
        ({"formato": "xml"}, "formato deve ser"),
        ({"max_tokens": 0}, "inteiro maior que zero"),
        ({"max_tokens": "muito"}, "inteiro maior que zero"),
        ({"temperature": 5}, "entre 0 e 2"),
        ({"reasoning_effort": ""}, "deve ser um texto"),
        ({"parametro_inventado": 1}, "desconhecido"),
    ],
)
def test_configuracao_invalida(bruto, mensagem):
    with pytest.raises(ErroConfiguracao, match=mensagem):
        montar_config_geracao("X", bruto)


def test_toml_inexistente_ou_com_erro(tmp_path):
    with pytest.raises(ErroConfiguracao, match="não encontrado"):
        carregar_configuracoes(tmp_path / "nao_existe.toml")
    ruim = tmp_path / "ruim.toml"
    ruim.write_text("[configuracoes.A\n", encoding="utf-8")
    with pytest.raises(ErroConfiguracao, match="erro de sintaxe"):
        carregar_configuracoes(ruim)


def test_toml_sem_configuracoes(tmp_path):
    vazio = tmp_path / "vazio.toml"
    vazio.write_text("[servico]\nmodelo = 'x'\n", encoding="utf-8")
    with pytest.raises(ErroConfiguracao, match="Nenhuma configuração"):
        carregar_configuracoes(vazio)


@pytest.mark.parametrize("chave, mensagem", [
    ("", "Credencial ausente"), ("   ", "Credencial ausente"),
    ("key_abc", "formato esperado"), ('"sk-abc"', "aspas"), ("sk-a b", "espaços"),
])
def test_credencial_invalida(chave, mensagem):
    with pytest.raises(ErroConfiguracao, match=mensagem):
        validar_chave(chave)


def test_credencial_nao_aparece_na_mensagem_nem_no_repr(servico):
    with pytest.raises(ErroConfiguracao) as erro:
        validar_chave("key_segredo123")
    assert "segredo123" not in str(erro.value)
    assert servico.chave not in repr(servico)


def test_servico_usa_ambiente_antes_do_toml():
    servico = carregar_servico(
        {"modelo": "do-toml", "timeout_segundos": 10},
        ambiente={"OPENAI_API_KEY": "sk-x", "OPENAI_MODEL": "do-ambiente"},
        carregar_dotenv=False)
    assert servico.modelo == "do-ambiente" and servico.timeout == 10


def test_servico_timeout_invalido():
    with pytest.raises(ErroConfiguracao, match="OPENAI_TIMEOUT"):
        carregar_servico({}, ambiente={"OPENAI_API_KEY": "sk-x", "OPENAI_TIMEOUT": "abc"},
                         carregar_dotenv=False)
