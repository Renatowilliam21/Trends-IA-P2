"""Apresentação de mensagens ao usuário."""
import sys


def mostrar(texto, saida=None):
    print(texto, file=saida or sys.stdout)


def mostrar_erro(erro, saida=None):
    print(f"Erro: {erro}", file=saida or sys.stderr)
