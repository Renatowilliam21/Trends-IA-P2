"""Chamada ao modelo, com medição de latência e de consumo."""
import time
from dataclasses import dataclass

import requests

from erros import ErroResposta, ErroServico


@dataclass(frozen=True)
class RespostaModelo:
    texto: str
    latencia_s: float
    tokens_entrada: int | None
    tokens_saida: int | None
    tokens_total: int | None


def _detalhe_do_erro(resposta):
    try:
        erro = resposta.json().get("error", {}) or {}
        partes = [str(erro.get("code", "")), str(erro.get("type", "")),
                  str(erro.get("message", ""))]
        return " ".join(partes).lower()
    except (ValueError, AttributeError, TypeError):
        return ""


def _mensagem_curta(resposta, limite=200):
    try:
        return str(resposta.json().get("error", {}).get("message", "")).strip()[:limite]
    except (ValueError, AttributeError, TypeError):
        return ""


def _inteiro(valor):
    return valor if isinstance(valor, int) and not isinstance(valor, bool) else None


def extrair_texto_e_uso(dados):
    """Valida o formato da resposta da API e devolve (texto, entrada, saida, total)."""
    try:
        escolha = dados["choices"][0]
        mensagem = escolha["message"]
    except (KeyError, IndexError, TypeError):
        raise ErroResposta("Resposta do serviço em formato inesperado.")
    if mensagem.get("refusal"):
        raise ErroResposta("O modelo recusou-se a responder a esta pergunta.")
    texto = (mensagem.get("content") or "").strip()
    if not texto:
        if escolha.get("finish_reason") == "length":
            raise ErroResposta("A resposta foi interrompida pelo limite de tokens antes de "
                               "gerar texto. Aumente max_tokens na configuração.")
        raise ErroResposta("O serviço devolveu uma resposta vazia.")
    uso = dados.get("usage") if isinstance(dados.get("usage"), dict) else {}
    return (texto, _inteiro(uso.get("prompt_tokens")),
            _inteiro(uso.get("completion_tokens")), _inteiro(uso.get("total_tokens")))


def chamar_modelo(corpo, servico):
    """Envia a requisição e devolve a resposta com latência e tokens. Levanta ErroAssistente."""
    cabecalhos = {"Authorization": f"Bearer {servico.chave}",
                  "Content-Type": "application/json"}
    inicio = time.perf_counter()
    try:
        resposta = requests.post(servico.url, json=corpo, headers=cabecalhos,
                                 timeout=servico.timeout)
    except requests.exceptions.Timeout:
        raise ErroServico(f"O serviço não respondeu em {servico.timeout} segundos.")
    except requests.exceptions.ConnectionError:
        raise ErroServico("Sem conexão com o serviço. Verifique sua internet.")
    except requests.exceptions.RequestException:
        raise ErroServico("Falha de comunicação com o serviço.")
    latencia = time.perf_counter() - inicio

    status = resposta.status_code
    detalhe = _detalhe_do_erro(resposta)
    if status in (401, 403):
        raise ErroServico("Credencial inválida ou sem permissão. Confira OPENAI_API_KEY no .env.")
    if status == 404 or "model_not_found" in detalhe:
        raise ErroServico(f"Modelo '{corpo.get('model')}' não encontrado ou sem acesso. "
                          "Confira OPENAI_MODEL ou configuracoes.toml.")
    if status == 429 and "insufficient_quota" in detalhe:
        raise ErroServico("Sem crédito na conta da API. A assinatura do ChatGPT não inclui a "
                          "API: adicione crédito em platform.openai.com.")
    if status == 429:
        raise ErroServico("Limite de uso excedido. Aguarde e tente de novo.")
    if status >= 500:
        raise ErroServico("O serviço está indisponível no momento.")
    if status != 200:
        motivo = _mensagem_curta(resposta)
        raise ErroServico(f"Requisição recusada pelo serviço (HTTP {status})"
                          + (f": {motivo}" if motivo else "."))
    try:
        dados = resposta.json()
    except ValueError:
        raise ErroServico("Resposta do serviço em formato inesperado.")
    texto, entrada, saida, total = extrair_texto_e_uso(dados)
    return RespostaModelo(texto, latencia, entrada, saida, total)
