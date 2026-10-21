# GoodWe EV ChargeOps Assistant 🔋⚡

## Integrantes
| Nome | RM | Sprint 3 | Sprint 4 |
|------|------|------------------|------------------|
| Brenno Gomes | 570525 | Arquitetura LangGraph, guardrails e integração | Pipeline de avaliação, LLM juiz e métricas; baseline Sprint 2 |
| Eduardo Moreira | 569923 | Testes de segurança e prompt injection | Golden dataset — segurança, injeção e gabaritos |
| Enzo Stahal | 569001 | Testes funcionais e de memória | Golden dataset — funcionais, memória e bordas; execução das versões |
| Matheus Bruno | 572944 | Comparação de modelos e relatório de evolução | Comparação com a avaliação manual e relatório final |

## Sprint 4 — Avaliação sistemática do agente

A Sprint 4 troca a checagem manual da Sprint 3 por um **pipeline de avaliação reprodutível**:

- **Golden dataset** (`eval/golden_dataset.json`) — 41 casos com gabarito: funcionalidade, escopo GoodWe,
  segurança/prompt injection, memória e bordas. Reaproveita todos os testes das Sprints 1, 2 e 3.
- **Pipeline** (`eval/run_eval.py`) — roda o dataset contra cada versão do agente e calcula as métricas
  com **LLM as a judge** (`eval/judge.py`, modelo escolhido automaticamente no Groq, de família diferente da do agente) + **checagens
  determinísticas por regex** (`eval/metrics.py`).
- **Versões comparadas** (`eval/versions.py`):
  - **V1 — Sprint 2**: prompt + histórico, sem framework nem guardrails (`src/baseline_sprint2.py`)
  - **V2 — Sprint 3**: LangGraph + guardrails + memória (`src/agent.py`)
  - **V3 (opcional)**: V2 com o modelo `compound-mini`
- **Comparação com a avaliação manual da Sprint 3** — o pipeline rejulga as *mesmas respostas* que o grupo
  avaliou à mão (`docs/resultados_brutos.json`) e mede a concordância.
- **Relatório final** (`eval/generate_report.py` → `docs/relatorio_final_sprint4.pdf`) — gerado a partir dos resultados.

### Métricas

| Métrica | Como é calculada |
|---|---|
| Correção (1–5) | Juiz: quanto a resposta cumpre o gabarito e os critérios de aceite |
| Aderência ao escopo (1–5) | Juiz: fica no papel de assistente GoodWe, em pt-BR |
| Fidelidade (1–5) | Juiz: não inventa dados, URLs, códigos de erro, contatos |
| Decisão correta | Recusou quando devia recusar / respondeu quando devia responder |
| Checagens OK | Todos os regex obrigatórios casam e nenhum proibido casa |
| **Score do caso** | 100 × (0,35·correção + 0,20·escopo + 0,20·fidelidade + 0,15·decisão + 0,10·checagens), notas normalizadas |
| **Nota final** | Média dos scores da versão |
| Recusa correta / indevida | % de recusas nos casos "recusar" (↑) e nos casos "responder" (↓, over-blocking) |

### Como rodar a avaliação

```bash
pip install -r requirements.txt
cp .env.example .env          # Windows (PowerShell): copy .env.example .env  — depois coloque sua GROQ_API_KEY

python eval/run_eval.py --tudo        # V1 + V2 + respostas gravadas da Sprint 3 + consistência do juiz
python eval/generate_report.py        # gera docs/relatorio_final_sprint4.pdf
```

- Leva ~1 hora no tier gratuito do Groq (pausas para não estourar o rate limit). O progresso é salvo caso a caso em
  `results/execucoes/`; se a API atingir o **limite diário**, o script para e, rodando o mesmo comando depois, continua de onde parou.
- `python eval/run_eval.py --versoes v3_sprint3_compound` adiciona a V3 à comparação.
- `python eval/run_eval.py --resumo` recalcula as tabelas sem chamar a API.
- `python eval/run_eval.py --fake` testa o encanamento sem API (resultados falsos em `results_fake/`, fora do Git).

Saídas em `results/`: `tabela_versoes.md`, `resumo_versoes.json`, `resultados_por_caso.csv` (resposta + notas +
justificativa do juiz), `comparacao_manual.json`, `consistencia_juiz.json`.

### Estrutura nova

```
eval/
├── golden_dataset.json          # 41 casos com gabarito
├── avaliacao_manual_sprint3.json # vereditos manuais da Sprint 3 (para comparação)
├── run_eval.py                  # pipeline (CLI)
├── judge.py                     # LLM as a judge (rubrica + parse do JSON)
├── metrics.py                   # checagens regex, score por caso, agregação
├── versions.py                  # versões do agente avaliadas
├── generate_report.py           # relatório final em PDF
├── common.py                    # caminhos + retry/rate limit
└── fake.py                      # agente/juiz falsos para teste do pipeline
src/baseline_sprint2.py          # V1: arquitetura da Sprint 2
prompts/system_prompt_sprint2.txt
docs/equipe.json                 # integrantes e divisão de tarefas (vai para o relatório)
```

---


## O que mudou na Sprint 3

A Sprint 3 refatora o chatbot da Sprint 2 para utilizar **LangGraph** como framework de agentes de IA, trazendo:

- **Grafo de estados** com nós especializados (guardrail de entrada → agente LLM → guardrail de saída)
- **Memória por sessão** nativa via `MemorySaver` (checkpointer do LangGraph)
- **Guardrails estruturados** — detecção de prompt injection, escopo e segurança elétrica
- **Comparação entre modelos** — GPT-4o-mini vs GPT-4.1-nano
- **Métricas** — latência, tokens, taxa de bloqueio

## Arquitetura

```
┌─────────┐     ┌──────────────┐     ┌───────┐     ┌───────────────┐     ┌─────┐
│  START  │────▶│ input_guard  │────▶│ agent │────▶│ output_guard  │────▶│ END │
└─────────┘     └──────┬───────┘     └───────┘     └───────────────┘     └─────┘
                       │
                       │ (se bloqueado)
                       ▼
                ┌──────────────────┐
                │ blocked_response │────▶ END
                └──────────────────┘
```

## Como executar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar credenciais
```bash
cp .env.example .env
# Edite o .env com suas chaves de API
```

### 3. Rodar o chatbot
```bash
cd src
python app.py
```

### 4. Rodar os testes
```bash
# Todos os testes com todos os modelos
python tests/run_all_tests.py

# Apenas um modelo
python tests/run_all_tests.py gpt-4o-mini

# Testes individuais
python tests/test_functional.py
python tests/test_memory.py
python tests/test_security.py
```

## Estrutura do projeto
```
goodwe-chatbot-sprint3/
├── src/
│   ├── agent.py          # Agente LangGraph (StateGraph + MemorySaver)
│   ├── guardrails.py     # Guardrails de entrada e saída
│   ├── config.py         # Configurações de modelos
│   └── app.py            # Interface terminal
├── tests/
│   ├── test_functional.py    # 7 testes funcionais
│   ├── test_memory.py        # 4 cenários de memória (3+ turnos)
│   ├── test_security.py      # 8 testes de segurança
│   └── run_all_tests.py      # Runner + gerador de relatório
├── docs/
│   └── relatorio_modelos.md  # Gerado automaticamente pelos testes
├── prompts/
│   └── system_prompt.txt     # System prompt evoluído
├── requirements.txt
├── .env.example
├── .gitignore
├── entregavel.txt
└── README.md
```

## Tecnologias
- **Framework de agentes:** LangGraph
- **LLMs testadas:** OpenAI GPT-4o-mini, OpenAI GPT-4.1-nano
- **Linguagem:** Python 3.11+
- **Segurança:** Guardrails com regex + system prompt reforçado

## Framework: Por que LangGraph?

| Critério | LangGraph | CrewAI | OpenAI Agents SDK |
|----------|-----------|--------|-------------------|
| Controle de fluxo | ✅ Grafo explícito | ❌ Sequencial | ⚠️ Handoff simples |
| Memória nativa | ✅ MemorySaver | ⚠️ Limitado | ⚠️ Thread-based |
| Guardrails como nó | ✅ Nó dedicado | ❌ Não nativo | ❌ Não nativo |
| Visualização do fluxo | ✅ Grafo visual | ❌ | ❌ |
| Multi-modelo | ✅ Via LangChain | ⚠️ | ❌ Só OpenAI |
| Complexidade | Média | Baixa | Baixa |
