"""Avaliação manual guiada: mostra pergunta, resposta esperada e respostas do modelo.

As respostas de um mesmo caso aparecem embaralhadas e sem o nome da configuração
(avaliação cega, como pede docs/criterios.md). O formato JSON ainda pode denunciar
a configuração B; isso é uma limitação declarada.
"""
import csv
import random
from pathlib import Path

from comparacao import NOTA_MAX, NOTA_MIN, ErroComparacao, ler_resultados

ESCALA = (
    "Escala (docs/criterios.md):\n"
    "  0 ausente, sem relação ou claramente incorreta (ou inventou valor/data)\n"
    "  1 parcial, com erro importante (número ou prazo errado limita a 1)\n"
    "  2 útil, mas incompleta ou imprecisa\n"
    "  3 correta, clara e adequada (ou reconhece a ausência e orienta onde buscar)\n"
    "Digite a nota, 's' para pular, 'q' para sair (o que já foi dado fica salvo)."
)


def gravar(caminho, linhas):
    campos = list(linhas[0].keys())
    try:
        with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=campos)
            escritor.writeheader()
            escritor.writerows(linhas)
    except PermissionError:
        raise ErroComparacao(
            f"Não consegui gravar {Path(caminho).name}. Ele deve estar aberto no Excel ou em "
            "outro programa. Feche-o e rode o comando de novo; as notas já gravadas continuam.")


def _grupos(linhas):
    """Agrupa por (caso, repetição), com ordem embaralhada de forma reproduzível."""
    grupos = {}
    for linha in linhas:
        grupos.setdefault((linha["caso_id"], linha["repeticao"]), []).append(linha)
    for chave, grupo in grupos.items():
        random.Random(f"{chave[0]}-{chave[1]}").shuffle(grupo)
    return grupos


def _pedir_nota(entrada, saida):
    while True:
        texto = entrada("Nota (0-3, s, q): ").strip().lower()
        if texto in ("s", "q"):
            return texto
        try:
            valor = int(texto)
        except ValueError:
            valor = None
        if valor is not None and NOTA_MIN <= valor <= NOTA_MAX:
            return str(valor)
        saida(f"Digite um inteiro de {NOTA_MIN} a {NOTA_MAX}, 's' ou 'q'.")


def avaliar(caminho, casos, entrada=input, saida=print):
    """Pede as notas que faltam e grava o CSV a cada nota. Devolve quantas foram dadas."""
    caminho = Path(caminho)
    linhas = ler_resultados(caminho)
    if "nota" not in linhas[0] or "observacao" not in linhas[0]:
        raise ErroComparacao("O CSV não tem as colunas 'nota' e 'observacao'.")
    por_id = {c.id: c for c in casos}
    pendentes = {k: [l for l in g if not l.get("erro") and not str(l.get("nota", "")).strip()]
                 for k, g in _grupos(linhas).items()}
    pendentes = {k: g for k, g in pendentes.items() if g}
    if not pendentes:
        saida("Nada a avaliar: todas as respostas já têm nota.")
        return 0
    saida(ESCALA)
    dadas = 0
    for (caso_id, rep), grupo in pendentes.items():
        caso = por_id.get(caso_id)
        saida("\n" + "=" * 70)
        saida(f"Caso {caso_id} (repetição {rep})"
              + (f" [{caso.tipo}]" if caso else ""))
        if caso:
            saida(f"Pergunta: {caso.pergunta}\nEsperado: {caso.resposta_esperada}"
                  f"\nReferência: {caso.referencia}")
        for numero, linha in enumerate(grupo, start=1):
            saida(f"\n--- Resposta {numero} de {len(grupo)} ---\n{linha['resposta']}\n")
            nota = _pedir_nota(entrada, saida)
            if nota == "q":
                saida(f"Saindo. {dadas} nota(s) gravada(s).")
                return dadas
            if nota == "s":
                continue
            linha["nota"] = nota
            obs = entrada("Observação (opcional, Enter para pular): ").strip()
            if obs:
                linha["observacao"] = obs
            gravar(caminho, linhas)
            dadas += 1
    saida(f"\nConcluído. {dadas} nota(s) gravada(s) em {caminho}.")
    return dadas
