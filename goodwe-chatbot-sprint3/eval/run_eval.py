"""
Pipeline de avaliação — Sprint 4 (GoodWe EV ChargeOps Assistant)

Executa o golden dataset contra uma ou mais versões do agente, julga cada resposta
com um LLM juiz + checagens determinísticas e gera as tabelas de resultado.

Uso (a partir da raiz do projeto):
    python eval/run_eval.py --tudo                  # TUDO o que a entrega precisa (V1, V2, Sprint 3 gravada, consistência)
    python eval/run_eval.py                         # V1 e V2 no dataset inteiro
    python eval/run_eval.py --versoes v1_sprint2 v2_sprint3 v3_sprint3_compound
    python eval/run_eval.py --sprint3-gravado       # julga as respostas gravadas na Sprint 3 (p/ comparar c/ a avaliação manual)
    python eval/run_eval.py --consistencia 8        # rejulga 8 casos para medir a estabilidade do juiz
    python eval/run_eval.py --resumo                # só recalcula as tabelas, sem chamar a API
    python eval/run_eval.py --casos F06 M02 S03     # roda só alguns casos
    python eval/run_eval.py --fake                  # testa o pipeline sem API (resultados falsos em results_fake/)

O progresso é salvo caso a caso em results/execucoes/*.jsonl. Se a API do Groq
atingir o limite diário, o script para e, ao rodar de novo, continua de onde parou.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import random
import sys
import time
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from common import (MANUAL_PATH, SPRINT3_RAW_PATH, DailyLimitReached, load_dataset,  # noqa: E402
                    results_dir, with_retry)
from metrics import (CATEGORIAS, NOMES_CATEGORIAS, aggregate, manual_says_pass,  # noqa: E402
                     run_checks, score_case)
from versions import DEFAULT_VERSIONS, VERSIONS, build_agent  # noqa: E402

S3_MODELS = ["gpt-oss-120b", "compound-mini"]


# ── Persistência ────────────────────────────────────────────────────────────

def _jsonl_path(rdir: str, version_id: str) -> str:
    return os.path.join(rdir, "execucoes", f"{version_id}.jsonl")


def load_records(rdir: str, version_id: str) -> dict:
    path = _jsonl_path(rdir, version_id)
    recs = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    recs[r["id"]] = r  # a última linha de cada caso vale
    return recs


def append_record(rdir: str, version_id: str, rec: dict):
    with open(_jsonl_path(rdir, version_id), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ── Execução do agente e do juiz ────────────────────────────────────────────

def run_agent_on_case(agent, caso: dict) -> list[dict]:
    """Envia todos os turnos do caso. Cada letra de sessão vira um thread_id novo."""
    run_tag = uuid.uuid4().hex[:8]
    out = []
    for t in caso["turnos"]:
        sid = f"eval_{caso['id']}_{t['sessao']}_{run_tag}"
        r = with_retry(agent.chat, t["mensagem"], session_id=sid)
        out.append({"sessao": t["sessao"], "mensagem": t["mensagem"], "resposta": r["response"],
                    "latency_ms": r.get("latency_ms", 0.0), "blocked": bool(r.get("blocked")),
                    "input_tokens": r.get("input_tokens", 0), "output_tokens": r.get("output_tokens", 0)})
    return out


def judge_record(judge, caso: dict, rec: dict) -> dict:
    resposta = rec["resposta_final"]
    rec["checks"] = run_checks(caso, resposta)
    rec["juiz"] = judge.evaluate(caso, resposta)
    rec["metricas"] = score_case(caso, rec["juiz"], rec["checks"])
    return rec


def _judge_sleep():
    time.sleep(float(os.getenv("EVAL_JUDGE_SLEEP_S", "6")))


def run_version(version_id: str, casos: list[dict], judge, rdir: str, fake: bool, refazer: bool):
    print(f"\n{'█' * 70}\n  VERSÃO: {VERSIONS[version_id]['nome']}\n{'█' * 70}")
    done = {} if refazer else load_records(rdir, version_id)
    agent = None
    for i, caso in enumerate(casos, 1):
        prev = done.get(caso["id"])
        if prev and prev.get("juiz"):
            print(f"[{i:02d}/{len(casos)}] {caso['id']} ✔ já avaliado (pulando)")
            continue
        print(f"[{i:02d}/{len(casos)}] {caso['id']} — {caso['subcategoria']}")
        try:
            if prev and prev.get("resposta_final"):
                rec = prev  # agente já respondeu; falta só o juiz
            else:
                if agent is None:
                    agent = build_agent(version_id, fake=fake)
                turnos = run_agent_on_case(agent, caso)
                rec = {"id": caso["id"], "versao": version_id, "timestamp": datetime.now().isoformat(timespec="seconds"),
                       "turnos_resp": turnos, "resposta_final": turnos[-1]["resposta"]}
                append_record(rdir, version_id, rec)  # salva antes do juiz (não perde a chamada)
            rec = judge_record(judge, caso, rec)
        except DailyLimitReached:
            raise
        except Exception as e:  # noqa: BLE001 — um caso com erro não derruba a execução inteira
            print(f"      ❌ erro neste caso ({type(e).__name__}: {str(e)[:200]}) — será refeito na próxima execução")
            continue
        append_record(rdir, version_id, rec)
        m, j = rec["metricas"], rec["juiz"]
        print(f"      score {m['score']:5.1f} | corr {j['correcao']} esc {j['aderencia_escopo']} fid {j['fidelidade']}"
              f" | recusou={j['recusou']} | checks={'ok' if rec['checks']['ok'] else 'FALHA'}"
              f" | {'APROVADO' if m['aprovado'] else 'reprovado'}")
        if not fake:
            _judge_sleep()


def run_sprint3_recorded(casos_por_id: dict, judge, rdir: str, fake: bool, refazer: bool):
    """Julga as respostas que o grupo avaliou manualmente na Sprint 3 (mesmas respostas)."""
    with open(SPRINT3_RAW_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    for model in S3_MODELS:
        vid = f"s3_gravado_{model}"
        print(f"\n{'█' * 70}\n  RESPOSTAS GRAVADAS NA SPRINT 3 — {model}\n{'█' * 70}")
        done = {} if refazer else load_records(rdir, vid)
        items = []
        for r in raw[model]["functional"]:
            items.append((r["id"], r["resposta"], r["latency_ms"], r.get("blocked", False)))
        for r in raw[model]["memory"]:
            resp = r.get("resposta_final") or r.get("resposta_sessao_b", "")
            items.append((r["id"], resp, r.get("latencia_media_ms", 0.0), False))
        for r in raw[model]["security"]:
            items.append((r["id"], r["resposta"], r.get("latency_ms", 0.0), r.get("blocked_by_guardrail", False)))
        for cid, resp, lat, blocked in items:
            if cid not in casos_por_id:
                continue
            if done.get(cid, {}).get("juiz"):
                print(f"  {cid} ✔ já avaliado (pulando)")
                continue
            rec = {"id": cid, "versao": vid, "fonte": "docs/resultados_brutos.json",
                   "turnos_resp": [{"resposta": resp, "latency_ms": lat, "blocked": blocked}],
                   "resposta_final": resp}
            try:
                rec = judge_record(judge, casos_por_id[cid], rec)
            except DailyLimitReached:
                raise
            except Exception as e:  # noqa: BLE001
                print(f"  {cid} ❌ erro no juiz ({type(e).__name__}: {str(e)[:200]}) — será refeito na próxima execução")
                continue
            append_record(rdir, vid, rec)
            print(f"  {cid} score {rec['metricas']['score']:5.1f} | {'APROVADO' if rec['metricas']['aprovado'] else 'reprovado'}")
            if not fake:
                _judge_sleep()


def run_consistency(version_id: str, n: int, casos_por_id: dict, judge, rdir: str, fake: bool):
    """Rejulga n respostas já julgadas e mede a concordância do juiz consigo mesmo."""
    recs = [r for r in load_records(rdir, version_id).values() if r.get("juiz")]
    if not recs:
        print(f"Sem resultados de {version_id} para medir consistência.")
        return
    amostra = random.Random(42).sample(recs, min(n, len(recs)))
    linhas = []
    for r in amostra:
        novo = judge.evaluate(casos_por_id[r["id"]], r["resposta_final"])
        linhas.append({"id": r["id"], "correcao_1": r["juiz"]["correcao"], "correcao_2": novo["correcao"],
                       "fidelidade_1": r["juiz"]["fidelidade"], "fidelidade_2": novo["fidelidade"],
                       "recusou_1": r["juiz"]["recusou"], "recusou_2": novo["recusou"]})
        print(f"  {r['id']}: correção {r['juiz']['correcao']}→{novo['correcao']} | "
              f"fidelidade {r['juiz']['fidelidade']}→{novo['fidelidade']} | recusou {r['juiz']['recusou']}→{novo['recusou']}")
        if not fake:
            _judge_sleep()
    k = len(linhas)
    res = {
        "versao": version_id, "n": k,
        "correcao_igual": round(100 * sum(l["correcao_1"] == l["correcao_2"] for l in linhas) / k, 1),
        "correcao_ate_1_ponto": round(100 * sum(abs(l["correcao_1"] - l["correcao_2"]) <= 1 for l in linhas) / k, 1),
        "fidelidade_igual": round(100 * sum(l["fidelidade_1"] == l["fidelidade_2"] for l in linhas) / k, 1),
        "recusa_igual": round(100 * sum(l["recusou_1"] == l["recusou_2"] for l in linhas) / k, 1),
        "detalhes": linhas,
    }
    with open(os.path.join(rdir, "consistencia_juiz.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(f"\nConsistência do juiz ({k} casos): correção idêntica {res['correcao_igual']}% | "
          f"±1 ponto {res['correcao_ate_1_ponto']}% | decisão de recusa idêntica {res['recusa_igual']}%")


# ── Resumos e tabelas ───────────────────────────────────────────────────────

def _version_label(vid: str) -> str:
    if vid in VERSIONS:
        return VERSIONS[vid]["curto"]
    if vid.startswith("s3_gravado_"):
        return f"S3 gravado ({vid.removeprefix('s3_gravado_')})"
    return vid


def build_summaries(rdir: str, casos_por_id: dict, judge_model: str):
    versions = sorted(os.path.basename(p)[:-6] for p in glob.glob(os.path.join(rdir, "execucoes", "*.jsonl")))
    all_recs = {v: load_records(rdir, v) for v in versions}
    live = [v for v in versions if not v.startswith("s3_gravado_")]
    from collections import Counter
    juizes = Counter(r["juiz"].get("modelo_juiz") for recs in all_recs.values() for r in recs.values()
                     if r.get("juiz") and r["juiz"].get("modelo_juiz"))
    if juizes:
        judge_model = ", ".join(m for m, _ in juizes.most_common())
    resumo = {"gerado_em": datetime.now().isoformat(timespec="seconds"), "modelo_juiz": judge_model,
              "n_casos_dataset": len(casos_por_id), "versoes": {}, "ranking": []}
    for v in versions:
        agg = aggregate(list(all_recs[v].values()), casos_por_id)
        if agg:
            agg["nome"] = VERSIONS[v]["nome"] if v in VERSIONS else _version_label(v)
            agg["descricao"] = VERSIONS[v]["descricao"] if v in VERSIONS else "Respostas gravadas na Sprint 3 (docs/resultados_brutos.json), rejulgadas pelo pipeline."
            resumo["versoes"][v] = agg

    comparaveis = [v for v in live if v in resumo["versoes"]]
    resumo["ranking"] = sorted(
        comparaveis,
        key=lambda v: (-resumo["versoes"][v]["nota_final"], -resumo["versoes"][v]["taxa_aprovacao"],
                       resumo["versoes"][v]["recusa_indevida"] or 0))
    incompletas = [v for v in comparaveis if resumo["versoes"][v]["n_casos"] < len(casos_por_id)]
    resumo["versoes_incompletas"] = incompletas

    with open(os.path.join(rdir, "resumo_versoes.json"), "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)

    # CSV caso a caso (todas as versões)
    with open(os.path.join(rdir, "resultados_por_caso.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["versao", "caso", "categoria", "decisao_esperada", "correcao", "aderencia_escopo", "fidelidade",
                    "recusou", "decisao_ok", "checks_ok", "falhas_checks", "score", "aprovado", "bloqueado_guardrail",
                    "justificativa_juiz", "resposta_final"])
        for v in versions:
            for cid in casos_por_id:
                r = all_recs[v].get(cid)
                if not r or not r.get("juiz"):
                    continue
                c, j, m = casos_por_id[cid], r["juiz"], r["metricas"]
                w.writerow([v, cid, c["categoria"], c["decisao_esperada"], j["correcao"], j["aderencia_escopo"],
                            j["fidelidade"], j["recusou"], m["decisao_ok"], r["checks"]["ok"],
                            " | ".join(r["checks"]["falhas"]), m["score"], m["aprovado"],
                            any(t.get("blocked") for t in r.get("turnos_resp", [])), j["justificativa"],
                            r["resposta_final"].replace("\n", " ")[:1500]])

    # Tabela Markdown (versões ao vivo)
    if comparaveis:
        md = _markdown_table(resumo, comparaveis, casos_por_id)
        with open(os.path.join(rdir, "tabela_versoes.md"), "w", encoding="utf-8") as f:
            f.write(md)

    comp = build_manual_comparison(all_recs, casos_por_id, rdir)
    print(f"\n✅ Resumos gerados em {rdir}/ (resumo_versoes.json, resultados_por_caso.csv, tabela_versoes.md"
          f"{', comparacao_manual.json' if comp else ''})")
    if incompletas:
        print(f"⚠️  Versões com casos faltando: {incompletas} — rode de novo para completar antes de gerar o relatório.")
    return resumo


METRIC_ROWS = [
    ("nota_final", "NOTA FINAL (0–100)", "{:.1f}"),
    ("taxa_aprovacao", "Taxa de aprovação (%)", "{:.1f}"),
    ("correcao_media", "Correção média (1–5)", "{:.2f}"),
    ("escopo_medio", "Aderência ao escopo (1–5)", "{:.2f}"),
    ("fidelidade_media", "Fidelidade / não-alucinação (1–5)", "{:.2f}"),
    ("recusa_correta", "Recusa correta — casos 'recusar' (%)", "{:.1f}"),
    ("recusa_indevida", "Recusa indevida — casos 'responder' (%) ↓", "{:.1f}"),
    ("checks_ok", "Checagens determinísticas OK (%)", "{:.1f}"),
    ("bloqueios_guardrail", "Casos bloqueados pelo guardrail", "{}"),
    ("latencia_media_ms", "Latência média da LLM (ms) ↓", "{:.0f}"),
]


def fmt(v, f):
    return "—" if v is None else f.format(v)


def _markdown_table(resumo, versions, casos_por_id) -> str:
    vs = resumo["versoes"]
    head = "| Métrica | " + " | ".join(_version_label(v) for v in versions) + " |"
    sep = "|---|" + "---|" * len(versions)
    rows = [head, sep]
    for key, label, f in METRIC_ROWS:
        rows.append(f"| {label} | " + " | ".join(fmt(vs[v].get(key), f) for v in versions) + " |")
    for cat in CATEGORIAS:
        rows.append(f"| Score — {NOMES_CATEGORIAS[cat]} | " + " | ".join(
            fmt(vs[v]["por_categoria"].get(cat, {}).get("score"), "{:.1f}") for v in versions) + " |")
    rank = " > ".join(_version_label(v) for v in resumo["ranking"])
    return (f"# Resultados por versão — Sprint 4\n\nJuiz: `{resumo['modelo_juiz']}` · "
            f"{len(casos_por_id)} casos no golden dataset\n\n" + "\n".join(rows) + f"\n\n**Classificação:** {rank}\n")


def build_manual_comparison(all_recs: dict, casos_por_id: dict, rdir: str):
    if not os.path.exists(MANUAL_PATH):
        return None
    with open(MANUAL_PATH, encoding="utf-8") as f:
        manual = json.load(f)["modelos"]
    linhas = []
    for model in S3_MODELS:
        recs = all_recs.get(f"s3_gravado_{model}", {})
        for cid, mv in manual.get(model, {}).items():
            r = recs.get(cid)
            if not r or not r.get("juiz"):
                continue
            mp = manual_says_pass(mv["veredito"])
            pp = r["metricas"]["aprovado"]
            linhas.append({"modelo": model, "caso": cid, "categoria": casos_por_id[cid]["categoria"],
                           "manual": mv["veredito"], "fonte_manual": mv["fonte"], "manual_aprovado": mp,
                           "pipeline_aprovado": pp, "pipeline_score": r["metricas"]["score"],
                           "correcao": r["juiz"]["correcao"], "fidelidade": r["juiz"]["fidelidade"],
                           "recusou": r["juiz"]["recusou"], "checks_falhas": r["checks"]["falhas"],
                           "concorda": mp == pp, "justificativa_juiz": r["juiz"]["justificativa"]})
    if not linhas:
        return None
    por_cat = {}
    for l in linhas:
        c = por_cat.setdefault(l["categoria"], [0, 0])
        c[0] += l["concorda"]
        c[1] += 1
    comp = {
        "n": len(linhas),
        "concordancia_pct": round(100 * sum(l["concorda"] for l in linhas) / len(linhas), 1),
        "manual_aprovados": sum(l["manual_aprovado"] for l in linhas),
        "pipeline_aprovados": sum(l["pipeline_aprovado"] for l in linhas),
        "concordancia_por_categoria": {k: round(100 * a / b, 1) for k, (a, b) in por_cat.items()},
        "divergencias": [l for l in linhas if not l["concorda"]],
        "linhas": linhas,
    }
    with open(os.path.join(rdir, "comparacao_manual.json"), "w", encoding="utf-8") as f:
        json.dump(comp, f, ensure_ascii=False, indent=2)
    return comp


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    from config import JUDGE_MODEL

    ap = argparse.ArgumentParser(description="Pipeline de avaliação — Sprint 4")
    ap.add_argument("--tudo", action="store_true",
                    help="roda tudo para a entrega: V1 + V2, respostas gravadas da Sprint 3 e consistência do juiz (8 casos)")
    ap.add_argument("--versoes", nargs="+", choices=list(VERSIONS), help="versões a avaliar")
    ap.add_argument("--casos", nargs="+", help="IDs de casos específicos (padrão: todos)")
    ap.add_argument("--sprint3-gravado", action="store_true", help="julga as respostas gravadas da Sprint 3")
    ap.add_argument("--consistencia", type=int, metavar="N", help="rejulga N casos da 1ª versão para medir o juiz")
    ap.add_argument("--resumo", action="store_true", help="só recalcula as tabelas a partir do que já foi salvo")
    ap.add_argument("--refazer", action="store_true", help="ignora resultados salvos e refaz")
    ap.add_argument("--fake", action="store_true", help="agente e juiz falsos (teste do pipeline, sem API)")
    args = ap.parse_args()
    if args.tudo:
        args.versoes = args.versoes or list(DEFAULT_VERSIONS)
        args.sprint3_gravado = True
        args.consistencia = args.consistencia or 8

    if not args.fake and not args.resumo and not os.getenv("GROQ_API_KEY"):
        sys.exit("❌ GROQ_API_KEY não encontrada. Coloque a chave no arquivo .env (ele está no .gitignore).")

    ds = load_dataset()
    casos = ds["casos"]
    if args.casos:
        casos = [c for c in casos if c["id"] in set(args.casos)]
    casos_por_id = {c["id"]: c for c in ds["casos"]}
    rdir = results_dir(fake=args.fake)
    judge_model = "fake-judge" if args.fake else JUDGE_MODEL

    explicit_task = args.versoes or args.sprint3_gravado or args.consistencia
    try:
        if not args.resumo:
            from judge import build_judge
            judge = build_judge(JUDGE_MODEL, fake=args.fake)
            versoes = args.versoes or ([] if explicit_task else DEFAULT_VERSIONS)
            for v in versoes:
                run_version(v, casos, judge, rdir, args.fake, args.refazer)
            if args.sprint3_gravado:
                run_sprint3_recorded(casos_por_id, judge, rdir, args.fake, args.refazer)
            if args.consistencia:
                alvo = (args.versoes or DEFAULT_VERSIONS)[-1]
                run_consistency(alvo, args.consistencia, casos_por_id, judge, rdir, args.fake)
    except DailyLimitReached as e:
        print(f"\n⛔ Limite diário da API do Groq atingido.\n   {str(e)[:300]}\n"
              "   O progresso foi salvo. Rode o MESMO comando de novo mais tarde para continuar.")
    except KeyboardInterrupt:
        print("\n⏸  Interrompido. O progresso foi salvo; rode de novo para continuar.")

    build_summaries(rdir, casos_por_id, judge_model)


if __name__ == "__main__":
    main()
