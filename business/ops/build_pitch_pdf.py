#!/usr/bin/env python3
"""Build the Booked Solid pitch PDF (2 pages: owner leave-behind + Aaron's talk track)."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle,
                                PageBreak, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

OUT = ("/home/hatch/workspace/goals/"
       "ai-front-desk-business-for-salons-and-barbershops/files/"
       "booked-solid-pitch.pdf")

BLACK = HexColor("#111111")
GRAY = HexColor("#555555")
LIGHT = HexColor("#F2F0EB")
ACCENT = HexColor("#B08D3E")

styles = {
    "brand": ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=40,
                            leading=44, textColor=BLACK),
    "tagline": ParagraphStyle("tagline", fontName="Helvetica", fontSize=17,
                              leading=22, textColor=GRAY),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=19,
                         leading=24, textColor=BLACK, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13.5,
                         leading=18, textColor=BLACK, spaceBefore=12,
                         spaceAfter=4),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=11.5,
                           leading=16.5, textColor=BLACK, spaceAfter=6),
    "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=11.5,
                             leading=16.5, textColor=BLACK, leftIndent=14,
                             bulletIndent=2, spaceAfter=3),
    "big": ParagraphStyle("big", fontName="Helvetica-Bold", fontSize=26,
                          leading=30, textColor=BLACK, alignment=TA_CENTER),
    "demo": ParagraphStyle("demo", fontName="Helvetica-Bold", fontSize=15,
                           leading=20, textColor=BLACK, alignment=TA_CENTER),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=9.5,
                            leading=13, textColor=GRAY, alignment=TA_CENTER),
    "script": ParagraphStyle("script", fontName="Helvetica-Oblique",
                             fontSize=11.5, leading=16.5, textColor=BLACK,
                             leftIndent=12, spaceAfter=6),
}


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8.5)
    canvas.setFillColor(GRAY)
    if doc.page == 1:
        canvas.drawCentredString(letter[0] / 2, 0.55 * inch,
                                 "Booked Solid  ·  New York, NY  ·  "
                                 "Aaron Kotchen  ·  917-565-7862")
    else:
        canvas.drawCentredString(letter[0] / 2, 0.55 * inch,
                                 "Aaron's copy. Not for the owner.")
    canvas.restoreState()


doc = BaseDocTemplate(OUT, pagesize=letter,
                      leftMargin=0.85 * inch, rightMargin=0.85 * inch,
                      topMargin=0.75 * inch, bottomMargin=0.8 * inch,
                      title="Booked Solid", author="Booked Solid")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height)
doc.addPageTemplates([PageTemplate(frames=[frame], onPage=footer)])

story = []
S = styles

# ---------- Page 1: the leave-behind ----------
story.append(Paragraph("BOOKED SOLID", S["brand"]))
story.append(Paragraph("Your front desk. Never closed.", S["tagline"]))
story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=2.2, color=ACCENT))
story.append(Spacer(1, 14))

story.append(Paragraph("Your shop closes at 7. Your customers call at 9.",
                       S["h1"]))
story.append(Paragraph(
    "Every night, people call your shop to book and get voicemail. Most "
    "never call back. They book the shop down the street that picked up. "
    "Five missed calls a week, half of them ready to book, at a $90 "
    "average ticket, is roughly <b>$970 a month</b> walking out the door. "
    "At Upper East Side prices, it is more.", S["body"]))

story.append(Paragraph("What Booked Solid does", S["h2"]))
for b in [
    "Answers every call, 24 hours a day, in your shop's name.",
    "Books appointments with the right barber or stylist, inside your hours.",
    "Quotes your real services and prices, and answers the everyday questions.",
    "Takes messages and call-back requests, and sends you every booking.",
    "Sounds like a front desk, because it is one. Trained on your shop.",
]:
    story.append(Paragraph(b, S["bullet"], bulletText="•"))

story.append(Spacer(1, 8))
demo_tbl = Table([[Paragraph("HEAR IT YOURSELF, RIGHT NOW", S["demo"])],
                  [Paragraph("Call (929) 307-2035 and book a haircut.",
                             S["demo"])],
                  [Paragraph("That is a live Booked Solid front desk "
                             "answering a demo shop. Yours would answer "
                             "as your shop.", S["small"])]],
                 colWidths=[doc.width])
demo_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
    ("BOX", (0, 0), (-1, -1), 1.2, ACCENT),
    ("TOPPADDING", (0, 0), (-1, 0), 10),
    ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
    ("TOPPADDING", (0, 1), (-1, 1), 2),
    ("BOTTOMPADDING", (0, 1), (-1, 1), 2),
]))
story.append(demo_tbl)
story.append(Spacer(1, 14))

story.append(Paragraph("The price", S["h2"]))
price_tbl = Table(
    [[Paragraph("$249.99", S["big"]), Paragraph("$199.99", S["big"])],
     [Paragraph("one-time setup, done for you", S["small"]),
      Paragraph("a month, per location", S["small"])]],
    colWidths=[doc.width / 2, doc.width / 2])
price_tbl.setStyle(TableStyle([
    ("LINEABOVE", (0, 0), (-1, 0), 0.8, BLACK),
    ("TOPPADDING", (0, 0), (-1, 0), 8),
    ("BOTTOMPADDING", (0, -1), (-1, -1), 2),
]))
story.append(price_tbl)
story.append(Spacer(1, 6))
story.append(Paragraph(
    "No contract. No per-minute games. One saved booking a week covers "
    "the month. We set it up, train it on your services and prices, and "
    "it can be answering your phone by tomorrow night.", S["body"]))

story.append(PageBreak())

# ---------- Page 2: Aaron's talk track ----------
S["brand"].fontSize = 32
S["brand"].leading = 36
S["h2"].spaceBefore = 8
S["script"].leading = 15.5
S["body"].leading = 15.5
story.append(Paragraph("THE WALK-IN", S["brand"]))
story.append(Paragraph("Your talk track. Two minutes, in and out.",
                       S["tagline"]))
story.append(Spacer(1, 6))
story.append(HRFlowable(width="100%", thickness=2.2, color=ACCENT))

story.append(Paragraph("The opener (30 seconds)", S["h2"]))
story.append(Paragraph(
    "\u201cHey, I'm Aaron, I run Booked Solid, we're local, right here "
    "in the neighborhood. Quick question: when your shop is closed and "
    "somebody calls to book, who answers?\u201d Then stop talking. Let "
    "them say voicemail. \u201cThat's exactly what we fix. Your phone "
    "gets answered 24/7 by a front desk that books real appointments "
    "with your barbers, at your prices. Don't take my word for it, "
    "call it.\u201d Hand them the sheet and let them dial the demo "
    "number on the spot.", S["script"]))

story.append(Paragraph("Three questions that sell it", S["h2"]))
for b in [
    "How many calls do you figure you miss after you close?",
    "What time do most of your booking calls come in?",
    "What do you book on now, Booksy, Fresha, Square, paper?",
]:
    story.append(Paragraph(b, S["bullet"], bulletText="•"))
story.append(Paragraph(
    "Every answer is a reason. Missed calls are lost money, evening "
    "calls are the ones going to voicemail, and whatever they book on, "
    "the desk feeds it the same details it takes on the call.",
    S["body"]))

story.append(Paragraph("When they push back", S["h2"]))
story.append(Paragraph("<b>\u201cWe already have online booking.\u201d</b>", S["body"]))
story.append(Paragraph(
    "Online booking catches people who find the link. Callers who hit "
    "voicemail mostly don't call back, they book whoever picks up. We "
    "catch the callers.", S["script"]))
story.append(Paragraph("<b>\u201cSounds expensive.\u201d</b>", S["body"]))
story.append(Paragraph(
    "One saved booking a week covers the month. One color appointment "
    "covers it twice. And there is no contract, so it has to earn its "
    "keep every month.", S["script"]))
story.append(Paragraph("<b>\u201cIs it a robot?\u201d</b>", S["body"]))
story.append(Paragraph(
    "Don't argue it. Say: call the number on the sheet and judge it "
    "yourself. It books, it quotes prices, it knows the barbers. If a "
    "caller ever wants a person, it takes a message and you get it "
    "right away.", S["script"]))
story.append(Paragraph("<b>\u201cI need to think about it.\u201d</b>", S["body"]))
story.append(Paragraph(
    "Leave the sheet and say: call the demo tonight, after you close, "
    "then call your own shop and compare. Get a day to come back.",
    S["script"]))

story.append(Paragraph("The close", S["h2"]))
story.append(Paragraph(
    "\u201cIt's $249.99 to set up and $199.99 a month, no contract. I "
    "can have it answering your phone by tomorrow night. All I need is "
    "your service list, your prices and your hours.\u201d Then be quiet. "
    "The first one who talks loses.", S["script"]))

doc.build(story)
print("built", OUT)
