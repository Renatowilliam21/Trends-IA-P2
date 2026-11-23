"""Chamada ao modelo: medições, autenticação e falhas (API simulada, sem rede)."""
import pytest
import requests

import cliente
from cliente import chamar_modelo, extrair_texto_e_uso
from erros import ErroResposta, ErroServico

CORPO = {"model": "m", "messages": []}


class RespostaFalsa:
    def __init__(self, status=200, corpo=None, json_invalido=False):
        self.status_code, self._corpo, self._invalido = status, corpo, json_invalido

    def json(self):
        if self._invalido:
            raise ValueError("json inválido")
        return self._corpo


def ok(texto="resposta", uso=True):
    corpo = {"choices": [{"message": {"content": texto}, "finish_reason": "stop"}]}
    if uso:
        corpo["usage"] = {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}
    return corpo


def erro(codigo, mensagem="erro"):
    return {"error": {"code": codigo, "type": codigo, "message": mensagem}}


@pytest.fixture
def simular(monkeypatch):
    def _simular(resposta=None, excecao=None, capturar=None):
        def falso_post(url, json=None, headers=None, timeout=None):
            if capturar is not None:
                capturar.update(url=url, json=json, headers=headers, timeout=timeout)
            if excecao:
                raise excecao
            return resposta
        monkeypatch.setattr(cliente.requests, "post", falso_post)
    return _simular


def test_devolve_texto_latencia_e_tokens(servico, simular):
    simular(RespostaFalsa(corpo=ok("7,0 (Art. 99).")))
    r = chamar_modelo(CORPO, servico)
    assert r.texto == "7,0 (Art. 99)." and r.latencia_s >= 0
    assert (r.tokens_entrada, r.tokens_saida, r.tokens_total) == (100, 20, 120)


def test_sem_informacao_de_uso_os_tokens_ficam_vazios(servico, simular):
    simular(RespostaFalsa(corpo=ok(uso=False)))
    r = chamar_modelo(CORPO, servico)
    assert r.tokens_entrada is None and r.tokens_total is None


def test_credencial_so_no_cabecalho(servico, simular):
    capturado = {}
    simular(RespostaFalsa(corpo=ok()), capturar=capturado)
    chamar_modelo(CORPO, servico)
    assert capturado["headers"]["Authorization"] == f"Bearer {servico.chave}"
    assert servico.chave not in str(capturado["json"])
    assert capturado["timeout"] == servico.timeout


@pytest.mark.parametrize("status, corpo, mensagem", [
    (401, erro("invalid_api_key"), "Credencial inválida"),
    (403, erro("forbidden"), "Credencial inválida"),
    (404, erro("model_not_found"), "não encontrado"),
    (429, erro("rate_limit_exceeded"), "Limite de uso"),
    (429, erro("insufficient_quota"), "Sem crédito"),
    (503, {}, "indisponível"),
    (400, erro("unsupported_value", "temperature nao suportada"), "HTTP 400.*temperature nao"),
])
def test_erros_http(servico, simular, status, corpo, mensagem):
    simular(RespostaFalsa(status=status, corpo=corpo))
    with pytest.raises(ErroServico, match=mensagem):
        chamar_modelo(CORPO, servico)


def test_credencial_invalida_nao_expoe_a_chave(servico, simular):
    simular(RespostaFalsa(status=401, corpo=erro("invalid_api_key")))
    with pytest.raises(ErroServico) as e:
        chamar_modelo(CORPO, servico)
    assert servico.chave not in str(e.value)


@pytest.mark.parametrize("excecao, mensagem", [
    (requests.exceptions.Timeout(), "não respondeu"),
    (requests.exceptions.ConnectionError(), "Sem conexão"),
    (requests.exceptions.RequestException(), "Falha de comunicação"),
])
def test_falhas_de_rede(servico, simular, excecao, mensagem):
    simular(excecao=excecao)
    with pytest.raises(ErroServico, match=mensagem):
        chamar_modelo(CORPO, servico)


def test_resposta_que_nao_e_json(servico, simular):
    simular(RespostaFalsa(json_invalido=True))
    with pytest.raises(ErroServico, match="formato inesperado"):
        chamar_modelo(CORPO, servico)


@pytest.mark.parametrize("dados, mensagem", [
    (None, "formato inesperado"), ({}, "formato inesperado"), ({"choices": []}, "formato inesperado"),
    (ok("  "), "vazia"),
    ({"choices": [{"message": {"content": None}, "finish_reason": "length"}]}, "limite de tokens"),
    ({"choices": [{"message": {"content": None, "refusal": "não"}}]}, "recusou"),
])
def test_respostas_problematicas(dados, mensagem):
    with pytest.raises(ErroResposta, match=mensagem):
        extrair_texto_e_uso(dados)
