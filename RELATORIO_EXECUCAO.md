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

O que mudou do Básico (detalhes e motivos em `docs/alteracoes.md`):

- 14 casos (8 do Básico mantidos e 6 novos) cobrindo as categorias direta, combinada, ambígua,
  ausente, fora de escopo e indutora;
- configurações A e B do Básico mantidas, mais a D (instrução de conferência de dados e
  cálculos), que testa a hipótese de que a conferência melhora casos de cálculo e de premissa
  falsa; a C segue desligada;
- fluxo em três etapas, com registro de eventos, nova tentativa limitada e encerramento
  controlado (`docs/falhas.md`).

Execução real:

- Arquivo de resultados: `resultados/execucao_20261122-222316.csv`, com os eventos em
  `execucao_20261122-222316.eventos.jsonl` e a comparação em `comparacao_intermediario.md`.
- Data: 22/11/2026, cerca das 22:23. Modelo: o registrado na coluna `modelo` do CSV
  (`gpt-5.6-terra` no Básico). Repetições: 1 por caso e configuração (14 x 3 = 42 chamadas).
- Situação final: 42 casos `concluido` (14 em cada configuração). Não houve falha de API,
  desvio de formato nem nova tentativa, então a execução real **não gerou falha para tratar**.
  O tratamento de falhas está demonstrado com a API simulada (`demonstrar-falhas`, `docs/falhas.md`).
- Avaliação: nota manual de 0 a 3, pelo comando `avaliar` (cega quanto à configuração).

Resumo por configuração:

| Configuração | Nota média | Latência média (s) | Tokens médios | Formato válido | Ausentes reconhecidos |
| --- | --- | --- | --- | --- | --- |
| A | 1,929 | 2,463 | 252,2 | 100% | 3 de 3 |
| B | 1,714 | 2,609 | 409,1 | 100% | 3 de 3 |
| D | 2,571 | 2,973 | 338,7 | 100% | 3 de 3 |

Balanço contra a linha de base (A): B melhorou 2 casos, empatou 9 e piorou 3. D melhorou 5,
empatou 8 e piorou 1. Em consumo, B usou cerca de 62% mais tokens que A e D cerca de 34% mais.
A latência de D ficou cerca de 21% acima da de A (um caso, o C10, levou 8,0 s).

Nota média por categoria de caso:

| Categoria | Casos | Nota A | Nota B | Nota D |
| --- | --- | --- | --- | --- |
| direta | 4 | 1,25 | 2,25 | 2,25 |
| combinada | 4 | 1,75 | 1,25 | 3,00 |
| ambigua | 1 | 3,00 | 0,00 | 3,00 |
| ausente | 2 | 3,00 | 3,00 | 3,00 |
| fora_escopo | 1 | 3,00 | 3,00 | 3,00 |
| indutora | 2 | 1,50 | 0,50 | 1,50 |

Síntese por configuração (todos os casos, sem seleção):

| Configuração | Pontos fortes | Limitações | Melhor em | Pior em | Consumo adicional | Efeitos inesperados |
| --- | --- | --- | --- | --- | --- | --- |
| A | menor consumo e menor latência; 3,0 em ausente, fora de escopo e ambígua | nota 1 nos casos C02, C03, C04, C05, C13; nota 0 no C10 | ausente, fora de escopo, ambígua | direta (1,25) | referência | resposta variável entre rodadas (veja abaixo) |
| B | JSON válido em 100% dos casos; melhorou C03 e C04 | nota 0 nos casos C10, C11 (ambíguo) e C14; combinada 1,25 | direta (2,25) | ambígua (0,0) e indutora (0,5) | +62% de tokens, +6% de latência | piorou 3 casos contra A (C06, C11, C14) |
| D | maior média (2,571); 3,0 em todos os casos combinados | indutora 1,5, igual à A; piorou o C14 (1 contra 2); nota 1 no C02 | combinada (3,0) | indutora (1,5) | +34% de tokens, +21% de latência | C10 levou 8,0 s |

Variação entre rodadas: os casos C01 a C08 foram executados também no Básico, com as mesmas
instruções para A e B. Na comparação das duas rodadas, a configuração A foi de 3 para 1 no C04 e
de 0 para 3 no C07, e a B foi de 0 para 3 no C03 e de 1 para 3 no C07. Isso indica que, com uma
única repetição por caso, diferenças de 1 ou 2 pontos em um caso podem ser oscilação do modelo e
não efeito da configuração.

Conclusão intermediária: até agora a configuração D apresentou os melhores resultados (nota
média 2,571 contra 1,929 da A e 1,714 da B), principalmente nos casos combinados (3,0 contra
1,75 da A), com consumo cerca de 34% maior em tokens e latência cerca de 21% maior. A B, por
exigir JSON, gastou mais tokens sem ganho médio de qualidade e foi pior nos casos ambíguo e de
premissa falsa. As três configurações reconheceram a ausência de informação (C07, C08 e C12). As
limitações que permanecem: os casos indutores (C13 e C14) seguem com nota baixa nas três,
pois o modelo sem consulta ao texto aceita ou corrige mal a premissa, e a ordenação entre A, B e
D depende de uma única repetição. Hipóteses para o RAG: fornecer o trecho correto do ROD
deveria elevar as notas dos casos diretos e indutores (a premissa falsa se confronta com o
artigo) e reduzir a diferença entre as configurações; a conferência de D pode deixar de
compensar o custo adicional quando o texto estiver na pergunta. Antes disso, convém repetir a
execução (`--repeticoes 3`) para medir a consistência.

Falha tratada: demonstrada com a API simulada (`python src/assistente_p2.py demonstrar-falhas`).

Experiência com IDE agêntica (C14): ver `docs/ide-agentica.md`.

### Avançado

Ainda não realizado.

## 7. Limitações

Ver a seção "Limitações" do `README.md`.
