"""Shared, print-quality publication system for Market Signals research.

Applies one editorial identity to the public historical sample, current full
executive edition, and decision-specific briefs. Uses vector PDF primitives,
embedded core PDF fonts (no external assets), descriptive charts, genuine
evidence citations and consistent A4 page furniture.

This module is visual only: all figures and claims come from the caller's
already verified edition manifest.
"""
from __future__ import annotations

from html import escape
from io import BytesIO
from math import isfinite
from urllib.parse import urlsplit

from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, KeepTogether, LongTable, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

NAVY=colors.HexColor("#142B3D")
MIDNIGHT=colors.HexColor("#102131")
INK=colors.HexColor("#183447")
SLATE=colors.HexColor("#40596C")
COPPER=colors.HexColor("#A86C49")
BRASS=colors.HexColor("#CF9D77")
MIST=colors.HexColor("#E8EFF0")
SAND=colors.HexColor("#F5F2EC")
PALE=colors.HexColor("#FAF9F5")
LINE=colors.HexColor("#DADFDC")
WHITE=colors.white
W,H=A4
LEFT=19*mm
RIGHT=19*mm
BODY=W-LEFT-RIGHT
STAMP="JAIR RIBEIRO  /  EXECUTIVE MARKET INTELLIGENCE"


def clean(text: object) -> str:
    value=str(text if text is not None else "")
    return (value.replace("\u2014"," - ").replace("\u2013","-")
        .replace("\u2018","'").replace("\u2019","'")
        .replace("\u201c",'"').replace("\u201d",'"')
        .replace("\u2022","-").replace("\u00a0"," ")
        .replace("\u2192","->").replace("\u2265",">=")
        .replace("\u2026","...").replace("\u00ad",""))


def _markup(value: object) -> str:
    return escape(clean(value),quote=False)


def source_url(url: object) -> str:
    value=str(url or "")
    parsed=urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Market publication requires verified HTTPS evidence.")
    return escape(value,quote=True)


def styles():
    # A paired serif headline and sans-serif analysis system. All core PDF
    # fonts remain searchable, printable, and portable on mobile readers.
    s={
      "eyebrow":ParagraphStyle("mp_eyebrow",fontName="Helvetica-Bold",
          fontSize=7.5,leading=11,textColor=COPPER,spaceAfter=7),
      "h1":ParagraphStyle("mp_h1",fontName="Times-Roman",
          fontSize=26,leading=30.5,textColor=NAVY,spaceAfter=10),
      "lead":ParagraphStyle("mp_lead",fontName="Times-Roman",
          fontSize=14,leading=19,textColor=SLATE,spaceAfter=13),
      "h2":ParagraphStyle("mp_h2",fontName="Helvetica-Bold",
          fontSize=10.7,leading=14.7,textColor=INK,spaceBefore=11,spaceAfter=5),
      "body":ParagraphStyle("mp_body",fontName="Helvetica",
          fontSize=9.05,leading=14.8,textColor=INK,spaceAfter=9),
      "body_compact":ParagraphStyle("mp_compact",fontName="Helvetica",
          fontSize=8.8,leading=13.6,textColor=INK,spaceAfter=7),
      "body_small":ParagraphStyle("mp_small",fontName="Helvetica",
          fontSize=8.05,leading=12.5,textColor=SLATE,spaceAfter=6),
      "caption":ParagraphStyle("mp_caption",fontName="Helvetica",
          fontSize=7.25,leading=10.8,textColor=SLATE,spaceAfter=4),
      "panel_label":ParagraphStyle("mp_panellabel",fontName="Helvetica-Bold",
          fontSize=7.5,leading=11.5,textColor=COPPER,spaceAfter=5),
      "panel_title":ParagraphStyle("mp_paneltitle",fontName="Times-Roman",
          fontSize=14.2,leading=18.2,textColor=NAVY,spaceAfter=6),
      "panel_body":ParagraphStyle("mp_panelbody",fontName="Helvetica",
          fontSize=8.6,leading=13.4,textColor=INK,spaceAfter=0),
      "metric":ParagraphStyle("mp_metric",fontName="Times-Roman",
          fontSize=24,leading=27.5,textColor=NAVY,spaceAfter=4),
      "metric_label":ParagraphStyle("mp_metriclabel",fontName="Helvetica-Bold",
          fontSize=8,leading=11.5,textColor=INK,spaceAfter=4),
      "metric_note":ParagraphStyle("mp_metricnote",fontName="Helvetica",
          fontSize=7.2,leading=10.3,textColor=SLATE),
      "table_head":ParagraphStyle("mp_tablehead",fontName="Helvetica-Bold",
          fontSize=7.3,leading=10.3,textColor=WHITE),
      "table":ParagraphStyle("mp_table",fontName="Helvetica",
          fontSize=7.5,leading=11.4,textColor=INK),
      "table_small":ParagraphStyle("mp_tablesmall",fontName="Helvetica",
          fontSize=6.9,leading=10.0,textColor=SLATE),
      "table_bold":ParagraphStyle("mp_tablebold",fontName="Helvetica-Bold",
          fontSize=7.7,leading=11.2,textColor=INK),
      "source":ParagraphStyle("mp_source",fontName="Helvetica",
          fontSize=7.3,leading=10.8,textColor=SLATE,spaceAfter=5),
      "folio":ParagraphStyle("mp_folio",fontName="Helvetica",
          fontSize=7.4,leading=10.8,textColor=SLATE),
      "right":ParagraphStyle("mp_right",fontName="Helvetica",
          fontSize=7.3,leading=11,textColor=SLATE,alignment=TA_RIGHT),
    }
    return s


def P(text,kind="body",*,raw=False,sty=None):
    s=sty or styles()
    return Paragraph(str(text) if raw else _markup(text),s[kind])


def text_on(canvas,text,style,x,top,width):
    item=P(text,raw=False,kind="body") if isinstance(style,str) else Paragraph(_markup(text),style)
    _,height=item.wrap(width,H)
    item.drawOn(canvas,x,top-height)
    return top-height


def cover_callback(spec: dict):
    """Produce a bespoke, evidence-led title page rather than a blank title."""
    title=clean(spec["title"])
    subtitle=clean(spec.get("subtitle") or "")
    assessment=clean(spec.get("assessment") or "")
    question=clean(spec.get("question") or "")
    edition=clean(spec.get("edition") or "")
    issue=clean(spec.get("issue") or "")
    metrics=list(spec.get("metrics") or [])
    if len(metrics)!=3 or any(len(x)!=3 for x in metrics):
        raise ValueError("Publication cover needs three verified metric summaries.")
    def draw(c,doc):
        c.saveState()
        c.setFillColor(MIDNIGHT);c.rect(0,0,W,H,stroke=0,fill=1)
        c.setFillColor(NAVY);c.rect(0,236,W,H-236,stroke=0,fill=1)
        # Oversized editorial motif is vector-only, with low-contrast geometry.
        c.setStrokeColor(colors.HexColor("#274358"))
        c.setLineWidth(1.3)
        for radius in [71,108,145,181]:
            c.circle(W+17,H-155,radius,stroke=1,fill=0)
        c.setStrokeColor(COPPER);c.setLineWidth(3)
        c.line(LEFT,H-66,LEFT+40,H-66)
        c.setFont("Helvetica-Bold",8.1);c.setFillColor(WHITE)
        c.drawString(LEFT,H-43,STAMP)
        c.setFont("Helvetica",8.1);c.setFillColor(colors.HexColor("#D9C7B8"))
        c.drawRightString(W-RIGHT,H-43,edition.upper())
        c.setFont("Helvetica-Bold",9);c.setFillColor(BRASS)
        c.drawString(LEFT,H-114,"MARKET SIGNALS / SWEDEN")
        title_style=ParagraphStyle("mp_cover_title",fontName="Times-Roman",
            fontSize=40,leading=43.5,textColor=WHITE)
        y=text_on(c,title,title_style,LEFT,H-132,BODY-22)
        sub_style=ParagraphStyle("mp_cover_sub",fontName="Times-Roman",
            fontSize=19.0,leading=24.3,textColor=colors.HexColor("#EADBCB"))
        y=text_on(c,subtitle,sub_style,LEFT,y-16,BODY-30)
        c.setStrokeColor(COPPER);c.setLineWidth(1)
        # Keep the argument adjacent to the headline. The former fixed 402pt
        # divider created a large visual hole on the title page.
        rule_y=min(y-25,490)
        c.line(LEFT,rule_y,W-RIGHT,rule_y)
        assess_style=ParagraphStyle("mp_cover_assess",fontName="Helvetica",
            fontSize=10.2,leading=17.0,textColor=colors.HexColor("#E8EEF1"))
        assess_text=assessment if len(assessment)<=540 else assessment[:537].rstrip()+"..."
        y2=text_on(c,assess_text,assess_style,LEFT,rule_y-20,BODY-24)
        if y2<255:
            raise ValueError("Cover text exceeds its designed reading area.")
        if question and y2>=320:
            qtop=min(y2-22,335)
            c.setFont("Helvetica-Bold",7.4);c.setFillColor(BRASS)
            c.drawString(LEFT,qtop,"THE EXECUTIVE QUESTION")
            question_style=ParagraphStyle("mp_cover_question",
                fontName="Times-Roman",fontSize=15.3,leading=19.4,
                textColor=WHITE)
            bottom=text_on(c,question[:155],question_style,
                           LEFT,qtop-13,BODY-27)
            if bottom<241:
                raise ValueError("Executive question overlaps the cover facts.")
        # Off-white metric band: exactly three fact boxes, never a generic slogan.
        c.setFillColor(SAND);c.rect(0,0,W,235,stroke=0,fill=1)
        c.setFillColor(COPPER);c.rect(0,233,W,2,stroke=0,fill=1)
        c.setFillColor(SLATE);c.setFont("Helvetica-Bold",8)
        c.drawString(LEFT,210,"THE EVIDENCE AT A GLANCE")
        card_w=(BODY-20)/3
        for i,(value,label,note) in enumerate(metrics):
            x=LEFT+i*(card_w+10)
            if i:
                c.setStrokeColor(LINE);c.line(x-5,72,x-5,187)
            value_style=ParagraphStyle("mp_cover_value",fontName="Times-Roman",
                fontSize=27,leading=29,textColor=NAVY)
            text_on(c,str(value),value_style,x,183,card_w-3)
            lab_style=ParagraphStyle("mp_cover_mlabel",fontName="Helvetica-Bold",
                fontSize=8.2,leading=11.5,textColor=INK)
            low=text_on(c,label,lab_style,x,143,card_w-7)
            note_style=ParagraphStyle("mp_cover_mnote",fontName="Helvetica",
                fontSize=7.8,leading=11.0,textColor=SLATE)
            text_on(c,note,note_style,x,min(low-5,113),card_w-9)
        c.setStrokeColor(LINE);c.line(LEFT,48,W-RIGHT,48)
        c.setFont("Helvetica-Bold",8.3);c.setFillColor(NAVY)
        c.drawString(LEFT,31,"JAIR RIBEIRO")
        c.setFont("Helvetica",7.8);c.setFillColor(SLATE)
        c.drawRightString(W-RIGHT,31,issue+"  |  jairribeiro.com")
        c.restoreState()
    return draw


def interior_callback(kicker="MARKET SIGNALS / EXECUTIVE RESEARCH"):
    def draw(c,doc):
        c.saveState()
        c.setFillColor(PALE);c.rect(0,0,W,H,stroke=0,fill=1)
        c.setFillColor(NAVY);c.rect(0,H-21*mm,W,21*mm,fill=1,stroke=0)
        c.setFillColor(COPPER);c.rect(LEFT,H-21*mm,38*mm,2,fill=1,stroke=0)
        c.setFillColor(WHITE);c.setFont("Helvetica-Bold",8)
        c.drawString(LEFT,H-13.1*mm,"JAIR RIBEIRO  /  MARKET SIGNALS")
        c.setFillColor(colors.HexColor("#C8D4DD"));c.setFont("Helvetica",7.6)
        c.drawRightString(W-RIGHT,H-13*mm,kicker[:49])
        c.setStrokeColor(LINE);c.line(LEFT,17.2*mm,W-RIGHT,17.2*mm)
        c.setFillColor(SLATE);c.setFont("Helvetica",7.7)
        c.drawString(LEFT,11.8*mm,"Independent executive research  |  jairribeiro.com")
        c.drawRightString(W-RIGHT,11.8*mm,f"{doc.page:02d}")
        c.restoreState()
    return draw


def new_publication(title,author="Jair Ribeiro | Enterprise AI & Data"):
    output=BytesIO()
    doc=SimpleDocTemplate(output,pagesize=A4,leftMargin=LEFT,
      rightMargin=RIGHT,topMargin=30*mm,bottomMargin=24*mm,
      title=clean(title),author=author,subject="Market Signals Advisory research")
    return output,doc


def assemble(story,cover,title,*,min_bytes=4000):
    output,doc=new_publication(title)
    # Cover is completely vector-drawn: no content flow can partially occupy
    # it or leave orphan text while the first content page is laid out.
    content=[Spacer(1,4),PageBreak(),*story]
    doc.build(content,onFirstPage=cover_callback(cover),
              onLaterPages=interior_callback())
    blob=output.getvalue()
    if not blob.startswith(b"%PDF") or len(blob)<min_bytes:
        raise ValueError("Market Signals PDF generation failed.")
    return blob


def section(story,number,title,lede="",*,sty=None):
    s=sty or styles()
    story.append(P(number.upper(),"eyebrow",sty=s))
    story.append(P(title,"h1",sty=s))
    if lede:
        story.append(P(lede,"lead",sty=s))
    story.append(HRFlowable(width="100%",thickness=1,color=LINE,spaceBefore=2,spaceAfter=13))


def subsection(story,title,body,*,sty=None):
    s=sty or styles()
    story.append(KeepTogether([P(title,"h2",sty=s),P(body,"body",sty=s)]))


def panel(label,title,body,*,dark=False,sty=None):
    s=sty or styles()
    # A single shaded and ruled editorial panel; no tiny unsupported badges.
    cell=[P(label.upper(),"panel_label",sty=s),P(title,"panel_title",sty=s),
          P(body,"panel_body",sty=s)]
    tb=Table([[cell]],colWidths=[BODY],hAlign="LEFT")
    tb.setStyle(TableStyle([
      ("BACKGROUND",(0,0),(-1,-1),MIST if dark else SAND),
      ("LINEBEFORE",(0,0),(0,-1),3.2,COPPER),
      ("LEFTPADDING",(0,0),(-1,-1),17),
      ("RIGHTPADDING",(0,0),(-1,-1),16),
      ("TOPPADDING",(0,0),(-1,-1),15),
      ("BOTTOMPADDING",(0,0),(-1,-1),15),
    ]))
    return tb


def metric_cards(items,*,sty=None):
    s=sty or styles()
    if len(items)!=3:
        raise ValueError("Comparative evidence panel requires three metrics.")
    gap=8
    col_width=(BODY-gap*2)/3
    cards=[]
    for value,label,note in items:
        cells=[P(value,"metric",sty=s),P(label,"metric_label",sty=s),
               P(note,"metric_note",sty=s)]
        t=Table([[cells]],colWidths=[col_width],hAlign="LEFT")
        t.setStyle(TableStyle([
          ("BACKGROUND",(0,0),(-1,-1),SAND),
          ("LINEABOVE",(0,0),(-1,0),2.1,COPPER),
          ("LEFTPADDING",(0,0),(-1,-1),12),
          ("RIGHTPADDING",(0,0),(-1,-1),9),
          ("TOPPADDING",(0,0),(-1,-1),12),
          ("BOTTOMPADDING",(0,0),(-1,-1),12),
        ]))
        cards.append(t)
    tb=Table([[cards[0],"",cards[1],"",cards[2]]],
             colWidths=[col_width,gap,col_width,gap,col_width])
    tb.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
                            ("LEFTPADDING",(0,0),(-1,-1),0),
                            ("RIGHTPADDING",(0,0),(-1,-1),0),
                            ("TOPPADDING",(0,0),(-1,-1),0),
                            ("BOTTOMPADDING",(0,0),(-1,-1),0)]))
    return tb


def bars(rows,*,label="Selected observations",suffix="",sty=None):
    """Compact comparative chart with native vector bars and labelled values."""
    s=sty or styles()
    if not rows:
        return P("No approved comparable observations.","body_small",sty=s)
    maximum=max(1,max(float(v) for _,v in rows))
    if any(not isfinite(float(v)) or float(v)<0 for _,v in rows):
        raise ValueError("Comparative chart requires finite nonnegative values.")
    out=[]
    for name,value in rows:
        num=float(value)
        measure=f"{int(num):,}" if num.is_integer() else f"{num:,.1f}"
        drawing=Drawing(74*mm,14)
        drawing.add(Rect(0,3,74*mm,8,fillColor=MIST,strokeColor=None))
        drawing.add(Rect(0,3,max(1,74*mm*num/maximum),8,
                         fillColor=NAVY,strokeColor=None))
        drawing.add(Rect(max(0,74*mm*num/maximum-2),3,2,8,
                         fillColor=COPPER,strokeColor=None))
        out.append([P(name,"table_bold",sty=s),drawing,
                    P(measure+suffix,"table_bold",sty=s)])
    tbl=Table(out,colWidths=[59*mm,74*mm,BODY-133*mm],hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LINEBELOW",(0,0),(-1,-1),0.35,LINE),
        ("TOPPADDING",(0,0),(-1,-1),12),
        ("BOTTOMPADDING",(0,0),(-1,-1),12),
        ("LEFTPADDING",(0,0),(-1,-1),3),
        ("RIGHTPADDING",(0,0),(-1,-1),2),
    ]))
    return tbl


def decision_table(items,*,sty=None):
    """Two readable columns beat the old cramped four-column checklist."""
    s=sty or styles()
    rows=[[P("DECISION AND ACCOUNTABILITY","table_head",sty=s),
           P("PRACTICAL NEXT ACTION","table_head",sty=s)]]
    for title,owner,horizon,action in items:
        rows.append([
            [P(title,"table_bold",sty=s),
             P(owner+"  |  "+horizon,"table_small",sty=s)],
            P(action,"table",sty=s),
        ])
    tbl=LongTable(rows,colWidths=[65*mm,BODY-65*mm],hAlign="LEFT",repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),NAVY),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,SAND]),
        ("LINEBELOW",(0,1),(-1,-1),.35,LINE),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("TOPPADDING",(0,0),(-1,-1),11),
        ("BOTTOMPADDING",(0,0),(-1,-1),11),
        ("LEFTPADDING",(0,0),(-1,-1),10),
        ("RIGHTPADDING",(0,0),(-1,-1),9),
    ]))
    return tbl


def sources_table(points,format_value,*,sty=None):
    """Compact, complete clickable evidence ledger, suitable for an appendix."""
    s=sty or styles()
    rows=[[P("EVIDENCE / PERIOD","table_head",sty=s),
           P("OBSERVATION / ORIGINAL SOURCE","table_head",sty=s)]]
    unique=set()
    for item in sorted(points,key=lambda p:(str(p["source_family"]),str(p["code"]))):
        code=str(item["code"])
        if code in unique:
            raise ValueError("Repeated source identifier in market publication.")
        unique.add(code)
        href=source_url(item["source_url"])
        source=escape(clean(item["source_title"]),quote=False)
        val=escape(clean(format_value(item)),quote=False)
        pub=escape(clean(item.get("period_label") or ""),quote=False)
        region=escape(clean(item.get("geography") or ""),quote=False)
        rows.append([
            [P(code,"table_bold",sty=s),P(pub+"  |  "+region,"table_small",sty=s)],
            Paragraph(
              f'<b>{_markup(item.get("metric_label") or "Selected senior AI/Data leadership advertisements")}</b>  /  {val}<br/>'
              f'<link href="{href}" color="#1F5773">{source} (original publisher)</link>',
              s["table"]),
        ])
    table=LongTable(rows,colWidths=[64*mm,BODY-64*mm],hAlign="LEFT",
                    repeatRows=1,splitByRow=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),NAVY),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,SAND]),
        ("LINEBELOW",(0,1),(-1,-1),.35,LINE),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("TOPPADDING",(0,0),(-1,-1),7),
        ("BOTTOMPADDING",(0,0),(-1,-1),7),
        ("LEFTPADDING",(0,0),(-1,-1),9),
        ("RIGHTPADDING",(0,0),(-1,-1),7),
    ]))
    return table
