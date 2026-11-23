"""Demonstração de falhas tratadas de forma controlada, sem rede e sem custo.

Roda o fluxo real com uma API simulada que falha de propósito e mostra o que o fluxo fez em
cada situação. Serve de evidência para a entrega e para quem for investigar o fluxo.
"""
import json

from casos import Caso
from cliente import RespostaModelo
from config import ParametrosFluxo, Servico, carregar_configuracoes
from erros import ErroResposta, ErroServico, ExecucaoInterrompida
from executor import executar, executar_caso
from registro import Registro

CASO = Caso("DEMO", "resposta", "Qual a média mínima para aprovação direta na graduação?",
            "7,0", "Art. 99, II", "direta")
JSON_OK = json.dumps({"resposta": "7,0.", "certeza": "alta", "informacao_ausente": False,
                      "fundamento": "Art. 99"})


def _ok(texto="Resposta de demonstração."):
    return lambda corpo, servico: RespostaModelo(texto, 0.4, 20, 8, 28)


def _sequencia(*itens):
    """API simulada que devolve, em ordem, erros (instâncias) ou respostas (callables)."""
    restantes = list(itens)

    def chamar(corpo, servico):
        item = restantes.pop(0) if len(restantes) > 1 else restantes[0]
        if isinstance(item, Exception):
            raise item
        return item(corpo, servico)
    return chamar


def _cenarios():
    timeout = ErroServico("O serviço não respondeu em 60 segundos.", transitorio=True)
    return [
        ("Entrada vazia", "A", dict(pergunta="   "), _ok()),
        ("Timeout que se recupera na 2ª tentativa", "A", {},
         _sequencia(timeout, _ok())),
        ("Timeout persistente (limite de tentativas)", "A", {}, _sequencia(timeout)),
        ("Credencial inválida (não repete)", "A", {},
         _sequencia(ErroServico("Credencial inválida ou sem permissão.", fatal=True))),
        ("Resposta vazia do serviço", "A", {},
         _sequencia(ErroResposta("O serviço devolveu uma resposta vazia."))),
        ("JSON fora do formato (configuração B)", "B", {}, _ok("Resposta sem JSON.")),
        ("JSON correto (configuração B)", "B", {}, _ok(JSON_OK)),
    ]


def demonstrar(registro_caminho=None, params=None, mostrar=print):
    """Executa os cenários e devolve a lista de resultados (nome, situação, chamadas, erro)."""
    params = params or ParametrosFluxo()
    _, configs = carregar_configuracoes()
    registro = Registro(registro_caminho)
    servico = Servico(chave="sk-nao-usada")
    sem_espera = lambda segundos: None
    resultados = []
    for nome, cfg, extra, api in _cenarios():
        linha = executar_caso(CASO, configs[cfg], servico, "demo", 1, api, params, registro,
                              sem_espera) if not extra else _com_pergunta(
            extra["pergunta"], configs[cfg], servico, api, params, registro, sem_espera)
        resultados.append((nome, linha["situacao_final"], linha["chamadas"], linha["erro"]))

    # Serviço fora do ar: o executor encerra após as falhas seguidas, sem insistir.
    indisponivel = ErroServico("O serviço está indisponível no momento.", transitorio=True)
    casos = [Caso(f"D{i}", "resposta", "Pergunta de demonstração?", "x", "x", "direta")
             for i in range(1, 6)]
    try:
        executar(casos, [configs["A"], configs["B"]], servico, chamar=_sequencia(indisponivel),
                 params=params, registro=registro, dormir=sem_espera, execucao_id="demo")
        resultados.append(("Serviço indisponível", "NÃO ENCERROU", 0, ""))
    except ExecucaoInterrompida as erro:
        resultados.append((f"Serviço indisponível (encerra após {params.falhas_seguidas_max} "
                           "casos)", "encerrado", len(erro.registros), str(erro)))

    mostrar("| Cenário | Situação final | Chamadas | Erro registrado |")
    mostrar("| --- | --- | --- | --- |")
    for nome, situacao, chamadas, erro in resultados:
        mostrar(f"| {nome} | {situacao} | {chamadas} | {erro or '-'} |")
    return resultados


def _com_pergunta(pergunta, config, servico, api, params, registro, dormir):
    from fluxo import executar_fluxo
    return executar_fluxo(CASO, config, servico, "demo", 1, api, params, registro, dormir,
                          pergunta=pergunta)
