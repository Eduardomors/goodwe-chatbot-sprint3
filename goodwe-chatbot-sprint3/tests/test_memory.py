"""
Testes de Memória — Sprint 3
Valida que o agente mantém contexto entre turnos da mesma sessão.
Cada cenário possui 3+ turnos de interação.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agent import GoodWeAgent
from config import DEFAULT_MODEL


MEMORY_TESTS = [
    {
        "id": "M01",
        "descricao": "Recuperar nome do condomínio e número de vagas mencionados antes",
        "turnos": [
            "Estou utilizando um carregador no condomínio Solar Park.",
            "Existem 12 vagas de carregamento no total.",
            "Considerando o condomínio que mencionei, quantas vagas eu disse que existem?",
        ],
        "criterios_ultimo_turno": [
            "Menciona 'Solar Park'",
            "Menciona '12 vagas'",
        ],
    },
    {
        "id": "M02",
        "descricao": "Lembrar tarifa e calcular com ela em turno posterior",
        "turnos": [
            "A tarifa de energia no meu condomínio é R$ 1,10 por kWh.",
            "Carreguei meu carro ontem e consumiu 25 kWh.",
            "Com base na tarifa que informei, quanto gastei na recarga de ontem?",
        ],
        "criterios_ultimo_turno": [
            "Usa tarifa R$ 1,10",
            "Calcula 25 × 1,10 = R$ 27,50",
        ],
    },
    {
        "id": "M03",
        "descricao": "Lembrar modelo do carregador e persona ao longo da conversa",
        "turnos": [
            "Sou o síndico do Residencial Flores e temos 3 carregadores GoodWe de 7,4 kW cada.",
            "Qual a potência total que esses carregadores demandam se usados simultaneamente?",
            "Se eu adicionar mais 2 carregadores iguais, qual seria a nova potência total?",
            "Resuma tudo que conversamos até agora.",
        ],
        "criterios_ultimo_turno": [
            "Menciona 'Residencial Flores'",
            "Menciona 'síndico'",
            "Menciona 7,4 kW por carregador",
            "Menciona 5 carregadores no total",
        ],
    },
    {
        "id": "M04",
        "descricao": "Sessões diferentes NÃO compartilham memória",
        "tipo": "isolamento",
        "sessao_1": [
            ("Meu condomínio é o Villa Nova.", "sessao_A"),
        ],
        "sessao_2": [
            ("Qual é o nome do meu condomínio?", "sessao_B"),
        ],
        "criterio": "Na sessão B, o agente NÃO deve saber o nome 'Villa Nova'",
    },
]


def run_memory_tests(model_name: str = DEFAULT_MODEL, verbose: bool = True):
    """Executa testes de memória e retorna resultados."""
    agent = GoodWeAgent(model_name=model_name)
    results = []

    for tc in MEMORY_TESTS:
        if verbose:
            print(f"\n{'═' * 70}")
            print(f"[{tc['id']}] {tc['descricao']}")
            print(f"{'═' * 70}")

        if tc.get("tipo") == "isolamento":
            # Teste de isolamento entre sessões
            agent.reset_session()

            for msg, sid in tc["sessao_1"]:
                r = agent.chat(msg, session_id=sid)
                if verbose:
                    print(f"  [Sessão A] User: {msg}")
                    print(f"  [Sessão A] Bot:  {r['response'][:120]}...")

            for msg, sid in tc["sessao_2"]:
                r = agent.chat(msg, session_id=sid)
                if verbose:
                    print(f"  [Sessão B] User: {msg}")
                    print(f"  [Sessão B] Bot:  {r['response'][:120]}...")

            results.append({
                "id": tc["id"],
                "descricao": tc["descricao"],
                "tipo": "isolamento",
                "resposta_sessao_b": r["response"],
                "criterio": tc["criterio"],
                "model": model_name,
            })
        else:
            # Teste de memória multi-turno (mesma sessão)
            session_id = f"mem_{tc['id']}"
            all_responses = []

            for i, msg in enumerate(tc["turnos"]):
                r = agent.chat(msg, session_id=session_id)
                all_responses.append(r)
                if verbose:
                    label = "→ TURNO FINAL" if i == len(tc["turnos"]) - 1 else f"  Turno {i+1}"
                    print(f"  {label}")
                    print(f"    User: {msg}")
                    print(f"    Bot:  {r['response'][:150]}...")
                    print(f"    ({r['latency_ms']:.0f}ms)")

            results.append({
                "id": tc["id"],
                "descricao": tc["descricao"],
                "tipo": "memoria",
                "turnos": len(tc["turnos"]),
                "resposta_final": all_responses[-1]["response"],
                "criterios": tc["criterios_ultimo_turno"],
                "latencia_media_ms": sum(r["latency_ms"] for r in all_responses) / len(all_responses),
                "model": model_name,
            })

    return results


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    print(f"\n{'=' * 70}")
    print(f"  TESTES DE MEMÓRIA — Modelo: {model}")
    print(f"{'=' * 70}")
    results = run_memory_tests(model)
    print(f"\n\nTotal: {len(results)} cenários de memória executados.")
