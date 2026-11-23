"""Fluxo em três etapas: registros, tentativas limitadas, falhas tratadas, sem segredos."""
import json

import pytest

from cliente import RespostaModelo
from config import ParametrosFluxo
from erros import ErroEntrada, ErroResposta, ErroServico, ExecucaoInterrompida
from executor import COLUNAS, executar, executar_caso
from fluxo import consultar_modelo, preparar_pergunta
from registro import Registro, limpar

JSON_RESP = json.dumps({"resposta": "7,0.", "certeza": "alta",
                        "informacao_ausente": False, "fundamento": "Art. 99"})
TIMEOUT = ErroServico("O serviço não respondeu em 60 segundos.", transitorio=True)
FATAL = ErroServico("Credencial inválida ou sem permissão.", fatal=True)


def api(*itens):
    """API simulada: devolve em ordem; o último item se repete."""
    restantes, chamadas = list(itens), []

    def chamar(corpo, servico):
        chamadas.append(corpo)
        item = restantes.pop(0) if len(restantes) > 1 else restantes[0]
        if isinstance(item, Exception):
            raise item
        return RespostaModelo(item, 0.5, 10, 5, 15)
    chamar.chamadas = chamadas
    return chamar


def rodar(caso, config, servico, chamar, params=None, **extra):
    registro = Registro()
    esperas = []
    linha = executar_caso(caso, config, servico, "e1", 1, chamar, params or ParametrosFluxo(),
                          registro, esperas.append, **extra)
    return linha, registro, esperas


def test_preparar_normaliza_e_recusa_vazio_e_longo():
    assert preparar_pergunta("  Qual   a  média? \n", 100) == "Qual a média?"
    with pytest.raises(ErroEntrada, match="vazia"):
        preparar_pergunta("   ", 100)
    with pytest.raises(ErroEntrada, match="máximo"):
        preparar_pergunta("x" * 101, 100)


def test_caminho_feliz_registra_as_tres_etapas(caso, config_a, servico):
    linha, registro, _ = rodar(caso, config_a, servico, api("Resposta."))
    assert linha["situacao_final"] == "concluido" and linha["chamadas"] == 1
    assert set(linha) == set(COLUNAS) and linha["versao_prompt"] and linha["tempo_total_s"] != ""
    etapas = [(e["etapa"], e["evento"]) for e in registro.eventos if e["evento"] != "tentativa"]
    assert etapas == [("preparar_pergunta", "inicio"), ("preparar_pergunta", "fim"),
                      ("consultar_modelo", "inicio"), ("consultar_modelo", "fim"),
                      ("organizar_resposta", "inicio"), ("organizar_resposta", "fim"),
                      ("caso", "fim")]


def test_eventos_trazem_os_campos_minimos(caso, config_a, servico):
    _, registro, _ = rodar(caso, config_a, servico, api("Resposta."))
    for e in registro.eventos:
        for campo in ("caso_id", "configuracao", "etapa", "evento", "data"):
            assert e[campo]
    fim = [e for e in registro.eventos if e["evento"] == "fim"]
    assert all("resultado" in e and "duracao_s" in e for e in fim)
    assert registro.eventos[-1]["situacao_final"] == "concluido"


def test_entrada_vazia_interrompe_sem_chamar_o_modelo(caso, config_a, servico):
    chamar = api("nunca")
    linha, registro, _ = rodar(caso, config_a, servico, chamar, pergunta="  ")
    assert linha["situacao_final"] == "interrompido" and linha["chamadas"] == 0
    assert chamar.chamadas == [] and "ErroEntrada" in linha["erro"]
    assert not any(e["etapa"] == "consultar_modelo" for e in registro.eventos)


def test_timeout_se_recupera_com_nova_tentativa_e_espera_crescente(caso, config_a, servico):
    linha, _, esperas = rodar(caso, config_a, servico, api(TIMEOUT, TIMEOUT, "Resposta."))
    assert linha["situacao_final"] == "concluido" and linha["chamadas"] == 3
    assert esperas == [1.0, 2.0]


def test_tentativas_tem_limite_e_nao_sao_indefinidas(caso, config_a, servico):
    chamar = api(TIMEOUT)
    linha, _, esperas = rodar(caso, config_a, servico, chamar,
                              ParametrosFluxo(max_tentativas=3))
    assert linha["situacao_final"] == "falha" and linha["chamadas"] == 3
    assert len(chamar.chamadas) == 3 and len(esperas) == 2


def test_falha_fatal_nao_repete(caso, config_a, servico):
    chamar = api(FATAL)
    linha, _, esperas = rodar(caso, config_a, servico, chamar)
    assert linha["situacao_final"] == "falha" and len(chamar.chamadas) == 1 and esperas == []


def test_resposta_vazia_do_servico_vira_falha_controlada(caso, config_a, servico):
    linha, _, _ = rodar(caso, config_a, servico, api(ErroResposta("resposta vazia")))
    assert linha["situacao_final"] == "falha" and "ErroResposta" in linha["erro"]


def test_json_fora_do_formato_e_parcial_e_aproveita_o_texto(caso, config_b, servico):
    linha, _, _ = rodar(caso, config_b, servico, api("Só texto, sem JSON."))
    assert linha["situacao_final"] == "parcial" and linha["formato_valido"] is False
    assert linha["resposta"] == "Só texto, sem JSON." and linha["erro"] == ""


def test_json_valido_e_concluido(caso, config_b, servico):
    linha, _, _ = rodar(caso, config_b, servico, api(JSON_RESP))
    assert linha["situacao_final"] == "concluido" and linha["resposta"] == "7,0."


def test_consultar_modelo_devolve_tentativas(servico):
    resposta, tentativas = consultar_modelo({}, servico, ParametrosFluxo(), api(TIMEOUT, "ok"),
                                            lambda s: None, lambda n, e: None)
    assert resposta.texto == "ok" and tentativas == 2


def test_registros_nao_guardam_credencial_pergunta_nem_resposta(caso, config_a, servico):
    segredo = ErroServico("falha com Bearer sk-SEGREDO1234567890 no cabeçalho", fatal=True)
    _, registro, _ = rodar(caso, config_a, servico, api(segredo))
    texto = json.dumps(registro.eventos, ensure_ascii=False)
    assert "SEGREDO" not in texto and "sk-" not in texto
    assert caso.pergunta not in texto and caso.resposta_esperada not in texto

    _, registro, _ = rodar(caso, config_a, servico, api("RESPOSTA SIGILOSA DO MODELO"))
    assert "SIGILOSA" not in json.dumps(registro.eventos, ensure_ascii=False)


def test_limpar_corta_e_remove_chaves():
    assert "[removido]" in limpar("chave sk-abcdefghijkl123")
    assert len(limpar("x" * 500)) <= 203


def test_registro_grava_arquivo_linha_a_linha(tmp_path, caso, config_a, servico):
    caminho = tmp_path / "pasta" / "eventos.jsonl"
    registro = Registro(caminho)
    executar_caso(caso, config_a, servico, "e1", 1, api("ok"), ParametrosFluxo(), registro,
                  lambda s: None)
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    assert len(linhas) == len(registro.eventos) and json.loads(linhas[0])["etapa"]


def test_versao_do_prompt_muda_com_a_instrucao(caso, config_a, config_b, servico):
    a, _, _ = rodar(caso, config_a, servico, api("ok"))
    b, _, _ = rodar(caso, config_b, servico, api(JSON_RESP))
    assert a["versao_prompt"] != b["versao_prompt"]
    a2, _, _ = rodar(caso, config_a, servico, api("ok"))
    assert a["versao_prompt"] == a2["versao_prompt"]


def test_executar_encerra_na_falha_fatal_e_preserva_registros(caso, config_a, config_b, servico):
    with pytest.raises(ExecucaoInterrompida) as erro:
        executar([caso, caso], [config_a, config_b], servico, chamar=api(FATAL),
                 dormir=lambda s: None)
    assert len(erro.value.registros) == 1 and "Credencial" in str(erro.value)


def test_executar_encerra_apos_falhas_seguidas_do_servico(caso, config_a, config_b, servico):
    chamar = api(TIMEOUT)
    with pytest.raises(ExecucaoInterrompida) as erro:
        executar([caso] * 5, [config_a, config_b], servico, chamar=chamar,
                 params=ParametrosFluxo(max_tentativas=2, falhas_seguidas_max=3),
                 dormir=lambda s: None)
    assert len(erro.value.registros) == 3 and len(chamar.chamadas) == 6   # 3 casos x 2 tentativas


def test_sucesso_zera_a_contagem_de_falhas_seguidas(caso, config_a, servico):
    sequencia = [TIMEOUT, TIMEOUT, "ok", TIMEOUT, TIMEOUT, "ok"]
    chamar = api(*sequencia)
    registros = executar([caso] * 3, [config_a], servico, chamar=chamar,
                         params=ParametrosFluxo(max_tentativas=1, falhas_seguidas_max=3),
                         dormir=lambda s: None)
    assert [r["situacao_final"] for r in registros] == ["falha", "falha", "concluido"]


def test_entrada_invalida_nao_conta_como_falha_do_servico(caso, config_a, servico):
    from fluxo import executar_fluxo
    sinal = {}
    executar_fluxo(caso, config_a, servico, "e", 1, api("ok"), pergunta="", sinal=sinal)
    assert sinal == {}
