from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def build_report_pdf(title: str, content: str) -> BytesIO:
    buffer = BytesIO()

    # Built-in CID font supports Chinese without external font files
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

    styles = getSampleStyleSheet()
    styles["Title"].fontName = "STSong-Light"
    styles["Title"].fontSize = 18
    styles["Title"].leading = 22

    body = styles["BodyText"]
    body.fontName = "STSong-Light"
    body.fontSize = 11
    body.leading = 16

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=title,
    )

    story = [Paragraph(title, styles["Title"]), Spacer(1, 10 * mm)]

    for line in content.splitlines():
        line = line.strip()
        if not line:
            story.append(Spacer(1, 4 * mm))
            continue
        story.append(Paragraph(line.replace("\t", "    "), body))
        story.append(Spacer(1, 2 * mm))

    doc.build(story)
    buffer.seek(0)
    return buffer
