"""Casos de teste: perguntas, respostas esperadas e tipo (resposta ou ausente)."""
import tomllib
from dataclasses import dataclass
from pathlib import Path

from config import RAIZ_PROJETO
from erros import ErroCasos

ARQUIVO_PADRAO = RAIZ_PROJETO / "dominio" / "casos.toml"
TIPOS = ("resposta", "ausente")
MINIMO_DE_CASOS = 6


@dataclass(frozen=True)
class Caso:
    id: str
    tipo: str
    pergunta: str
    resposta_esperada: str
    referencia: str


def carregar_casos(caminho=ARQUIVO_PADRAO):
    caminho = Path(caminho)
    try:
        with open(caminho, "rb") as arquivo:
            bruto = tomllib.load(arquivo)
    except FileNotFoundError:
        raise ErroCasos(f"Arquivo de casos não encontrado: {caminho.name}")
    except tomllib.TOMLDecodeError as erro:
        raise ErroCasos(f"{caminho.name} tem erro de sintaxe: {erro}")
    except OSError as erro:
        raise ErroCasos(f"Não foi possível ler {caminho.name}: {erro.strerror}")

    itens = bruto.get("caso")
    if not isinstance(itens, list) or not itens:
        raise ErroCasos("Nenhum caso encontrado: use tabelas [[caso]].")

    casos, vistos = [], set()
    for posicao, item in enumerate(itens, start=1):
        for campo in ("id", "tipo", "pergunta", "resposta_esperada", "referencia"):
            valor = item.get(campo) if isinstance(item, dict) else None
            if not isinstance(valor, str) or not valor.strip():
                raise ErroCasos(f"Caso nº {posicao}: o campo '{campo}' é obrigatório.")
        if item["tipo"] not in TIPOS:
            raise ErroCasos(f"Caso {item['id']}: tipo deve ser 'resposta' ou 'ausente'.")
        if item["id"] in vistos:
            raise ErroCasos(f"Identificador de caso repetido: {item['id']}.")
        vistos.add(item["id"])
        casos.append(Caso(item["id"], item["tipo"], item["pergunta"].strip(),
                          item["resposta_esperada"].strip(), item["referencia"].strip()))

    if len(casos) < MINIMO_DE_CASOS:
        raise ErroCasos(
            f"São necessários pelo menos {MINIMO_DE_CASOS} casos (encontrados: {len(casos)})."
        )
    if not any(c.tipo == "ausente" for c in casos):
        raise ErroCasos("Inclua pelo menos um caso do tipo 'ausente' (informação não existente).")
    return casos
