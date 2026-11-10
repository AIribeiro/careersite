#!/usr/bin/env python3
"""Original source-locked 8-control executive governance artwork (2026-11-10)."""
import argparse, importlib.util
from pathlib import Path
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[1]
mod=ROOT/"scripts/build_agents_agentic_executive_infographic.py"
sp=importlib.util.spec_from_file_location("premium_base",mod)
G=importlib.util.module_from_spec(sp);sp.loader.exec_module(G)
NAVY=G.NAVY; NAVY2=G.NAVY2; CYAN=G.CYAN; INK=G.INK
COPPER=G.COPPER; TEAL=G.TEAL; STEEL=G.STEEL; PAPER=G.PAPER; WHITE=G.WHITE

# Each one is traceable to a distinct control domain in the reviewed CMS article.
GROUPS=[
("01  SEE THE WORK","Visibility and risk classification","search",TEAL,
 [("01","AI INVENTORY","Record the workflow, AI component, purpose, data, use status and a named process owner.","Proof: reconcile live usage with access and supplier records.","Owner: business process owner","search"),
  ("02","RISK CLASSIFICATION","Separate legal classification from operational risk; consider harm, scale, reversibility and autonomy.","Proof: rationale, legal scope screening, renewal trigger.","Owner: process owner + risk advisers","target")]),
("02  TEST THE CONSEQUENCES","People, evidence and release quality","shield",COPPER,
 [("03","IMPACT ASSESSMENT","Examine privacy, people, rights, misuse, accessible recourse and downstream decisions.","Proof: proportional assessment, mitigations, sign-off.","Owner: business + privacy and legal","shield"),
  ("04","TESTING AND ASSURANCE","Test real tasks, difficult cases, security, fairness, failure recovery and material changes.","Proof: acceptance tests and independent challenge.","Owner: delivery + independent reviewer","search")]),
("03  KEEP ACTIONS WITHIN AUTHORITY","Data and meaningful human intervention","layers",TEAL,
 [("05","DATA CONTROLS","Approve sources, access, purpose, lineage, output handling, retention and leakage safeguards.","Proof: access, deletion and data-quality checks.","Owner: data + security; process owner accountable","layers"),
  ("06","HUMAN OVERSIGHT","Assign review, escalation, override, suspension and a safe fallback to trained people.","Proof: witnessed stop-and-restore exercise.","Owner: process owner and operational reviewers","shield")]),
("04  CONTROL AND RENEW PERMISSION","Runtime checks and independent feedback","loop",STEEL,
 [("07","AGENT AND ACTION CONTROLS","Bind identity, tools, limits, transaction context and separation of duties at execution.","Proof: disallowed and valid-but-wrong actions blocked.","Owner: business defines; security enforces","agent"),
  ("08","MONITORING AND AUDIT","Observe outcomes, drift, exceptions, incidents and logs; review sampled silent failures.","Proof: alert tests, audit samples and review actions.","Owner: service owner + independent assurance","chart")]),
]

def draw_header(im,title1,title2,short):
    G.gradient(im,NAVY,NAVY2,0,354)
    d=ImageDraw.Draw(im);G.waves(d,im.width,213,9)
    G.text(d,52,36,"EXECUTIVE AI BRIEFING  /  OPERATING CONTROLS",22,CYAN,True)
    d.line((52,81,615,81),fill=CYAN,width=4)
    G.text(d,51,104,title1,67,WHITE,True)
    G.text(d,51,197,title2,56,(238,191,151),True)
    G.para(d,57,287,short,24,im.width-100,35,(220,241,246))

def card(d,x,y,w,h,item,accent,compact=False):
    num,name,desc,proof,owner,ico=item
    G.roundrect(d,x,y,w,h,21)
    d.rounded_rectangle((x+17,y+17,x+75,y+65),radius=13,fill=(226,237,239))
    G.text(d,x+29,y+26,num,22,accent,True)
    G.icon(d,x+95,y+57,ico,accent,.62)
    sz=26 if not compact else 25
    G.text(d,x+135,y+23,name,G.fit(d,name,sz,w-158,True,19),INK,True)
    ty=y+86
    ty=G.para(d,x+30,ty,desc,21 if not compact else 22,w-60,32,INK)
    d.line((x+29,ty+7,x+w-30,ty+7),fill=(211,223,226),width=2)
    ty=G.para(d,x+30,ty+20,proof,20 if not compact else 21,w-60,29,accent,True)
    G.para(d,x+30,ty+7,owner,18 if not compact else 20,w-60,27,G.MUTED)

def desktop(out):
    W,H=1460,2440
    im=Image.new("RGB",(W,H),PAPER)
    draw_header(im,"8 AI GOVERNANCE","CONTROLS THAT WORK","From ownership and evidence to runtime limits and renewal.")
    d=ImageDraw.Draw(im)
    G.roundrect(d,40,375,W-80,108,23,fill=(237,244,245))
    G.icon(d,100,430,"shield",TEAL,.52)
    G.text(d,153,397,"THE EXECUTIVE TEST",26,TEAL,True)
    G.para(d,153,438,"Can the business prove a control works when an AI-enabled action actually happens?",22,1170,32,INK)
    for i,(heading,sub,ico,colour,pair) in enumerate(GROUPS):
        top=510+i*434
        G.section(d,40,top,heading,sub,ico,W-80,colour)
        for j,item in enumerate(pair):
            x=40+j*706
            card(d,x,top+101,678,308,item,colour)
    bottom=510+4*434
    d.rounded_rectangle((40,bottom+5,W-40,bottom+128),radius=23,fill=(231,240,242))
    G.text(d,65,bottom+19,"A PERMITTED ACTION CAN STILL BE THE WRONG ACTION",24,INK,True)
    G.para(d,65,bottom+61,"Check the customer, recipient, amount, timing and business context before execution.",23,W-140,33,G.MUTED)
    d.rounded_rectangle((40,bottom+153,W-40,bottom+234),radius=18,fill=NAVY2)
    G.text(d,63,bottom+168,"RELEASE GATE",25,CYAN,True)
    G.text(d,291,bottom+169,"APPROVE   /   LIMIT   /   REPAIR   /   STOP",27,WHITE,True)
    G.footer(im,2310)
    im.save(out/"desktop.png",optimize=True)

def mobile(out):
    W,H=900,4330
    im=Image.new("RGB",(W,H),PAPER)
    G.gradient(im,NAVY,NAVY2,0,360)
    d=ImageDraw.Draw(im);G.waves(d,W,220,6)
    G.text(d,35,40,"EXECUTIVE AI BRIEFING / OPERATING CONTROLS",18,CYAN,True)
    G.text(d,32,107,"8 AI GOVERNANCE",53,WHITE,True)
    G.text(d,32,196,"CONTROLS",66,(238,191,151),True)
    G.para(d,36,293,"Prove what the system may do, and why that authority can continue.",22,835,34,(226,241,246))
    G.roundrect(d,23,380,W-46,144,22,fill=(233,242,243))
    G.text(d,45,395,"THE TEST",27,TEAL,True)
    G.para(d,45,440,"Does the control work at the moment an action happens?",24,800,34,INK)
    y=550
    for heading,sub,ico,colour,pair in GROUPS:
        G.section(d,23,y,heading,sub,ico,854,colour)
        y+=99
        for item in pair:
            card(d,23,y,854,358,item,colour,True)
            y+=379
        y+=20
    d.rounded_rectangle((23,y,877,y+112),radius=20,fill=(232,241,242))
    G.text(d,42,y+12,"PERMITTED DOES NOT ALWAYS MEAN APPROPRIATE",21,INK,True)
    G.para(d,42,y+53,"Check recipient, amount, timing and context before action.",21,805,30,G.MUTED)
    y+=140
    d.rounded_rectangle((23,y,877,y+130),radius=22,fill=NAVY2)
    G.text(d,43,y+18,"THE LEADERSHIP RELEASE GATE",24,CYAN,True)
    G.text(d,43,y+72,"APPROVE  /  LIMIT  /  REPAIR  /  STOP",25,WHITE,True)
    G.footer(im,H-130,"Enterprise AI  •  Governance  •  Business Transformation")
    im.save(out/"mobile.png",optimize=True)
    assert y+130 < H-145,(y,H)

def pdf(out):
    im=Image.open(out/"desktop.png").convert("RGB")
    jpg=out/"print-onepage.jpg"
    im.save(jpg,"JPEG",quality=94,subsampling=0,optimize=True)
    c=canvas.Canvas(str(out/"infographic.pdf"),pagesize=A4,pageCompression=1)
    c.setTitle("Eight AI Governance Controls — Executive Operating Test")
    c.setAuthor("Jair Ribeiro")
    w,h=A4
    scale=min((w-22)/im.width,(h-22)/im.height)
    iw,ih=im.width*scale,im.height*scale
    c.drawImage(ImageReader(str(jpg)),(w-iw)/2,(h-ih)/2,width=iw,height=ih)
    c.showPage();c.save()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    desktop(out);mobile(out);pdf(out)
    for n in ("desktop.png","mobile.png","infographic.pdf"):
        print(n,(out/n).stat().st_size)
if __name__=="__main__": main()
