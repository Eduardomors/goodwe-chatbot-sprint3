"""
Testes Funcionais — Sprint 3
Reutiliza os 5 casos da Sprint 2 + 2 novos para cobertura adicional.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agent import GoodWeAgent
from config import DEFAULT_MODEL


FUNCTIONAL_TESTS = [
    {
        "id": "F01",
        "persona": "Morador",
        "categoria": "Consulta de consumo",
        "pergunta": "Como posso verificar o consumo de energia do meu apartamento no mês passado?",
        "criterios": [
            "Orienta acessar painel ou aplicativo",
            "Indica onde encontrar histórico de consumo",
            "Menciona métricas como kWh e custo",
        ],
    },
    {
        "id": "F02",
        "persona": "Síndico",
        "categoria": "Orquestração de potência",
        "pergunta": (
            "Três moradores estão carregando ao mesmo tempo e a energia do condomínio caiu. "
            "O que aconteceu e como posso evitar que isso se repita?"
        ),
        "criterios": [
            "Explica conceito de sobrecarga",
            "Menciona balanceamento/orquestração de potência",
            "Indica como configurar",
        ],
    },
    {
        "id": "F03",
        "persona": "Síndico",
        "categoria": "Relatório e faturamento",
        "pergunta": "Como gero um relatório mensal de consumo por unidade para cobrar cada morador separadamente?",
        "criterios": [
            "Descreve acesso a relatórios",
            "Menciona filtro por período e unidade",
            "Indica exportação (PDF/Excel)",
        ],
    },
    {
        "id": "F04",
        "persona": "Técnico",
        "categoria": "Diagnóstico de falha",
        "pergunta": "O carregador do box 7 está exibindo erro E04 constantemente. O que significa e como resolver?",
        "criterios": [
            "Identifica código E04",
            "Descreve causa provável",
            "Oferece passos de resolução",
        ],
    },
    {
        "id": "F05",
        "persona": "Morador",
        "categoria": "Agendamento e tarifa",
        "pergunta": "É possível agendar a recarga para o horário de madrugada, quando a tarifa de energia é mais barata? Como configuro isso?",
        "criterios": [
            "Confirma possibilidade de agendamento",
            "Explica como configurar",
            "Menciona tarifa fora de ponta",
        ],
    },
    {
        "id": "F06",
        "persona": "Morador",
        "categoria": "Cálculo de custo",
        "pergunta": "Se eu consumir 45 kWh e a tarifa for R$ 0,95 por kWh, quanto vou pagar?",
        "criterios": [
            "Apresenta o cálculo correto (45 × 0.95 = 42.75)",
            "Mostra a fórmula utilizada",
        ],
    },
    {
        "id": "F07",
        "persona": "Síndico",
        "categoria": "Regras do condomínio",
        "pergunta": "Como configuro um limite de 4 horas máximas de recarga por sessão para evitar que alguém monopolize o carregador?",
        "criterios": [
            "Indica onde configurar limite de tempo",
            "Menciona gestão de sessões",
            "Permanece no escopo GoodWe",
        ],
    },
]


def run_functional_tests(model_name: str = DEFAULT_MODEL, verbose: bool = True):
    """Executa todos os testes funcionais e retorna resultados."""
    agent = GoodWeAgent(model_name=model_name)
    results = []

    for tc in FUNCTIONAL_TESTS:
        agent.reset_session()

        if verbose:
            print(f"\n{'─' * 70}")
            print(f"[{tc['id']}] {tc['categoria']} | Persona: {tc['persona']}")
            print(f"Pergunta: {tc['pergunta'][:80]}...")

        result = agent.chat(tc["pergunta"], session_id=f"test_{tc['id']}")

        if verbose:
            print(f"Resposta: {result['response'][:200]}...")
            print(f"Latência: {result['latency_ms']:.0f}ms | Tokens: ~{result['input_tokens']}→~{result['output_tokens']}")

        results.append({
            **tc,
            "resposta": result["response"],
            "latency_ms": result["latency_ms"],
            "input_tokens": result["input_tokens"],
            "output_tokens": result["output_tokens"],
            "blocked": result["blocked"],
            "model": model_name,
        })

    return results


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    print(f"\n{'=' * 70}")
    print(f"  TESTES FUNCIONAIS — Modelo: {model}")
    print(f"{'=' * 70}")
    results = run_functional_tests(model)
    print(f"\n\nTotal: {len(results)} testes executados.")
