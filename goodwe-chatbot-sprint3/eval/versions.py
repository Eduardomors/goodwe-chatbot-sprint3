"""
Versões do agente avaliadas pelo pipeline.

Todas expõem a mesma interface: chat(mensagem, session_id) -> dict com
response, latency_ms, input_tokens, output_tokens, blocked.
"""

from __future__ import annotations

from common import SRC  # noqa: F401 — garante src/ no sys.path

VERSIONS = {
    "v1_sprint2": {
        "nome": "V1 — Sprint 2 (prompt + histórico, sem framework)",
        "curto": "V1 Sprint 2",
        "descricao": "Chamada direta à LLM com o system prompt da Sprint 1/2 + few-shot e histórico em lista. "
                     "Sem LangGraph e sem guardrails. Modelo gpt-oss-120b (mesmo da V2, para isolar a arquitetura).",
        "modelo": "gpt-oss-120b",
    },
    "v2_sprint3": {
        "nome": "V2 — Sprint 3 (LangGraph + guardrails, gpt-oss-120b)",
        "curto": "V2 Sprint 3",
        "descricao": "Versão final da Sprint 3: StateGraph com input_guard → agent → output_guard, "
                     "MemorySaver por sessão, system prompt evoluído. Modelo gpt-oss-120b.",
        "modelo": "gpt-oss-120b",
    },
    "v3_sprint3_compound": {
        "nome": "V3 — Sprint 3 com compound-mini (variação)",
        "curto": "V3 compound-mini",
        "descricao": "Mesmo grafo da V2, trocando o modelo para groq/compound-mini (a alternativa testada na Sprint 3).",
        "modelo": "compound-mini",
    },
}

DEFAULT_VERSIONS = ["v1_sprint2", "v2_sprint3"]


def build_agent(version_id: str, fake: bool = False):
    if fake:
        from fake import FakeAgent
        return FakeAgent(version_id)
    if version_id == "v1_sprint2":
        from baseline_sprint2 import Sprint2Chatbot
        return Sprint2Chatbot(model_name=VERSIONS[version_id]["modelo"])
    from agent import GoodWeAgent
    return GoodWeAgent(model_name=VERSIONS[version_id]["modelo"])
