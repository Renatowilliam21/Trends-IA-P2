"""Executor: mesmo caso em configurações diferentes, registros comparáveis, erros registrados."""
import csv
import json

from cliente import RespostaModelo
from erros import ErroServico
from executor import COLUNAS, executar, executar_caso, salvar

JSON_RESP = json.dumps({"resposta": "7,0.", "certeza": "alta",
                        "informacao_ausente": False, "fundamento": "Art. 99"})


def falso(com_tokens=True, texto=None):
    def chamar(corpo, servico):
        livre = "texto corrido" in corpo["messages"][0]["content"]
        t = texto or ("Resposta livre." if livre else JSON_RESP)
        tokens = (100, 20, 120) if com_tokens else (None, None, None)
        return RespostaModelo(t, 1.234, *tokens)
    return chamar


def test_registro_completo(caso, config_a, servico):
    r = executar_caso(caso, config_a, servico, "exec1", chamar=falso())
    assert set(r) == set(COLUNAS)
    assert (r["caso_id"], r["configuracao"], r["repeticao"]) == ("T1", "A", 1)
    assert r["latencia_s"] == 1.234 and r["tokens_total"] == 120
    assert (r["consumo_medida"], r["consumo_valor"]) == ("tokens", 120)
    assert r["formato_valido"] is True and r["erro"] == "" and r["nota"] == ""
    assert json.loads(r["parametros"])["formato"] == "livre"


def test_sem_tokens_usa_chamadas_como_medida(caso, config_a, servico):
    r = executar_caso(caso, config_a, servico, "e", chamar=falso(com_tokens=False))
    assert (r["consumo_medida"], r["consumo_valor"], r["tokens_total"]) == ("chamadas", 1, "")


def test_erro_vira_registro_e_nao_interrompe(caso, config_a, servico):
    def quebra(corpo, servico):
        raise ErroServico("O serviço está indisponível no momento.")
    r = executar_caso(caso, config_a, servico, "e", chamar=quebra)
    assert "ErroServico" in r["erro"] and "indisponível" in r["erro"]
    assert r["resposta"] == "" and r["latencia_s"] == ""


def test_mesmo_caso_em_todas_as_configuracoes(caso, config_a, config_b, servico):
    registros = executar([caso], [config_a, config_b], servico, chamar=falso())
    assert [(r["caso_id"], r["configuracao"]) for r in registros] == [("T1", "A"), ("T1", "B")]
    assert len({r["execucao_id"] for r in registros}) == 1


def test_a_logica_nao_e_duplicada_so_o_formato_muda(caso, config_a, config_b, servico):
    enviados = []

    def captura(corpo, servico):
        enviados.append(corpo)
        return RespostaModelo("ok", 0.1, None, None, None)

    executar([caso], [config_a, config_b], servico, chamar=captura)
    a, b = enviados
    assert a["model"] == b["model"] and a["max_completion_tokens"] == b["max_completion_tokens"]
    assert a["messages"][1] == b["messages"][1]                   # mesma pergunta
    assert a["messages"][0] != b["messages"][0]                   # só a instrução de formato
    assert a["messages"][0]["content"].split("\n\n")[0] == b["messages"][0]["content"].split("\n\n")[0]


def test_ordem_intercala_configuracoes_e_repete(caso, config_a, config_b, servico):
    registros = executar([caso], [config_a, config_b], servico, repeticoes=2, chamar=falso())
    assert [(r["repeticao"], r["configuracao"]) for r in registros] == \
        [(1, "A"), (1, "B"), (2, "A"), (2, "B")]


def test_callback_recebe_cada_registro(caso, config_a, config_b, servico):
    vistos = []
    executar([caso], [config_a, config_b], servico, chamar=falso(), ao_terminar=vistos.append)
    assert len(vistos) == 2


def test_json_fora_do_formato_e_registrado(caso, config_b, servico):
    r = executar_caso(caso, config_b, servico, "e", chamar=falso(texto="só texto"))
    assert r["formato_valido"] is False and "não é JSON" in r["motivo_formato"]


def test_salvar_grava_csv_e_jsonl(tmp_path, caso, config_a, config_b, servico):
    registros = executar([caso], [config_a, config_b], servico, chamar=falso())
    csv_path, jsonl_path = salvar(registros, tmp_path / "saida")
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        linhas = list(csv.DictReader(f))
    assert [l["configuracao"] for l in linhas] == ["A", "B"] and list(linhas[0]) == COLUNAS
    assert len(jsonl_path.read_text(encoding="utf-8").splitlines()) == 2
