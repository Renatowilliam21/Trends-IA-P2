"""Conjunto ampliado, comparação por categoria, demonstração de falhas e comando executar."""
import csv

import assistente_p2 as cli
import executor
from casos import CATEGORIAS, carregar_casos
from cliente import RespostaModelo
from comparacao import comparar, renderizar_markdown
from config import carregar_fluxo
from demonstracao import demonstrar
from erros import ErroServico


def test_conjunto_tem_pelo_menos_oito_casos_e_todas_as_categorias_pedidas():
    casos = carregar_casos()
    assert len(casos) >= 8
    assert set(CATEGORIAS) <= {c.categoria for c in casos}
    assert all(c.categoria for c in casos)
    # reconhecimento de incerteza ou recusa: ao menos um caso em que o certo é não responder
    assert sum(c.tipo == "ausente" for c in casos) >= 1


def test_casos_do_basico_foram_mantidos():
    por_id = {c.id: c for c in carregar_casos()}
    assert all(f"C0{i}" in por_id for i in range(1, 9))
    assert "7,0" in por_id["C01"].resposta_esperada


def test_fluxo_do_projeto_tem_limites_finitos():
    p = carregar_fluxo()
    assert 1 <= p.max_tentativas <= 5 and p.falhas_seguidas_max >= 1


def _linhas():
    base = dict(tipo="resposta", repeticao="1", erro="", latencia_s="1", tokens_total="100",
                formato_valido="True", recusa_detectada="False", chamadas="1",
                tempo_total_s="1.5", situacao_final="concluido")
    dados = [("C01", "direta", "A", "3"), ("C01", "direta", "B", "1"),
             ("C09", "combinada", "A", "1"), ("C09", "combinada", "B", "3")]
    return [{**base, "caso_id": c, "categoria": cat, "configuracao": cfg, "nota": n}
            for c, cat, cfg, n in dados]


def test_comparacao_traz_nota_por_categoria_e_situacoes():
    resultado = comparar(_linhas(), "A")
    assert resultado["categorias"]["direta"]["A"]["nota_media"] == 3
    assert resultado["categorias"]["combinada"]["B"]["nota_media"] == 3
    assert resultado["situacoes"]["A"]["concluido"] == 2
    texto = renderizar_markdown(resultado)
    assert "Nota média por categoria" in texto and "Situação final" in texto


def test_comparacao_continua_funcionando_com_csv_antigo():
    antigas = [{k: v for k, v in l.items()
                if k not in ("categoria", "situacao_final", "chamadas", "tempo_total_s")}
               for l in _linhas()]
    resultado = comparar(antigas, "A")
    assert resultado["categorias"] is None and resultado["situacoes"] is None
    assert "Nota média por categoria" not in renderizar_markdown(resultado)


def test_demonstracao_cobre_as_falhas_e_nao_fica_em_laco(tmp_path):
    saidas = []
    resultados = demonstrar(tmp_path / "ev.jsonl", mostrar=saidas.append)
    por_nome = {n: (s, c) for n, s, c, _ in resultados}
    assert por_nome["Entrada vazia"] == ("interrompido", 0)
    assert por_nome["Timeout que se recupera na 2ª tentativa"] == ("concluido", 2)
    assert por_nome["Timeout persistente (limite de tentativas)"][0] == "falha"
    assert por_nome["Timeout persistente (limite de tentativas)"][1] <= carregar_fluxo().max_tentativas
    assert por_nome["Credencial inválida (não repete)"] == ("falha", 1)
    assert por_nome["JSON fora do formato (configuração B)"][0] == "parcial"
    assert any(s == "encerrado" for _, s, _, _ in resultados)
    assert (tmp_path / "ev.jsonl").read_text(encoding="utf-8").strip()


def test_comando_demonstrar_falhas(tmp_path, capsys):
    assert cli.main(["demonstrar-falhas", "--saida", str(tmp_path)]) == 0
    assert "Cenário" in capsys.readouterr().out
    assert (tmp_path / "demonstracao_falhas.eventos.jsonl").exists()


def test_executar_com_servico_fora_do_ar_salva_parcial_e_sai_com_codigo_2(
        tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-teste")
    original = executor.executar_caso

    def fora_do_ar(corpo, servico):
        raise ErroServico("O serviço está indisponível no momento.", transitorio=True)

    def com_api_falsa(caso, config, servico, execucao_id, repeticao=1, chamar=None, *a, **k):
        return original(caso, config, servico, execucao_id, repeticao, fora_do_ar, *a, **k)

    monkeypatch.setattr(executor, "executar_caso", com_api_falsa)
    monkeypatch.setattr(executor, "time", type("T", (), {"sleep": staticmethod(lambda s: None),
                                                           "perf_counter": __import__("time").perf_counter}))
    assert cli.main(["executar", "--saida", str(tmp_path), "--max-tentativas", "1"]) == 2
    saida = capsys.readouterr()
    assert "Execução encerrada" in saida.err and "Traceback" not in saida.err
    with open(next(tmp_path.glob("*.csv")), newline="", encoding="utf-8-sig") as f:
        linhas = list(csv.DictReader(f))
    assert 1 <= len(linhas) < 42 and all(l["situacao_final"] == "falha" for l in linhas)


def test_max_tentativas_invalido(capsys):
    assert cli.main(["executar", "--max-tentativas", "0"]) == 1
    assert "--max-tentativas" in capsys.readouterr().err
