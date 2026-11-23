# Experiência com IDE agêntica (C14)

> **A preencher pelo autor.** A exigência é uma experiência prática documentada: delegar uma
> tarefa real e delimitada a uma IDE com recursos agênticos, revisar, testar e decidir. O texto
> abaixo é um roteiro. O que está entre colchetes deve ser substituído pelo que realmente
> aconteceu. Se a ferramenta propôs algo ruim, registre isso também: faz parte da avaliação.

## Tarefa delegada (sugestões, escolha uma)

- ampliar os testes de `src/formato.py` com mais desvios de JSON;
- refatorar `src/comparacao.py` separando cálculo e apresentação;
- criar um comando que resuma a coluna `observacao` por categoria.

Evite pedidos amplos como "faça todo o projeto".

## Registro

| Item | Conteúdo |
| --- | --- |
| Ferramenta e versão | [ex.: nome da IDE, modelo usado] |
| Tarefa delegada | [uma frase] |
| Instrução resumida | [o que você pediu, com o contexto do projeto que forneceu] |
| Alteração produzida | [arquivos e linhas alterados, por exemplo `git diff --stat`] |
| Resultado da revisão | [o que você leu, o que entendeu, se respeitou o escopo e as dependências] |
| Problemas identificados | [erros, excessos, mudanças fora do escopo] |
| Correções feitas | [o que você ajustou ou descartou] |
| Teste utilizado | [comando e resultado, antes e depois] |
| Decisão | [incorporar, incorporar com ajustes ou descartar, e por quê] |

## Antes de incorporar

- [ ] li o diff completo e entendi cada alteração
- [ ] a alteração respeita o escopo pedido e não mexeu em arquivos alheios
- [ ] verifiquei dependências novas
- [ ] `python -m pytest` passa; comparei o comportamento antes e depois
- [ ] corrigi ou descartei o que não era adequado
