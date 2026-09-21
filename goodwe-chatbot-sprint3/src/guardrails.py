"""
Guardrails — verificações de segurança executadas ANTES e DEPOIS da LLM.

Nó de entrada (input_guard):
  - Detecta prompt injection e jailbreak
  - Detecta perguntas fora do escopo

Nó de saída (output_guard):
  - Verifica se a resposta vazou o system prompt
  - Verifica se a resposta contém conteúdo fora do escopo
"""

import re

# ── Padrões de prompt injection / jailbreak ──────────────────────────────────

INJECTION_PATTERNS = [
    r"ignore\s+(todas\s+)?(as\s+)?(suas\s+)?instru[çc][õo]es",
    r"ignore\s+(all\s+)?(your\s+)?(previous\s+)?instructions",
    r"revele\s+(seu\s+)?system\s*prompt",
    r"reveal\s+(your\s+)?system\s*prompt",
    r"mostre\s+(seu\s+)?prompt\s+(de\s+)?sistema",
    r"esque[çc]a\s+(tudo|todas)",
    r"forget\s+(everything|all)",
    r"voc[eê]\s+agora\s+[ée]\s+",
    r"you\s+are\s+now\s+",
    r"aja\s+como\s+(se\s+fosse\s+)?",
    r"act\s+as\s+(if\s+)?(you\s+were\s+)?",
    r"(fa[çc]a\s+de\s+conta|finja)\s+que",
    r"pretend\s+(that\s+)?you",
    r"jailbreak",
    r"dan\s*mode",
    r"developer\s*mode",
    r"modo\s+desenvolvedor",
    r"n[aã]o\s+h[aá]\s+restri[çc][õo]es",
    r"sem\s+restri[çc][õo]es",
    r"responda\s+qualquer\s+(coisa|pergunta)",
]

# ── Palavras-chave fora do escopo ────────────────────────────────────────────

OFF_TOPIC_KEYWORDS = [
    "receita de bolo", "futebol", "novela", "horóscopo", "previsão do tempo",
    "bitcoin", "criptomoeda", "ações da bolsa", "investimento em",
    "piada", "conte uma história", "escreva um poema",
]

# ── Mensagens de bloqueio ────────────────────────────────────────────────────

INJECTION_BLOCK_MSG = (
    "Entendo sua mensagem, mas preciso manter meu foco no que faço de melhor: "
    "auxiliar na gestão de eletropostos e recarga de veículos elétricos em "
    "condomínios com carregadores GoodWe. 😊\n\n"
    "Como posso ajudar com recarga EV hoje?"
)

OFF_TOPIC_BLOCK_MSG = (
    "Essa pergunta foge um pouco do meu escopo! Sou especializado em recarga "
    "de veículos elétricos e gestão de eletropostos GoodWe em condomínios.\n\n"
    "Posso ajudar com agendamento de recarga, consumo, relatórios, "
    "diagnóstico de falhas ou regras do condomínio. O que precisa?"
)

LEAK_PATTERNS = [
    r"system\s*prompt",
    r"## SEU PAPEL",
    r"## REGRAS DE SEGURANÇA",
    r"COMPORTAMENTO ESPERADO",
    r"few-shot",
]


# ── Funções de verificação ───────────────────────────────────────────────────

def check_prompt_injection(user_input: str) -> bool:
    """Retorna True se detectar tentativa de prompt injection."""
    text = user_input.lower().strip()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def check_off_topic(user_input: str) -> bool:
    """Retorna True se a mensagem parecer fora do escopo."""
    text = user_input.lower().strip()
    for keyword in OFF_TOPIC_KEYWORDS:
        if keyword in text:
            return True
    return False


def check_output_leak(response: str) -> bool:
    """Retorna True se a resposta vazar conteúdo do system prompt."""
    for pattern in LEAK_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE):
            return True
    return False


def run_input_guard(user_input: str) -> str | None:
    """
    Executa guardrails de entrada.
    Retorna a mensagem de bloqueio se detectar problema, ou None se estiver ok.
    """
    if check_prompt_injection(user_input):
        return INJECTION_BLOCK_MSG
    if check_off_topic(user_input):
        return OFF_TOPIC_BLOCK_MSG
    return None


def run_output_guard(response: str) -> str:
    """
    Executa guardrails de saída.
    Se detectar vazamento do system prompt, substitui a resposta.
    """
    if check_output_leak(response):
        return (
            "Desculpe, não posso compartilhar detalhes sobre minhas instruções internas. "
            "Posso ajudar com algo relacionado à recarga de veículos elétricos?"
        )
    return response
