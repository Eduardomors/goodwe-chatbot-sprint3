"""
Configurações centralizadas — modelos, parâmetros e constantes.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


@dataclass
class ModelConfig:
    provider: str
    model_name: str
    temperature: float = 0.4
    max_tokens: int = 1024


MODELS = {
    "gpt-oss-120b": ModelConfig(
        provider="groq",
        model_name="openai/gpt-oss-120b",
        temperature=0.4,
        max_tokens=1024,
    ),
    "compound-mini": ModelConfig(
        provider="groq",
        model_name="groq/compound-mini",
        temperature=0.4,
        max_tokens=1024,
    ),
}

DEFAULT_MODEL = "gpt-oss-120b"


def get_system_prompt() -> str:
    prompt_path = os.path.join(
        os.path.dirname(__file__), "..", "prompts", "system_prompt.txt"
    )
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()