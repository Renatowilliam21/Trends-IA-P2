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

O arquivo `dominio/casos.toml` reúne 8 perguntas, cada uma com resposta esperada, artigo de
referência e tipo:

- **resposta:** a informação está no ROD, e a resposta esperada é conhecida;
- **ausente:** a informação não está no ROD (conferido na versão completa do documento), e a
  resposta correta é reconhecer a ausência em vez de inventar.

Os casos foram escritos antes da primeira execução e não devem ser alterados depois de ver
as respostas do modelo.
