"""
Gera o RELATÓRIO FINAL da Sprint 4 em PDF a partir dos resultados do pipeline.

Uso (depois de rodar o pipeline):
    python eval/generate_report.py
    → docs/relatorio_final_sprint4.pdf

Todas as tabelas e números saem de results/ (resumo_versoes.json, comparacao_manual.json,
consistencia_juiz.json e results/execucoes/*.jsonl). Nada é digitado à mão.
Os textos de análise são montados a partir dos números; revisem e complementem
a seção de hipóteses se quiserem.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from common import ROOT, load_dataset, results_dir  # noqa: E402
from metrics import CATEGORIAS, NOMES_CATEGORIAS, PESOS  # noqa: E402
from run_eval import METRIC_ROWS, _version_label, fmt, load_records  # noqa: E402
from versions import VERSIONS  # noqa: E402

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,  # noqa: E402
                                Spacer, Table, TableStyle)

AZUL = colors.HexColor("#1F3A5F")
VERMELHO = colors.HexColor("#C8102E")
CINZA = colors.HexColor("#F2F4F7")
VERDE = colors.HexColor("#E3F4E8")
ROSA = colors.HexColor("#FBE4E6")

# Helvetica (fonte padrão do PDF) não tem alguns símbolos; trocamos por equivalentes.
_SUBS = {"≥": ">=", "≤": "<=", "→": "->", "↓": "", "↑": "", "✔": "sim", "✘": "não", "≈": "~", "·": "-",
         "…": "...", "÷": "/"}


def _cut(t: str, n: int) -> str:
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "..."


def s(text) -> str:
    t = "" if text is None else str(text)
    for a, b in _SUBS.items():
        t = t.replace(a, b)
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


ss = getSampleStyleSheet()
ST = {
    "title": ParagraphStyle("t", parent=ss["Title"], fontSize=20, textColor=AZUL, spaceAfter=6),
    "subtitle": ParagraphStyle("st", parent=ss["Normal"], fontSize=11, alignment=TA_CENTER, textColor=colors.grey),
    "h1": ParagraphStyle("h1", parent=ss["Heading1"], fontSize=15, textColor=AZUL, spaceBefore=10, spaceAfter=6),
    "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12, textColor=AZUL, spaceBefore=8, spaceAfter=4),
    "body": ParagraphStyle("b", parent=ss["Normal"], fontSize=9.5, leading=13.5, alignment=TA_JUSTIFY, spaceAfter=5),
    "bullet": ParagraphStyle("bl", parent=ss["Normal"], fontSize=9.5, leading=13, leftIndent=12, bulletIndent=2, spaceAfter=2),
    "cell": ParagraphStyle("c", parent=ss["Normal"], fontSize=7.8, leading=9.6),
    "cellb": ParagraphStyle("cb", parent=ss["Normal"], fontSize=7.8, leading=9.6, fontName="Helvetica-Bold"),
    "head": ParagraphStyle("hd", parent=ss["Normal"], fontSize=8, leading=10, textColor=colors.white, fontName="Helvetica-Bold"),
    "small": ParagraphStyle("sm", parent=ss["Normal"], fontSize=8, leading=10, textColor=colors.grey),
    "box": ParagraphStyle("bx", parent=ss["Normal"], fontSize=9.5, leading=13.5, backColor=CINZA, borderPadding=6, spaceAfter=8),
}


def P(text, style="body"):
    return Paragraph(text, ST[style])


def bullets(items):
    return [Paragraph(i, ST["bullet"], bulletText="•") for i in items]


def table(rows, widths, header=True, zebra=True, highlight=None):
    data = []
    for i, r in enumerate(rows):
        st = "head" if (header and i == 0) else "cell"
        data.append([c if not isinstance(c, str) else Paragraph(c, ST[st]) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#C9CED6")),
             ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), AZUL))
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), CINZA))
    for (r, c, color) in (highlight or []):
        style.append(("BACKGROUND", (c, r), (c, r), color))
    t.setStyle(TableStyle(style))
    return t


# ── Gráfico ─────────────────────────────────────────────────────────────────

def chart_categories(resumo, versions, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cats = [c for c in CATEGORIAS if any(c in resumo["versoes"][v]["por_categoria"] for v in versions)]
    palette = ["#1F3A5F", "#C8102E", "#7A8CA3", "#E3A008"]
    fig, ax = plt.subplots(figsize=(7.2, 3.0), dpi=200)
    n = len(versions)
    w = 0.8 / n
    for i, v in enumerate(versions):
        vals = [resumo["versoes"][v]["por_categoria"].get(c, {}).get("score", 0) for c in cats]
        xs = [k + (i - (n - 1) / 2) * w for k in range(len(cats))]
        bars = ax.bar(xs, vals, w * 0.92, label=_version_label(v), color=palette[i % len(palette)])
        for b, val in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, val + 1, f"{val:.0f}", ha="center", va="bottom", fontsize=6.5)
    ax.set_xticks(range(len(cats)))
    ax.set_xticklabels([NOMES_CATEGORIAS[c] for c in cats], fontsize=8)
    ax.set_ylim(0, 108)
    ax.set_ylabel("Score médio (0–100)", fontsize=8)
    ax.tick_params(axis="y", labelsize=7)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(fontsize=7, frameon=False, ncol=n, loc="upper center", bbox_to_anchor=(0.5, 1.13))
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


# ── Textos montados a partir dos dados ──────────────────────────────────────

def _blocked_legit(rdir, vid, casos_por_id):
    recs = load_records(rdir, vid)
    return [cid for cid, r in recs.items() if r.get("juiz") and casos_por_id[cid]["decisao_esperada"] == "responder"
            and any(t.get("blocked") for t in r.get("turnos_resp", []))]


def _better(a, b, key, lower_is_better=False):
    if a.get(key) is None or b.get(key) is None:
        return 0
    d = a[key] - b[key]
    return -d if lower_is_better else d


def texto_classificacao(resumo, rdir, casos_por_id):
    vs, rk = resumo["versoes"], resumo["ranking"]
    best = rk[0]
    out = [f"Pelo pipeline, a versão com melhor desempenho foi a <b>{s(VERSIONS[best]['nome'])}</b>, com nota final "
           f"<b>{vs[best]['nota_final']:.1f}</b> e taxa de aprovação de {vs[best]['taxa_aprovacao']:.1f}%."]
    for other in rk[1:]:
        a, b = vs[best], vs[other]
        ganhos, perdas = [], []
        for key, label, low in [("taxa_aprovacao", "taxa de aprovação", False), ("correcao_media", "correção", False), ("escopo_medio", "aderência ao escopo", False),
                                ("fidelidade_media", "fidelidade", False), ("recusa_correta", "recusa correta", False),
                                ("recusa_indevida", "recusa indevida", True), ("checks_ok", "checagens objetivas", False),
                                ("latencia_media_ms", "latência", True)]:
            d = _better(a, b, key, low)
            if d > 0.001:
                ganhos.append(label)
            elif d < -0.001:
                perdas.append(label)
        frase = (f"Em relação à {s(_version_label(other))} (nota {b['nota_final']:.1f}, diferença de "
                 f"{a['nota_final'] - b['nota_final']:+.1f} ponto(s)), a vencedora foi melhor em: "
                 f"{', '.join(ganhos) if ganhos else 'nenhuma métrica isolada'}")
        frase += f"; e pior em: {', '.join(perdas)}." if perdas else "."
        out.append(frase)
    if abs(vs[rk[0]]["nota_final"] - vs[rk[-1]]["nota_final"]) < 3:
        out.append("A diferença de nota entre as versões é pequena (menos de 3 pontos), então a classificação deve ser lida "
                   "junto com as métricas específicas (principalmente recusa correta e recusa indevida), e não só pela nota.")
    for v in rk:
        bl = _blocked_legit(rdir, v, casos_por_id)
        if bl:
            out.append(f"Na {s(_version_label(v))}, o guardrail de entrada bloqueou perguntas legítimas que deveriam ser "
                       f"respondidas ({', '.join(bl)}). São falsos positivos do filtro por regex (palavras-gatilho como "
                       f"\"investimento em\" e \"finja que\"), que puxam para baixo a recusa indevida e a correção dessa versão.")
    return out


def texto_evolucao(resumo):
    vs = resumo["versoes"]
    if "v1_sprint2" not in vs or "v2_sprint3" not in vs:
        return []
    a, b = vs["v1_sprint2"], vs["v2_sprint3"]
    linhas = [f"Da Sprint 2 (V1) para a Sprint 3 (V2), a nota final foi de {a['nota_final']:.1f} para {b['nota_final']:.1f} "
              f"({b['nota_final'] - a['nota_final']:+.1f}). A recusa correta em pedidos que deveriam ser recusados foi de "
              f"{fmt(a['recusa_correta'], '{:.1f}')}% para {fmt(b['recusa_correta'], '{:.1f}')}%, e a recusa indevida "
              f"(over-blocking) foi de {fmt(a['recusa_indevida'], '{:.1f}')}% para {fmt(b['recusa_indevida'], '{:.1f}')}%."]
    var = []
    for cat in CATEGORIAS:
        ca, cb = a["por_categoria"].get(cat), b["por_categoria"].get(cat)
        if ca and cb:
            var.append(f"{NOMES_CATEGORIAS[cat]} {ca['score']:.1f} -> {cb['score']:.1f} ({cb['score'] - ca['score']:+.1f})")
    if var:
        linhas.append("Variação do score por categoria (V1 -> V2): " + "; ".join(var) + ".")
    return linhas


# ── Documento ───────────────────────────────────────────────────────────────

def build(rdir, out_path, fake):
    with open(os.path.join(rdir, "resumo_versoes.json"), encoding="utf-8") as f:
        resumo = json.load(f)
    comp = None
    if os.path.exists(os.path.join(rdir, "comparacao_manual.json")):
        with open(os.path.join(rdir, "comparacao_manual.json"), encoding="utf-8") as f:
            comp = json.load(f)
    consist = None
    if os.path.exists(os.path.join(rdir, "consistencia_juiz.json")):
        with open(os.path.join(rdir, "consistencia_juiz.json"), encoding="utf-8") as f:
            consist = json.load(f)
    with open(os.path.join(ROOT, "docs", "equipe.json"), encoding="utf-8") as f:
        equipe = json.load(f)
    ds = load_dataset()
    casos = ds["casos"]
    casos_por_id = {c["id"]: c for c in casos}
    versions = [v for v in resumo["ranking"]]
    if len(versions) < 2:
        sys.exit("❌ É preciso ter pelo menos 2 versões avaliadas (results/execucoes/). Rode o pipeline antes.")
    vs = resumo["versoes"]

    story = []
    W = A4[0] - 3.4 * cm

    # Capa
    story += [Spacer(1, 2.2 * cm), P("Relatório Final — Sprint 04", "title"),
              P("Avaliação sistemática do agente GoodWe EV ChargeOps Assistant", "subtitle"), Spacer(1, 4),
              P("EV Challenge 2026 — GoodWe · Challenge Integrador · FIAP", "subtitle"), Spacer(1, 1 * cm)]
    if fake:
        story.append(P("<font color='#C8102E'><b>SIMULAÇÃO — gerado com agente e juiz FALSOS (--fake). "
                       "NÃO ENTREGAR: os números abaixo não são resultados reais.</b></font>", "box"))
    best = versions[0]
    story.append(P(
        f"<b>Resumo.</b> Construímos um golden dataset com <b>{len(casos)} casos</b> (funcionalidade, escopo, segurança, "
        f"memória e bordas), reaproveitando todos os testes das Sprints 1, 2 e 3, e um pipeline de avaliação que roda "
        f"esse dataset contra o agente e calcula as métricas automaticamente, com <b>LLM as a judge</b> "
        f"(<i>{s(resumo['modelo_juiz'])}</i>) e checagens determinísticas por regex. Avaliamos {len(versions)} versões do "
        f"agente; a melhor foi a <b>{s(VERSIONS[best]['nome'])}</b> (nota {vs[best]['nota_final']:.1f}/100). Também "
        f"rejulgamos as respostas exatas que o grupo avaliou à mão na Sprint 3 para comparar as duas avaliações"
        + (f" (concordância de <b>{comp['concordancia_pct']:.1f}%</b>)." if comp else "."), "box"))
    eq_rows = [["Integrante", "RM"]] + [[s(i["nome"]), s(i["rm"])] for i in equipe["integrantes"]]
    story += [Spacer(1, 6), table(eq_rows, [8 * cm, 3 * cm]),
              Spacer(1, 6), P(f"Turma {s(equipe['turma'])} · Repositório: {s(equipe['repositorio'])}", "small"),
              P(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} a partir de results/ (juiz: {s(resumo['modelo_juiz'])})", "small"),
              PageBreak()]

    # 1. Golden dataset
    story.append(P("1. Golden dataset", "h1"))
    story.append(P("O golden dataset (<i>eval/golden_dataset.json</i>) é o conjunto fixo de perguntas usado para medir "
                   "todas as versões do mesmo jeito. Cada caso tem: categoria, persona, os turnos da conversa, a "
                   "<b>decisão esperada</b> (responder ou recusar), um <b>gabarito</b> em texto com a resposta esperada, "
                   "os <b>critérios de aceite</b> e, quando há um valor objetivo, <b>checagens por regex</b> "
                   "(ex.: o cálculo 45 × 0,95 precisa conter \"42,75\"; a sessão B não pode conter \"Villa Nova\")."))
    story.append(P("Critérios de construção", "h2"))
    story += bullets([s(c) for c in ds["criterios_de_construcao"]])
    from collections import Counter
    cat_c = Counter(c["categoria"] for c in casos)
    dec_c = Counter((c["categoria"], c["decisao_esperada"]) for c in casos)
    reaproveitados = Counter(c["categoria"] for c in casos if not c["origem"].startswith("Nova"))
    rows = [["Categoria", "Casos", "Reaproveitados (S1–S3)", "Novos (S4)", "Esperado: responder", "Esperado: recusar"]]
    for cat in CATEGORIAS:
        rows.append([NOMES_CATEGORIAS[cat], str(cat_c[cat]), str(reaproveitados[cat]), str(cat_c[cat] - reaproveitados[cat]),
                     str(dec_c[(cat, "responder")]), str(dec_c[(cat, "recusar")])])
    rows.append(["<b>Total</b>", f"<b>{len(casos)}</b>", f"<b>{sum(reaproveitados.values())}</b>",
                 f"<b>{len(casos) - sum(reaproveitados.values())}</b>",
                 f"<b>{sum(v for (c, d), v in dec_c.items() if d == 'responder')}</b>",
                 f"<b>{sum(v for (c, d), v in dec_c.items() if d == 'recusar')}</b>"])
    story += [Spacer(1, 4), table(rows, [3.4 * cm, 1.4 * cm, 3.2 * cm, 2 * cm, 3 * cm, 3 * cm])]
    story.append(P("Os casos novos cobrem lacunas que os testes anteriores não mediam: injeção ofuscada e por tradução, "
                   "pedido de dados pessoais de outro morador, \"gambiarra\" elétrica (trocar disjuntor por um maior), "
                   "correção de informação na memória, código de erro desconhecido, entrada inválida, mensagem vaga, "
                   "pergunta em inglês e — importante — perguntas <b>legítimas</b> que contêm palavras-gatilho "
                   "(\"investimento em\", \"finja que\"), para medir se o agente recusa o que não deveria. "
                   "A lista completa com gabaritos está no Apêndice A."))

    # 2. Pipeline
    story += [P("2. Pipeline de avaliação", "h1")]
    story.append(P("O pipeline (<i>eval/run_eval.py</i>) executa, para cada versão do agente, todos os casos do golden "
                   "dataset (cada letra de sessão vira um <i>thread_id</i> novo, então casos de memória têm vários turnos "
                   "e o de isolamento usa duas sessões), guarda as respostas e as avalia de duas formas independentes:"))
    flow = [["Golden dataset\n(%d casos)" % len(casos), "»", "Versão do agente\n(V1, V2, ...)", "»",
             "Resposta final\n+ latência", "»", "LLM juiz (notas 1–5)\n+ checagens regex", "»", "Métricas por caso\ne por versão"]]
    ft = Table([[Paragraph(s(c).replace("\n", "<br/>"), ST["cellb"]) for c in flow[0]]],
               colWidths=[2.9 * cm, 0.6 * cm, 2.9 * cm, 0.6 * cm, 2.6 * cm, 0.6 * cm, 3.2 * cm, 0.6 * cm, 2.6 * cm])
    ft.setStyle(TableStyle([("BACKGROUND", (i, 0), (i, 0), CINZA) for i in (0, 2, 4, 6, 8)] +
                           [("BOX", (i, 0), (i, 0), 0.6, AZUL) for i in (0, 2, 4, 6, 8)] +
                           [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    story += [ft, Spacer(1, 6)]
    story += bullets([
        f"<b>LLM as a judge</b> (<i>eval/judge.py</i>): o modelo <i>{s(resumo['modelo_juiz'])}</i>, temperatura 0, recebe a "
        "base de conhecimento do agente, a conversa, o gabarito, os critérios e uma rubrica fixa, e devolve um JSON com "
        "notas de 1 a 5 para correção, aderência ao escopo e fidelidade, além de dizer se o agente recusou o pedido. "
        + ("Escolhemos um juiz de <b>outra família</b> que a do agente (gpt-oss) para reduzir o viés de autopreferência."  if "gpt-oss" not in resumo["modelo_juiz"] else "O juiz é da mesma família do agente (gpt-oss), único modelo disponível na conta; isso é uma limitação (ver seção 7)."),
        "<b>Checagens determinísticas</b> (<i>eval/metrics.py</i>): regex que precisam (ou não podem) aparecer na resposta — "
        "valores de cálculo, ausência de trechos do system prompt, de telefones/e-mails, de \"Villa Nova\" na sessão B etc. "
        "Não dependem de LLM e servem de âncora objetiva para o juiz.",
        "<b>Por que não DeepEval/Ragas:</b> as duas usam a OpenAI como juiz padrão (o grupo não tem billing na OpenAI desde a "
        "Sprint 3) e as métricas do Ragas (faithfulness, context recall) pressupõem um contexto recuperado por RAG, que o "
        "agente não tem. Implementamos a mesma ideia do G-Eval do DeepEval — critérios em linguagem natural + rubrica + "
        "nota numérica — diretamente no Groq, o que também deixa cada métrica transparente no código.",
        "<b>Robustez:</b> o progresso é salvo caso a caso (<i>results/execucoes/*.jsonl</i>); em limite de requisições "
        "o script espera e tenta de novo, e no limite diário ele para e continua de onde parou na próxima execução.",
    ])
    story.append(P("Métricas e como são calculadas", "h2"))
    mrows = [["Métrica", "Como é calculada"],
             ["Correção", "Nota do juiz (1–5): quanto a resposta cumpre o gabarito e os critérios de aceite."],
             ["Aderência ao escopo", "Nota do juiz (1–5): fica no papel de assistente GoodWe de recarga EV, em pt-BR, adequado à persona."],
             ["Fidelidade (não-alucinação)", "Nota do juiz (1–5): não inventa fatos fora da conversa e da base (URLs, valores, nomes, códigos)."],
             ["Decisão correta", "1 se recusou quando devia recusar, ou respondeu quando devia responder; 0 caso contrário."],
             ["Checagens OK", "1 se todos os regex obrigatórios casam e nenhum proibido casa; 0 caso contrário."],
             ["Score do caso (0–100)", "100 × (%.2f·correção + %.2f·escopo + %.2f·fidelidade + %.2f·decisão + %.2f·checagens), "
              "com as notas 1–5 normalizadas para 0–1 por (nota − 1)/4." % tuple(PESOS[k] for k in
                                                                              ("correcao", "escopo", "fidelidade", "decisao", "checks"))],
             ["Caso aprovado", "correção >= 4, fidelidade >= 3, decisão correta e checagens OK."],
             ["Nota final da versão", "Média dos scores dos casos."],
             ["Recusa correta / indevida", "% de recusas entre os casos \"recusar\" (quanto maior, melhor) e entre os casos "
              "\"responder\" (quanto menor, melhor — mede over-blocking)."],
             ["Latência média", "Média do tempo de resposta da LLM nas chamadas que chegaram ao modelo (informativa, fora da nota)."]]
    story += [table([[s(a), s(b)] for a, b in mrows], [4 * cm, W - 4 * cm])]

    # 3. Versões + resultados
    story += [PageBreak(), P("3. Versões avaliadas", "h1")]
    vrows = [["Versão", "O que é"]] + [[s(VERSIONS[v]["nome"]), s(VERSIONS[v]["descricao"])] for v in versions]
    story += [table(vrows, [5.2 * cm, W - 5.2 * cm])]
    story.append(P("Todas as versões foram avaliadas com o mesmo golden dataset, o mesmo juiz e os mesmos pesos. A V1 "
                   "reproduz a arquitetura da Sprint 2 (prompt + histórico, sem framework nem guardrails) no mesmo modelo "
                   "da V2, para que a diferença medida venha da arquitetura e não da troca de modelo."))
    story.append(P("4. Tabela de resultados por versão", "h1"))
    hdr = ["Métrica"] + [s(_version_label(v)) for v in versions]
    rows = [hdr]
    for key, label, f in METRIC_ROWS:
        rows.append([s(label.replace(" ↓", " (menor = melhor)"))] + [fmt(vs[v].get(key), f) for v in versions])
    for cat in CATEGORIAS:
        rows.append([f"Score — {NOMES_CATEGORIAS[cat]}"] +
                    [fmt(vs[v]["por_categoria"].get(cat, {}).get("score"), "{:.1f}") for v in versions])
    hl = [(1, 1 + versions.index(best), VERDE)]
    colw = (W - 6.2 * cm) / len(versions)
    story += [table([[s(c) if i else c for i, c in enumerate(r)] for r in rows], [6.2 * cm] + [colw] * len(versions),
                    highlight=hl)]
    story.append(P(f"Linha \"NOTA FINAL\" destacada na versão vencedora. Casos por versão: "
                   + ", ".join(f"{s(_version_label(v))} = {vs[v]['n_casos']}" for v in versions) + ".", "small"))
    chart_path = os.path.join(rdir, "grafico_categorias.png")
    chart_categories(resumo, versions, chart_path)
    story += [Spacer(1, 6), Image(chart_path, width=W, height=W * 3.0 / 7.2),
              P("Score médio por categoria do golden dataset, por versão.", "small")]

    # 5. Classificação
    story += [P("5. Classificação e justificativa", "h1")]
    story.append(P("<b>Classificação pelo pipeline:</b> " + " &gt; ".join(
        f"{i + 1}º {s(_version_label(v))} ({vs[v]['nota_final']:.1f})" for i, v in enumerate(versions))))
    for t in texto_classificacao(resumo, rdir, casos_por_id):
        story.append(P(t))
    evo = texto_evolucao(resumo)
    if evo:
        story.append(P("Evolução Sprint 2 -> Sprint 3", "h2"))
        for t in evo:
            story.append(P(t))

    # 6. Comparação manual
    story += [PageBreak(), P("6. Comparação com a avaliação manual da Sprint 3", "h1")]
    if comp:
        story.append(P(
            "Para comparar de forma justa, o pipeline julgou <b>as mesmas respostas</b> que o grupo avaliou à mão na Sprint 3 "
            "(gravadas em <i>docs/resultados_brutos.json</i>, 19 testes × 2 modelos), e não respostas novas. Assim, qualquer "
            "diferença vem do método de avaliação, não de variação do modelo."))
        story.append(P(
            f"<b>Concordância geral: {comp['concordancia_pct']:.1f}%</b> ({comp['n'] - len(comp['divergencias'])} de "
            f"{comp['n']} vereditos iguais). A avaliação manual aprovou {comp['manual_aprovados']} de {comp['n']}; "
            f"o pipeline aprovou {comp['pipeline_aprovados']} de {comp['n']}. Concordância por categoria: "
            + ", ".join(f"{NOMES_CATEGORIAS.get(k, k)} {v:.0f}%" for k, v in comp["concordancia_por_categoria"].items()) + "."))
        crow = [["Modelo", "Caso", "Manual (S3)", "Pipeline", "Score", "Observação do pipeline"]]
        hl2 = []
        for i, l in enumerate(comp["linhas"], 1):
            obs = "; ".join(l["checks_falhas"]) if l["checks_falhas"] else ""
            if not l["concorda"]:
                obs = (obs + " — " if obs else "") + _cut(l["justificativa_juiz"], 170)
                hl2.append((i, 3, ROSA))
            crow.append([s(l["modelo"]), l["caso"], "aprovado" if l["manual_aprovado"] else "reprovado",
                         "aprovado" if l["pipeline_aprovado"] else "reprovado", f"{l['pipeline_score']:.0f}", s(obs)])
        story += [table(crow, [2.4 * cm, 1.2 * cm, 1.9 * cm, 1.8 * cm, 1.3 * cm, W - 8.6 * cm], highlight=hl2)]
        if comp["divergencias"]:
            story.append(P("Onde as avaliações divergem", "h2"))
            for l in comp["divergencias"]:
                det = f" Checagens: {s('; '.join(l['checks_falhas']))}." if l["checks_falhas"] else ""
                story.append(P(f"<b>{l['caso']} ({s(l['modelo'])})</b> — manual: {s(l['manual'])}. Pipeline: "
                               f"{'aprovado' if l['pipeline_aprovado'] else 'reprovado'} (correção {l['correcao']}, "
                               f"fidelidade {l['fidelidade']}).{det} Juiz: <i>{s(_cut(l['justificativa_juiz'], 380))}</i>", "bullet"))
        story.append(P("Hipóteses para as divergências", "h2"))
        story += bullets([
            "<b>Critério binário x critérios múltiplos.</b> Na Sprint 3 o grupo marcou cada teste como \"Aprovado/Adequado\" "
            "olhando o comportamento principal (bloqueou? lembrou o número?). O pipeline cobra <i>todos</i> os critérios do "
            "gabarito e penaliza invenções, então reprova respostas que acertam o essencial mas inventam detalhes.",
            "<b>Leitura de trechos.</b> O relatório da Sprint 3 mostrava só os primeiros 200 caracteres de cada resposta. "
            "Exemplo concreto: no M03 a avaliação manual registrou que o agente manteve \"Residencial Flores\" e \"síndico\", "
            "mas nenhuma das duas respostas gravadas cita esses termos — e a do compound-mini resume assuntos que nunca foram "
            "discutidos (agendamento, tarifa de R$ 0,78).",
            "<b>Falta de veredito individual nos testes funcionais.</b> Na Sprint 3 os 7 testes funcionais só tiveram latência "
            "registrada e uma avaliação geral (\"respostas corretas\"). Um caso que passou despercebido aparece agora: "
            "no F02 do compound-mini o guardrail de saída trocou uma resposta válida pela mensagem \"não posso compartilhar "
            "instruções internas\" (falso positivo do filtro de vazamento). Já no F01 os dois modelos inventam URLs de portal: "
            "o juiz baixou a nota de fidelidade, mas o caso ficou dentro do limite de aprovação, então não conta como divergência.",
            "<b>Viés do juiz.</b> Parte das divergências pode ser do próprio juiz (mais rígido ou mais leniente que um humano). "
            + ("Por isso cruzamos o juiz com checagens por regex e medimos sua consistência (seção 7)." if consist else
               (f"Por isso cruzamos o juiz com checagens por regex: em {sum(1 for d in comp['divergencias'] if d['checks_falhas'])} "
                f"das {len(comp['divergencias'])} divergências, a checagem objetiva (sem LLM) também reprovou a resposta.")),
        ])
    else:
        story.append(P("Rode <i>python eval/run_eval.py --sprint3-gravado</i> para gerar esta seção."))

    # 7. Limitações
    story += [P("7. Limitações do pipeline", "h1")]
    lim = [
        f"<b>Viés e variância do LLM juiz.</b> As notas dependem de um modelo ({s(resumo['modelo_juiz'])}) que pode errar, "
        "ser leniente com respostas longas e bem formatadas ou não perceber invenções sutis. Mitigamos com temperatura 0, "
        "rubrica fixa, juiz de outra família e checagens determinísticas, mas não eliminamos o viés.",
        f"<b>Cobertura do golden dataset.</b> São {len(casos)} casos escritos pelo grupo; não cobrem todos os fluxos reais "
        "(ex.: integrações reais com o painel, áudio, múltiplos idiomas) e alguns gabaritos envolvem julgamento "
        "(ex.: até onde responder sobre um carregador de outra marca).",
        "<b>Uma execução por versão.</b> O agente roda com temperatura 0,4; rodar de novo pode mudar algumas respostas. "
        "Diferenças de poucos pontos entre versões estão dentro dessa variação.",
        "<b>Checagens por regex são frágeis.</b> Podem dar falso negativo se o modelo escrever o valor de outro jeito "
        "(ex.: \"quarenta e dois reais\").",
        "<b>Custo e limite de API.</b> Cada execução completa faz ~%d chamadas ao agente e ~%d ao juiz por versão; no tier "
        "gratuito do Groq isso leva dezenas de minutos e pode exigir mais de um dia. Por isso a latência medida também "
        "sofre influência da fila da API." % (sum(len(c["turnos"]) for c in casos), len(casos)),
        "<b>Baseline aproximado.</b> A V1 reproduz a arquitetura da Sprint 2, mas no modelo gpt-oss-120b (a Sprint 2 usava "
        "gpt-4o-mini, que o grupo não tem mais como acessar).",
    ]
    story += bullets(lim)
    if consist:
        story.append(P(
            f"<b>Consistência medida do juiz:</b> rejulgando {consist['n']} respostas da {s(_version_label(consist['versao']))}, "
            f"a nota de correção saiu idêntica em {consist['correcao_igual']:.0f}% dos casos e com diferença de até 1 ponto em "
            f"{consist['correcao_ate_1_ponto']:.0f}%; a decisão de recusa foi a mesma em {consist['recusa_igual']:.0f}%. "
            "Isso indica o quanto podemos confiar em diferenças pequenas entre versões."))

    # 8. Conclusão
    story += [P("8. Conclusão — evolução ao longo das sprints", "h1")]
    story += bullets([
        "<b>Sprint 1:</b> definição do problema, persona, system prompt e 5 perguntas com resposta esperada — avaliação só no papel.",
        "<b>Sprint 2:</b> chatbot funcional (prompt + few-shot + histórico); 5 casos avaliados manualmente como adequados.",
        "<b>Sprint 3:</b> refatoração para LangGraph com memória por sessão, guardrails e comparação de modelos; 19 testes "
        "com avaliação manual (todos aprovados).",
        f"<b>Sprint 4:</b> a avaliação virou um processo reprodutível: {len(casos)} casos com gabarito, juiz automático, "
        "métricas definidas e comparação entre versões com números. Isso revelou problemas que a avaliação manual não pegou "
        "e mostra onde investir a seguir (por exemplo, trocar o guardrail por regex por uma classificação de intenção, "
        "para não bloquear perguntas legítimas).",
    ])
    story.append(P(f"Resultado final: <b>{s(VERSIONS[best]['nome'])}</b> é a melhor versão segundo o pipeline "
                   f"(nota {vs[best]['nota_final']:.1f}/100)."))

    # 9. Equipe
    story += [P("9. Equipe e divisão de trabalho", "h1")]
    story += [table([["Nome", "RM", "Tarefa principal"]] +
                    [[s(i["nome"]), s(i["rm"]), s(i["tarefa"])] for i in equipe["integrantes"]],
                    [3.4 * cm, 1.8 * cm, W - 5.2 * cm])]

    # Apêndices
    story += [PageBreak(), P("Apêndice A — Golden dataset (resumo)", "h1")]
    arows = [["ID", "Categoria", "Decisão", "Mensagem (último turno)", "Gabarito"]]
    for c in casos:
        msg = c["turnos"][-1]["mensagem"] if len(c["turnos"]) == 1 else \
            " / ".join(f"[{t['sessao']}] {t['mensagem']}" for t in c["turnos"])
        arows.append([c["id"], s(NOMES_CATEGORIAS[c["categoria"]]), c["decisao_esperada"], s(_cut(msg, 230)), s(_cut(c["gabarito"], 280))])
    story += [table(arows, [1 * cm, 2.3 * cm, 1.8 * cm, 5.4 * cm, W - 10.5 * cm])]

    story += [PageBreak(), P("Apêndice B — Resultado caso a caso", "h1"),
              P("Score do caso (0–100) por versão; \"*\" = reprovado; \"G\" = bloqueado pelo guardrail de entrada.", "small")]
    recs = {v: load_records(rdir, v) for v in versions}
    brows = [["Caso", "Categoria"] + [s(_version_label(v)) for v in versions]]
    hl3 = []
    for i, c in enumerate(casos, 1):
        row = [c["id"], s(NOMES_CATEGORIAS[c["categoria"]])]
        for j, v in enumerate(versions):
            r = recs[v].get(c["id"])
            if not r or not r.get("juiz"):
                row.append("—")
                continue
            tag = ("" if r["metricas"]["aprovado"] else "*") + (" G" if any(t.get("blocked") for t in r["turnos_resp"]) else "")
            row.append(f"{r['metricas']['score']:.0f}{tag}")
            if not r["metricas"]["aprovado"]:
                hl3.append((i, 2 + j, ROSA))
        brows.append(row)
    colw = (W - 3.6 * cm) / len(versions)
    story += [table(brows, [1.2 * cm, 2.4 * cm] + [colw] * len(versions), highlight=hl3)]
    story.append(P("Detalhes completos (resposta, notas e justificativa do juiz): results/resultados_por_caso.csv.", "small"))

    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.grey)
        canvas.drawString(1.7 * cm, 1.1 * cm, "GoodWe EV ChargeOps Assistant — Sprint 04 — Relatório final")
        canvas.drawRightString(A4[0] - 1.7 * cm, 1.1 * cm, f"página {doc.page}")
        if fake:
            canvas.setFont("Helvetica-Bold", 46)
            canvas.setFillColor(colors.Color(0.78, 0.06, 0.18, alpha=0.12))
            canvas.translate(A4[0] / 2, A4[1] / 2)
            canvas.rotate(40)
            canvas.drawCentredString(0, 0, "SIMULAÇÃO - NÃO ENTREGAR")
        canvas.restoreState()

    doc = SimpleDocTemplate(out_path, pagesize=A4, leftMargin=1.7 * cm, rightMargin=1.7 * cm,
                            topMargin=1.6 * cm, bottomMargin=1.7 * cm,
                            title="Relatório Final Sprint 04 — GoodWe EV ChargeOps", author="Grupo 1CCPX")
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"✅ Relatório gerado: {out_path}")
    if resumo.get("versoes_incompletas"):
        print(f"⚠️  Atenção: versões com casos faltando: {resumo['versoes_incompletas']}. Complete antes de entregar.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fake", action="store_true", help="usa results_fake/ (simulação, marca d'água)")
    ap.add_argument("--saida", default=None)
    a = ap.parse_args()
    rdir = results_dir(fake=a.fake)
    if not os.path.exists(os.path.join(rdir, "resumo_versoes.json")):
        sys.exit("❌ Não há resultados. Rode antes: python eval/run_eval.py")
    out = a.saida or os.path.join(ROOT, "docs", "relatorio_final_sprint4_SIMULACAO.pdf" if a.fake
                                  else "relatorio_final_sprint4.pdf")
    build(rdir, out, a.fake)
