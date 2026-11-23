# Uso de IA no desenvolvimento

**Ferramenta usada no desenvolvimento:** Claude (Anthropic), em conversa de chat com acesso a
terminal, para esta versão de referência.
**Serviço de LLM da aplicação:** OpenAI, por API REST.

## O que a IA fez

- Propôs a estrutura do repositório, as configurações A, B e C e os casos de teste.
- Escreveu o código, os testes simulados e a documentação.
- Redigiu a primeira versão da escala de avaliação.

## O que foi verificado por uma pessoa

- Os testes simulados rodam sem rede e sem custo (`python -m pytest`).
- As respostas esperadas dos casos foram conferidas contra o texto do ROD.
- A execução real, as notas e a conclusão provisória são feitas por quem avalia, não pela IA.

## Intermediário

A IDE agêntica pedida em C14 é uma experiência do próprio autor e está registrada em
`docs/ide-agentica.md`. A conversa com Claude usada para montar esta referência não substitui
esse registro.

## Observação

Quem reaproveitar este material para a própria entrega deve descrever aqui o seu uso de IA
com as próprias palavras, o que aceitou, o que corrigiu e o que recusou.
