# Falhas previstas e tratamento

Cada etapa do fluxo (`src/fluxo.py`) trata as suas falhas, registra o ocorrido em
`execucao_*.eventos.jsonl` e termina o caso com uma situação final clara. Nada fica em laço:
as novas tentativas têm limite (`max_tentativas`, padrão 3) e a execução inteira encerra de
forma controlada quando insistir não adianta.

| Situação | Etapa | O que o fluxo faz | Situação final |
| --- | --- | --- | --- |
| Pergunta vazia ou longa demais | 1 | recusa antes de chamar o modelo | `interrompido` |
| Credencial ausente ou mal formada | antes do fluxo | mensagem clara e saída com erro, sem chamada | (não inicia) |
| Credencial inválida, modelo inexistente, sem crédito | 2 | sem nova tentativa; encerra a execução e salva os registros | `falha`, execução encerrada |
| Timeout, limite de uso, conexão ou erro 5xx | 2 | até 3 tentativas, esperas de 1 s, 2 s e 4 s | `concluido` se recuperar, senão `falha` |
| Serviço fora do ar | 2 | após 3 casos seguidos com falha do serviço, encerra e salva os registros | `falha`, execução encerrada |
| Resposta vazia ou em formato inesperado da API | 2 | registra o erro, sem nova tentativa | `falha` |
| JSON fora do contrato (configuração B) | 3 | valida, registra o desvio e aproveita o texto | `parcial` |
| Configuração, casos ou prompt inválidos | antes do fluxo | mensagem clara e saída com erro | (não inicia) |

O código de saída de `executar` é 0 (tudo certo), 1 (erro de uso ou de configuração) ou 2
(execução encerrada de forma controlada, com resultados parciais salvos).

## Demonstração

`python src/assistente_p2.py demonstrar-falhas` roda o fluxo real contra uma API simulada que
falha de propósito. Não usa rede nem credencial. Resultado de uma execução (simulada):

| Cenário | Situação final | Chamadas |
| --- | --- | --- |
| Entrada vazia | interrompido | 0 |
| Timeout que se recupera na 2ª tentativa | concluido | 2 |
| Timeout persistente (limite de tentativas) | falha | 3 |
| Credencial inválida (não repete) | falha | 1 |
| Resposta vazia do serviço | falha | 1 |
| JSON fora do formato (configuração B) | parcial | 1 |
| JSON correto (configuração B) | concluido | 1 |
| Serviço indisponível | encerrado após 3 casos | 3 |

Os eventos ficam em `resultados/demonstracao_falhas.eventos.jsonl`. Esses cenários são
simulados e provam o tratamento. A execução real, com a API verdadeira, está no relatório.

## Como investigar uma falha

1. Abra o CSV da execução e filtre `situacao_final` diferente de `concluido`.
2. Procure o mesmo `caso_id` e `configuracao` em `execucao_*.eventos.jsonl`: cada etapa mostra
   início, resultado, duração e erro.
3. A coluna `versao_prompt` diz qual instrução estava ativa; `chamadas` mostra quantas
   tentativas o caso consumiu.
