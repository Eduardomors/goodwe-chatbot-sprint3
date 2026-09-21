"""
Gera o Relatório de Evolução (PDF, máx 5 páginas) exigido na Sprint 3.
Uso: python generate_report_pdf.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable,
)

WIDTH, HEIGHT = A4
MARGIN = 2 * cm
OUTPUT = "/mnt/user-data/outputs/relatorio_evolucao_sprint3.pdf"

# ── Estilos ──────────────────────────────────────────────────────────────────

styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    "Cover", parent=styles["Title"], fontSize=22, spaceAfter=6,
    textColor=HexColor("#1a1a2e"), alignment=TA_CENTER,
))
styles.add(ParagraphStyle(
    "Subtitle", parent=styles["Normal"], fontSize=12, spaceAfter=20,
    textColor=HexColor("#555555"), alignment=TA_CENTER,
))
styles.add(ParagraphStyle(
    "SectionTitle", parent=styles["Heading2"], fontSize=14, spaceBefore=16,
    spaceAfter=8, textColor=HexColor("#16213e"),
))
styles.add(ParagraphStyle(
    "Body", parent=styles["Normal"], fontSize=10, leading=14,
    alignment=TA_JUSTIFY, spaceAfter=8,
))
styles.add(ParagraphStyle(
    "Small", parent=styles["Normal"], fontSize=8, textColor=HexColor("#888888"),
    alignment=TA_CENTER,
))
styles.add(ParagraphStyle(
    "CellStyle", parent=styles["Normal"], fontSize=9, leading=11,
))

ACCENT = HexColor("#0f3460")
LIGHT_BG = HexColor("#f0f4f8")


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )
    story = []

    # ════════════════════════════════════════════════════════════════════
    # CAPA
    # ════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("Relatório de Evolução — Sprint 3", styles["Cover"]))
    story.append(Paragraph("GoodWe EV ChargeOps Assistant", styles["Subtitle"]))
    story.append(Paragraph("EV Challenge 2026 — Agentes de IA e Evolução Conversacional", styles["Subtitle"]))
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="60%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 1 * cm))

    team = [
        ["Nome", "RM", "Responsabilidade"],
        ["Brenno Gomes", "570525", "Arquitetura LangGraph, guardrails e integração"],
        ["Eduardo Moreira", "569923", "Testes de segurança e prompt injection"],
        ["Enzo Stahal", "569001", "Testes funcionais e de memória"],
        ["Matheus Bruno", "572944", "Comparação de modelos e relatório"],
    ]
    t = Table(team, colWidths=[5 * cm, 2.5 * cm, 9 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Disciplina: Prompt and Artificial Intelligence — FIAP — 1ESPK", styles["Small"]))
    story.append(Paragraph("Setembro 2026", styles["Small"]))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════
    # 1. RESUMO DA EVOLUÇÃO
    # ════════════════════════════════════════════════════════════════════
    story.append(Paragraph("1. Resumo da Evolução", styles["SectionTitle"]))

    story.append(Paragraph(
        "Nas Sprints 1 e 2, o grupo desenvolveu o GoodWe EV ChargeOps Assistant como um chatbot "
        "operacional que utilizava a API da OpenAI de forma direta (chamada HTTP), com gerenciamento "
        "manual do histórico de mensagens em uma lista Python e interface via terminal. O modelo "
        "utilizado foi o GPT-4o-mini com temperature 0.4.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "Na Sprint 3, a arquitetura foi completamente refatorada para utilizar o <b>LangGraph</b> como "
        "framework de agentes de IA. O chatbot passou a operar como um grafo de estados com nós "
        "especializados: guardrail de entrada (detecção de prompt injection e escopo), agente LLM "
        "(chamada ao modelo com contexto) e guardrail de saída (validação da resposta). "
        "A memória conversacional agora é gerenciada nativamente pelo <b>MemorySaver</b> "
        "(checkpointer do LangGraph), eliminando a necessidade de gerenciamento manual do histórico.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "Além disso, foram adicionados: suporte a múltiplos modelos (OpenAI GPT-4o-mini e "
        "Gemini 2.0 Flash), testes automatizados de segurança com 8 cenários (incluindo prompt "
        "injection em português e inglês), testes de memória com 4 cenários multi-turno, e um "
        "pipeline de testes que gera automaticamente o relatório comparativo entre modelos.",
        styles["Body"],
    ))

    # ════════════════════════════════════════════════════════════════════
    # 2. REFATORAÇÃO
    # ════════════════════════════════════════════════════════════════════
    story.append(Paragraph("2. Decisões de Refatoração", styles["SectionTitle"]))

    story.append(Paragraph(
        "<b>Framework escolhido: LangGraph.</b> O LangGraph foi selecionado por oferecer controle "
        "explícito do fluxo conversacional através de um grafo de estados — diferente de frameworks "
        "como CrewAI (sequencial) ou OpenAI Agents SDK (limitado ao ecossistema OpenAI). O grafo "
        "permite inserir nós de guardrail antes e depois da LLM, tornando a segurança parte da "
        "arquitetura e não apenas do prompt.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "<b>Memória via MemorySaver.</b> Na Sprint 2, o histórico era mantido em uma lista Python "
        "que se perdia ao encerrar o processo. O MemorySaver do LangGraph persiste o estado do grafo "
        "por sessão (thread_id), permitindo que o agente recupere informações de turnos anteriores "
        "sem intervenção manual. Cada sessão é isolada — informações da sessão A não vazam para a "
        "sessão B.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "<b>Trade-offs identificados:</b> (1) O LangGraph adiciona complexidade em relação à chamada "
        "direta da API — mais dependências e curva de aprendizado. (2) O MemorySaver em memória RAM "
        "não persiste entre reinicializações do processo (seria necessário SQLiteSaver ou PostgresSaver "
        "em produção). (3) A camada de guardrails por regex tem limitações — padrões muito agressivos "
        "podem gerar falsos positivos.",
        styles["Body"],
    ))

    # ════════════════════════════════════════════════════════════════════
    # 3. COMPARATIVO ANTES × DEPOIS
    # ════════════════════════════════════════════════════════════════════
    story.append(Paragraph("3. Comparativo Antes x Depois", styles["SectionTitle"]))

    comp_data = [
        ["Aspecto", "Sprints 1-2", "Sprint 3"],
        ["Arquitetura", "Chamada direta à API OpenAI", "LangGraph StateGraph com 4 nós"],
        ["Framework", "Nenhum (requests/openai SDK)", "LangGraph + LangChain"],
        ["Memória", "Lista Python manual", "MemorySaver (checkpointer nativo)"],
        ["Guardrails", "Apenas no system prompt", "Nós dedicados (regex + prompt)"],
        ["Modelos testados", "1 (GPT-4o-mini)", "2 (GPT-4o-mini + Gemini 2.0 Flash)"],
        ["Testes funcionais", "5 casos", "7 casos"],
        ["Testes de memória", "0 (não existiam)", "4 cenários (3+ turnos cada)"],
        ["Testes de segurança", "0 (não existiam)", "8 cenários (incl. prompt injection)"],
        ["Métricas coletadas", "Nenhuma", "Latência, tokens, taxa bloqueio"],
        ["Multi-modelo", "Não", "Sim (troca via /model ou config)"],
    ]

    t = Table(comp_data, colWidths=[4 * cm, 5.5 * cm, 7 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t)

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "<b>A nova arquitetura tornou o chatbot melhor?</b> Sim. A Sprint 3 trouxe ganhos mensuráveis: "
        "segurança estrutural (guardrails como nós, não apenas texto), memória nativa sem código manual, "
        "testabilidade (19 testes automatizados vs 5 manuais), e flexibilidade de modelo. "
        "O custo foi o aumento de complexidade na configuração inicial.",
        styles["Body"],
    ))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════
    # 4. PROBLEMAS ENCONTRADOS E SOLUÇÕES
    # ════════════════════════════════════════════════════════════════════
    story.append(Paragraph("4. Problemas Encontrados e Soluções", styles["SectionTitle"]))

    # Problema 1
    story.append(Paragraph("<b>Problema 1: Guardrail bloqueando perguntas legítimas (falso positivo)</b>", styles["Body"]))
    story.append(Paragraph(
        "Durante os testes iniciais, o padrão de regex para detectar prompt injection bloqueava "
        "perguntas como <i>\"Ignore se já respondi, mas qual a potência do carregador?\"</i> porque "
        "continha a palavra \"ignore\".",
        styles["Body"],
    ))
    story.append(Paragraph(
        "<b>Alternativas consideradas:</b> (A) Remover o padrão \"ignore\" completamente — "
        "reduziria a segurança. (B) Usar classificador de ML para detecção — mais preciso mas "
        "complexo e lento. (C) Refinar os padrões regex para exigir contexto adicional.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "<b>Solução adotada:</b> Opção C — os padrões regex foram refinados para exigir combinações "
        "como \"ignore + instruções\" ou \"ignore + todas\", reduzindo falsos positivos sem "
        "comprometer a detecção de ataques reais.",
        styles["Body"],
    ))

    story.append(Spacer(1, 0.3 * cm))

    # Problema 2
    story.append(Paragraph("<b>Problema 2: Memória acumulando tokens excessivos em conversas longas</b>", styles["Body"]))
    story.append(Paragraph(
        "O MemorySaver armazena todo o histórico da sessão. Em conversas com 15+ turnos, o "
        "volume de tokens enviados à LLM crescia significativamente, aumentando custo e latência.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "<b>Alternativas consideradas:</b> (A) Limitar o histórico às últimas N mensagens — "
        "simples mas perde contexto antigo. (B) Implementar sumarização automática do histórico — "
        "complexo e adiciona outra chamada LLM. (C) Usar janela deslizante com as últimas 10 mensagens.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "<b>Solução adotada:</b> Opção C — para o escopo do projeto acadêmico, a janela deslizante "
        "com as 10 últimas mensagens oferece um equilíbrio entre memória e custo. Em produção, "
        "a sumarização (opção B) seria a evolução natural.",
        styles["Body"],
    ))

    # ════════════════════════════════════════════════════════════════════
    # 5. DIVISÃO DA EQUIPE
    # ════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("5. Divisão da Equipe", styles["SectionTitle"]))

    div_data = [
        ["Integrante", "RM", "Principal Responsabilidade"],
        ["Brenno Gomes", "570525",
         "Arquitetura do agente LangGraph (StateGraph, nós, roteamento), "
         "implementação dos guardrails e integração multi-modelo"],
        ["Eduardo Moreira", "569923",
         "Criação e execução dos testes de segurança (prompt injection, escopo, "
         "segurança elétrica) e validação dos guardrails"],
        ["Enzo Stahal", "569001",
         "Testes funcionais (7 casos), testes de memória (4 cenários multi-turno) "
         "e análise qualitativa das respostas"],
        ["Matheus Bruno", "572944",
         "Experimentação com modelos (GPT-4o-mini vs Gemini), geração do "
         "relatorio_modelos.md e redação do relatório de evolução"],
    ]

    t = Table(div_data, colWidths=[3.5 * cm, 2 * cm, 11 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEADING", (0, 0), (-1, -1), 11),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="40%", thickness=0.5, color=HexColor("#CCCCCC")))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Repositório: github.com/Eduardomors/goodwe-chatbot-sprint3",
        styles["Small"],
    ))

    # Build
    doc.build(story)
    print(f"✅ PDF gerado: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()
