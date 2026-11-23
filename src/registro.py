"""Registro de eventos do fluxo: uma linha JSON por evento, sem segredos."""
import json
import re
from datetime import datetime
from pathlib import Path

LIMITE_TEXTO = 200
PADROES_SECRETOS = (
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{8,}"),
)


def limpar(texto):
    """Remove credenciais e corta textos longos antes de gravar."""
    texto = str(texto or "")
    for padrao in PADROES_SECRETOS:
        texto = padrao.sub("[removido]", texto)
    texto = " ".join(texto.split())
    return texto if len(texto) <= LIMITE_TEXTO else texto[:LIMITE_TEXTO] + "..."


class Registro:
    """Guarda os eventos em memória e, se houver caminho, também no arquivo (modo append).

    Nunca recebe o texto da pergunta, o prompt nem a resposta do modelo: só tamanhos,
    situações e mensagens de erro já limpas.
    """

    def __init__(self, caminho=None):
        self.eventos = []
        self.caminho = Path(caminho) if caminho else None
        if self.caminho:
            self.caminho.parent.mkdir(parents=True, exist_ok=True)

    def evento(self, **campos):
        for chave in ("erro", "resumo"):
            if chave in campos:
                campos[chave] = limpar(campos[chave])
        campos = {"data": datetime.now().astimezone().isoformat(timespec="milliseconds"),
                  **campos}
        self.eventos.append(campos)
        if self.caminho:
            with open(self.caminho, "a", encoding="utf-8") as arquivo:
                arquivo.write(json.dumps(campos, ensure_ascii=False) + "\n")
        return campos
