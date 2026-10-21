"""
Utilitários do pipeline de avaliação: caminhos, leitura do dataset e
tratamento de rate limit do Groq (retry com espera).
"""

from __future__ import annotations

import json
import os
import re
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

DATASET_PATH = os.path.join(ROOT, "eval", "golden_dataset.json")
MANUAL_PATH = os.path.join(ROOT, "eval", "avaliacao_manual_sprint3.json")
SPRINT3_RAW_PATH = os.path.join(ROOT, "docs", "resultados_brutos.json")


def results_dir(fake: bool = False) -> str:
    d = os.path.join(ROOT, "results_fake" if fake else "results")
    os.makedirs(os.path.join(d, "execucoes"), exist_ok=True)
    return d


def load_dataset() -> dict:
    with open(DATASET_PATH, encoding="utf-8") as f:
        return json.load(f)


class DailyLimitReached(Exception):
    """Limite diário de tokens/requisições atingido — salvar e parar."""


_WAIT_RE = re.compile(r"try again in (?:(\d+)h)?(?:(\d+)m)?(?:([\d.]+)s)?", re.I)


def _wait_seconds(msg: str) -> float | None:
    m = _WAIT_RE.search(msg)
    if not m or not any(m.groups()):
        return None
    h, mi, s = m.groups()
    return int(h or 0) * 3600 + int(mi or 0) * 60 + float(s or 0)


def with_retry(fn, *args, max_tries: int = 6, **kwargs):
    """Executa fn com retry em caso de rate limit (HTTP 429) do Groq.

    - espera o tempo que a API pedir (ou backoff exponencial);
    - se a API pedir mais de 3 minutos, é limite diário: levanta DailyLimitReached
      para o runner salvar o progresso e encerrar (basta rodar de novo depois).
    """
    delay = 10.0
    for attempt in range(1, max_tries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:  # noqa: BLE001 — o SDK levanta tipos diferentes
            msg = str(e)
            is_rate = "429" in msg or "rate limit" in msg.lower() or "rate_limit" in msg.lower()
            is_transient = is_rate or any(t in msg for t in ("503", "502", "timed out", "Connection"))
            if not is_transient or attempt == max_tries:
                raise
            wait = _wait_seconds(msg) if is_rate else None
            if wait is not None and wait > 180:
                raise DailyLimitReached(msg) from e
            wait = (wait + 2) if wait is not None else delay
            print(f"    ⏳ limite/erro temporário da API — aguardando {wait:.0f}s (tentativa {attempt}/{max_tries})")
            time.sleep(wait)
            delay = min(delay * 2, 120)
