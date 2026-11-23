"""Avaliação manual guiada, com entrada simulada."""
import csv

import pytest

from avaliacao import avaliar
from casos import carregar_casos
from comparacao import ler_resultados, validar_notas
from executor import COLUNAS


def _csv(tmp_path, n_casos=2):
    linhas = []
    for caso in ("C01", "C02")[:n_casos]:
        for cfg in ("A", "B"):
            l = {c: "" for c in COLUNAS}
            l.update(caso_id=caso, tipo="resposta", configuracao=cfg, repeticao="1",
                     resposta=f"resposta {caso}{cfg}")
            linhas.append(l)
    caminho = tmp_path / "execucao_x.csv"
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS)
        w.writeheader()
        w.writerows(linhas)
    return caminho


def _entradas(*valores):
    it = iter(valores)
    return lambda prompt="": next(it)


def test_grava_notas_e_observacoes(tmp_path):
    caminho = _csv(tmp_path)
    saidas = []
    n = avaliar(caminho, carregar_casos(), _entradas("3", "ok", "2", "", "1", "", "0", "errou"),
                saidas.append)
    assert n == 4
    linhas = ler_resultados(caminho)
    assert validar_notas(linhas) == []
    assert any(l["observacao"] == "ok" for l in linhas)


def test_nao_revela_configuracao_na_tela(tmp_path):
    caminho = _csv(tmp_path, 1)
    saidas = []
    avaliar(caminho, carregar_casos(), _entradas("q"), saidas.append)
    texto = "\n".join(saidas)
    assert "Resposta 1 de 2" in texto and "Configuração" not in texto
    assert "configuracao" not in texto.lower().replace("configuração", "")


def test_nota_invalida_pede_de_novo_e_sair_salva_o_que_deu(tmp_path):
    caminho = _csv(tmp_path, 1)
    saidas = []
    n = avaliar(caminho, carregar_casos(), _entradas("9", "x", "2", "", "q"), saidas.append)
    assert n == 1
    assert any("inteiro" in s for s in saidas)
    assert sum(1 for l in ler_resultados(caminho) if l["nota"] == "2") == 1


def test_retoma_so_o_que_falta(tmp_path):
    caminho = _csv(tmp_path)
    avaliar(caminho, carregar_casos(), _entradas("3", "", "q"), lambda *_: None)
    saidas = []
    n = avaliar(caminho, carregar_casos(), _entradas("1", "", "1", "", "1", ""), saidas.append)
    assert n == 3 and validar_notas(ler_resultados(caminho)) == []


def test_sem_pendencias(tmp_path, capsys):
    caminho = _csv(tmp_path, 1)
    avaliar(caminho, carregar_casos(), _entradas("1", "", "1", ""), lambda *_: None)
    saidas = []
    assert avaliar(caminho, carregar_casos(), _entradas(), saidas.append) == 0
    assert "Nada a avaliar" in saidas[0]


def test_arquivo_bloqueado_da_erro_claro(tmp_path, monkeypatch):
    import builtins
    from comparacao import ErroComparacao
    caminho = _csv(tmp_path, 1)
    real = builtins.open

    def bloqueado(arquivo, modo="r", *a, **k):
        if "w" in modo:
            raise PermissionError(13, "Permission denied")
        return real(arquivo, modo, *a, **k)

    monkeypatch.setattr(builtins, "open", bloqueado)
    with pytest.raises(ErroComparacao, match="aberto no Excel"):
        avaliar(caminho, carregar_casos(), _entradas("3", ""), lambda *_: None)
