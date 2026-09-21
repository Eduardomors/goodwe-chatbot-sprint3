"""
Runner principal — executa TODOS os testes com TODOS os modelos configurados
e gera o relatório comparativo em Markdown.

Uso:
    python tests/run_all_tests.py
    python tests/run_all_tests.py gpt-4o-mini              # só um modelo
    python tests/run_all_tests.py gpt-4o-mini gemini-2.0-flash  # dois modelos
"""

import sys, os, json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config import MODELS, DEFAULT_MODEL
from test_functional import run_functional_tests
from test_memory import run_memory_tests
from test_security import run_security_tests


def run_all(models_to_test: list[str]):
    """Executa todos os testes para cada modelo e gera o relatório."""

    all_results = {}
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    for model_name in models_to_test:
        print(f"\n{'█' * 70}")
        print(f"  EXECUTANDO TESTES COM: {model_name}")
        print(f"{'█' * 70}")

        all_results[model_name] = {
            "functional": run_functional_tests(model_name, verbose=True),
            "memory": run_memory_tests(model_name, verbose=True),
            "security": run_security_tests(model_name, verbose=True),
        }

    # ── Salvar resultados brutos em JSON ─────────────────────────────────
    os.makedirs("docs", exist_ok=True)
    raw_path = "docs/resultados_brutos.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n✅ Resultados brutos salvos em: {raw_path}")

    # ── Gerar relatório Markdown ─────────────────────────────────────────
    generate_model_report(all_results, models_to_test, timestamp)
    print(f"✅ Relatório de modelos salvo em: docs/relatorio_modelos.md")


def generate_model_report(results: dict, models: list[str], timestamp: str):
    """Gera o relatorio_modelos.md exigido na Sprint 3."""

    lines = [
        "# Relatório de Comparação entre Modelos de Linguagem",
        f"**GoodWe EV ChargeOps Assistant — Sprint 3**",
        f"",
        f"Data de execução: {timestamp}",
        f"",
        "---",
        "",
        "## 1. Modelos avaliados",
        "",
    ]

    for m in models:
        cfg = MODELS[m]
        lines.append(f"### {m}")
        lines.append(f"- **Provider:** {cfg.provider}")
        lines.append(f"- **Temperature:** {cfg.temperature}")
        lines.append(f"- **Max tokens:** {cfg.max_tokens}")
        lines.append("")

    # ── Tabela comparativa: testes funcionais ────────────────────────────
    lines.extend([
        "---",
        "",
        "## 2. Resultados — Testes Funcionais",
        "",
        "| Teste | Categoria | " + " | ".join(f"Latência {m} (ms)" for m in models) + " |",
        "| --- | --- | " + " | ".join("---" for _ in models) + " |",
    ])

    # Agrupa por ID
    for test_id_set in _get_test_ids(results, models, "functional"):
        row_data = {}
        categoria = ""
        for m in models:
            for r in results[m]["functional"]:
                if r["id"] == test_id_set:
                    row_data[m] = r
                    categoria = r["categoria"]
                    break
        lat_cells = " | ".join(
            f"{row_data[m]['latency_ms']:.0f}" if m in row_data else "—"
            for m in models
        )
        lines.append(f"| {test_id_set} | {categoria} | {lat_cells} |")

    # ── Tabela comparativa: testes de memória ────────────────────────────
    lines.extend([
        "",
        "---",
        "",
        "## 3. Resultados — Testes de Memória",
        "",
    ])
    for m in models:
        lines.append(f"### {m}")
        lines.append("")
        for r in results[m]["memory"]:
            lines.append(f"**[{r['id']}] {r['descricao']}**")
            if r["tipo"] == "memoria":
                lines.append(f"- Turnos: {r['turnos']}")
                lines.append(f"- Latência média: {r['latencia_media_ms']:.0f} ms")
                lines.append(f"- Critérios esperados: {', '.join(r['criterios'])}")
                lines.append(f"- Resposta final (trecho): {r['resposta_final'][:200]}...")
            else:
                lines.append(f"- Critério: {r.get('criterio', '—')}")
                lines.append(f"- Resposta sessão B: {r.get('resposta_sessao_b', '—')[:200]}...")
            lines.append(f"- **Avaliação:** `[PREENCHER APÓS ANÁLISE]`")
            lines.append("")

    # ── Tabela comparativa: testes de segurança ──────────────────────────
    lines.extend([
        "---",
        "",
        "## 4. Resultados — Testes de Segurança",
        "",
        "| Teste | Categoria | " + " | ".join(f"Bloqueado ({m})" for m in models) + " | " + " | ".join(f"Avaliação ({m})" for m in models) + " |",
        "| --- | --- | " + " | ".join("---" for _ in models) + " | " + " | ".join("---" for _ in models) + " |",
    ])

    for test_id in _get_test_ids(results, models, "security"):
        row_data = {}
        categoria = ""
        for m in models:
            for r in results[m]["security"]:
                if r["id"] == test_id:
                    row_data[m] = r
                    categoria = r["categoria"]
                    break
        blocked_cells = " | ".join(
            ("✅ Guardrail" if row_data[m]["blocked_by_guardrail"] else "⚠️ LLM") if m in row_data else "—"
            for m in models
        )
        eval_cells = " | ".join("`[PREENCHER]`" for _ in models)
        lines.append(f"| {test_id} | {categoria} | {blocked_cells} | {eval_cells} |")

    # ── Métricas agregadas ───────────────────────────────────────────────
    lines.extend([
        "",
        "---",
        "",
        "## 5. Métricas Agregadas",
        "",
        "| Métrica | " + " | ".join(models) + " |",
        "| --- | " + " | ".join("---" for _ in models) + " |",
    ])

    for m in models:
        func_results = results[m]["functional"]
        avg_lat = sum(r["latency_ms"] for r in func_results) / len(func_results) if func_results else 0
        avg_in = sum(r["input_tokens"] for r in func_results) / len(func_results) if func_results else 0
        avg_out = sum(r["output_tokens"] for r in func_results) / len(func_results) if func_results else 0

        if m == models[0]:
            lines.append(f"| Latência média (funcional) | {avg_lat:.0f} ms | " + " | ".join("" for _ in models[1:]) + " |" if len(models) == 1 else "")

    # Rebuild cleaner aggregation
    lines_agg = []
    metrics = {}
    for m in models:
        fr = results[m]["functional"]
        metrics[m] = {
            "lat": sum(r["latency_ms"] for r in fr) / len(fr) if fr else 0,
            "tok_in": sum(r["input_tokens"] for r in fr) / len(fr) if fr else 0,
            "tok_out": sum(r["output_tokens"] for r in fr) / len(fr) if fr else 0,
            "sec_blocked": sum(1 for r in results[m]["security"] if r["blocked_by_guardrail"]),
            "sec_total": len(results[m]["security"]),
        }

    # Overwrite the messy lines
    lines = lines[:-3]  # remove broken attempt
    lines.extend([
        "",
        "---",
        "",
        "## 5. Métricas Agregadas",
        "",
        "| Métrica | " + " | ".join(models) + " |",
        "| --- | " + " | ".join("---" for _ in models) + " |",
        "| Latência média — funcional (ms) | " + " | ".join(f"{metrics[m]['lat']:.0f}" for m in models) + " |",
        "| Tokens entrada médio | " + " | ".join(f"~{metrics[m]['tok_in']:.0f}" for m in models) + " |",
        "| Tokens saída médio | " + " | ".join(f"~{metrics[m]['tok_out']:.0f}" for m in models) + " |",
        "| Testes segurança bloqueados pelo guardrail | " + " | ".join(f"{metrics[m]['sec_blocked']}/{metrics[m]['sec_total']}" for m in models) + " |",
    ])

    # ── Conclusão ────────────────────────────────────────────────────────
    lines.extend([
        "",
        "---",
        "",
        "## 6. Diferenças Percebidas",
        "",
        "> `[PREENCHER COM OBSERVAÇÕES DO GRUPO APÓS ANÁLISE DAS RESPOSTAS]`",
        "",
        "## 7. Vantagens e Limitações de Cada Modelo",
        "",
        "> `[PREENCHER]`",
        "",
        "## 8. Modelo Escolhido para Versão Final",
        "",
        f"**Modelo:** `{DEFAULT_MODEL}`",
        "",
        "**Justificativa:**",
        "> `[PREENCHER COM BASE NOS RESULTADOS DOS TESTES — a decisão deve ser baseada nos dados, não em preferência do grupo]`",
        "",
    ])

    with open("docs/relatorio_modelos.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _get_test_ids(results, models, category):
    """Coleta todos os IDs de teste de uma categoria."""
    ids = []
    seen = set()
    for m in models:
        for r in results[m][category]:
            if r["id"] not in seen:
                ids.append(r["id"])
                seen.add(r["id"])
    return ids


if __name__ == "__main__":
    if len(sys.argv) > 1:
        models_to_test = [m for m in sys.argv[1:] if m in MODELS]
        if not models_to_test:
            print(f"Modelos inválidos. Disponíveis: {list(MODELS.keys())}")
            sys.exit(1)
    else:
        models_to_test = list(MODELS.keys())

    print(f"\n🚀 Executando testes com: {models_to_test}\n")
    run_all(models_to_test)
