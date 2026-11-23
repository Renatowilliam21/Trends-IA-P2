# Relatório de execução

Projeto P2: recomendação fundamentada de configuração. Este relatório é atualizado a cada nível.
Os números do nível Básico vêm da execução real registrada em `resultados/` e da avaliação
manual do autor.

## 1. Domínio e tarefa

Perguntas de estudantes sobre o Regulamento da Organização Didática (ROD) do IFCE (Resolução
Consup nº 35/2015). Oito casos em `dominio/casos.toml`: seis com resposta no ROD e dois cuja
resposta não existe no documento (C07 e C08). Detalhes em `docs/dominio.md`.

## 2. Configurações comparadas

| Config | Modelo | O que muda | Estado |
| --- | --- | --- | --- |
| A | modelo de `configuracoes.toml` | linha de base, texto livre | ativa |
| B | mesmo modelo | só o formato de saída (JSON por instrução textual) | ativa |
| C | mesmo modelo | só `reasoning_effort = low` | desligada |

## 3. Critérios e condições

- Escala de 0 a 3 definida em `docs/criterios.md` antes da execução, aplicada manualmente.
- Condição sem RAG: o prompt contém só instruções e pergunta. Um teste automatizado garante que
  respostas esperadas e referências não chegam ao prompt.
- Latência medida por chamada; consumo em tokens (ou número de chamadas, se a API não informar),
  registrado em coluna própria.

## 4. Execução

- Arquivo de resultados: `resultados/execucao_20261122-212549.csv` (cópia fiel em `.jsonl`).
- Data: 22/11/2026, 21:25 (fuso -03:00).
- Modelo: `gpt-5.6-terra`, parâmetros `max_tokens = 2048` em A e B.
- Repetições: 1 por caso e configuração (8 casos x 2 configurações = 16 chamadas).
- Chamadas com erro: 0 de 16.
- Avaliação: nota manual de 0 a 3, dada com o comando `avaliar` (respostas embaralhadas e sem o
  nome da configuração, o que reduz o viés, embora o JSON da B ainda possa denunciá-la).
- Comparação completa: `resultados/comparacao.md`.

## 5. Resultados

Linha de base: A.

| Configuração | Execuções | Erros | Nota média | Latência média (s) | Tokens médios | Formato válido | Ausentes reconhecidos |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 8 | 0 | 1,625 | 2,231 | 231,0 | 100% | 2 de 2 |
| B | 8 | 0 | 1,375 | 2,390 | 405,6 | 100% | 2 de 2 |

| Caso | Nota A | Nota B | B vs A | Latência A / B (s) |
| --- | --- | --- | --- | --- |
| C01 | 2 | 3 | melhorou | 2,075 / 1,345 |
| C02 | 1 | 1 | igual | 2,320 / 5,856 |
| C03 | 1 | 0 | piorou | 2,370 / 1,701 |
| C04 | 3 | 3 | igual | 1,973 / 3,723 |
| C05 | 1 | 0 | piorou | 2,625 / 1,977 |
| C06 | 2 | 0 | piorou | 2,346 / 1,720 |
| C07 | 0 | 1 | melhorou | 1,740 / 1,361 |
| C08 | 3 | 3 | igual | 2,400 / 1,440 |

Balanço de B contra A: 2 casos melhoraram, 3 ficaram iguais e 3 pioraram.

Observações:

- B consumiu cerca de 76% mais tokens que A (405,6 contra 231,0 em média), efeito esperado das
  chaves e campos do JSON.
- A latência média foi parecida. O caso C02 em B (5,856 s) pesa na média e é uma única medida.
- O indicador automático marcou os dois casos ausentes como reconhecidos em A, mas o C07 em A
  recebeu nota 0. O indicador é uma checagem textual simples e não substitui a nota.

## 6. Evolução por nível

### Básico

Conclusão provisória: com 8 casos e uma repetição por configuração, a linha de base (A, texto
livre) obteve nota média 1,625 e a configuração B (JSON por instrução textual) 1,375. B melhorou
2 casos e piorou 3, com consumo cerca de 76% maior em tokens e latência semelhante. A diferença
de qualidade é pequena demais para sustentar uma preferência firme. Provisoriamente, recomendo
manter A para esta tarefa, pois B não trouxe ganho de qualidade e custa mais tokens. O benefício
esperado de B, a saída estruturada para processamento automático, não foi medido neste nível.
A nota média abaixo de 2 nas duas configurações indica que, sem RAG, o modelo erra ou omite
dados do regulamento, o que justifica testar recuperação de contexto nas etapas seguintes.

O que ainda não dá para afirmar: se a diferença entre A e B se mantém com repetições, com mais
casos ou com outro modelo, e se a configuração C (esforço de raciocínio baixo) muda o quadro.

### Intermediário

Estado: referência construída e testada com API simulada. **A execução real, as notas e a
conclusão abaixo dependem da rodada do autor e não foram preenchidas com valores inventados.**

O que mudou do Básico (detalhes e motivos em `docs/alteracoes.md`):

- 14 casos (8 do Básico mantidos e 6 novos) cobrindo as categorias direta, combinada, ambígua,
  ausente, fora de escopo e indutora;
- configurações A e B do Básico mantidas, mais a D (instrução de conferência de dados e
  cálculos), que testa a hipótese de que a conferência melhora casos de cálculo e de premissa
  falsa; a C segue desligada;
- fluxo em três etapas, com registro de eventos, nova tentativa limitada e encerramento
  controlado (`docs/falhas.md`).

Execução real:

- Arquivo de resultados: A preencher após a execução real.
- Data, modelo e repetições: A preencher após a execução real.
- Situação final dos casos (concluído, parcial, falha, interrompido): A preencher.

Resultados (saída do comando `comparar`): A preencher após a execução real.

| Categoria | Nota A | Nota B | Nota D |
| --- | --- | --- | --- |
| direta | A preencher | A preencher | A preencher |
| combinada | A preencher | A preencher | A preencher |
| ambigua | A preencher | A preencher | A preencher |
| ausente | A preencher | A preencher | A preencher |
| fora_escopo | A preencher | A preencher | A preencher |
| indutora | A preencher | A preencher | A preencher |

Síntese por configuração (usar todos os casos, sem selecionar os favoráveis):

| Configuração | Pontos fortes | Limitações | Melhor em | Pior em | Consumo adicional | Efeitos inesperados |
| --- | --- | --- | --- | --- | --- | --- |
| A | A preencher | A preencher | A preencher | A preencher | referência | A preencher |
| B | A preencher | A preencher | A preencher | A preencher | A preencher | A preencher |
| D | A preencher | A preencher | A preencher | A preencher | A preencher | A preencher |

Conclusão intermediária (A preencher após a execução real): qual configuração teve os
melhores resultados até agora, em quais tipos de caso, quais limitações permanecem e quais
hipóteses serão investigadas com o RAG.

Falha tratada demonstrada: `python src/assistente_p2.py demonstrar-falhas` (simulada, sem custo)
e, se ocorrer na execução real, o caso correspondente em `execucao_*.eventos.jsonl`.

Experiência com IDE agêntica (C14): ver `docs/ide-agentica.md` (a preencher pelo autor).

### Avançado

Ainda não realizado.

## 7. Limitações

Ver a seção "Limitações" do `README.md`.
