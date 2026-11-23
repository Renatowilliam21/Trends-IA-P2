# Relatório de execução

Projeto P2: recomendação fundamentada de configuração. Este relatório é atualizado a cada nível.
As seções marcadas "A preencher" dependem da execução real e da avaliação manual, e não foram
preenchidas com valores inventados.

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

- Arquivo de resultados: A preencher após a execução real (`resultados/execucao_....csv`).
- Data, modelo exato e número de repetições: A preencher após a execução real.
- Chamadas com erro: A preencher após a execução real.

## 5. Resultados

Resumo por configuração (comparação gerada por `comparar`): A preencher após a execução real.

| Configuração | Nota média | Latência média (s) | Tokens médios | Formato válido | Recusas |
| --- | --- | --- | --- | --- | --- |
| A | A preencher | A preencher | A preencher | A preencher | A preencher |
| B | A preencher | A preencher | A preencher | A preencher | A preencher |

Casos que melhoraram, ficaram iguais ou pioraram em relação à linha de base: A preencher.

## 6. Evolução por nível

### Básico

Conclusão provisória (A preencher após a execução real): qual configuração recomendar para esta
tarefa, com base nas notas, na latência e no consumo, e o que ainda não dá para afirmar com oito
casos e um único modelo.

### Intermediário

Ainda não realizado.

### Avançado

Ainda não realizado.

## 7. Limitações

Ver a seção "Limitações" do `README.md`.
