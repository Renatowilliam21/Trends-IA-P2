"""Execução do mesmo conjunto de casos em várias configurações, sem duplicar lógica."""
import csv
import json
import time
from datetime import datetime
from pathlib import Path

from cliente import chamar_modelo
from config import ParametrosFluxo
from erros import ExecucaoInterrompida
from fluxo import executar_fluxo
from registro import Registro

COLUNAS = [
    "execucao_id", "caso_id", "tipo", "categoria", "configuracao", "repeticao", "data",
    "modelo", "parametros", "versao_prompt", "situacao_final", "chamadas", "tempo_total_s",
    "latencia_s", "tokens_entrada", "tokens_saida", "tokens_total", "consumo_medida",
    "consumo_valor", "formato_valido", "motivo_formato", "recusa_detectada", "erro",
    "resposta", "nota", "observacao",
]


def agora():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def novo_id():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def executar_caso(caso, config, servico, execucao_id, repeticao=1, chamar=chamar_modelo,
                  params=None, registro=None, dormir=time.sleep, sinal=None, pergunta=None):
    """Executa UM caso em UMA configuração e devolve o registro (nunca levanta erro previsto)."""
    return executar_fluxo(caso, config, servico, execucao_id, repeticao, chamar, params,
                          registro, dormir, pergunta=pergunta, agora=agora, sinal=sinal)


def executar(casos, configs, servico, repeticoes=1, chamar=chamar_modelo, ao_terminar=None,
             params=None, registro=None, dormir=time.sleep, execucao_id=None):
    """Roda todos os casos em todas as configurações.

    A ordem intercala as configurações em cada caso (repetição, caso, configuração) para que
    oscilações de rede ou de carga do serviço afetem todas de forma parecida.

    Encerra de forma controlada (ExecucaoInterrompida, com os registros até ali) quando uma
    falha é fatal (credencial, modelo, crédito) ou quando o serviço falha em
    params.falhas_seguidas_max casos seguidos.
    """
    params = params or ParametrosFluxo()
    registro = registro if registro is not None else Registro()
    execucao_id = execucao_id or novo_id()
    registros, seguidas = [], 0
    for repeticao in range(1, repeticoes + 1):
        for caso in casos:
            for config in configs:
                sinal = {}
                linha = executar_caso(caso, config, servico, execucao_id, repeticao, chamar,
                                      params, registro, dormir, sinal)
                registros.append(linha)
                if ao_terminar:
                    ao_terminar(linha)
                motivo = None
                if sinal.get("fatal"):
                    motivo = "falha que se repetiria em todas as chamadas: " + linha["erro"]
                elif sinal.get("servico_falhou"):
                    seguidas += 1
                    if seguidas >= params.falhas_seguidas_max:
                        motivo = (f"o serviço falhou em {seguidas} casos seguidos "
                                  f"(último erro: {linha['erro']})")
                elif linha["situacao_final"] in ("concluido", "parcial"):
                    seguidas = 0
                if motivo:
                    registro.evento(execucao_id=execucao_id, etapa="execucao",
                                    evento="encerramento", resultado="erro",
                                    resumo=f"{len(registros)} caso(s) executado(s)", erro=motivo)
                    raise ExecucaoInterrompida(
                        f"Execução encerrada: {motivo}. Os {len(registros)} registro(s) até aqui "
                        "foram preservados.", registros)
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
