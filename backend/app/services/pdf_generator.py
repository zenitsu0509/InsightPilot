import os
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    Preformatted,
    HRFlowable,
    PageBreak,
)


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="HeroTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=26,
            textColor=colors.HexColor("#111827"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeader",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            spaceAfter=6,
            textColor=colors.HexColor("#111827"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportBody",
            parent=styles["BodyText"],
            fontSize=11,
            leading=16,
        )
    )
    styles.add(
        ParagraphStyle(
            name="MetaLabel",
            parent=styles["BodyText"],
            fontSize=8,
            textColor=colors.HexColor("#6b7280"),
            leading=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="QueryText",
            parent=styles["BodyText"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#111827"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="MetricValue",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=colors.HexColor("#111827"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="MetricLabel",
            parent=styles["BodyText"],
            fontSize=9,
            textColor=colors.HexColor("#6b7280"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="CaptionSmall",
            parent=styles["BodyText"],
            fontSize=9,
            textColor=colors.HexColor("#6b7280"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="InsightBullet",
            parent=styles["BodyText"],
            leftIndent=14,
            bulletIndent=6,
            bulletFontName="Helvetica",
            bulletFontSize=10,
            leading=16,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeBlock",
            parent=styles["BodyText"],
            fontName="Courier",
            fontSize=9,
            leading=14,
            backColor=colors.whitesmoke,
        )
    )
    return styles


def _format_insights(insights: str, styles) -> list:
    blocks = []
    lines = [line.strip() for line in (insights or "").splitlines() if line.strip()]
    if not lines:
        return [Paragraph("No insights provided.", styles["ReportBody"])]

    for line in lines:
        if line[0] in {"-", "*", "•"}:
            text = line.lstrip("-•* ").strip()
            blocks.append(Paragraph(text, styles["InsightBullet"], bulletText="•"))
        else:
            blocks.append(Paragraph(line, styles["ReportBody"]))
        blocks.append(Spacer(1, 4))
    return blocks


def _build_data_table(data_sample):
    if not data_sample:
        return None

    columns = list(data_sample[0].keys())
    rows = [columns]
    for row in data_sample[:10]:
        rows.append([str(row.get(col, "")) for col in columns])

    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f9fafb")),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#111827")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
            ]
        )
    )
    return table


def _build_query_callout(query: str, styles):
    display = query or "No question provided"
    content = [
        [Paragraph("BUSINESS QUESTION", styles["MetaLabel"])],
        [Paragraph(display, styles["QueryText"])]
    ]
    table = Table(content, colWidths=[6.5 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f4ff")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#c7d2fe")),
                ("INNERPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def _build_metric_cards(stats: dict, styles):
    if not stats:
        return None

    data = []
    row = []
    for label, value in stats.items():
        cell = [
            Paragraph(label, styles["MetricLabel"]),
            Paragraph(value, styles["MetricValue"]),
        ]
        row.append(cell)

    data.append(row)

    col_width = (6.5 * inch) / len(stats)
    table = Table(data, colWidths=[col_width] * len(stats))
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9fafb")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("INNERPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def _format_value(value):
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def _render_trend_section(trend_analysis, styles):
    blocks = [Paragraph("Trend Diagnostics", styles["SectionHeader"])]
    if not trend_analysis:
        blocks.append(Paragraph("Not enough chronological data to compute a trend.", styles["ReportBody"]))
        return blocks

    blocks.append(Paragraph(trend_analysis.get("summary", ""), styles["ReportBody"]))
    stats = [
        ["Starting value", _format_value(trend_analysis.get("start"))],
        ["Ending value", _format_value(trend_analysis.get("end"))],
        ["Slope", _format_value(trend_analysis.get("slope"))],
    ]
    if trend_analysis.get("change_pct") is not None:
        stats.append(["% Change", f"{trend_analysis['change_pct']:+.1f}%"])

    table = Table(stats, colWidths=[2.3 * inch, 4 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9fafb")),
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
                ("INNERPADDING", (0, 0), (-1, -1), 6),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ]
        )
    )
    blocks.extend([Spacer(1, 6), table])
    return blocks


def _render_anomaly_section(anomaly_analysis, styles):
    blocks = [Paragraph("Anomaly Highlights", styles["SectionHeader"])]
    if not anomaly_analysis:
        blocks.append(Paragraph("No statistical anomalies detected across the observed period.", styles["ReportBody"]))
        return blocks

    blocks.append(Paragraph(anomaly_analysis.get("summary", ""), styles["ReportBody"]))
    table_rows = [["Period", "Value", "z-score"]]
    for entry in anomaly_analysis.get("anomalies", [])[:8]:
        table_rows.append([
            entry.get("period", "?"),
            _format_value(entry.get("value")),
            f"{entry.get('z_score', 0):+.2f}",
        ])
    table = Table(table_rows, repeatRows=1, colWidths=[2 * inch, 2.5 * inch, 1.5 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f3f4f6")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
            ]
        )
    )
    blocks.extend([Spacer(1, 6), table])
    return blocks


def generate_pdf_report(
    report_path: str,
    title: str,
    query: str,
    sql_query: str,
    insights: str,
    chart_image_path: str = None,
    chart_summary: str = None,
    trend_analysis: Optional[dict] = None,
    anomaly_analysis: Optional[dict] = None,
    data_sample=None,
):
    styles = _build_styles()
    doc = SimpleDocTemplate(
        report_path,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    story = []

    generated_at = datetime.utcnow().strftime("%B %d, %Y %H:%M UTC")
    row_count = len(data_sample or [])
    column_count = len(data_sample[0]) if data_sample else 0

    story.append(Paragraph(title, styles["HeroTitle"]))
    story.append(Paragraph("Autonomous insight report", styles["CaptionSmall"]))
    story.append(Spacer(1, 10))

    story.append(_build_query_callout(query, styles))
    story.append(Spacer(1, 12))

    metrics = {
        "Rows Returned": f"{row_count:,}" if row_count else "0",
        "Columns": str(column_count),
        "Generated": generated_at,
    }
    metric_table = _build_metric_cards(metrics, styles)
    if metric_table:
        story.append(metric_table)
        story.append(Spacer(1, 18))

    story.append(Paragraph("This auto-generated briefing captures the freshest SQL results, advanced analytics, and executive visuals from InsightPilot.", styles["ReportBody"]))
    story.append(Spacer(1, 14))
    story.append(PageBreak())

    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#e5e7eb")))
    story.append(Spacer(1, 14))

    story.append(Paragraph("SQL Used", styles["SectionHeader"]))
    story.append(
        Preformatted(sql_query.strip() or "No SQL generated", styles["CodeBlock"], maxLineLength=80)
    )
    story.append(Spacer(1, 12))

    story.append(Paragraph("Insights", styles["SectionHeader"]))
    for block in _format_insights(insights, styles):
        story.append(block)
    story.append(Spacer(1, 10))

    table = _build_data_table(data_sample or [])
    if table:
        story.append(Paragraph("Data Preview", styles["SectionHeader"]))
        story.append(table)
        story.append(Spacer(1, 12))

    for block in _render_trend_section(trend_analysis, styles):
        story.append(block)
    story.append(Spacer(1, 12))

    for block in _render_anomaly_section(anomaly_analysis, styles):
        story.append(block)
    story.append(Spacer(1, 12))

    if chart_image_path and os.path.exists(chart_image_path):
        story.append(Paragraph("Visualization", styles["SectionHeader"]))
        img = Image(chart_image_path)
        img._restrictSize(6.5 * inch, 4.5 * inch)
        img.hAlign = "CENTER"
        story.append(img)
        if chart_summary:
            story.append(Spacer(1, 6))
            story.append(Paragraph(chart_summary, styles["CaptionSmall"]))
    elif chart_summary:
        story.append(Paragraph("Visualization Summary", styles["SectionHeader"]))
        story.append(Paragraph(chart_summary, styles["ReportBody"]))

    doc.build(story)
    return report_path
