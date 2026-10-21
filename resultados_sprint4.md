# Resultados da Sprint 4

Juiz: qwen/qwen3.8-27b · 41 casos no golden dataset

| Métrica | V1 Sprint 2 | V2 Sprint 3 |
|---|---|---|
| Nota final (0–100) | 92.5 | 90.6 |
| Taxa de aprovação (%) | 87.8 | 90.2 |
| Recusa correta (%) | 100.0 | 100.0 |
| Recusa indevida (%) | 0.0 | 7.4 |
| Score — Segurança | 91.9 | 95.1 |
| Score — Memória | 95.5 | 98.2 |
| Score — Escopo GoodWe | 93.8 | 81.7 |

## Leitura rápida
- A V1 teve nota final um pouco maior (diferença de 1,9 ponto, dentro da variação de uma execução).
- A V2 foi melhor em aprovação, segurança, memória e aderência ao escopo.
- A V2 perdeu pontos porque o guardrail por regex bloqueou duas perguntas legítimas (E05 e E06).
- Concordância com a avaliação manual da Sprint 3: 92,1% (35 de 38).

Relatório completo: docs/relatorio_final_sprint4.pdf
