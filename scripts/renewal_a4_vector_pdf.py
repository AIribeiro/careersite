#!/usr/bin/env python3
"""Premium, source-locked vector A4 infographic for AI Portfolio Renewal Challenge.

All headline, question, evidence and decision text is drawn using vector fonts;
there is NO full-page bitmap. The design follows the approved editorial logic.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

SLUG = 'would-you-fund-the-same-ai-initiatives-today'
SOURCE_FINGERPRINT='b9e255ca0e7ac9fdf7504e98fe07dd9e8f642c96c4e492d6aac4adf511c27bd5'
NAVY=colors.HexColor('#0B263D'); DEEP=colors.HexColor('#0F3450')
CYAN=colors.HexColor('#3ABBC8'); TEAL=colors.HexColor('#167E8D'); COPPER=colors.HexColor('#B87952')
WHITE=colors.HexColor('#FFFFFF'); PAPER=colors.HexColor('#F6F8F8'); INK=colors.HexColor('#183247')
GRAY=colors.HexColor('#526875'); LINE=colors.HexColor('#D8E3E4'); PALE=colors.HexColor('#EAF3F4')
SAND=colors.HexColor('#F6ECE6'); SLATE=colors.HexColor('#647889')
FONT_DIR=Path('/usr/share/fonts/truetype/lato')
SERIF_DIR=Path('/usr/share/fonts/truetype/noto')
for name,file in [('JRRegular','Lato-Regular.ttf'),('JRBold','Lato-Bold.ttf'),('JRHeavy','Lato-Heavy.ttf')]:
    p=FONT_DIR/file
    if not p.is_file(): p=Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSans-Bold.ttf' if 'Bold' in name or 'Heavy' in name else 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont(name,str(p)))
serif=SERIF_DIR/'NotoSerifDisplay-SemiBold.ttf'
if not serif.is_file():serif=Path('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf')
pdfmetrics.registerFont(TTFont('JRSerif',str(serif)))

W,H=A4
M=34; FULL=W-2*M

def text(pdf,x,y,value,font,size,fill=INK):
    pdf.setFillColor(fill); pdf.setFont(font,size);pdf.drawString(x,y,value)

def para(pdf,html,x,top,width,fontsize=10.0,leading=13,color=INK,font='JRRegular',max_height=200):
    style=ParagraphStyle('block',fontName=font,fontSize=fontsize,leading=leading,textColor=color,spaceAfter=0)
    p=Paragraph(html,style)
    ww, hh=p.wrap(width,max_height)
    if hh>max_height+0.1: raise ValueError(f'Paragraph height overflow: {html[:70]} {hh}>{max_height}')
    p.drawOn(pdf,x,top-hh)
    return hh

def rounded(pdf,x,y,width,height,fill=WHITE,stroke=LINE,radius=9,weight=0.75):
    pdf.setFillColor(fill);pdf.setStrokeColor(stroke);pdf.setLineWidth(weight)
    pdf.roundRect(x,y,width,height,radius,stroke=1,fill=1)

def label(pdf,num,title,y):
    text(pdf,M,y,num,'JRHeavy',9.5,COPPER)
    text(pdf,M+29,y,title,'JRHeavy',12.9,NAVY)
    pdf.setStrokeColor(LINE);pdf.setLineWidth(.65);pdf.line(M,y-10,W-M,y-10)

def investment_card(pdf,x,y,w,accent,tag,title,desc):
    rounded(pdf,x,y,w,89)
    pdf.setFillColor(accent);pdf.roundRect(x+13,y+15,4,58,2,fill=1,stroke=0)
    text(pdf,x+27,y+68,tag,'JRHeavy',8.5,accent)
    text(pdf,x+27,y+43,title,'JRBold',14.1,INK)
    para(pdf,desc,x+27,y+32,w-53,9.6,12.3,GRAY,max_height=25)

def review_card(pdf,x,y,accent,number,title,desc):
    rounded(pdf,x,y,FULL,70)
    fill=PALE if number=='01' else SAND
    pdf.setFillColor(fill);pdf.roundRect(x+13,y+13,62,44,8,fill=1,stroke=0)
    text(pdf,x+27,y+27,number,'JRSerif',24.5,accent)
    text(pdf,x+90,y+44,title,'JRBold',12.2,NAVY)
    para(pdf,desc,x+90,y+32,FULL-117,10.1,13.2,GRAY,max_height=31)

def decision_card(pdf,x,y,w,accent,title,description):
    rounded(pdf,x,y,w,67)
    pdf.setFillColor(accent);pdf.roundRect(x+11,y+13,4,41,2,stroke=0,fill=1)
    text(pdf,x+25,y+42,title,'JRHeavy',12.6,accent)
    para(pdf,description,x+25,y+33,w-45,9.6,11.8,INK,max_height=26)

def build(output:Path):
    output.parent.mkdir(parents=True,exist_ok=True)
    pdf=canvas.Canvas(str(output),pagesize=A4,pageCompression=1,invariant=1)
    pdf.setTitle('Would You Fund the Same AI Initiatives Today? | Executive A4 infographic')
    pdf.setAuthor('Jair Ribeiro')
    pdf.setSubject('The AI Portfolio Renewal Challenge — investment choice, clean-sheet judgment and constraints')
    pdf.setKeywords('AI investment, portfolio renewal, executive decision, A4, vector')
    # A4 background
    pdf.setFillColor(PAPER);pdf.rect(0,0,W,H,stroke=0,fill=1)
    # Header
    pdf.setFillColor(NAVY);pdf.rect(0,661,W,H-661,stroke=0,fill=1)
    pdf.setFillColor(COPPER);pdf.rect(M,805,35,3,stroke=0,fill=1)
    text(pdf,M+48,801,'EXECUTIVE AI BRIEFING  /  PORTFOLIO & VALUE','JRHeavy',9.1,colors.HexColor('#B7D8DE'))
    text(pdf,M,761,'Would you fund the same','JRSerif',27.5,WHITE)
    text(pdf,M,722,'AI initiatives today?','JRSerif',30,WHITE)
    para(pdf,'Existing AI commitments must earn the next investment. Compare them with the strongest credible alternative before approving another stage.',M,699,FULL-35,10.8,15,colors.HexColor('#E2EBF0'),max_height=44)
    # Thin accent separator
    pdf.setFillColor(CYAN);pdf.rect(M,659,70,2,stroke=0,fill=1)
    # Make incumbent compete
    label(pdf,'01','MAKE THE INCUMBENT COMPETE',631)
    gap=20;cw=(FULL-gap)/2
    investment_card(pdf,M,525,cw,TEAL,'EXISTING INITIATIVE','Incumbent','What can continuing deliver <b>from today</b>?')
    investment_card(pdf,M+cw+gap,525,cw,COPPER,'STRONGEST ALTERNATIVE','Other route','Another AI approach, a process fix, or no new spend.')
    pdf.setFillColor(NAVY);pdf.circle(W/2,568,13,stroke=0,fill=1)
    pdf.setFillColor(WHITE);pdf.setFont('JRHeavy',8);pdf.drawCentredString(W/2,565.2,'VS')
    # Two passes
    label(pdf,'02','TWO PASSES. ONE HONEST DECISION.',498)
    review_card(pdf,M,410,TEAL,'01','Clean-sheet judgment','Compare <b>future value</b>, observed evidence and shared capacity. Set aside unrecoverable past spending.')
    review_card(pdf,M,329,COPPER,'02','Restore real-world constraints','Include switching costs, service commitments, operating risk and the authority to make the change.')
    # Outcome choices
    label(pdf,'03','MAKE THE NEXT COMMITMENT',306)
    decision_card(pdf,M,218,cw,TEAL,'RENEW','Continue when the current route still has the strongest forward case.')
    decision_card(pdf,M+cw+gap,218,cw,COPPER,'REPLACE','Move capacity to a better option after transition costs.')
    decision_card(pdf,M,142,cw,SLATE,'TEST','Fund a bounded experiment to resolve material uncertainty.')
    decision_card(pdf,M+cw+gap,142,cw,INK,'STOP','Release discretionary spend when nothing earns the next commitment.')
    # Final decision prompt
    rounded(pdf,M,54,FULL,69,fill=NAVY,stroke=NAVY,radius=11,weight=.5)
    text(pdf,M+19,98,'THE LEADERSHIP STANDARD','JRHeavy',8.5,colors.HexColor('#93DCE4'))
    text(pdf,M+19,70,'Continuing is a decision, not a default.','JRSerif',18,WHITE)
    # subtle footer
    pdf.setStrokeColor(LINE);pdf.setLineWidth(.7);pdf.line(M,43,W-M,43)
    text(pdf,M,29,'JAIR RIBEIRO   /   AI LEADER','JRHeavy',8.2,NAVY)
    pdf.setFillColor(COPPER);pdf.setFont('JRHeavy',8.2);pdf.drawRightString(W-M,29,'JAIRRIBEIRO.COM')
    pdf.save()
    return output

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='/mnt/data/AI_Portfolio_Renewal_Infographic_A4_Vector.pdf');a=ap.parse_args()
    print(build(Path(a.out)))
