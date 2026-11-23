# Alterações do nível Intermediário

Cada mudança em relação ao Básico, com o motivo. As respostas esperadas e a escala foram
escritas **antes** da execução ampliada.

## Casos

| Mudança | Motivo |
| --- | --- |
| Os 8 casos do Básico foram mantidos sem alterar pergunta nem resposta esperada | permite comparar as duas rodadas |
| Campo `categoria` acrescentado a todos os casos | a análise precisa dizer em que tipos de caso cada configuração foi melhor ou pior |
| Novos C09 e C10 (combinada) | exigem cálculo (Art. 100) e combinação de dois artigos (Arts. 111 e 112) |
| Novo C11 (ambigua) | "Quero trancar" admite trancamento de matrícula ou de componente |
| Novo C12 (fora_escopo) | pergunta sobre o tempo, alheia ao ROD |
| Novos C13 e C14 (indutora) | premissa falsa embutida (média 6,0 na graduação; trancar disciplina a qualquer tempo) |
| Respostas esperadas dos novos casos conferidas no texto do ROD | Arts. 98 a 100, 110 a 112, 149 a 155 |

## Critérios

Acrescentada a seção "Critérios por categoria de caso" em `docs/criterios.md`, com o
significado das notas em combinada, ambigua, fora_escopo e indutora.

## Configurações

| Mudança | Motivo |
| --- | --- |
| A e B mantidas como no Básico | o conjunto ampliado deve ser medido com as mesmas configurações |
| Nova configuração D, ativa | hipótese tirada do Básico: B piorou nos casos de cálculo e de condições (C03, C05, C06). Se pedir ao modelo que confira dados e refaça cálculos antes de concluir ajudar, D deve superar A nesses casos |
| D difere de A só na instrução final do prompt (`prompts/formato_conferir.txt`) | comparação justa: mesmo modelo, mesmos parâmetros, mesma base de instruções |
| C continua desligada | o suporte do modelo a `reasoning_effort` segue sem confirmação |

## Fluxo e registros

| Mudança | Motivo |
| --- | --- |
| Execução em três etapas (preparar pergunta, consultar modelo, organizar resposta) | cada etapa tem entrada, saída e tratamento de falha próprios |
| Registro de eventos em `execucao_*.eventos.jsonl` | permite investigar cada passo sem reler o CSV |
| Colunas novas no CSV: categoria, situacao_final, chamadas, tempo_total_s, versao_prompt | rastreabilidade e custo por caso |
| Nova tentativa limitada (até 3) só para falhas transitórias | resposta ao timeout e à instabilidade, sem tentativas indefinidas |
| Encerramento controlado após falha fatal ou após 3 falhas seguidas de serviço | evita gastar chamadas quando o serviço está fora ou a credencial é inválida |
