## Comparação (linha de base: A)

### Resumo por configuração

| Configuração | Execuções | Erros | Nota média | Latência média (s) | Tokens médios | Formato válido | Ausentes reconhecidos |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 14 | 0 | 1.929 | 2.463 | 252.214 | 100.0% | 3 de 3 |
| B | 14 | 0 | 1.714 | 2.609 | 409.071 | 100.0% | 3 de 3 |
| D | 14 | 0 | 2.571 | 2.973 | 338.714 | 100.0% | 3 de 3 |

### Caso a caso

| Caso | Nota A | Nota B | Nota D | B vs A | D vs A | Latência (s) |
| --- | --- | --- | --- | --- | --- | --- |
| C01 | 2.0 | 2.0 | 2.0 | igual | igual | A: 2.759 / B: 3.123 / D: 2.189 |
| C02 | 1.0 | 1.0 | 1.0 | igual | igual | A: 2.594 / B: 3.751 / D: 2.539 |
| C03 | 1.0 | 3.0 | 3.0 | melhorou | melhorou | A: 2.483 / B: 2.276 / D: 2.011 |
| C04 | 1.0 | 3.0 | 3.0 | melhorou | melhorou | A: 2.05 / B: 4.81 / D: 4.49 |
| C05 | 1.0 | 1.0 | 3.0 | igual | melhorou | A: 2.229 / B: 3.327 / D: 2.839 |
| C06 | 3.0 | 1.0 | 3.0 | piorou | igual | A: 2.494 / B: 1.811 / D: 2.339 |
| C07 | 3.0 | 3.0 | 3.0 | igual | igual | A: 1.783 / B: 1.619 / D: 2.013 |
| C08 | 3.0 | 3.0 | 3.0 | igual | igual | A: 2.086 / B: 1.589 / D: 1.986 |
| C09 | 3.0 | 3.0 | 3.0 | igual | igual | A: 3.435 / B: 3.262 / D: 3.675 |
| C10 | 0.0 | 0.0 | 3.0 | igual | melhorou | A: 3.43 / B: 2.363 / D: 8.002 |
| C11 | 3.0 | 0.0 | 3.0 | piorou | igual | A: 2.807 / B: 1.931 / D: 2.58 |
| C12 | 3.0 | 3.0 | 3.0 | igual | igual | A: 1.755 / B: 1.753 / D: 2.355 |
| C13 | 1.0 | 1.0 | 2.0 | igual | melhorou | A: 2.242 / B: 3.065 / D: 2.386 |
| C14 | 2.0 | 0.0 | 1.0 | piorou | piorou | A: 2.33 / B: 1.84 / D: 2.22 |

### Balanço contra a linha de base

- B: 2 caso(s) melhoraram, 9 ficaram iguais e 3 pioraram.
- D: 5 caso(s) melhoraram, 8 ficaram iguais e 1 pioraram.

### Nota média por categoria de caso

| Categoria | Casos | Nota A | Nota B | Nota D |
| --- | --- | --- | --- | --- |
| direta | 4 | 1.25 | 2.25 | 2.25 |
| combinada | 4 | 1.75 | 1.25 | 3.0 |
| ausente | 2 | 3.0 | 3.0 | 3.0 |
| ambigua | 1 | 3.0 | 0.0 | 3.0 |
| fora_escopo | 1 | 3.0 | 3.0 | 3.0 |
| indutora | 2 | 1.5 | 0.5 | 1.5 |

### Situação final, chamadas e tempo

| Configuração | Concluído | Parcial | Falha | Interrompido | Chamadas médias | Tempo total médio (s) |
| --- | --- | --- | --- | --- | --- | --- |
| A | 14 | 0 | 0 | 0 | 1.0 | 2.476 |
| B | 14 | 0 | 0 | 0 | 1.0 | 2.621 |
| D | 14 | 0 | 0 | 0 | 1.0 | 2.987 |
