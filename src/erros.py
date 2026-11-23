"""Erros previstos, todos com mensagem pensada para o usuário final."""


class ErroAssistente(Exception):
    """Falha prevista. A mensagem explica o que aconteceu e o que fazer."""


class ErroConfiguracao(ErroAssistente):
    """Configuração, credencial ou arquivo de parâmetros ausente ou inválido."""


class ErroCasos(ErroAssistente):
    """Arquivo de casos de teste ausente ou inválido."""


class ErroServico(ErroAssistente):
    """Falha de comunicação, autenticação ou disponibilidade do serviço.

    transitorio: vale tentar de novo (timeout, limite de taxa, instabilidade).
    fatal: toda chamada seguinte falharia do mesmo modo (credencial, modelo, crédito).
    """

    def __init__(self, mensagem, transitorio=False, fatal=False):
        super().__init__(mensagem)
        self.transitorio = transitorio
        self.fatal = fatal


class ErroEntrada(ErroAssistente):
    """Pergunta vazia, longa demais ou inválida, detectada antes de chamar o modelo."""


class ExecucaoInterrompida(ErroAssistente):
    """A execução foi encerrada de forma controlada; os registros parciais seguem em .registros."""

    def __init__(self, mensagem, registros):
        super().__init__(mensagem)
        self.registros = registros


class ErroResposta(ErroAssistente):
    """Resposta vazia, bloqueada ou em formato inesperado."""
