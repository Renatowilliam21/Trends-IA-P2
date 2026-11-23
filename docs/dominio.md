# Domínio e tarefa

## Domínio

Regulamento da Organização Didática (ROD) do IFCE, Resolução Consup nº 35, de 22 de junho
de 2015. É um documento público. Estudantes e servidores têm dificuldade para localizar
regras em documentos institucionais longos, e um assistente poderia apoiar essa busca.

## Tarefa delimitada

Responder, em português, perguntas objetivas de estudantes sobre três assuntos do ROD:
avaliação e aprovação, segunda chamada e trancamento. A resposta deve ser curta, citar o
artigo quando o modelo souber e indicar claramente quando não há informação suficiente.

## Corpus de referência

Três trechos do ROD, usados **somente por quem avalia** para definir as respostas
esperadas. Eles não são enviados ao modelo no Básico (condição sem RAG).

| Trecho | Artigos | Assunto |
| --- | --- | --- |
| Avaliação | 97 a 100 | etapas, média parcial, aprovação e avaliação final |
| Segunda chamada | 110 a 112 | prazos e procedimento |
| Trancamento | 149 a 155 | trancamento de matrícula e de componente curricular |

Os textos estão no repositório de apoio do P0 (`dados/`). O conteúdo oficial prevalece
sobre qualquer transcrição.

## Casos de teste

O arquivo `dominio/casos.toml` reúne 14 perguntas (8 do Básico, melhoradas, mais 6 do
Intermediário), cada uma com resposta esperada, artigo de referência, tipo e categoria:

- **resposta:** a informação está no ROD, e a resposta esperada é conhecida;
- **ausente:** não há resposta no ROD (informação inexistente, conferida na versão completa do
  documento, ou pergunta fora do escopo), e a resposta correta é reconhecer isso em vez de
  inventar.

A **categoria** descreve o desafio do caso. O conjunto cobre todas as pedidas no Intermediário:

| Categoria | Casos | Desafio |
| --- | --- | --- |
| direta | C01 a C04 | resposta direta no texto |
| combinada | C05, C06, C09, C10 | exige combinar informações ou calcular |
| ambigua | C11 | a pergunta admite mais de uma leitura |
| ausente | C07, C08 | a informação não existe no ROD |
| fora_escopo | C12 | assunto alheio ao ROD |
| indutora | C13, C14 | a pergunta traz uma premissa falsa que convida a inventar |

Os casos de reconhecimento de incerteza ou recusa são C07, C08 e C12.

Os casos foram escritos antes da primeira execução e não devem ser alterados depois de ver
as respostas do modelo.
