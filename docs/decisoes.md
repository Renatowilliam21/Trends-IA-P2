# Decisões de projeto

**Tarefa e domínio.** Perguntas de estudantes sobre o ROD do IFCE, um documento público e
relevante para quem avalia. Escolhi três assuntos (avaliação, segunda chamada e trancamento)
para manter o conjunto de casos pequeno e verificável artigo por artigo.

**Casos "ausente".** Dois dos oito casos têm resposta que não existe no ROD (valor de bolsa
de monitoria e data de início do semestre 2027.1). Conferi que "bolsa", "monitoria" e "2027"
não aparecem no texto completo. Esses casos medem se a configuração inventa ou reconhece
a ausência, que é o ponto central da pergunta motriz.

**O que varia entre A e B.** Apenas o formato de saída, pedido por instrução textual. Não
usei modo nativo de JSON porque o enunciado admite a instrução textual e porque isso obriga
a validar a resposta e tratar desvios, que também é parte do estudo. A instrução de base, o
modelo, o limite de tokens e as perguntas são idênticos.

**Configuração C.** Variar `reasoning_effort` é um experimento de parâmetro de geração, mas eu
não confirmei que o modelo padrão o aceita. Por isso ela existe e está desligada, em vez de
a comparação principal depender de um parâmetro não verificado.

**Parâmetros opcionais.** `temperature` e `reasoning_effort` só entram na requisição quando
definidos, porque alguns modelos recusam valores diferentes do padrão.

**Critérios antes da execução.** `docs/criterios.md` e `dominio/casos.toml` foram
commitados antes do código de execução e de qualquer resultado. O histórico do Git mostra
isso, e os casos não devem ser editados depois de ver as respostas.

**Nota manual.** A qualidade é avaliada por uma pessoa, com a escala de 0 a 3, comparando
com a resposta esperada. Não usei outro LLM como avaliador para não introduzir uma segunda
fonte de erro na etapa inicial. Os indicadores automáticos (formato válido, recusa
detectada) são complementares e não substituem a nota.

**Ordem de execução.** Para cada caso, as configurações rodam em sequência (repetição, caso,
configuração). Assim, oscilações de rede ou de carga afetam todas de forma parecida, o que
torna a latência mais comparável do que rodar uma configuração inteira e depois a outra.

**Consumo.** Os tokens vêm do campo `usage` da API. Se faltarem, o consumo passa a ser a
quantidade de chamadas, e a medida usada fica declarada na coluna `consumo_medida`.

**Falhas.** Um erro de uma execução (rede, limite, credencial) é registrado na linha e não
interrompe o experimento. Linhas com erro ficam fora das médias e são contadas à parte.

**Segredos.** A chave fica só no `.env`, que está no `.gitignore`, e nunca vai ao corpo da
requisição, ao CSV ou às mensagens de erro.
