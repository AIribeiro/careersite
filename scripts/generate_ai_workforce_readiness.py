#!/usr/bin/env python3
"""Original source-locked premium infographic: AI workforce readiness release decision."""
from __future__ import annotations
import argparse
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

ROOT=Path(__file__).resolve().parents[1]
NAVY="#06213A"; NAVY2="#123D60"; CYAN="#04C7EC"; COPPER="#BF8965"
TEAL="#267A7A"; STEEL="#57788D"; INK="#173149"; TEXT="#4B6273"
BG="#FCFAF7"; WHITE="#FFFFFF"; EDGE="#DDE7E9"; PALE="#EDF5F6"
REG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ROWS=[
("01","ACCOUNTABILITY","Name the business owner","One sponsor for enterprise readiness; one process owner for demonstrated competence.","person"),
("02","SAFE BASELINE","Define permitted practice","Approved tools; privacy, security, verification, limits and escalation in daily work.","shield"),
("03","FUNDED LEARNING","Budget beyond the licence","Practice time, peer support, coaching and updates belong in the investment case.","coins"),
("04","REAL WORK","Demonstrate proficiency","Use real tasks and AI champions; assess decisions, not training attendance.","work"),
("05","TALENT SYSTEM","Plan for AI judgment","Assess role-specific skills in hiring, onboarding, career growth and role changes.","people"),
("06","OPERATING EVIDENCE","Decide from outcomes","Review quality, rework, appropriate use and results; expand, support or hold.","bars"),
]
METRICS=[
("82%","of surveyed CEOs","use AI"),
("22%","report a comprehensive","AI governance policy"),
("42%","of organisations with","full or partial policy","train on AI use/policies"),
("6%","require AI skills","in job postings"),
("39%","do not consider","AI skills in hiring"),
]
def rgb(c):return tuple(int(c[i:i+2],16) for i in (1,3,5))
def f(sz,bold=False):return ImageFont.truetype(BOLD if bold else REG,sz)
def t(d,x,y,s,z,c,b=False):d.text((x,y),s,font=f(z,b),fill=c)
def wrap(d,content,width,size,bold=False):
    out=[];line=""
    for word in content.split():
        candidate=(line+" "+word).strip()
        if d.textbbox((0,0),candidate,font=f(size,bold))[2]<=width:line=candidate
        else:
            if line:out.append(line)
            line=word
    if line:out.append(line)
    return out
def p(d,x,y,s,w,z,c,b=False,limit=4,leading=1.33):
    lines=wrap(d,s,w,z,b)
    if len(lines)>limit:raise ValueError("Text overflow: "+s+" -> "+repr(lines))
    for ln in lines:t(d,x,y,ln,z,c,b);y+=int(z*leading)
    return y
def rr(d,coords,fill,r=18,stroke=EDGE,sw=2):d.rounded_rectangle(coords,radius=r,fill=fill,outline=stroke,width=sw)
def gradient(im,box,start,end):
    d=ImageDraw.Draw(im);a=rgb(start);b=rgb(end);x0,y0,x1,y1=box
    for y in range(y0,y1):
        u=(y-y0)/max(1,y1-y0-1);c=tuple(int(a[i]*(1-u)+b[i]*u) for i in range(3))
        d.line((x0,y,x1,y),fill=c)
def icon(d,which,x,y,s=74,color=INK):
    z=s/70;X=lambda a:int(x+a*z);Y=lambda a:int(y+a*z);W=max(3,int(3.2*z))
    if which=="person":
        d.ellipse((X(25),Y(3),X(46),Y(24)),outline=color,width=W)
        d.arc((X(13),Y(25),X(58),Y(78)),180,360,fill=color,width=W)
        d.ellipse((X(48),Y(40),X(64),Y(56)),outline=COPPER,width=W)
    elif which=="shield":
        d.line([(X(35),Y(3)),(X(60),Y(14)),(X(54),Y(49)),(X(35),Y(66)),(X(16),Y(49)),(X(10),Y(14)),(X(35),Y(3))],fill=color,width=W)
        d.line([(X(24),Y(34)),(X(33),Y(43)),(X(48),Y(25))],fill=COPPER,width=W)
    elif which=="coins":
        for cx,cy in ((8,23),(33,14),(16,45)):
            d.ellipse((X(cx),Y(cy),X(cx+27),Y(cy+13)),outline=color,width=W)
            d.arc((X(cx),Y(cy+5),X(cx+27),Y(cy+24)),0,180,fill=color,width=W)
        d.line((X(42),Y(54),X(57),Y(54)),fill=COPPER,width=W)
    elif which=="work":
        d.rounded_rectangle((X(5),Y(13),X(65),Y(57)),radius=int(5*z),outline=color,width=W)
        d.line((X(26),Y(65),X(44),Y(65)),fill=color,width=W)
        d.line((X(35),Y(57),X(35),Y(65)),fill=color,width=W)
        t(d,X(22),Y(23),"AI",int(19*z),COPPER,True)
    elif which=="people":
        for cx,cy in ((10,17),(32,7),(51,18)):
            d.ellipse((X(cx),Y(cy),X(cx+14),Y(cy+14)),outline=color,width=W)
        d.arc((X(17),Y(26),X(55),Y(68)),185,355,fill=COPPER,width=W)
        d.arc((X(0),Y(32),X(28),Y(65)),185,355,fill=color,width=W)
        d.arc((X(43),Y(32),X(70),Y(65)),185,355,fill=color,width=W)
    elif which=="bars":
        for ax,h in ((10,18),(30,33),(50,52)):
            d.rectangle((X(ax),Y(62-h),X(ax+12),Y(62)),outline=color,width=W)
        d.line((X(4),Y(63),X(67),Y(63)),fill=COPPER,width=W)
def portrait(im,x,y,r):
    src=ROOT/"images"/"profile_red_bg.jpg.jpg"
    d=ImageDraw.Draw(im)
    d.ellipse((x-r-5,y-r-5,x+r+5,y+r+5),fill=WHITE)
    if not src.is_file():return
    with Image.open(src) as image:
        if image.width>800:
            a,b=image.size;image=image.crop((int(a*.42),int(b*.16),int(a*.70),int(b*.60)))
        image=ImageOps.fit(image.convert("RGB"),(2*r,2*r),method=Image.Resampling.LANCZOS,centering=(.5,.4))
    mask=Image.new("L",(2*r,2*r),0);ImageDraw.Draw(mask).ellipse((0,0,2*r,2*r),fill=255)
    im.paste(image,(x-r,y-r),mask)
def head(im,mobile):
    w=im.width;h=530 if mobile else 365;gradient(im,(0,0,w,h),NAVY,NAVY2);d=ImageDraw.Draw(im)
    for k in range(4):d.arc((-80,40+k*20,w+200,360+k*19),190,330,fill="#245A79",width=3)
    x=43 if mobile else 72
    d.rectangle((x,49,x+9,122),fill=COPPER)
    t(d,x+31,54,"EXECUTIVE AI BRIEFING   /   ADOPTION",20 if mobile else 22,CYAN,True)
    if mobile:
        t(d,x,149,"AI ACCESS IS NOT",48,WHITE,True)
        t(d,x,220,"WORKFORCE",52,WHITE,True)
        t(d,x,290,"READINESS",56,"#D8A782",True)
        p(d,x,390,"A release decision: six commitments before the next expansion.",w-86,25,"#E4EDF4",limit=3)
    else:
        t(d,x,145,"AI ACCESS IS NOT",67,WHITE,True)
        t(d,x,232,"WORKFORCE READINESS",66,"#E5B68D",True)
        t(d,x+2,325,"Six commitments turn a licence into operating capability.",24,"#DCEBF4")
def metrics(im,mobile):
    d=ImageDraw.Draw(im);w=im.width
    if mobile:
        y=548;t(d,45,y,"VISTAGE CEO RESEARCH  /  2026",24,TEAL,True)
        for i,m in enumerate(METRICS):
            col=i%2;row=i//2;x=39+col*359;top=605+row*177
            rr(d,(x,top,x+344,top+164),WHITE,16,EDGE)
            t(d,x+18,top+13,m[0],49,TEAL,True)
            for j,line in enumerate(m[1:]):t(d,x+19,top+79+j*27,line,19,INK)
        p(d,44,1155,"42% is conditional on respondents with comprehensive or partial AI policies. Different survey questions; not a readiness score.",w-90,18,TEXT,limit=4)
    else:
        y=389;t(d,68,y,"RESEARCH SIGNALS  /  NOT A CAPABILITY SCORE",21,TEAL,True)
        for i,m in enumerate(METRICS):
            x=39+i*274;top=447
            rr(d,(x,top,x+261,top+184),WHITE,17,EDGE)
            t(d,x+20,top+10,m[0],53,TEAL,True)
            for j,line in enumerate(m[1:]):t(d,x+19,top+89+j*26,line,18,INK)
        t(d,62,651,"Vistage CEO research, 2026. The 42% training figure applies only to the subgroup with full or partial policies.",18,TEXT)
def row(im,y,i,mobile):
    d=ImageDraw.Draw(im);w=im.width;n,tag,title,detail,glyph=ROWS[i];x=37 if mobile else 56
    height=272 if mobile else 182;right=w-x
    rr(d,(x,y,right,y+height),WHITE,22,EDGE)
    d.rounded_rectangle((x+13,y+21,x+(126 if mobile else 137),y+(147 if mobile else 155)),radius=17,fill=PALE,outline="#D0E5E6",width=2)
    icon(d,glyph,x+34,y+46,74 if mobile else 80)
    accent=TEAL if i<3 else COPPER
    d.rounded_rectangle((x+151 if mobile else x+159,y+26,x+156 if mobile else x+164,y+height-26),radius=2,fill=accent)
    bx=x+179 if mobile else x+196
    t(d,bx,y+22,n+"    "+tag,22 if mobile else 21,accent,True)
    p(d,bx,y+72,title,right-bx-24,29 if mobile else 31,INK,True,limit=2)
    p(d,bx,y+125,detail,right-bx-25,21 if mobile else 21,TEXT,limit=4)
def section_label(im,y,heading,sub):
    d=ImageDraw.Draw(im);t(d,58,y,heading,27,TEAL,True);t(d,58,y+44,sub,20,TEXT)
def decision(im,y,mobile):
    d=ImageDraw.Draw(im);w=im.width;x=36 if mobile else 55;right=w-x
    h=300 if mobile else 202
    gradient(im,(x,y,right,y+h),NAVY,NAVY2)
    d.rectangle((x,y,x+10,y+h),fill=CYAN)
    t(d,x+37,y+22,"EXECUTIVE RELEASE GATE",25 if mobile else 27,"#A7EFF9",True)
    p(d,x+37,y+82,"EXPAND   /   SUPPORT   /   HOLD",right-x-75,36 if mobile else 42,WHITE,True,limit=2)
    p(d,x+37,y+(171 if mobile else 152),"Decide from demonstrated competence, safe use and work outcomes—not licences or attendance.",right-x-74,20,"#E1EDF3",limit=3)
def foot(im,y,mobile):
    gradient(im,(0,y,im.width,im.height),NAVY,NAVY2);d=ImageDraw.Draw(im)
    d.rectangle((0,y,im.width,y+5),fill=CYAN)
    radius=51 if mobile else 50;cx=91 if mobile else 97;cy=y+83
    portrait(im,cx,cy,radius)
    xx=cx+radius+26
    t(d,xx,y+35,"Jair Ribeiro",29,WHITE,True)
    t(d,xx,y+81,"AI LEADER",19,CYAN,True)
    p(d,xx,y+115,"Enterprise AI Adoption · Governance · Business Transformation",im.width-xx-25,16,"#DBE8F1",limit=2)
def render(mobile=False):
    w,h=(800,3790) if mobile else (1400,2320)
    im=Image.new("RGB",(w,h),BG);head(im,mobile);metrics(im,mobile)
    d=ImageDraw.Draw(im)
    if mobile:
        section_label(im,1275,"THE CAPABILITY CONTRACT","Establish the conditions. Prove they work.")
        for i in range(6):row(im,1390+i*284,i,True)
        decision(im,3110,True);foot(im,3500,True)
    else:
        section_label(im,699,"THE CAPABILITY CONTRACT","A business-led programme, tested inside real workflows.")
        for i in range(6):row(im,785+i*191,i,False)
        decision(im,1960,False);foot(im,2170,False)
    return im
def build(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    for name,mobile in (("desktop",False),("mobile",True)):
        im=render(mobile)
        im.save(out/(name+".png"),optimize=True)
        im.save(out/(name+".webp"),format="WEBP",quality=84,method=6)
        print(name,im.size,(out/(name+".webp")).stat().st_size)
    pdf=canvas.Canvas(str(out/"infographic.pdf"),pagesize=A4)
    for name in ("desktop",):
        with Image.open(out/(name+".png")) as art:
            w,h=art.size
            for page in ((0,1159),(1159,h)):
                crop=art.crop((0,page[0],w,page[1]))
                sub=out/("_pdf_part.png");crop.save(sub)
                pw,ph=A4;scale=min((pw-36)/crop.width,(ph-44)/crop.height)
                ww,hh=crop.width*scale,crop.height*scale
                pdf.drawImage(str(sub),(pw-ww)/2,(ph-hh)/2,width=ww,height=hh)
                pdf.showPage()
    pdf.setTitle("AI Workforce Readiness Is a Release Decision")
    pdf.setAuthor("Jair Ribeiro")
    pdf.save()
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--output",required=True)
    build(a.parse_args().output)
