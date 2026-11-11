#!/usr/bin/env python3
"""Source-locked executive AI adoption/emotional-intelligence infographic.
Original analytical diagram; no client or employer claims. One-page A4.
"""
import argparse
import importlib.util
from pathlib import Path
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("premium",ROOT/"scripts/build_agents_agentic_executive_infographic.py")
G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
NAVY,NAVY2,CYAN,INK,COPPER,TEAL,STEEL,PAPER,WHITE=(G.NAVY,G.NAVY2,G.CYAN,G.INK,G.COPPER,G.TEAL,G.STEEL,G.PAPER,G.WHITE)
SIG=[
 ("01","RESISTANCE","Concern about job security, autonomy, professional identity or unresolved risks.","Ask what the person is trying to protect. Test whether the work or decision rights must change.","shield",TEAL),
 ("02","SKEPTICISM","Doubts about reliability, business value, safety or promises that were not delivered.","Invite specific failure cases. Compare the output, corrections and costs with a baseline.","search",STEEL),
 ("03","LOW ENGAGEMENT","Unclear relevance, competing priorities, fatigue or little say in the process.","Examine the actual workflow and managerial support. Remove practical barriers.","flow",COPPER),
 ("04","UNEVEN AI LITERACY","Different experience, confidence and ability to judge AI limitations.","Set role-specific practice: verify output, protect data, escalate and remain accountable.","layers",TEAL)
]
STEPS=[
 ("01","RECOGNIZE","Notice the signal, without diagnosing a person.","search"),
 ("02","UNDERSTAND","Explore competing explanations and real work.","agent"),
 ("03","RESPOND","Choose an action proportional to the cause.","target"),
 ("04","VERIFY","Check changes in work, trust and outcomes.","chart"),
]
CAPS=[
 ("SELF-AWARENESS","Notice defensiveness and assumptions."),
 ("SELF-REGULATION","Stay calm when the project is challenged."),
 ("PERSPECTIVE-TAKING","Consider the roles and consequences affected."),
 ("CONSTRUCTIVE CHALLENGE","Test claims instead of defending or dismissing."),
 ("RELATIONSHIP JUDGMENT","Keep challenge safe and accountability clear."),
]
def ctext(d,x,y,s,sz,col=INK,b=False):
    G.text(d,x,y,s,sz,col,b)
def pill(d,x,y,w,h,col):
    d.rounded_rectangle((x,y,x+w,y+h),radius=18,fill=col)
def header(im,mobile=False):
    w=im.width; h=355 if mobile else 325
    G.gradient(im,NAVY,NAVY2,0,h)
    d=ImageDraw.Draw(im);G.waves(d,w,h-100,6)
    if not mobile:
        ctext(d,52,30,"EXECUTIVE AI BRIEFING  /  HUMAN JUDGMENT",22,CYAN,True)
        d.line((52,81,660,81),fill=CYAN,width=4)
        ctext(d,49,103,"EMOTIONAL INTELLIGENCE",60,WHITE,True)
        ctext(d,49,184,"IN AI LEADERSHIP",75,(239,192,153),True)
        G.para(d,54,281,"Read the human signals behind adoption. Test their meaning. Make an accountable decision.",23,w-120,32,(226,239,243))
    else:
        ctext(d,30,35,"EXECUTIVE AI BRIEFING / HUMAN JUDGMENT",19,CYAN,True)
        ctext(d,27,105,"EMOTIONAL",56,WHITE,True)
        ctext(d,27,180,"INTELLIGENCE + AI",52,(239,192,153),True)
        G.para(d,31,267,"Diagnose resistance, skepticism, engagement and AI literacy before deciding.",21,w-65,31,(230,244,246))
def footer_mobile(im,y):
    G.gradient(im,NAVY,NAVY2,y,im.height);d=ImageDraw.Draw(im)
    G.portrait(im,81,y+73,45)
    ctext(d,147,y+25,"Jair Ribeiro",40,WHITE,True)
    ctext(d,149,y+81,"AI LEADER",25,CYAN,True)
    ctext(d,147,y+120,"Enterprise AI Adoption  •  Governance",20,(225,241,245))
    ctext(d,147,y+149,"Business Transformation",20,(225,241,245))
def signal_card(d,x,y,w,h,item,small=False):
    num,title,problem,response,ic,col=item
    G.roundrect(d,x,y,w,h,21)
    pill(d,x+16,y+15,w-32,66,col)
    G.icon(d,x+62,y+47,ic,WHITE,.59)
    ctext(d,x+111,y+22,num+"  "+title,28 if not small else 27,WHITE,True)
    ctext(d,x+30,y+105,"WHAT MAY BE HAPPENING",17,col,True)
    yy=G.para(d,x+30,y+140,problem,21 if not small else 22,w-60,30,INK)
    d.line((x+30,yy+9,x+w-30,yy+9),fill=(211,224,228),width=2)
    ctext(d,x+30,yy+21,"EXECUTIVE RESPONSE",17,col,True)
    G.para(d,x+30,yy+52,response,21 if not small else 22,w-60,30,INK)
def desktop(out):
    W,H=1460,2065
    im=Image.new("RGB",(W,H),PAPER);header(im);d=ImageDraw.Draw(im)
    G.roundrect(d,40,348,1380,166,22,fill=(233,242,244))
    G.icon(d,98,430,"target",TEAL,.75)
    ctext(d,153,367,"THE LEADERSHIP DECISION",27,TEAL,True)
    G.para(d,154,411,"Listen to what people are experiencing, then use evidence to decide what the business should change. Empathy is not agreement; adoption is not a login count.",24,1210,36,INK)
    ctext(d,45,541,"FOUR ADOPTION SIGNALS — FOUR DIFFERENT INQUIRIES",29,INK,True)
    for i,it in enumerate(SIG):
        x=43+(i%2)*708;y=593+(i//2)*299
        signal_card(d,x,y,679,276,it)
    ctext(d,45,1211,"AN EXECUTIVE RESPONSE FRAMEWORK",29,INK,True)
    for i,(num,title,desc,ic) in enumerate(STEPS):
        x=43+i*354
        G.roundrect(d,x,1263,327,187,21,fill=(246,250,250))
        G.icon(d,x+54,1318,ic,(36,117,129),.60)
        ctext(d,x+99,1285,num,21,COPPER,True)
        ctext(d,x+99,1321,title,25,INK,True)
        G.para(d,x+28,1380,desc,21,272,30,STEEL)
    ctext(d,45,1480,"FIVE CAPABILITIES EXECUTIVES CAN PRACTISE",29,INK,True)
    for i,(cap,detail) in enumerate(CAPS):
        x=44+i*282
        G.roundrect(d,x,1532,265,244,18)
        d.rounded_rectangle((x+15,1548,x+250,1608),radius=13,fill=(230,241,242))
        ctext(d,x+25,1565,cap,G.fit(d,cap,21,213,True,14),TEAL,True)
        G.para(d,x+22,1632,detail,21,219,34,INK)
    G.roundrect(d,43,1803,1374,114,22,fill=(232,242,244))
    G.icon(d,99,1854,"loop",COPPER,.65)
    ctext(d,145,1816,"EXECUTIVE PROOF",24,TEAL,True)
    G.para(d,145,1852,"Show the concern, competing explanations, owner, chosen action and evidence of changed work.",23,1200,32,INK)
    G.footer(im,1940)
    im.save(out/"desktop.png",optimize=True)
def mobile(out):
    W,H=900,4260
    im=Image.new("RGB",(W,H),PAPER);header(im,True);d=ImageDraw.Draw(im)
    G.roundrect(d,22,377,856,260,24,fill=(233,242,244))
    ctext(d,48,398,"THE LEADERSHIP DECISION",29,TEAL,True)
    G.para(d,48,457,"Recognize the human reaction, test what causes it and decide what must change in the work. Empathy does not replace evidence or accountability.",23,793,37,INK)
    ctext(d,26,664,"FOUR SIGNALS",38,INK,True)
    for i,it in enumerate(SIG):
        signal_card(d,23,734+i*390,854,364,it,True)
    y=2334
    ctext(d,27,y,"THE RESPONSE ROUTINE",36,INK,True)
    for i,(num,title,desc,ic) in enumerate(STEPS):
        sy=y+74+i*218
        G.roundrect(d,23,sy,854,193,22)
        G.icon(d,105,sy+94,ic,TEAL,.83)
        ctext(d,170,sy+26,num+"   "+title,29,INK,True)
        G.para(d,171,sy+81,desc,23,660,35,STEEL)
    y=3320
    ctext(d,27,y,"FIVE LEADERSHIP CAPABILITIES",32,INK,True)
    for i,(cap,detail) in enumerate(CAPS):
        cy=y+63+i*124
        G.roundrect(d,23,cy,854,107,18)
        ctext(d,45,cy+14,cap,24,TEAL,True)
        G.para(d,45,cy+53,detail,21,800,30,INK)
    y=4025
    G.roundrect(d,23,y,854,66,13,fill=(235,243,244))
    G.para(d,43,y+13,"PROOF: concerns investigated, actions owned and work outcomes reviewed.",20,811,31,INK,True)
    footer_mobile(im,4100)
    im.save(out/"mobile.png",optimize=True)
def pdf(out):
    p=out/"infographic.pdf"
    src=out/"desktop.png"
    c=canvas.Canvas(str(p),pagesize=A4,pageCompression=1)
    c.drawImage(ImageReader(str(src)),0,0,width=A4[0],height=A4[1])
    c.showPage();c.save()
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",required=True)
    o=Path(ap.parse_args().output);o.mkdir(parents=True,exist_ok=True)
    desktop(o);mobile(o);pdf(o)
    for f in ("desktop.png","mobile.png","infographic.pdf"):print(f,(o/f).stat().st_size)
if __name__=="__main__": main()
