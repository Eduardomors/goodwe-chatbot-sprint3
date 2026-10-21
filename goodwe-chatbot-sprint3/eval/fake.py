"""
Agente e juiz FALSOS, só para testar o encanamento do pipeline sem gastar API
(`python eval/run_eval.py --fake`). Os números gerados aqui NÃO são resultados
reais e vão para a pasta results_fake/, separada de results/.
"""

from __future__ import annotations

import random
import re

from common import SRC  # noqa: F401
from guardrails import run_input_guard


class FakeAgent:
    def __init__(self, version_id: str):
        self.version_id = version_id
        self.mem: dict[str, list[str]] = {}

    def chat(self, msg: str, session_id: str = "default") -> dict:
        hist = self.mem.setdefault(session_id, [])
        hist.append(msg)
        if self.version_id != "v1_sprint2":
            blocked = run_input_guard(msg)
            if blocked:
                return {"response": blocked, "latency_ms": 0.0, "input_tokens": 0, "output_tokens": 0, "blocked": True}
        nums = re.findall(r"(\d+(?:,\d+)?)\s*kWh", " ".join(hist))
        resp = "Acesse o painel em Relatórios para ver kWh e custo. Em caso de dúvida, consulte o suporte técnico."
        if nums:
            resp += f" Cálculo: {nums[-1]} kWh × tarifa."
        return {"response": resp, "latency_ms": random.uniform(900, 3000), "input_tokens": 1100,
                "output_tokens": 300, "blocked": False}


class FakeJudge:
    model_name = "fake-judge"

    def evaluate(self, caso: dict, resposta: str) -> dict:
        recusou = "foge um pouco do meu escopo" in resposta or "manter meu foco" in resposta
        r = random.Random(hash((caso["id"], resposta)) & 0xFFFF)
        return {"correcao": r.randint(2, 5), "aderencia_escopo": r.randint(3, 5), "fidelidade": r.randint(3, 5),
                "recusou": recusou, "criterios_atendidos": [True] * len(caso["criterios"]),
                "justificativa": "Avaliação FALSA gerada só para testar o pipeline.", "modelo_juiz": self.model_name}
