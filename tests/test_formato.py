"""Validação de formato e detecção de recusa (indicadores automáticos)."""
import json

import pytest

from formato import detectar_recusa, processar

JSON_OK = {"resposta": "7,0 e 75% de frequência.", "certeza": "alta",
           "informacao_ausente": False, "fundamento": "Art. 99"}


def test_livre_valido():
    r = processar("livre", "A média é 7,0 (Art. 99).")
    assert r.formato_valido and r.texto == "A média é 7,0 (Art. 99)." and not r.recusa_detectada


def test_livre_vazio():
    r = processar("livre", "   ")
    assert not r.formato_valido and "vazia" in r.motivo


@pytest.mark.parametrize("texto", [
    "Não tenho informação suficiente para responder com segurança.",
    "Não sei dizer o valor exato.", "Não encontrei essa informação.",
    "Isso não consta no regulamento.", "Não há informação sobre isso.",
    "Não posso confirmar esse valor.",
])
def test_recusas_reconhecidas(texto):
    assert detectar_recusa(texto)


@pytest.mark.parametrize("texto", ["A média é 7,0.", "O prazo é de 5 dias letivos (Art. 110)."])
def test_respostas_normais_nao_sao_recusa(texto):
    assert not detectar_recusa(texto)


def test_json_valido():
    r = processar("json", json.dumps(JSON_OK))
    assert r.formato_valido and r.texto == JSON_OK["resposta"]
    assert r.certeza == "alta" and r.fundamento == "Art. 99" and not r.recusa_detectada


def test_json_com_informacao_ausente_conta_como_recusa():
    obj = dict(JSON_OK, informacao_ausente=True, certeza="baixa", fundamento=None,
               resposta="Não tenho informação suficiente.")
    r = processar("json", json.dumps(obj))
    assert r.formato_valido and r.recusa_detectada and r.fundamento is None


def test_json_dentro_de_bloco_de_codigo_e_desvio_recuperado():
    r = processar("json", "```json\n" + json.dumps(JSON_OK) + "\n```")
    assert not r.formato_valido and "cercado" in r.motivo
    assert r.texto == JSON_OK["resposta"]          # ainda dá para avaliar a resposta


def test_texto_que_nao_e_json():
    r = processar("json", "A média é 7,0.")
    assert not r.formato_valido and "não é JSON" in r.motivo and r.texto == "A média é 7,0."


@pytest.mark.parametrize("mudanca, trecho", [
    ({"certeza": "certissima"}, "certeza"),
    ({"informacao_ausente": "sim"}, "informacao_ausente"),
    ({"resposta": ""}, "resposta"),
    ({"fundamento": 99}, "fundamento"),
    ({"extra": 1}, "não pedidas"),
])
def test_json_fora_do_contrato(mudanca, trecho):
    r = processar("json", json.dumps(dict(JSON_OK, **mudanca)))
    assert not r.formato_valido and trecho in r.motivo


def test_json_sem_chaves():
    r = processar("json", json.dumps({"resposta": "ok"}))
    assert not r.formato_valido and "chaves ausentes" in r.motivo


def test_json_que_nao_e_objeto():
    r = processar("json", "[1, 2, 3]")
    assert not r.formato_valido
