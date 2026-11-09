#!/usr/bin/env python3
"""Source-locked, original executive infographic: AI Agents & Agentic AI.

This release graphic is a decision aid to a specific reviewed Executive AI Briefing.
No statistics, company case histories or maturity certification are implied.
"""
from pathlib import Path
from math import sin
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[1]
NAVY=(5,31,54)
NAVY2=(8,55,82)
CYAN=(4,196,223)
INK=(19,43,62)
MUTED=(79,102,113)
COPPER=(192,132,91)
TEAL=(27,121,133)
STEEL=(95,119,143)
PAPER=(250,250,247)
WHITE=(255,255,254)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TITLE=FONT
def f(size,bold=False): return ImageFont.truetype(BOLD if bold else FONT,size)
def text(d,x,y,s,size=24,color=INK,bold=False):
    d.text((int(x),int(y)),str(s),font=f(size,bold),fill=color)
def fit(d,s,size,w,bold=False,minsize=16):
    while d.textlength(s,font=f(size,bold))>w and size>minsize: size-=1
    return size
def wrap(d,s,size,w,bold=False):
    out=[]; buf=""
    for word in s.split():
        nxt=(buf+" "+word).strip()
        if buf and d.textlength(nxt,font=f(size,bold))>w:
            out.append(buf);buf=word
        else: buf=nxt
    if buf: out.append(buf)
    return out
def para(d,x,y,s,size=23,width=500,line=35,color=MUTED,bold=False):
    for i,t in enumerate(wrap(d,s,size,width,bold)):text(d,x,y+i*line,t,size,color,bold)
    return y+len(wrap(d,s,size,width,bold))*line
def roundrect(d,x,y,w,h,r=22,fill=WHITE,outline=(213,225,229),border=2):
    d.rounded_rectangle((x+3,y+7,x+w+3,y+h+7),radius=r,fill=(231,237,238))
    d.rounded_rectangle((x,y,x+w,y+h),radius=r,fill=fill,outline=outline,width=border)
def gradient(im,top,bottom,y0,y1):
    d=ImageDraw.Draw(im)
    for y in range(y0,y1):
        alpha=(y-y0)/max(1,y1-y0)
        d.line((0,y,im.width,y),fill=tuple(round(top[i]*(1-alpha)+bottom[i]*alpha) for i in range(3)))
def waves(d,W,y0,n=9):
    for j in range(n):
        pts=[(x,y0+9*j+int(20*sin(x/135+j*.36))) for x in range(0,W+1,5)]
        d.line(pts,fill=(7,85+j*3,116+j*3),width=2)
def icon(d,x,y,name,color=TEAL,scale=1):
    s=scale; z=lambda n:int(n*s); w=max(3,z(4))
    if name=="target":
        for r in (31,19,7):d.ellipse((x-z(r),y-z(r),x+z(r),y+z(r)),outline=color,width=w)
        d.line((x,y,x+z(37),y-z(37)),fill=COPPER,width=w)
    elif name=="flow":
        for xx,yy in [(-26,-21),(26,-21),(0,27)]:
            d.rounded_rectangle((x+z(xx-12),y+z(yy-12),x+z(xx+12),y+z(yy+12)),radius=z(4),outline=color,width=w)
        d.line((x-z(14),y-z(21),x+z(14),y-z(21)),fill=color,width=w)
        d.line((x,y-z(21),x,y+z(13)),fill=color,width=w)
    elif name=="agent":
        d.ellipse((x-z(32),y-z(31),x+z(32),y+z(33)),outline=color,width=w)
        d.ellipse((x-z(10),y-z(9),x+z(10),y+z(11)),outline=color,width=w)
        for dx,dy in [(-22,18),(22,18),(-20,-20),(20,-20)]:
            d.line((x+z(dx*.5),y+z(dy*.5),x+z(dx),y+z(dy)),fill=color,width=w)
            d.ellipse((x+z(dx-4),y+z(dy-4),x+z(dx+4),y+z(dy+4)),fill=color)
    elif name=="layers":
        for off in [0,12,24]:
            pts=[(x,y-z(31)+z(off)),(x+z(38),y-z(9)+z(off)),(x,y+z(13)+z(off)),(x-z(38),y-z(9)+z(off))]
            d.line(pts+[pts[0]],fill=color,width=w,joint="curve")
    elif name=="shield":
        pts=[(x,y-z(39)),(x+z(34),y-z(26)),(x+z(29),y+z(21)),(x,y+z(42)),(x-z(29),y+z(21)),(x-z(34),y-z(26)),(x,y-z(39))]
        d.line(pts,fill=color,width=w,joint="curve")
        d.line([(x-z(18),y),(x-z(2),y+z(16)),(x+z(20),y-z(16))],fill=COPPER,width=w+1)
    elif name=="search":
        d.ellipse((x-z(28),y-z(30),x+z(15),y+z(14)),outline=color,width=w)
        d.line((x+z(13),y+z(12),x+z(40),y+z(38)),fill=color,width=w+2)
    elif name=="loop":
        d.arc((x-z(34),y-z(33),x+z(34),y+z(33)),20,190,fill=color,width=w+1)
        d.arc((x-z(34),y-z(33),x+z(34),y+z(33)),200,365,fill=color,width=w+1)
        d.polygon([(x-z(36),y-z(3)),(x-z(42),y-z(25)),(x-z(19),y-z(17))],fill=color)
        d.polygon([(x+z(36),y+z(3)),(x+z(42),y+z(25)),(x+z(19),y+z(17))],fill=color)
    elif name=="clock":
        d.ellipse((x-z(31),y-z(31),x+z(31),y+z(31)),outline=color,width=w)
        d.line((x,y,x,y-z(19)),fill=color,width=w)
        d.line((x,y,x+z(17),y+z(12)),fill=COPPER,width=w)
    elif name=="chart":
        for j,h in enumerate((20,36,52)):d.rounded_rectangle((x+z(-35+j*25),y+z(27-h),x+z(-20+j*25),y+z(27)),radius=z(3),fill=color)
    else:
        d.rounded_rectangle((x-z(28),y-z(33),x+z(28),y+z(33)),radius=z(6),outline=color,width=w)
def section(d,x,y,title,subtitle,iconname,W,bar=TEAL):
    d.rounded_rectangle((x,y,x+W,y+85),radius=18,fill=bar)
    icon(d,x+48,y+40,iconname,(232,250,252),.68)
    text(d,x+90,y+15,title,28,WHITE,True)
    text(d,x+92,y+52,subtitle,17,(230,243,245))
def portrait(im,x,y,r):
    p=ROOT/"static/briefing-roi-portrait.webp"
    if not p.exists():return
    src=Image.open(p).convert("RGB")
    src=ImageOps.fit(src,(2*r,2*r),method=Image.Resampling.LANCZOS,centering=(.5,.33))
    mask=Image.new("L",(2*r,2*r),0)
    ImageDraw.Draw(mask).ellipse((0,0,2*r-1,2*r-1),fill=255)
    d=ImageDraw.Draw(im)
    d.ellipse((x-r-5,y-r-5,x+r+5,y+r+5),fill=WHITE)
    im.paste(src,(x-r,y-r),mask)
def footer(im,y,descriptor="Enterprise AI Adoption  •  Governance  •  Business Transformation"):
    gradient(im,NAVY,NAVY2,y,im.height)
    d=ImageDraw.Draw(im);waves(d,im.width,im.height-68,5)
    portrait(im,98,y+65,47)
    d=ImageDraw.Draw(im)
    text(d,165,y+16,"Jair Ribeiro",39,WHITE,True)
    text(d,167,y+66,"AI LEADER",23,CYAN,True)
    text(d,360,y+71,descriptor,19,(226,239,245))
ARCH=[
 ("MODEL + RETRIEVAL","One defined answer","Summarise a specified file; explain a policy.","model"),
 ("DEFINED WORKFLOW","Predictable sequence","Extract, check, route, then seek approval.","flow"),
 ("BOUNDED AGENT","Uncertain next step","Search, decide the next tool, check the result.","agent"),
 ("COORDINATED AGENTS","Genuine specialist benefit","Different roles or permissions; reviewed handoffs.","layers"),
]
SIX=[
 ("01","BUSINESS OUTCOME","Named process owner and a baseline for quality, time, cost and customer effect.","target"),
 ("02","MINIMUM DISCRETION","Show why a prompt or fixed workflow is insufficient; compare alternatives.","flow"),
 ("03","ACTION PERMISSION","Allowed identity, data, tools and write actions; human approval and limits.","shield"),
 ("04","FAILURE CONTROLS","Bound time, retries and spend; stop, recover and record every action.","loop"),
 ("05","INDEPENDENT PROOF","Sample non-escalated cases; test silent mistakes, handoffs and prohibited acts.","search"),
 ("06","RENEWABLE MANDATE","Assign operations, incidents and review; restrict or revoke when evidence shifts.","clock"),
]
RISKS=[
 ("Wrong action","Tool, argument or evidence errors","Representative cases; tool allowlists"),
 ("Broken handoff","Lost state, duplicate or stale steps","State and transaction validation"),
 ("Untrusted content","Prompt injection through retrieved data","Least privilege; inputs not authority"),
 ("Runaway execution","Excess retries, latency or spend","Iteration, cost and time ceilings"),
 ("Silent failure","Errors that never reach a person","Independent sampling and audits"),
]
METRICS=[
 ("BUSINESS","End-to-end quality, time, customer result"),
 ("CONTROL","Unsafe attempts, unreported errors, interventions"),
 ("ECONOMICS","Full cost per acceptable result; realized benefit"),
]
def desktop(out):
    W,H=1460,3190
    im=Image.new("RGB",(W,H),PAPER)
    gradient(im,NAVY,NAVY2,0,372)
    d=ImageDraw.Draw(im);waves(d,W,240,13)
    text(d,66,45,"EXECUTIVE AI BRIEFING  /  DECISION MAP",22,CYAN,True)
    d.line((65,89,500,89),fill=CYAN,width=4)
    text(d,62,118,"AI AGENTS &",78,WHITE,True)
    text(d,62,218,"AGENTIC AI",95,(239,197,153),True)
    text(d,68,334,"Select the right architecture. Control the authority. Prove the outcome.",25,(230,246,249))
    d=ImageDraw.Draw(im)
    roundrect(d,42,394,1376,268,24)
    text(d,72,419,"THE DISTINCTION THAT MATTERS",27,INK,True)
    d.line((72,464,1388,464),fill=(205,220,225),width=2)
    icon(d,122,548,"agent",TEAL,.95)
    text(d,193,480,"AI AGENT",28,TEAL,True)
    para(d,193,521,"A model-directed decision unit that can select tools and next actions inside limits.",22,490,33)
    d.line((737,475,737,632),fill=(207,222,229),width=3)
    icon(d,810,550,"loop",COPPER,.95)
    text(d,886,480,"AGENTIC BEHAVIOUR",28,(164,98,63),True)
    para(d,886,521,"Goal-seeking execution that adapts to feedback; one agent or many.",22,460,33)
    text(d,76,612,"Agent count is not an autonomy measure. A multi-agent system may still follow fixed steps.",19,STEEL)
    section(d,43,689,"01  CHOOSE THE SIMPLEST SUFFICIENT DESIGN","Four options, selected by the real uncertainty in the work","flow",1373,TEAL)
    for i,(name,trigger,example,symbol) in enumerate(ARCH):
        col=i%2;row=i//2;x=43+col*703;y=797+row*236
        roundrect(d,x,y,674,213,24)
        icon(d,x+66,y+75,symbol,TEAL,.9)
        text(d,x+119,y+20,name,25,INK,True)
        text(d,x+120,y+66,trigger,22,TEAL,True)
        para(d,x+120,y+106,example,20,514,32)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((70,1277,1386,1347),radius=16,fill=(222,238,240))
    text(d,89,1293,"USE AGENT LOOPS ONLY WHEN THE NEXT STEP MUST CHANGE WITH THE EVIDENCE.",23,INK,True)
    section(d,43,1372,"02  SIX LEADERSHIP DECISIONS","The operating contract every proposed agent should be able to show","shield",1373,(166,113,78))
    for i,(num,name,detail,symbol) in enumerate(SIX):
        col=i%2;row=i//2;x=43+col*703;y=1475+row*222
        roundrect(d,x,y,674,201,22)
        d.rounded_rectangle((x+21,y+18,x+77,y+64),radius=12,fill=(230,239,242))
        text(d,x+30,y+25,num,22,TEAL,True)
        icon(d,x+104,y+123,symbol,TEAL,.72)
        text(d,x+144,y+26,name,25,INK,True)
        para(d,x+145,y+72,detail,20,492,32)
    section(d,43,2166,"03  EXPECT FAILURES BETWEEN DECISIONS","Independent controls must check the completed outcome, not merely the agent's trace","search",1373,STEEL)
    d=ImageDraw.Draw(im)
    roundrect(d,43,2274,1373,412,24)
    d.rounded_rectangle((59,2288,1397,2350),radius=11,fill=(228,238,240))
    text(d,80,2306,"FAILURE MODE",23,INK,True)
    text(d,515,2306,"WHY IT HAPPENS",23,INK,True)
    text(d,994,2306,"EXPECTED PROOF",23,INK,True)
    for i,(a,b,c) in enumerate(RISKS):
        y=2366+i*58
        if i%2:d.rectangle((60,y-7,1396,y+51),fill=(249,250,249))
        text(d,80,y,a,19,INK,True)
        para(d,515,y,b,17,420,25)
        para(d,994,y,c,17,377,25)
        if i<4:d.line((76,y+50,1384,y+50),fill=(222,231,232),width=2)
    section(d,43,2713,"04  MEASURE WHAT AUTONOMY CHANGES","Do not confuse fewer escalations with fewer undetected mistakes","chart",1373,NAVY2)
    for i,(head,desc) in enumerate(METRICS):
        x=43+i*470
        roundrect(d,x,2824,437,171,22)
        text(d,x+22,2842,head,24,TEAL if i!=1 else (166,106,75),True)
        para(d,x+22,2886,desc,18,394,29)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((44,3013,1414,3067),radius=15,fill=(229,238,240))
    text(d,65,3023,"RELEASE RULE   Approve only the authority, evidence and stop rights a real business outcome justifies.",22,INK,True)
    footer(im,3080)
    im.save(out/"desktop.png",optimize=True)
def mobile(out):
    W,H=900,4930
    im=Image.new("RGB",(W,H),PAPER)
    gradient(im,NAVY,NAVY2,0,430)
    d=ImageDraw.Draw(im);waves(d,W,298,9)
    text(d,38,46,"EXECUTIVE AI BRIEFING / DECISION MAP",21,CYAN,True)
    text(d,33,120,"AI AGENTS &",58,WHITE,True)
    text(d,33,216,"AGENTIC AI",71,(240,194,153),True)
    para(d,38,338,"Choose the design. Set the limits. Prove the business result.",25,820,36,(231,243,245))
    d=ImageDraw.Draw(im)
    roundrect(d,23,451,854,348,24)
    text(d,45,470,"WHAT THE TERMS MEAN",29,INK,True)
    icon(d,91,563,"agent",TEAL,.85)
    text(d,161,529,"AI AGENT",24,TEAL,True)
    para(d,161,569,"Chooses a next step or tool inside assigned limits.",22,660,32)
    icon(d,91,701,"loop",COPPER,.85)
    text(d,161,661,"AGENTIC BEHAVIOUR",24,(170,103,69),True)
    para(d,161,704,"Adapts a goal-directed process to new information.",22,660,32)
    section(d,23,828,"01  ARCHITECTURE CHOICE","Complexity requires a reason","flow",854,TEAL)
    for i,(name,trigger,example,symbol) in enumerate(ARCH):
        y=935+i*219
        roundrect(d,23,y,854,198,22)
        icon(d,94,y+93,symbol,TEAL,.9)
        text(d,158,y+21,name,27,INK,True)
        text(d,159,y+70,trigger,23,TEAL,True)
        para(d,159,y+109,example,20,675,32)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((23,1824,877,1904),radius=16,fill=(225,238,241))
    para(d,43,1843,"One adaptive agent can be enough. Multiple agents are not automatically better.",21,810,30,INK,True)
    section(d,23,1932,"02  THE AUTHORITY CONTRACT","Six approvals and the proof behind each","shield",854,(166,113,78))
    for i,(num,name,detail,symbol) in enumerate(SIX):
        y=2042+i*250
        roundrect(d,23,y,854,228,22)
        d.rounded_rectangle((42,y+20,105,y+75),radius=12,fill=(226,239,242))
        text(d,56,y+30,num,24,TEAL,True)
        icon(d,108,y+147,symbol,TEAL,.9)
        text(d,172,y+26,name,27,INK,True)
        para(d,172,y+83,detail,23,664,35)
    section(d,23,3564,"03  FAILURE & INDEPENDENT CHECKS","Failures can occur inside and between agents","search",854,STEEL)
    roundrect(d,23,3671,854,441,22)
    d=ImageDraw.Draw(im)
    for i,(a,b,c) in enumerate(RISKS):
        y=3688+i*82
        text(d,43,y,a.upper(),19,INK,True)
        para(d,263,y,b,17,565,26)
        para(d,263,y+30,"Check: "+c,16,560,25,TEAL)
        if i<4:d.line((43,y+74,856,y+74),fill=(217,231,232),width=2)
    section(d,23,4140,"04  OUTCOMES TO MEASURE","Always audit non-escalated cases","chart",854,NAVY2)
    for i,(head,desc) in enumerate(METRICS):
        y=4253+i*146
        roundrect(d,23,y,854,128,22)
        text(d,45,y+17,head,24,TEAL,True)
        para(d,45,y+57,desc,20,800,31)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((23,4717,877,4787),radius=18,fill=(223,237,240))
    para(d,45,4730,"APPROVE SMALL. CHECK INDEPENDENTLY. EXPAND ON EVIDENCE.",21,814,29,INK,True)
    footer(im,4800,"Enterprise AI  •  Governance  •  Business Value")
    im.save(out/"mobile.png",optimize=True)
def pdf(out):
    # A4 source-identical print bundle. Three readable pages, no text re-generation.
    page=A4
    C=canvas.Canvas(str(out/"infographic.pdf"),pagesize=page)
    C.setAuthor("Jair Ribeiro")
    C.setTitle("AI Agents & Agentic AI — Executive Decision Map")
    src=Image.open(out/"desktop.png").convert("RGB")
    # Print as three continuous source-locked panels with deliberate overlap.
    cuts=[(0,1185),(1050,2255),(2110,3190)]
    for n,(top,bottom) in enumerate(cuts):
        panel=src.crop((0,top,1460,bottom))
        local=out/f"print-{n+1}.jpg"
        panel.save(local,"JPEG",quality=93,subsampling=0,optimize=True)
        pw,ph=page
        scale=min((pw-32)/panel.width,(ph-45)/panel.height)
        w,h=panel.width*scale,panel.height*scale
        C.drawImage(ImageReader(str(local)),(pw-w)/2,(ph-h)/2,width=w,height=h)
        C.setFont("Helvetica",8)
        C.setFillColorRGB(.23,.33,.39)
        C.drawRightString(pw-18,14,f"Jair Ribeiro | Executive AI Briefing | {n+1}/3")
        C.showPage()
    C.save()
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    args=p.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    desktop(out);mobile(out);pdf(out)
    for name in ("desktop.png","mobile.png","infographic.pdf"):
        print(name,(out/name).stat().st_size)
if __name__=="__main__":
    main()
