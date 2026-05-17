import io
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

# ── Palette ──────────────────────────────────────────────────────────────────
DARK = colors.HexColor("#0d0f14")
SURFACE = colors.HexColor("#14171f")
ACCENT = colors.HexColor("#c8a96e")
GREEN = colors.HexColor("#3ecf8e")
RED = colors.HexColor("#f04e5e")
YELLOW = colors.HexColor("#f0c94e")
TEXT = colors.HexColor("#e8eaf0")
MUTED = colors.HexColor("#7a7f96")
WHITE = colors.white

W, H = A4
MARGIN = 18 * mm


# ── Styles ───────────────────────────────────────────────────────────────────
def _styles():
    getSampleStyleSheet()
    return {
        "label": ParagraphStyle(
            "label", fontSize=7, textColor=ACCENT, spaceAfter=2, leading=10
        ),
        "title": ParagraphStyle(
            "title",
            fontSize=24,
            textColor=WHITE,
            fontName="Helvetica-Bold",
            spaceAfter=4,
            leading=28,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontSize=9, textColor=MUTED, spaceAfter=0, leading=12
        ),
        "section": ParagraphStyle(
            "section",
            fontSize=10,
            textColor=ACCENT,
            fontName="Helvetica-Bold",
            spaceBefore=10,
            spaceAfter=4,
            leading=14,
        ),
        "body": ParagraphStyle(
            "body", fontSize=9, textColor=TEXT, leading=15, spaceAfter=6
        ),
        "kpi_name": ParagraphStyle(
            "kpi_name", fontSize=7, textColor=MUTED, leading=10
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value",
            fontSize=14,
            textColor=WHITE,
            fontName="Helvetica-Bold",
            leading=18,
        ),
        "kpi_delta": ParagraphStyle("kpi_delta", fontSize=8, leading=10),
        "bullet": ParagraphStyle(
            "bullet",
            fontSize=9,
            textColor=TEXT,
            leading=14,
            leftIndent=10,
            spaceAfter=3,
        ),
        "tag": ParagraphStyle(
            "tag", fontSize=8, textColor=TEXT, leading=12, spaceAfter=2
        ),
        "footer": ParagraphStyle(
            "footer",
            fontSize=7,
            textColor=MUTED,
            alignment=TA_CENTER,
            leading=10,
        ),
    }


def _tone_color(ton: str) -> colors.Color:
    return {"optimiste": GREEN, "neutre": YELLOW, "pessimiste": RED}.get(
        ton.lower(), YELLOW
    )


def _delta_color(sens: str) -> colors.Color:
    return {"pos": GREEN, "neg": RED}.get(sens, MUTED)


# ── Sections ─────────────────────────────────────────────────────────────────


def _header(s, filename: str, ton: str, raison: str) -> list:
    tone_color = _tone_color(ton)
    tone_label = ton.capitalize()

    # Top bar (dark background via table)
    header_data = [
        [
            Paragraph(
                "REPORT READER",
                ParagraphStyle(
                    "brand",
                    fontSize=8,
                    textColor=ACCENT,
                    fontName="Helvetica-Bold",
                    leading=10,
                ),
            ),
            Paragraph(
                f"Generated {date.today().strftime('%B %d, %Y')}",
                ParagraphStyle(
                    "date",
                    fontSize=8,
                    textColor=MUTED,
                    alignment=TA_RIGHT,
                    leading=10,
                ),
            ),
        ]
    ]
    header_table = Table(
        header_data, colWidths=[W - 2 * MARGIN - 60 * mm, 60 * mm]
    )
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), DARK),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (-1, -1), (-1, -1), 0),
            ]
        )
    )

    clean_name = filename.replace(".pdf", "").replace("_", " ").title()
    elements = []
    elements.append(Paragraph("FINANCIAL ANALYSIS REPORT", s["label"]))
    elements.append(Paragraph(clean_name, s["title"]))

    # Tone badge inline
    tone_data = [
        [
            Paragraph(
                "OVERALL TONE",
                ParagraphStyle(
                    "tl",
                    fontSize=7,
                    textColor=MUTED,
                    leading=10,
                ),
            ),
            Paragraph(
                f"● {tone_label}",
                ParagraphStyle(
                    "tv",
                    fontSize=9,
                    textColor=tone_color,
                    fontName="Helvetica-Bold",
                    leading=12,
                ),
            ),
            Paragraph(
                raison,
                ParagraphStyle("tr", fontSize=8, textColor=MUTED, leading=12),
            ),
        ]
    ]
    tone_table = Table(
        tone_data, colWidths=[28 * mm, 28 * mm, W - 2 * MARGIN - 56 * mm]
    )
    tone_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("LINEABOVE", (0, 0), (-1, 0), 1, ACCENT),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    elements.append(Spacer(1, 4 * mm))
    elements.append(tone_table)
    elements.append(Spacer(1, 6 * mm))
    elements.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2a2f42"))
    )
    elements.append(Spacer(1, 4 * mm))
    return elements


def _summary(s, resume: str) -> list:
    return [
        Paragraph("EXECUTIVE SUMMARY", s["section"]),
        Paragraph(resume, s["body"]),
        Spacer(1, 4 * mm),
    ]


def _kpis(s, kpis: list) -> list:
    if not kpis:
        return []
    elements = [Paragraph("KEY FINANCIAL KPIs", s["section"])]
    rows = []
    row = []
    for kpi in kpis:
        delta_color = _delta_color(kpi.get("sens", "neu"))
        delta = kpi.get("variation", "N/A")
        cell = [
            Paragraph(kpi.get("nom", ""), s["kpi_name"]),
            Paragraph(kpi.get("valeur", "—"), s["kpi_value"]),
            Paragraph(
                delta,
                ParagraphStyle(
                    "kd", fontSize=8, textColor=delta_color, leading=10
                ),
            ),
        ]
        row.append(cell)
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        while len(row) < 3:
            row.append([Paragraph("", s["kpi_name"])])
        rows.append(row)
    col_w = (W - 2 * MARGIN) / 3
    for row in rows:
        t = Table([row], colWidths=[col_w] * 3)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("LINEABOVE", (0, 0), (-1, 0), 2, ACCENT),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#2a2f42"),
                    ),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        elements.append(t)
        elements.append(Spacer(1, 2 * mm))
    elements.append(Spacer(1, 4 * mm))
    return elements


def _themes(s, themes: list) -> list:
    if not themes:
        return []
    elements = [Paragraph("STRATEGIC THEMES", s["section"])]
    tags = "   ".join(f"[ {t} ]" for t in themes)
    elements.append(
        Paragraph(
            tags,
            ParagraphStyle(
                "tags",
                fontSize=8,
                textColor=TEXT,
                leading=16,
                spaceAfter=6,
            ),
        )
    )
    elements.append(Spacer(1, 2 * mm))
    return elements


def _risks_opps(s, risques: list, opportunites: list) -> list:
    elements = [Paragraph("RISKS & OPPORTUNITIES", s["section"])]
    left_items = [
        Paragraph(
            "⚠  RISKS",
            ParagraphStyle(
                "rh",
                fontSize=8,
                textColor=RED,
                fontName="Helvetica-Bold",
                leading=12,
                spaceAfter=4,
            ),
        )
    ]
    for r in risques:
        left_items.append(
            Paragraph(
                f"• {r}",
                ParagraphStyle(
                    "ri",
                    fontSize=8,
                    textColor=TEXT,
                    leading=13,
                    leftIndent=6,
                    spaceAfter=3,
                ),
            )
        )
    right_items = [
        Paragraph(
            "✓  OPPORTUNITIES",
            ParagraphStyle(
                "oh",
                fontSize=8,
                textColor=GREEN,
                fontName="Helvetica-Bold",
                leading=12,
                spaceAfter=4,
            ),
        )
    ]
    for o in opportunites:
        right_items.append(
            Paragraph(
                f"• {o}",
                ParagraphStyle(
                    "oi",
                    fontSize=8,
                    textColor=TEXT,
                    leading=13,
                    leftIndent=6,
                    spaceAfter=3,
                ),
            )
        )
    half = (W - 2 * MARGIN - 6 * mm) / 2
    t = Table([[left_items, right_items]], colWidths=[half, half])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#1c0f14")),
                ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#0f1c14")),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("LINEABOVE", (0, 0), (0, 0), 2, RED),
                ("LINEABOVE", (1, 0), (1, 0), 2, GREEN),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#2a2f42"),
                ),
            ]
        )
    )
    elements.append(t)
    return elements


def _footer(s) -> list:
    return [
        Spacer(1, 8 * mm),
        HRFlowable(
            width="100%", thickness=1, color=colors.HexColor("#2a2f42")
        ),
        Spacer(1, 3 * mm),
        Paragraph(
            "Generated by Report Reader · Powered by Claude AI", s["footer"]
        ),
    ]


def generate_pdf(result: dict, filename: str) -> bytes:
    """Generate a styled PDF report and return it as bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )
    s = _styles()
    story = []
    story += _header(
        s, filename, result.get("ton", "neutre"), result.get("raison_ton", "")
    )
    story += _summary(s, result.get("resume", ""))
    story += _kpis(s, result.get("kpis", []))
    story += _themes(s, result.get("themes", []))
    story += _risks_opps(
        s, result.get("risques", []), result.get("opportunites", [])
    )
    story += _footer(s)
    doc.build(story, onFirstPage=_page_bg, onLaterPages=_page_bg)
    return buffer.getvalue()


def _page_bg(canvas, doc):
    """Paint dark background on every page."""
    canvas.saveState()
    canvas.setFillColor(DARK)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.restoreState()
