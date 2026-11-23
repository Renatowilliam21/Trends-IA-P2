"""Linha de comando: fluxo completo com API simulada e sem chave real."""
import csv
import json

import assistente_p2 as cli
import executor
from cliente import RespostaModelo

JSON_RESP = json.dumps({"resposta": "7,0.", "certeza": "alta",
                        "informacao_ausente": False, "fundamento": "Art. 99"})


def api_falsa(corpo, servico):
    livre = "texto corrido" in corpo["messages"][0]["content"]
    return RespostaModelo("Resposta livre." if livre else JSON_RESP, 0.5, 10, 5, 15)


def test_listar(capsys):
    assert cli.main(["listar"]) == 0
    saida = capsys.readouterr().out
    assert "Casos (14)" in saida and "A (ativa)" in saida and "D (ativa)" in saida
    assert "C (desligada)" in saida


def test_dry_run_nao_precisa_de_chave_e_nao_envia(capsys, monkeypatch):
    def proibido(*a, **k):
        raise AssertionError("não deveria chamar a API")
    monkeypatch.setattr(executor, "chamar_modelo", proibido)
    assert cli.main(["executar", "--dry-run"]) == 0
    saida = capsys.readouterr().out
    assert "42 chamadas" in saida and "Nada foi enviado" in saida
    assert "Configuração A" in saida and "Configuração B" in saida
    assert "sk-nao-usada" not in saida


def test_executar_sem_credencial(capsys):
    assert cli.main(["executar"]) == 1
    erro = capsys.readouterr().err
    assert "Credencial ausente" in erro and "Traceback" not in erro


def test_executar_e_comparar_de_ponta_a_ponta(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-teste")
    monkeypatch.setattr("config.load_dotenv", lambda: None)
    original = executor.executar_caso

    def com_api_falsa(caso, config, servico, execucao_id, repeticao=1, chamar=None, *a, **k):
        return original(caso, config, servico, execucao_id, repeticao, api_falsa, *a, **k)

    monkeypatch.setattr(executor, "executar_caso", com_api_falsa)
    assert cli.main(["executar", "--saida", str(tmp_path)]) == 0
    csv_path = next(tmp_path.glob("*.csv"))
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        linhas = list(csv.DictReader(f))
    assert len(linhas) == 42 and {l["configuracao"] for l in linhas} == {"A", "B", "D"}
    assert {l["situacao_final"] for l in linhas} <= {"concluido", "parcial"}
    assert next(tmp_path.glob("*.eventos.jsonl")).exists()

    # sem notas, a comparação recusa e explica
    capsys.readouterr()
    assert cli.main(["comparar", str(csv_path)]) == 1
    assert "nota não preenchida" in capsys.readouterr().err

    # preenchendo as notas, a comparação funciona e grava o Markdown
    for l in linhas:
        l["nota"] = "3" if l["configuracao"] == "B" else "2"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)
    destino = tmp_path / "comparacao.md"
    assert cli.main(["comparar", str(csv_path), "--saida", str(destino)]) == 0
    assert "14 caso(s) melhoraram" in destino.read_text(encoding="utf-8")


def test_configuracoes_insuficientes(capsys):
    assert cli.main(["executar", "--dry-run", "--configs", "A"]) == 1
    assert "pelo menos duas" in capsys.readouterr().err


def test_repeticoes_invalidas(capsys):
    assert cli.main(["executar", "--dry-run", "--repeticoes", "0"]) == 1
    assert "1 ou mais" in capsys.readouterr().err
