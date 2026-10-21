"""
Baseline Sprint 2 — reprodução da arquitetura da Sprint 2 para a avaliação da Sprint 4.

Como era a Sprint 2:
  - chamada direta à LLM (sem framework de agentes)
  - system prompt da Sprint 1 + 3 exemplos few-shot
  - histórico de conversa numa lista Python por sessão
  - SEM guardrails de entrada/saída
  - temperature 0.4, max_tokens 1024

Diferença inevitável: a Sprint 2 usava gpt-4o-mini (OpenAI). Como o grupo migrou
para o Groq na Sprint 3, aqui o baseline roda no MESMO modelo da versão final
(gpt-oss-120b). Assim, a comparação V1 x V2 isola o efeito da arquitetura
(LangGraph + guardrails + prompt evoluído), e não o efeito de trocar de modelo.

A interface (`chat` / `reset_session`) é igual à do GoodWeAgent da Sprint 3,
para o pipeline de avaliação tratar as duas versões do mesmo jeito.
"""

from __future__ import annotations

import os
import time

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from config import MODELS

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "system_prompt_sprint2.txt")


class Sprint2Chatbot:
    def __init__(self, model_name: str = "gpt-oss-120b"):
        self.model_name = model_name
        cfg = MODELS[model_name]
        self.llm = ChatGroq(model=cfg.model_name, temperature=cfg.temperature, max_tokens=cfg.max_tokens)
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()
        self.histories: dict[str, list] = {}

    def chat(self, user_message: str, session_id: str = "default") -> dict:
        history = self.histories.setdefault(session_id, [])
        history.append(HumanMessage(content=user_message))
        messages = [SystemMessage(content=self.system_prompt)] + history

        time.sleep(float(os.getenv("AGENT_SLEEP_S", "15")))
        start = time.time()
        response = self.llm.invoke(messages)
        latency = (time.time() - start) * 1000

        history.append(AIMessage(content=response.content))
        input_text = self.system_prompt + " ".join(m.content for m in history[:-1])
        return {
            "response": response.content,
            "latency_ms": round(latency, 1),
            "input_tokens": len(input_text) // 4,
            "output_tokens": len(response.content) // 4,
            "blocked": False,  # não existe guardrail nesta versão
        }

    def reset_session(self, session_id: str | None = None):
        if session_id is None:
            self.histories = {}
        else:
            self.histories.pop(session_id, None)
