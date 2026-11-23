# P2: recomendação fundamentada de configuração (nível Básico)

Aplicação de linha de comando em Python que executa o **mesmo conjunto de perguntas** em
**duas ou mais configurações do mesmo LLM**, registra qualidade, latência e consumo e
compara os resultados. A tarefa é responder perguntas de estudantes sobre o Regulamento da
Organização Didática (ROD) do IFCE, **sem RAG**: o modelo recebe só as instruções e a
pergunta, e as respostas esperadas servem apenas para avaliar.

Etapa atual: **Básico** (integração, linha de base e primeira comparação).
Tag de entrega: `p2-basico`.

## Requisitos

- Python 3.11 ou superior (testado em 3.13 no Linux)
- Git
- Chave de API da OpenAI (https://platform.openai.com/api-keys), com crédito na conta de
  desenvolvedor. A assinatura do ChatGPT não inclui acesso à API.

## Instalação

Linux ou macOS:

```bash
git clone https://github.com/Renatowilliam21/Trends-IA-P2.git
cd Trends-IA-P2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
git clone https://github.com/Renatowilliam21/Trends-IA-P2.git
cd Trends-IA-P2
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuração

1. Crie o `.env` a partir do modelo e coloque a chave (começa com `sk-`, sem aspas):

   ```bash
   cp .env.example .env              # Windows: copy .env.example .env
   ```

   ```text
   OPENAI_API_KEY=sk-...sua-chave...
   ```

   O `.env` está no `.gitignore` e nunca deve ser enviado ao GitHub.

2. Confira o modelo e as configurações em `configuracoes.toml` (sem segredos). Nomes de
   modelos mudam com frequência. Para trocar sem editar o arquivo, use `OPENAI_MODEL` no `.env`.

## Uso

```bash
python src/assistente_p2.py listar                 # mostra casos e configurações
python src/assistente_p2.py executar --dry-run     # mostra o que seria enviado, sem chave
python src/assistente_p2.py executar               # roda de verdade (gasta crédito)
```

A execução grava em `resultados/` dois arquivos com o mesmo nome:

- `execucao_AAAAMMDD-HHMMSS.csv`: abra no Excel ou no editor, **preencha as colunas `nota` e
  `observacao`** seguindo `docs/criterios.md`;
- `execucao_AAAAMMDD-HHMMSS.jsonl`: cópia fiel, para conferência.

Depois de preencher as notas:

```bash
python src/assistente_p2.py comparar resultados/execucao_AAAAMMDD-HHMMSS.csv --saida resultados/comparacao.md
```

O comando recusa comparar enquanto houver nota em branco e lista o que falta.

Outras opções do `executar`: `--configs A B` (escolhe quais), `--repeticoes 3` (repete cada
caso, para medir consistência) e `--casos` / `--configuracoes` (outros arquivos).

## As configurações comparadas

| Configuração | O que muda em relação à linha de base | Estado |
| --- | --- | --- |
| A | nada: linha de base, resposta em texto livre | ativa |
| B | só o formato de saída: JSON definido por instrução textual | ativa |
| C | só o parâmetro `reasoning_effort = low` | desligada (experimental) |

A e B usam o mesmo modelo, o mesmo `max_tokens`, as mesmas instruções de base e as mesmas
perguntas. A única diferença é a instrução de formato (`prompts/formato_*.txt`). Como não se
usa modo nativo de JSON, a aplicação valida a resposta (`src/formato.py`) e registra os
desvios (JSON fora do contrato, bloco de código, texto solto).

Para ligar a C, mude `ativa = true` em `configuracoes.toml`. Se o modelo não aceitar o
parâmetro, a API recusa e o erro fica registrado, sem interromper a execução.

## O que é registrado por execução

Cada linha do CSV traz: identificador do caso, configuração, repetição, data, modelo,
parâmetros, latência (s), tokens de entrada, saída e total, medida de consumo (`tokens`, ou
`chamadas` se a API não informar), formato válido, motivo do desvio, recusa detectada, erro,
resposta, nota e observação. Latência e consumo são registrados separadamente.

## Estrutura do código

| Arquivo | Responsabilidade |
| --- | --- |
| `src/assistente_p2.py` | linha de comando (listar, executar, comparar) |
| `src/config.py` | credencial, serviço e configurações de geração |
| `src/casos.py` | carga e validação dos casos de teste |
| `src/prompts.py` | montagem do prompt (sem corpus) e do corpo da requisição |
| `src/cliente.py` | chamada à API, latência, tokens e tratamento de falhas |
| `src/formato.py` | validação do formato e detecção de recusa |
| `src/executor.py` | executa os casos nas configurações e grava os resultados |
| `src/comparacao.py` | resumo por configuração e comparação caso a caso |
| `dominio/casos.toml` | perguntas, respostas esperadas e referências (nunca enviadas ao modelo) |
| `docs/criterios.md` | escala de avaliação, definida antes da execução |

## Testes

```bash
python -m pytest              # simulados: sem rede, sem chave, sem custo
python -m pytest -m real      # reais: 2 chamadas à OpenAI (exige chave e crédito)
```

Os testes simulados cobrem credencial ausente e inválida, falhas de rede, resposta fora do
formato, o contrato do JSON, a execução do mesmo caso em duas configurações, o registro de
consumo e a comparação. Um deles garante que as respostas esperadas e o texto do ROD
**nunca** vão ao prompt. Os testes reais ficam à parte e não rodam por padrão.

## Documentação

- `docs/dominio.md`: domínio, tarefa e corpus de referência
- `docs/criterios.md`: critérios e escala de avaliação
- `docs/decisoes.md`: decisões de projeto
- `docs/uso-de-ia.md`: uso de IA no desenvolvimento
- `RELATORIO_EXECUCAO.md`: configurações, resultados e conclusão provisória por nível

## Limitações

- Oito casos e um único modelo: a conclusão do Básico é provisória e não generaliza.
- A nota é manual. A detecção de recusa é uma verificação textual simples e pode errar.
- O modelo pode conhecer partes do ROD de seu treinamento. Isso faz parte do que se mede
  na condição sem RAG, e não é falha do experimento.
- A latência inclui a rede e varia entre execuções; uma única rodada não a estabiliza.
