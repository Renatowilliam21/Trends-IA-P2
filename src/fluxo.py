"""Fluxo rastreável de um caso em uma configuração, em três etapas.

1. preparar_pergunta : valida e normaliza a pergunta (entrada: texto; saída: texto limpo).
2. consultar_modelo  : chama o LLM, com nova tentativa limitada para falhas transitórias
                       (entrada: pergunta limpa e configuração; saída: resposta e consumo).
3. organizar_resposta: valida o formato e extrai o texto a avaliar (saída: texto e indicadores).

Cada etapa registra início, resultado, duração e erro. A situação final do caso é uma de:
concluido, parcial (formato fora do esperado, mas resposta aproveitada), falha (a etapa de
consulta ou de organização não produziu resposta) e interrompido (pergunta inválida, o
modelo nem foi chamado).
"""
import json
import time
from dataclasses import replace

from cliente import chamar_modelo
from config import ParametrosFluxo
from erros import ErroAssistente, ErroEntrada, ErroServico
from formato import processar
from prompts import montar_corpo, versao_prompt
from registro import Registro, limpar

ESPERA_MAXIMA_S = 8.0


def preparar_pergunta(pergunta, max_caracteres):
    """Etapa 1. Remove espaços repetidos e recusa entrada vazia ou longa demais."""
    texto = " ".join((pergunta or "").split())
    if not texto:
        raise ErroEntrada("A pergunta está vazia.")
    if len(texto) > max_caracteres:
        raise ErroEntrada(f"A pergunta tem {len(texto)} caracteres; o máximo é {max_caracteres}.")
    return texto


def consultar_modelo(corpo, servico, params, chamar, dormir, ao_tentar):
    """Etapa 2. Devolve (resposta, tentativas). Repete só falhas transitórias, no máximo
    params.max_tentativas vezes, com espera crescente. Levanta o último erro se esgotar."""
    ultimo = None
    for tentativa in range(1, params.max_tentativas + 1):
        try:
            resposta = chamar(corpo, servico)
        except ErroServico as erro:
            ao_tentar(tentativa, erro)
            ultimo = (erro, tentativa)
            if not erro.transitorio or tentativa == params.max_tentativas:
                break
            dormir(min(params.espera_base_s * 2 ** (tentativa - 1), ESPERA_MAXIMA_S))
        except ErroAssistente as erro:
            ao_tentar(tentativa, erro)
            ultimo = (erro, tentativa)
            break
        else:
            ao_tentar(tentativa, None)
            return resposta, tentativa
    erro, tentativas = ultimo
    erro.tentativas = tentativas
    raise erro


def _etapa(registro, contexto, nome, funcao, resumir=None):
    registro.evento(**contexto, etapa=nome, evento="inicio")
    inicio = time.perf_counter()
    try:
        resultado = funcao()
    except ErroAssistente as erro:
        registro.evento(**contexto, etapa=nome, evento="fim", resultado="erro",
                        duracao_s=round(time.perf_counter() - inicio, 3),
                        erro=f"{type(erro).__name__}: {erro}")
        raise
    registro.evento(**contexto, etapa=nome, evento="fim", resultado="ok",
                    duracao_s=round(time.perf_counter() - inicio, 3),
                    resumo=resumir(resultado) if resumir else "")
    return resultado


def executar_fluxo(caso, config, servico, execucao_id, repeticao=1, chamar=chamar_modelo,
                   params=None, registro=None, dormir=time.sleep, pergunta=None,
                   agora=None, sinal=None):
    """Roda as três etapas e devolve o registro do caso (nunca levanta erro previsto).

    `pergunta` permite substituir o texto do caso (usado na demonstração de entrada vazia).
    `agora` é uma função que devolve a data em texto, para o registro.
    `sinal` (dict opcional) recebe 'servico_falhou' e 'fatal' quando a consulta falha, para o
    executor decidir se encerra a execução.
    """
    params = params or ParametrosFluxo()
    registro = registro if registro is not None else Registro()
    inicio_total = time.perf_counter()
    linha = {
        "execucao_id": execucao_id, "caso_id": caso.id, "tipo": caso.tipo,
        "categoria": getattr(caso, "categoria", ""), "configuracao": config.nome,
        "repeticao": repeticao, "data": agora() if agora else "", "modelo": servico.modelo,
        "parametros": json.dumps(config.parametros(), ensure_ascii=False, sort_keys=True),
        "versao_prompt": versao_prompt(config), "situacao_final": "", "chamadas": 0,
        "tempo_total_s": "", "latencia_s": "", "tokens_entrada": "", "tokens_saida": "",
        "tokens_total": "", "consumo_medida": "chamadas", "consumo_valor": 0,
        "formato_valido": "", "motivo_formato": "", "recusa_detectada": "",
        "erro": "", "resposta": "", "nota": "", "observacao": "",
    }
    contexto = {"execucao_id": execucao_id, "caso_id": caso.id, "categoria": linha["categoria"],
                "configuracao": config.nome, "repeticao": repeticao,
                "versao_prompt": linha["versao_prompt"]}
    situacao, erro_final = "concluido", None

    def terminar():
        linha["situacao_final"] = situacao
        linha["tempo_total_s"] = round(time.perf_counter() - inicio_total, 3)
        if erro_final is not None:
            linha["erro"] = limpar(f"{type(erro_final).__name__}: {erro_final}")
        if linha["consumo_medida"] == "chamadas":
            linha["consumo_valor"] = linha["chamadas"]
        registro.evento(**contexto, etapa="caso", evento="fim", situacao_final=situacao,
                        duracao_s=linha["tempo_total_s"], chamadas=linha["chamadas"],
                        tokens_total=linha["tokens_total"],
                        erro=linha["erro"], resultado="ok" if situacao in
                        ("concluido", "parcial") else "erro")
        return linha

    # Etapa 1
    try:
        texto = _etapa(registro, contexto, "preparar_pergunta",
                       lambda: preparar_pergunta(pergunta if pergunta is not None
                                                 else caso.pergunta, params.max_caracteres),
                       lambda t: f"{len(t)} caracteres")
    except ErroEntrada as erro:
        situacao, erro_final = "interrompido", erro
        return terminar()

    # Etapa 2
    corpo = montar_corpo(replace(caso, pergunta=texto), config, servico)
    tentativas = {"n": 0}

    def ao_tentar(numero, erro):
        tentativas["n"] = numero
        linha["chamadas"] = numero
        registro.evento(**contexto, etapa="consultar_modelo", evento="tentativa",
                        tentativa=numero, resultado="erro" if erro else "ok",
                        erro=f"{type(erro).__name__}: {erro}" if erro else "")

    try:
        resposta, _ = _etapa(
            registro, contexto, "consultar_modelo",
            lambda: consultar_modelo(corpo, servico, params, chamar, dormir, ao_tentar),
            lambda r: f"tentativas={tentativas['n']}, tokens={r[0].tokens_total}")
    except ErroAssistente as erro:
        situacao, erro_final = "falha", erro
        linha["chamadas"] = getattr(erro, "tentativas", tentativas["n"]) or tentativas["n"]
        if sinal is not None:
            sinal["servico_falhou"] = isinstance(erro, ErroServico)
            sinal["fatal"] = bool(getattr(erro, "fatal", False))
        return terminar()
    linha.update({
        "latencia_s": round(resposta.latencia_s, 3),
        "tokens_entrada": _vazio(resposta.tokens_entrada),
        "tokens_saida": _vazio(resposta.tokens_saida),
        "tokens_total": _vazio(resposta.tokens_total),
    })
    if resposta.tokens_total is not None:
        linha["consumo_medida"], linha["consumo_valor"] = "tokens", resposta.tokens_total

    # Etapa 3
    try:
        resultado = _etapa(registro, contexto, "organizar_resposta",
                           lambda: processar(config.formato, resposta.texto),
                           lambda r: f"formato_valido={r.formato_valido}, "
                                     f"recusa={r.recusa_detectada}, {len(r.texto)} caracteres")
    except ErroAssistente as erro:
        situacao, erro_final = "falha", erro
        return terminar()
    linha.update({"formato_valido": resultado.formato_valido,
                  "motivo_formato": resultado.motivo,
                  "recusa_detectada": resultado.recusa_detectada,
                  "resposta": resultado.texto})
    if not resultado.formato_valido:
        situacao = "parcial"
    return terminar()


def _vazio(valor):
    return "" if valor is None else valor
