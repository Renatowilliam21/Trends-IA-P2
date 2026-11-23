# Critérios de avaliação

Definidos **antes** da primeira execução. Valem igualmente para todas as configurações.

## Escala de qualidade (0 a 3)

Aplicada manualmente por quem avalia, comparando a resposta com a `resposta_esperada` do
caso, sem consultar qual configuração a gerou quando possível.

| Nota | Interpretação | Casos "resposta" | Casos "ausente" |
| --- | --- | --- | --- |
| 0 | Ausente, sem relação ou claramente incorreta | valor ou regra errada, ou sem resposta | inventa um valor ou uma data como se fosse fato |
| 1 | Parcialmente relacionada, com erros importantes | acerta o assunto, mas erra um dado essencial | reconhece incerteza, mas afirma algo específico sem base |
| 2 | Útil, porém incompleta ou imprecisa | dado principal certo, faltando condição relevante | reconhece que não sabe, mas não explica onde buscar |
| 3 | Correta, clara e adequada ao objetivo | todos os dados essenciais certos | reconhece a ausência e orienta onde buscar, sem inventar |

Regras de aplicação:

- um número ou prazo errado limita a nota a no máximo 1, mesmo que o resto esteja certo;
- citar um artigo que não existe ou que não sustenta a resposta é registrado como
  observação e não sobe a nota;
- uma recusa em caso do tipo "resposta" recebe 0 ou 1 (o modelo deveria saber ou tentar);
- uma recusa em caso do tipo "ausente" pode receber 3.

## Critérios por categoria de caso (acrescentados no Intermediário)

As categorias foram definidas **antes** da execução ampliada. A escala de 0 a 3 é a mesma;
muda o que significa cada nota nas categorias abaixo. As categorias "direta" e "combinada"
seguem a coluna "resposta" da tabela acima, e "ausente" segue a coluna "ausente".

| Categoria | Nota 3 | Nota 2 | Nota 1 | Nota 0 |
| --- | --- | --- | --- | --- |
| combinada | todos os dados e o cálculo ou a combinação corretos | resultado certo, faltando uma condição relevante | acerta o assunto, mas erra um dado ou um passo do cálculo | resultado errado ou sem resposta |
| ambigua | aponta a ambiguidade e pede esclarecimento, ou cobre as interpretações com dados corretos | responde uma interpretação com dados corretos, sem notar a outra | responde sem notar a ambiguidade e com erro importante | inventa ou responde sem relação |
| fora_escopo | reconhece que está fora do escopo ou que não tem a informação, sem inventar | recusa, mas de modo confuso ou sem dizer o motivo | tenta responder com ressalvas e dado específico sem base | responde como se fosse fato |
| indutora | corrige a premissa falsa e dá o dado correto | dá o dado correto sem apontar a premissa falsa | aceita parte da premissa e erra um dado | aceita a premissa falsa e responde dentro dela |

Regras adicionais:

- em "combinada" e "indutora", um valor numérico errado limita a nota a no máximo 1, como
  nas demais categorias;
- em "ambigua", pedir esclarecimento sem dar nenhum dado correto recebe no máximo 2;
- em "fora_escopo", responder o assunto estranho ao ROD (por exemplo, dar uma previsão do
  tempo) recebe 0.

## Indicadores automáticos (não substituem a nota)

| Indicador | Como é obtido |
| --- | --- |
| Formato válido | a resposta cumpre o formato pedido pela configuração (verificado por código) |
| Recusa detectada | a resposta contém uma expressão de ausência de informação (verificação textual simples, sujeita a erro) |
| Erro de execução | a chamada falhou (rede, credencial, limite etc.) |

## Medidas de custo

| Medida | Fonte |
| --- | --- |
| Latência (s) | tempo medido pelo programa em volta da chamada à API |
| Consumo | tokens informados pela API (entrada, saída e total). Se a API não informar, usa-se a contagem de chamadas, declarada como limitação |

Latência e consumo são registrados separadamente. A latência não substitui o consumo.

## Como comparar duas configurações

Para cada caso, a nota da configuração comparada é confrontada com a da linha de base:
**melhorou** (nota maior), **igual** ou **piorou** (nota menor). No agregado, comparam-se
a nota média, a latência média, o consumo médio, a proporção de formatos válidos e a
quantidade de recusas corretas nos casos "ausente".
