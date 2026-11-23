"""Linha de comando do P2: executa os casos em várias configurações e compara.

Uso:
    python src/assistente_p2.py listar
    python src/assistente_p2.py executar --dry-run
    python src/assistente_p2.py executar
    python src/assistente_p2.py comparar resultados/execucao_AAAAMMDD-HHMMSS.csv
"""
import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

from apresentacao import mostrar, mostrar_erro
from casos import ARQUIVO_PADRAO as CASOS_PADRAO
from casos import carregar_casos
from avaliacao import avaliar
from comparacao import comparar, ler_resultados, renderizar_markdown
from config import (ARQUIVO_PADRAO, RAIZ_PROJETO, Servico, carregar_configuracoes,
                    carregar_fluxo,
                    carregar_servico, escolher_configs)
from demonstracao import demonstrar
from erros import ErroAssistente, ExecucaoInterrompida
from executor import executar, novo_id, salvar
from registro import Registro
from prompts import montar_corpo

PASTA_RESULTADOS = RAIZ_PROJETO / "resultados"


def criar_analisador():
    analisador = argparse.ArgumentParser(description="P2: comparação de configurações de um LLM.")
    sub = analisador.add_subparsers(dest="comando", required=True)
    sub.add_parser("listar", help="mostra os casos e as configurações")
    ex = sub.add_parser("executar", help="roda os casos nas configurações")
    ex.add_argument("--configs", nargs="+", help="nomes das configurações (padrão: as ativas)")
    ex.add_argument("--repeticoes", type=int, default=1, help="repetições de cada caso")
    ex.add_argument("--casos", default=str(CASOS_PADRAO))
    ex.add_argument("--configuracoes", default=str(ARQUIVO_PADRAO))
    ex.add_argument("--saida", default=str(PASTA_RESULTADOS))
    ex.add_argument("--max-tentativas", type=int,
                    help="chamadas por caso em falhas transitórias (padrão: configuracoes.toml)")
    ex.add_argument("--dry-run", action="store_true",
                    help="mostra o que seria enviado, sem chamar a API e sem precisar de chave")
    de = sub.add_parser("demonstrar-falhas",
                        help="mostra o tratamento de falhas com uma API simulada (sem custo)")
    de.add_argument("--saida", default=str(PASTA_RESULTADOS))
    av = sub.add_parser("avaliar", help="pede as notas uma a uma e grava no CSV (avaliação cega)")
    av.add_argument("arquivo")
    av.add_argument("--casos", default=str(CASOS_PADRAO))
    co = sub.add_parser("comparar", help="compara as configurações a partir do CSV com notas")
    co.add_argument("arquivo")
    co.add_argument("--base", default="A", help="configuração usada como linha de base")
    co.add_argument("--saida", help="grava o Markdown da comparação neste arquivo")
    return analisador


def comando_listar(args):
    casos = carregar_casos()
    _, configs = carregar_configuracoes()
    mostrar(f"Casos ({len(casos)}):")
    for c in casos:
        mostrar(f"  {c.id} [{c.categoria or c.tipo}] {c.pergunta}")
    mostrar("\nConfigurações:")
    for c in configs.values():
        estado = "ativa" if c.ativa else "desligada"
        mostrar(f"  {c.nome} ({estado}): {c.descricao}\n      variação: {c.variacao}")


def comando_executar(args):
    if args.repeticoes < 1:
        raise ErroAssistente("--repeticoes deve ser 1 ou mais.")
    if args.max_tentativas is not None and args.max_tentativas < 1:
        raise ErroAssistente("--max-tentativas deve ser 1 ou mais.")
    casos = carregar_casos(args.casos)
    dados_servico, todas = carregar_configuracoes(args.configuracoes)
    configs = escolher_configs(todas, args.configs)

    if args.dry_run:
        servico = Servico(chave="sk-nao-usada", modelo=str(dados_servico.get("modelo", "")))
        mostrar(f"Simulação: {len(casos)} casos x {len(configs)} configurações "
                f"x {args.repeticoes} repetição(ões) = "
                f"{len(casos) * len(configs) * args.repeticoes} chamadas. Nada foi enviado.\n")
        for config in configs:
            corpo = montar_corpo(casos[0], config, servico)
            corpo["messages"] = [dict(m) for m in corpo["messages"]]
            mostrar(f"--- Configuração {config.nome}: requisição para o caso {casos[0].id} ---")
            mostrar(json.dumps(corpo, ensure_ascii=False, indent=2))
        return 0

    servico = carregar_servico(dados_servico)
    total = len(casos) * len(configs) * args.repeticoes
    contador = {"n": 0}

    def progresso(registro):
        contador["n"] += 1
        situacao = "ERRO" if registro["erro"] else f"{registro['latencia_s']} s"
        mostrar(f"[{contador['n']}/{total}] {registro['caso_id']} {registro['configuracao']}: {situacao}")

    params = carregar_fluxo(args.configuracoes)
    if args.max_tentativas is not None:
        params = replace(params, max_tentativas=args.max_tentativas)
    execucao_id = novo_id()
    registro = Registro(Path(args.saida) / f"execucao_{execucao_id}.eventos.jsonl")
    interrompida = None
    try:
        registros = executar(casos, configs, servico, args.repeticoes, ao_terminar=progresso,
                             params=params, registro=registro, execucao_id=execucao_id)
    except ExecucaoInterrompida as erro:
        registros, interrompida = erro.registros, erro
    caminho_csv, caminho_jsonl = salvar(registros, args.saida)
    erros = sum(1 for r in registros if r["erro"])
    mostrar(f"\nResultados: {caminho_csv}\nCópia fiel: {caminho_jsonl}\n"
            f"Eventos do fluxo: {registro.caminho}\n"
            f"Casos com erro ou interrupção: {erros} de {len(registros)}.")
    if interrompida:
        mostrar_erro(interrompida)
        mostrar("Os registros parciais foram salvos. Corrija o problema e rode de novo.")
        return 2
    mostrar("Próximo passo: rode 'avaliar' para dar as notas e depois 'comparar'.")
    return 0


def comando_demonstrar_falhas(args):
    caminho = Path(args.saida) / "demonstracao_falhas.eventos.jsonl"
    if caminho.exists():
        caminho.unlink()
    demonstrar(caminho, carregar_fluxo())
    mostrar(f"\nEventos gravados em {caminho}")
    return 0


def comando_comparar(args):
    resultado = comparar(ler_resultados(args.arquivo), args.base)
    texto = renderizar_markdown(resultado)
    mostrar(texto)
    if args.saida:
        Path(args.saida).write_text(texto, encoding="utf-8")
        mostrar(f"Comparação gravada em {args.saida}")
    return 0


def comando_avaliar(args):
    casos = carregar_casos(args.casos)
    avaliar(args.arquivo, casos)
    return 0


COMANDOS = {"listar": comando_listar, "executar": comando_executar,
            "demonstrar-falhas": comando_demonstrar_falhas,
            "avaliar": comando_avaliar, "comparar": comando_comparar}


def main(argv=None):
    args = criar_analisador().parse_args(argv)
    try:
        return COMANDOS[args.comando](args) or 0
    except ErroAssistente as erro:
        mostrar_erro(erro)
        return 1


if __name__ == "__main__":
    sys.exit(main())
