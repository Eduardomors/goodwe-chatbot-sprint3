# GoodWe EV ChargeOps Assistant — Sprint 3 🔋⚡

## Integrantes
| Nome | RM | Responsabilidade |
|------|------|------------------|
| Brenno Gomes | 570525 | Arquitetura LangGraph, guardrails e integração |
| Eduardo Moreira | 569923 | Testes de segurança e prompt injection |
| Enzo Stahal | 569001 | Testes funcionais e de memória |
| Matheus Bruno | 572944 | Comparação de modelos e relatório de evolução |

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
