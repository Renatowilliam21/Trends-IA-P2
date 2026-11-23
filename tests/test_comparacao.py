"""Comparação entre configurações a partir do CSV com notas."""
import pytest

from comparacao import (ErroComparacao, comparar, ler_resultados, renderizar_markdown,
                        validar_notas)


def linha(caso, config, nota, tipo="resposta", rep=1, lat="2.0", tokens="100", erro="",
          formato="True", recusa="False"):
    return {"caso_id": caso, "tipo": tipo, "configuracao": config, "repeticao": str(rep),
            "nota": str(nota), "latencia_s": lat, "tokens_total": tokens, "erro": erro,
            "formato_valido": formato, "recusa_detectada": recusa}


@pytest.fixture
def linhas():
    return [
        linha("C1", "A", 2, lat="2.0"), linha("C1", "B", 3, lat="3.0", tokens="150"),
        linha("C2", "A", 3), linha("C2", "B", 3),
        linha("C3", "A", 1), linha("C3", "B", 0, formato="False"),
        linha("C4", "A", 0, tipo="ausente"),
        linha("C4", "B", 3, tipo="ausente", recusa="True"),
    ]


def test_status_por_caso(linhas):
    r = comparar(linhas, "A")
    status = {c["caso"]: c["status"]["B"] for c in r["casos"]}
    assert status == {"C1": "melhorou", "C2": "igual", "C3": "piorou", "C4": "melhorou"}


def test_resumo_por_configuracao(linhas):
    r = comparar(linhas, "A")["configuracoes"]
    assert r["A"]["nota_media"] == 1.5 and r["B"]["nota_media"] == 2.25
    assert r["B"]["latencia_media_s"] == 2.25 and r["B"]["tokens_medios"] == 112.5
    assert r["B"]["formato_valido_pct"] == 75.0
    assert (r["B"]["ausentes_reconhecidos"], r["B"]["ausentes_total"]) == (1, 1)
    assert r["A"]["ausentes_reconhecidos"] == 0


def test_virgula_decimal_na_nota():
    linhas = [linha("C1", "A", "2,5"), linha("C1", "B", "3")]
    assert comparar(linhas, "A")["configuracoes"]["A"]["nota_media"] == 2.5


def test_nota_nao_preenchida(linhas):
    linhas[0]["nota"] = ""
    with pytest.raises(ErroComparacao, match="C1/A/rep1: nota não preenchida"):
        comparar(linhas, "A")


def test_nota_fora_da_escala(linhas):
    linhas[0]["nota"] = "5"
    assert "fora da escala" in validar_notas(linhas)[0]


def test_linhas_com_erro_nao_exigem_nota_e_saem_da_media(linhas):
    linhas.append(linha("C5", "A", "", erro="ErroServico: indisponível"))
    linhas.append(linha("C5", "B", 3))
    r = comparar(linhas, "A")
    assert r["configuracoes"]["A"]["erros"] == 1
    assert r["configuracoes"]["A"]["nota_media"] == 1.5


def test_base_inexistente(linhas):
    with pytest.raises(ErroComparacao, match="Linha de base 'Z'"):
        comparar(linhas, "Z")


def test_consistencia_entre_repeticoes():
    linhas = [linha("C1", "A", 3, rep=1), linha("C1", "A", 3, rep=2),
              linha("C1", "B", 3, rep=1), linha("C1", "B", 1, rep=2)]
    consistencia = comparar(linhas, "A")["casos"][0]["consistencia"]
    assert consistencia == {"A": True, "B": False}


def test_markdown_tem_tabelas_e_balanco(linhas):
    texto = renderizar_markdown(comparar(linhas, "A"))
    assert "### Resumo por configuração" in texto and "### Caso a caso" in texto
    assert "B vs A" in texto
    assert "2 caso(s) melhoraram, 1 ficaram iguais e 1 pioraram" in texto


def test_ler_resultados_arquivo_inexistente(tmp_path):
    with pytest.raises(ErroComparacao, match="não encontrado"):
        ler_resultados(tmp_path / "nao_existe.csv")
