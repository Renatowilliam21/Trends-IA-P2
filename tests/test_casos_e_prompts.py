"""Casos de teste e prompts. Inclui a garantia de que NÃO há RAG no Básico."""
import pytest

from casos import ARQUIVO_PADRAO, MINIMO_DE_CASOS, carregar_casos
from config import ConfigGeracao, carregar_configuracoes
from erros import ErroCasos
from prompts import instrucoes, montar_corpo, montar_mensagens


def test_casos_do_projeto_atendem_o_enunciado():
    casos = carregar_casos(ARQUIVO_PADRAO)
    assert len(casos) >= MINIMO_DE_CASOS
    assert any(c.tipo == "ausente" for c in casos)
    assert any(c.tipo == "resposta" for c in casos)
    assert len({c.id for c in casos}) == len(casos)


def _escrever(tmp_path, texto):
    arquivo = tmp_path / "casos.toml"
    arquivo.write_text(texto, encoding="utf-8")
    return arquivo


def _caso(i, tipo="resposta"):
    return (f'[[caso]]\nid="C{i}"\ntipo="{tipo}"\npergunta="p{i}?"\n'
            f'resposta_esperada="r{i}"\nreferencia="Art. {i}"\n')


def test_poucos_casos(tmp_path):
    arquivo = _escrever(tmp_path, _caso(1) + _caso(2, "ausente"))
    with pytest.raises(ErroCasos, match="pelo menos 6"):
        carregar_casos(arquivo)


def test_exige_caso_ausente(tmp_path):
    arquivo = _escrever(tmp_path, "".join(_caso(i) for i in range(1, 8)))
    with pytest.raises(ErroCasos, match="'ausente'"):
        carregar_casos(arquivo)


def test_id_repetido(tmp_path):
    texto = "".join(_caso(i) for i in range(1, 7)) + _caso(1, "ausente")
    with pytest.raises(ErroCasos, match="repetido"):
        carregar_casos(_escrever(tmp_path, texto))


def test_campo_faltando(tmp_path):
    texto = "".join(_caso(i) for i in range(1, 7)) + '[[caso]]\nid="X"\ntipo="ausente"\n'
    with pytest.raises(ErroCasos, match="'pergunta' é obrigatório"):
        carregar_casos(_escrever(tmp_path, texto))


def test_tipo_invalido(tmp_path):
    texto = "".join(_caso(i) for i in range(1, 7)) + _caso(7, "talvez")
    with pytest.raises(ErroCasos, match="tipo deve ser"):
        carregar_casos(_escrever(tmp_path, texto))


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(ErroCasos, match="não encontrado"):
        carregar_casos(tmp_path / "nao_existe.toml")


def test_instrucoes_incluem_formato_da_configuracao(config_a, config_b):
    assert "texto corrido" in instrucoes(config_a)
    assert "objeto JSON" in instrucoes(config_b)
    assert "Não tenho informação suficiente" in instrucoes(config_a)   # regra de ausência


def test_mensagens_so_tem_instrucao_e_pergunta(caso, config_a):
    mensagens = montar_mensagens(caso, config_a)
    assert [m["role"] for m in mensagens] == ["system", "user"]
    assert mensagens[1]["content"] == caso.pergunta


def test_prompt_nunca_contem_o_corpus_nem_as_referencias():
    """Condição sem RAG: nada das respostas esperadas ou do ROD pode ir ao modelo."""
    _, configs = carregar_configuracoes()
    from config import Servico
    servico = Servico(chave="sk-x")
    for caso in carregar_casos():
        for config in configs.values():
            enviado = str(montar_corpo(caso, config, servico))
            assert caso.resposta_esperada not in enviado
            assert caso.referencia not in enviado
            assert "Resolução Consup" not in enviado


def test_corpo_omite_parametros_opcionais_quando_nao_definidos(caso, config_a, servico):
    corpo = montar_corpo(caso, config_a, servico)
    assert "temperature" not in corpo and "reasoning_effort" not in corpo
    assert corpo["max_completion_tokens"] == config_a.max_tokens
    assert corpo["model"] == servico.modelo


def test_corpo_inclui_parametros_opcionais_quando_definidos(caso, servico):
    config = ConfigGeracao(nome="C", temperature=0.2, reasoning_effort="low")
    corpo = montar_corpo(caso, config, servico)
    assert corpo["temperature"] == 0.2 and corpo["reasoning_effort"] == "low"


def test_corpo_nunca_leva_a_chave(caso, config_a, servico):
    assert servico.chave not in str(montar_corpo(caso, config_a, servico))
