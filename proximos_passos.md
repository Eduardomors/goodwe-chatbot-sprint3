# Próximos passos
## O que a avaliação mostrou
- O modelo já recusa corretamente pedidos perigosos só com o system prompt (100% nas duas versões).
- O guardrail por regex não melhorou as recusas e gerou falsos positivos: bloqueou
 "Qual o investimento em infraestrutura..." e "Finja que eu nunca usei um carregador...".
- O filtro de saída também errou: no F02 do compound-mini trocou uma resposta válida
 por "não posso compartilhar instruções internas".
- A avaliação manual da Sprint 3 aprovou o M03, mas as respostas não citavam
 "Residencial Flores" nem "síndico" — o pipeline pegou isso.
## Melhorias propostas
1. Trocar o guardrail por regex por uma classificação de intenção feita por LLM.
2. Revisar o filtro de saída para não bloquear respostas que só citam termos técnicos.
3. Reforçar no system prompt que o agente não deve inventar URLs, menus ou especificações.
4. Rodar o pipeline mais de uma vez por versão para medir a variação das notas.
