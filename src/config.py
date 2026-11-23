"""Configuração do serviço e das configurações de geração comparadas."""
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from erros import ErroConfiguracao

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
ARQUIVO_PADRAO = RAIZ_PROJETO / "configuracoes.toml"
API_URL = "https://api.openai.com/v1/chat/completions"
MODELO_PADRAO = "gpt-5.6-terra"
TIMEOUT_PADRAO = 60
FORMATOS = ("livre", "json", "conferir")
CAMPOS_ACEITOS = {"ativa", "descricao", "variacao", "formato", "max_tokens",
                  "temperature", "reasoning_effort"}


@dataclass(frozen=True)
class Servico:
    """Dados de acesso ao serviço. A chave nunca aparece no repr."""

    chave: str = field(repr=False)
    modelo: str = MODELO_PADRAO
    url: str = API_URL
    timeout: int = TIMEOUT_PADRAO


@dataclass(frozen=True)
class ConfigGeracao:
    """Uma configuração de geração a comparar."""

    nome: str
    descricao: str = ""
    variacao: str = ""
    formato: str = "livre"
    max_tokens: int = 2048
    temperature: float | None = None
    reasoning_effort: str | None = None
    ativa: bool = True

    def parametros(self):
        """Parâmetros de geração enviados (só os definidos), para registro."""
        dados = {"formato": self.formato, "max_tokens": self.max_tokens}
        if self.temperature is not None:
            dados["temperature"] = self.temperature
        if self.reasoning_effort is not None:
            dados["reasoning_effort"] = self.reasoning_effort
        return dados


def validar_chave(chave):
    """Confere a credencial localmente, sem enviá-la a ninguém."""
    chave = (chave or "").strip()
    if not chave:
        raise ErroConfiguracao(
            "Credencial ausente. Defina OPENAI_API_KEY no arquivo .env (veja .env.example)."
        )
    if any(c.isspace() for c in chave) or chave[0] in "\"'" or chave[-1] in "\"'":
        raise ErroConfiguracao(
            "A credencial em OPENAI_API_KEY contém espaços ou aspas. Cole apenas a chave."
        )
    if not chave.startswith("sk-"):
        raise ErroConfiguracao(
            "A credencial em OPENAI_API_KEY não tem o formato esperado (chaves da OpenAI "
            "começam com 'sk-'). Gere uma em platform.openai.com/api-keys."
        )
    return chave


def ler_toml(caminho):
    caminho = Path(caminho)
    try:
        with open(caminho, "rb") as arquivo:
            return tomllib.load(arquivo)
    except FileNotFoundError:
        raise ErroConfiguracao(f"Arquivo de configurações não encontrado: {caminho.name}")
    except tomllib.TOMLDecodeError as erro:
        raise ErroConfiguracao(f"{caminho.name} tem erro de sintaxe: {erro}")
    except OSError as erro:
        raise ErroConfiguracao(f"Não foi possível ler {caminho.name}: {erro.strerror}")


def _inteiro_positivo(valor, nome, onde):
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 1:
        raise ErroConfiguracao(f"{onde}: {nome} deve ser um inteiro maior que zero.")
    return valor


def montar_config_geracao(nome, bruto):
    """Valida uma tabela [configuracoes.X] e devolve a ConfigGeracao."""
    onde = f"Configuração {nome}"
    if not isinstance(bruto, dict):
        raise ErroConfiguracao(f"{onde}: formato inválido.")
    desconhecidos = set(bruto) - CAMPOS_ACEITOS
    if desconhecidos:
        raise ErroConfiguracao(
            f"{onde}: campo(s) desconhecido(s): {', '.join(sorted(desconhecidos))}."
        )
    formato = bruto.get("formato", "livre")
    if formato not in FORMATOS:
        raise ErroConfiguracao(f"{onde}: formato deve ser um de {', '.join(FORMATOS)}.")
    temperatura = bruto.get("temperature")
    if temperatura is not None:
        if isinstance(temperatura, bool) or not isinstance(temperatura, (int, float)) \
                or not 0 <= temperatura <= 2:
            raise ErroConfiguracao(f"{onde}: temperature deve estar entre 0 e 2.")
    esforco = bruto.get("reasoning_effort")
    if esforco is not None and (not isinstance(esforco, str) or not esforco.strip()):
        raise ErroConfiguracao(f"{onde}: reasoning_effort deve ser um texto.")
    return ConfigGeracao(
        nome=nome,
        descricao=str(bruto.get("descricao", "")),
        variacao=str(bruto.get("variacao", "")),
        formato=formato,
        max_tokens=_inteiro_positivo(bruto.get("max_tokens", 2048), "max_tokens", onde),
        temperature=float(temperatura) if temperatura is not None else None,
        reasoning_effort=esforco.strip() if esforco else None,
        ativa=bool(bruto.get("ativa", True)),
    )


def carregar_configuracoes(caminho=ARQUIVO_PADRAO):
    """Lê o TOML e devolve (dados do serviço sem chave, dict nome -> ConfigGeracao)."""
    bruto = ler_toml(caminho)
    tabelas = bruto.get("configuracoes")
    if not isinstance(tabelas, dict) or not tabelas:
        raise ErroConfiguracao("Nenhuma configuração encontrada em [configuracoes.*].")
    configs = {nome: montar_config_geracao(nome, t) for nome, t in tabelas.items()}
    return bruto.get("servico", {}), configs


@dataclass(frozen=True)
class ParametrosFluxo:
    """Limites do fluxo: nova tentativa, espera e encerramento controlado."""

    max_tentativas: int = 3
    espera_base_s: float = 1.0
    falhas_seguidas_max: int = 3
    max_caracteres: int = 1000


def carregar_fluxo(caminho=ARQUIVO_PADRAO):
    """Lê a tabela [fluxo] (opcional) e valida os limites."""
    dados = ler_toml(caminho).get("fluxo", {})
    if not isinstance(dados, dict):
        raise ErroConfiguracao("[fluxo] deve ser uma tabela.")
    desconhecidos = set(dados) - {"max_tentativas", "espera_base_s", "falhas_seguidas_max",
                                   "max_caracteres"}
    if desconhecidos:
        raise ErroConfiguracao(f"[fluxo]: campo(s) desconhecido(s): "
                               f"{', '.join(sorted(desconhecidos))}.")
    padrao = ParametrosFluxo()
    espera = dados.get("espera_base_s", padrao.espera_base_s)
    if isinstance(espera, bool) or not isinstance(espera, (int, float)) or espera < 0:
        raise ErroConfiguracao("[fluxo]: espera_base_s deve ser um número maior ou igual a zero.")
    return ParametrosFluxo(
        max_tentativas=_inteiro_positivo(dados.get("max_tentativas", padrao.max_tentativas),
                                         "max_tentativas", "[fluxo]"),
        espera_base_s=float(espera),
        falhas_seguidas_max=_inteiro_positivo(
            dados.get("falhas_seguidas_max", padrao.falhas_seguidas_max),
            "falhas_seguidas_max", "[fluxo]"),
        max_caracteres=_inteiro_positivo(dados.get("max_caracteres", padrao.max_caracteres),
                                         "max_caracteres", "[fluxo]"),
    )


def escolher_configs(configs, nomes=None):
    """Seleciona as configurações a executar: as pedidas, ou todas as ativas."""
    if nomes:
        faltando = [n for n in nomes if n not in configs]
        if faltando:
            raise ErroConfiguracao(
                f"Configuração inexistente: {', '.join(faltando)}. "
                f"Disponíveis: {', '.join(configs)}."
            )
        escolhidas = [configs[n] for n in nomes]
    else:
        escolhidas = [c for c in configs.values() if c.ativa]
    if len(escolhidas) < 2:
        raise ErroConfiguracao(
            "A comparação precisa de pelo menos duas configurações. "
            "Ative outra em configuracoes.toml ou use --configs A B."
        )
    return escolhidas


def carregar_servico(dados_servico, ambiente=None, carregar_dotenv=True):
    """Monta o Servico a partir do TOML, do ambiente e da credencial do .env."""
    if carregar_dotenv:
        load_dotenv()
    ambiente = os.environ if ambiente is None else ambiente
    chave = validar_chave(ambiente.get("OPENAI_API_KEY"))
    modelo = (ambiente.get("OPENAI_MODEL") or "").strip() \
        or str(dados_servico.get("modelo") or MODELO_PADRAO)
    bruto_timeout = (ambiente.get("OPENAI_TIMEOUT") or "").strip() \
        or dados_servico.get("timeout_segundos") or TIMEOUT_PADRAO
    try:
        timeout = int(bruto_timeout)
    except (TypeError, ValueError):
        raise ErroConfiguracao("OPENAI_TIMEOUT deve ser um número inteiro de segundos.")
    if timeout < 1:
        raise ErroConfiguracao("OPENAI_TIMEOUT deve ser maior que zero.")
    return Servico(chave=chave, modelo=modelo, timeout=timeout)
