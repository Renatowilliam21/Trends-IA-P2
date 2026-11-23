"""Montagem do prompt. Condição SEM RAG: só instruções e a pergunta, nunca o corpus."""
import hashlib
from pathlib import Path

from config import RAIZ_PROJETO
from erros import ErroConfiguracao

PASTA = RAIZ_PROJETO / "prompts"


def _ler(nome, pasta=None):
    caminho = Path(pasta or PASTA) / nome
    try:
        return caminho.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        raise ErroConfiguracao(f"Arquivo de prompt não encontrado: {nome}")
    except (OSError, UnicodeDecodeError):
        raise ErroConfiguracao(f"Não foi possível ler o prompt {nome} (use UTF-8).")


def instrucoes(config, pasta=None):
    """Instruções do sistema: base comum + instrução de formato da configuração."""
    base = _ler("base.txt", pasta)
    formato = _ler(f"formato_{config.formato}.txt", pasta)
    return f"{base}\n\n{formato}"


def montar_mensagens(caso, config, pasta=None):
    """Mensagens enviadas ao modelo: instruções e pergunta. Sem trechos do ROD."""
    return [
        {"role": "system", "content": instrucoes(config, pasta)},
        {"role": "user", "content": caso.pergunta},
    ]


def montar_corpo(caso, config, servico, pasta=None):
    """Corpo JSON da requisição, com os parâmetros de geração da configuração."""
    corpo = {
        "model": servico.modelo,
        "max_completion_tokens": config.max_tokens,
        "messages": montar_mensagens(caso, config, pasta),
    }
    # Opcionais só vão quando definidos: alguns modelos recusam valores fora do padrão.
    if config.temperature is not None:
        corpo["temperature"] = config.temperature
    if config.reasoning_effort is not None:
        corpo["reasoning_effort"] = config.reasoning_effort
    return corpo


def versao_prompt(config, pasta=None):
    """Identificador curto (hash) das instruções efetivas, para registrar qual prompt rodou."""
    return hashlib.sha256(instrucoes(config, pasta).encode("utf-8")).hexdigest()[:8]
