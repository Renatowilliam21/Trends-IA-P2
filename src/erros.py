"""Erros previstos, todos com mensagem pensada para o usuário final."""


class ErroAssistente(Exception):
    """Falha prevista. A mensagem explica o que aconteceu e o que fazer."""


class ErroConfiguracao(ErroAssistente):
    """Configuração, credencial ou arquivo de parâmetros ausente ou inválido."""


class ErroCasos(ErroAssistente):
    """Arquivo de casos de teste ausente ou inválido."""


class ErroServico(ErroAssistente):
    """Falha de comunicação, autenticação ou disponibilidade do serviço."""


class ErroResposta(ErroAssistente):
    """Resposta vazia, bloqueada ou em formato inesperado."""
