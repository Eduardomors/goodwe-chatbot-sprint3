"""
GoodWe EV ChargeOps Assistant — Interface Terminal (Sprint 3)
Utiliza o agente LangGraph com memória por sessão e guardrails.
"""

import sys
import uuid

from agent import GoodWeAgent
from config import DEFAULT_MODEL, MODELS

BANNER = """
╔═══════════════════════════════════════════════════════════════════╗
║         GoodWe EV ChargeOps Assistant — Sprint 3                 ║
║         EV Challenge 2026 | Powered by LangGraph                 ║
╠═══════════════════════════════════════════════════════════════════╣
║  Comandos:                                                        ║
║   /reset   → limpa a memória da sessão                           ║
║   /model   → altera o modelo de linguagem                        ║
║   /stats   → exibe estatísticas do último turno                  ║
║   /sair    → encerra o chatbot                                   ║
╚═══════════════════════════════════════════════════════════════════╝
"""


def main():
    print(BANNER)

    model_name = DEFAULT_MODEL
    print(f"  Modelo ativo: {model_name}")
    print(f"  Modelos disponíveis: {', '.join(MODELS.keys())}")

    try:
        agent = GoodWeAgent(model_name=model_name)
    except Exception as e:
        print(f"\n❌ Erro ao inicializar agente: {e}")
        sys.exit(1)

    session_id = str(uuid.uuid4())
    last_result = None

    print(f"\n✅ Agente inicializado (sessão: {session_id[:8]}...)")
    print("   Como posso ajudar com recarga EV hoje?\n")

    while True:
        try:
            user_input = input("Você: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nEncerrando chatbot...")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd == "/sair":
            print("Até logo! 👋")
            break

        elif cmd == "/reset":
            session_id = str(uuid.uuid4())
            agent.reset_session(session_id)
            print(f"\n[Sessão resetada. Nova sessão: {session_id[:8]}...]\n")
            continue

        elif cmd == "/model":
            print(f"\nModelos disponíveis: {', '.join(MODELS.keys())}")
            choice = input("Escolha: ").strip()
            if choice in MODELS:
                model_name = choice
                agent = GoodWeAgent(model_name=model_name)
                session_id = str(uuid.uuid4())
                print(f"[Modelo alterado para: {model_name}]\n")
            else:
                print("[Modelo inválido. Mantendo o atual.]\n")
            continue

        elif cmd == "/stats":
            if last_result:
                print(f"\n[Stats do último turno]")
                print(f"  Modelo:       {model_name}")
                print(f"  Latência:     {last_result['latency_ms']:.0f} ms")
                print(f"  Tokens (in):  ~{last_result['input_tokens']}")
                print(f"  Tokens (out): ~{last_result['output_tokens']}")
                print(f"  Bloqueado:    {'Sim' if last_result['blocked'] else 'Não'}\n")
            else:
                print("\n[Nenhuma interação ainda.]\n")
            continue

        # Envia mensagem para o agente
        print("\nAssistente: ", end="", flush=True)
        try:
            last_result = agent.chat(user_input, session_id=session_id)
            print(last_result["response"])
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            last_result = None
        print()


if __name__ == "__main__":
    main()
