"""Execução do mesmo conjunto de casos em várias configurações, sem duplicar lógica."""
import csv
import json
from datetime import datetime
from pathlib import Path

from cliente import chamar_modelo
from erros import ErroAssistente
from formato import processar
from prompts import montar_corpo

COLUNAS = [
    "execucao_id", "caso_id", "tipo", "configuracao", "repeticao", "data", "modelo",
    "parametros", "latencia_s", "tokens_entrada", "tokens_saida", "tokens_total",
    "consumo_medida", "consumo_valor", "formato_valido", "motivo_formato",
    "recusa_detectada", "erro", "resposta", "nota", "observacao",
]


def agora():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def executar_caso(caso, config, servico, execucao_id, repeticao=1, chamar=chamar_modelo):
    """Executa UM caso em UMA configuração e devolve o registro (nunca levanta erro previsto)."""
    registro = {
        "execucao_id": execucao_id, "caso_id": caso.id, "tipo": caso.tipo,
        "configuracao": config.nome, "repeticao": repeticao, "data": agora(),
        "modelo": servico.modelo,
        "parametros": json.dumps(config.parametros(), ensure_ascii=False, sort_keys=True),
        "latencia_s": "", "tokens_entrada": "", "tokens_saida": "", "tokens_total": "",
        "consumo_medida": "chamadas", "consumo_valor": 1,
        "formato_valido": "", "motivo_formato": "", "recusa_detectada": "",
        "erro": "", "resposta": "", "nota": "", "observacao": "",
    }
    corpo = montar_corpo(caso, config, servico)
    try:
        resposta = chamar(corpo, servico)
    except ErroAssistente as erro:
        registro["erro"] = f"{type(erro).__name__}: {erro}"
        return registro

    resultado = processar(config.formato, resposta.texto)
    registro.update({
        "latencia_s": round(resposta.latencia_s, 3),
        "tokens_entrada": _vazio(resposta.tokens_entrada),
        "tokens_saida": _vazio(resposta.tokens_saida),
        "tokens_total": _vazio(resposta.tokens_total),
        "formato_valido": resultado.formato_valido,
        "motivo_formato": resultado.motivo,
        "recusa_detectada": resultado.recusa_detectada,
        "resposta": resultado.texto,
    })
    if resposta.tokens_total is not None:
        registro["consumo_medida"], registro["consumo_valor"] = "tokens", resposta.tokens_total
    return registro


def _vazio(valor):
    return "" if valor is None else valor


def executar(casos, configs, servico, repeticoes=1, chamar=chamar_modelo, ao_terminar=None):
    """Roda todos os casos em todas as configurações.

    A ordem intercala as configurações em cada caso (repetição, caso, configuração) para que
    oscilações de rede ou de carga do serviço afetem todas de forma parecida.
    """
    execucao_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    registros = []
    for repeticao in range(1, repeticoes + 1):
        for caso in casos:
            for config in configs:
                registro = executar_caso(caso, config, servico, execucao_id, repeticao, chamar)
                registros.append(registro)
                if ao_terminar:
                    ao_terminar(registro)
    return registros


def salvar(registros, pasta):
    """Grava CSV (para preencher a nota) e JSONL (cópia fiel). Devolve os dois caminhos."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    base = f"execucao_{registros[0]['execucao_id']}"
    caminho_csv, caminho_jsonl = pasta / f"{base}.csv", pasta / f"{base}.jsonl"
    with open(caminho_csv, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(registros)
    with open(caminho_jsonl, "w", encoding="utf-8") as arquivo:
        for r in registros:
            arquivo.write(json.dumps(r, ensure_ascii=False) + "\n")
    return caminho_csv, caminho_jsonl
