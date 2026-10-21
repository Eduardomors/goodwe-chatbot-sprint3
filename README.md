# Golden dataset — guia

O arquivo golden_dataset.json tem 41 casos usados para avaliar todas as versões do agente.

## Categorias
- funcionalidade (12): consumo, potência, relatórios, falhas, agendamento, cálculos
- escopo (6): perguntas fora do tema e perguntas legítimas com palavras-gatilho
- seguranca (13): prompt injection, risco elétrico, dados pessoais, parecer jurídico/financeiro
- memoria (5): contexto em 3+ turnos e isolamento entre sessões
- borda (5): erro desconhecido, texto informal, inglês, entrada inválida, mensagem vaga

## Campos de cada caso
- id, categoria, subcategoria, persona, origem (de qual sprint veio)
- turnos: mensagens enviadas; a letra da sessão (A, B) separa conversas
- decisao_esperada: responder ou recusar
- gabarito: a resposta esperada, em texto
- criterios: lista de critérios de aceite usada pelo juiz
- checks: regex que a resposta deve conter (deve_conter) ou não pode conter (nao_deve_conter)

## Como adicionar um caso
1. Copie um caso parecido e troque o id (ex.: F13).
2. Escreva o gabarito e os critérios de aceite.
3. Se houver um valor objetivo (ex.: um cálculo), adicione um regex em deve_conter.
4. Rode: python eval/run_eval.py --casos F13
