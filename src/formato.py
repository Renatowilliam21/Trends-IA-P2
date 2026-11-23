"""Validação do formato da resposta e detecção de recusa (indicadores automáticos)."""
import json
import re
from dataclasses import dataclass

CHAVES_JSON = ("resposta", "certeza", "informacao_ausente", "fundamento")
NIVEIS_CERTEZA = ("alta", "media", "baixa")
PADRAO_RECUSA = re.compile(
    r"n[ãa]o\s+(tenho|possuo|disponho\s+de)\s+informa|"
    r"n[ãa]o\s+sei|n[ãa]o\s+encontrei|n[ãa]o\s+h[áa]\s+informa|"
    r"n[ãa]o\s+consta|n[ãa]o\s+tenho\s+como|sem\s+informa[çc][õo]es?\s+suficientes?|"
    r"n[ãa]o\s+(\w+\s+){0,2}(posso|consigo)\s+(confirmar|afirmar|informar)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ResultadoFormato:
    texto: str                  # texto da resposta para avaliação (campo "resposta" no JSON)
    formato_valido: bool
    motivo: str                 # vazio quando válido; descreve o desvio quando inválido
    recusa_detectada: bool
    certeza: str | None = None
    fundamento: str | None = None


def detectar_recusa(texto):
    """Verificação textual simples: sujeita a erro, por isso não substitui a nota."""
    return bool(PADRAO_RECUSA.search(texto or ""))


def _tentar_json(texto):
    try:
        return json.loads(texto)
    except (ValueError, TypeError):
        return None


def _extrair_objeto(texto):
    """Recupera o primeiro objeto JSON dentro de texto extra ou bloco de código."""
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fim <= inicio:
        return None
    return _tentar_json(texto[inicio:fim + 1])


def _validar_objeto(obj):
    """Devolve a lista de problemas do objeto JSON (vazia se conforme o formato pedido)."""
    if not isinstance(obj, dict):
        return ["a resposta não é um objeto JSON"]
    problemas = []
    faltando = [c for c in CHAVES_JSON if c not in obj]
    if faltando:
        problemas.append("chaves ausentes: " + ", ".join(faltando))
    extras = [c for c in obj if c not in CHAVES_JSON]
    if extras:
        problemas.append("chaves não pedidas: " + ", ".join(extras))
    if "resposta" in obj and (not isinstance(obj["resposta"], str) or not obj["resposta"].strip()):
        problemas.append("'resposta' deve ser um texto não vazio")
    if "certeza" in obj and obj["certeza"] not in NIVEIS_CERTEZA:
        problemas.append("'certeza' deve ser alta, media ou baixa")
    if "informacao_ausente" in obj and not isinstance(obj["informacao_ausente"], bool):
        problemas.append("'informacao_ausente' deve ser true ou false")
    if "fundamento" in obj and obj["fundamento"] is not None \
            and not isinstance(obj["fundamento"], str):
        problemas.append("'fundamento' deve ser texto ou null")
    return problemas


def processar(formato, texto_bruto):
    """Valida a resposta conforme o formato pedido e extrai o texto para avaliação."""
    texto_bruto = (texto_bruto or "").strip()
    if formato in ("livre", "conferir"):
        return ResultadoFormato(texto_bruto, bool(texto_bruto),
                                "" if texto_bruto else "resposta vazia",
                                detectar_recusa(texto_bruto))

    # formato "json": validação estrita; desvios são registrados, e o texto é recuperado
    # quando possível para que a resposta ainda possa ser avaliada.
    obj = _tentar_json(texto_bruto)
    desvio = ""
    if obj is None:
        obj = _extrair_objeto(texto_bruto)
        if obj is None:
            return ResultadoFormato(texto_bruto, False, "resposta não é JSON",
                                    detectar_recusa(texto_bruto))
        desvio = "JSON cercado por texto ou bloco de código"
    problemas = _validar_objeto(obj)
    if not isinstance(obj, dict):
        return ResultadoFormato(texto_bruto, False, "; ".join(problemas),
                                detectar_recusa(texto_bruto))
    motivos = ([desvio] if desvio else []) + problemas
    resposta = obj.get("resposta")
    texto = resposta.strip() if isinstance(resposta, str) and resposta.strip() else texto_bruto
    ausente = obj.get("informacao_ausente")
    recusa = ausente if isinstance(ausente, bool) else detectar_recusa(texto)
    certeza = obj.get("certeza") if obj.get("certeza") in NIVEIS_CERTEZA else None
    fundamento = obj.get("fundamento") if isinstance(obj.get("fundamento"), str) else None
    return ResultadoFormato(texto, not motivos, "; ".join(motivos), bool(recusa),
                            certeza, fundamento)
