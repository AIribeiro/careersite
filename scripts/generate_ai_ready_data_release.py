#!/usr/bin/env python3
"""Generate source-locked desktop, mobile and printable artwork for AI-ready data."""
from __future__ import annotations
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

N="#06213A"; N2="#0D4162"; C="#04C7EC"; T="#087E87"
P="#BF8965"; W="#FFFFFF"; F="#FCFAF7"; I="#132A40"; M="#526779"; E="#D6E5E8"
ROOT=Path(__file__).resolve().parents[1]
REG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def font(n,b=False): return ImageFont.truetype(BOLD if b else REG,n)
def txt(d,x,y,s,n=21,color=I,b=False): d.text((x,y),s,font=font(n,b),fill=color)
def wrap(d,s,n,w,b=False):
    result=[];line=""
    for token in s.split():
        test=(line+" "+token).strip()
        if d.textbbox((0,0),test,font=font(n,b))[2] <= w: line=test
        else:
            if line: result.append(line)
            line=token
    if line:result.append(line)
    return result
def para(d,x,y,s,n=20,w=500,color=M,b=False,limit=3,step=1.26):
    ls=wrap(d,s,n,w,b)
    if len(ls)>limit: raise ValueError(f"Text overflow: {s}: {ls}")
    for line in ls:txt(d,x,y,line,n,color,b);y+=int(n*step)
    return y
def box(d,rect,fill=W,r=20,stroke=E): d.rounded_rectangle(rect,radius=r,fill=fill,outline=stroke,width=2)
def rgb(h):return tuple(int(h[i:i+2],16) for i in (1,3,5))
def gradient(d,w,a,b,y0,y1):
    p,q=rgb(a),rgb(b)
    for y in range(y0,y1):
        z=(y-y0)/max(1,y1-y0)
        d.line((0,y,w,y),fill=tuple(round(p[i]*(1-z)+q[i]*z) for i in range(3)))
def emblem(d,name,x,y):
    color=N
    if name=="target":
        d.ellipse((x+6,y+6,x+50,y+50),outline=color,width=4)
        d.ellipse((x+20,y+20,x+36,y+36),outline=color,width=3)
        d.line((x+28,y+28,x+50,y+5),fill=color,width=4)
    elif name=="data":
        d.ellipse((x+8,y+4,x+50,y+23),outline=color,width=4)
        d.arc((x+8,y+37,x+50,y+57),0,180,fill=color,width=4)
        d.line((x+8,y+14,x+8,y+46),fill=color,width=4)
        d.line((x+50,y+14,x+50,y+46),fill=color,width=4)
        d.line((x+8,y+31,x+50,y+31),fill=color,width=3)
    elif name=="rights":
        d.line([(x+28,y+3),(x+50,y+12),(x+47,y+39),(x+28,y+57),(x+9,y+39),(x+6,y+12),(x+28,y+3)],fill=color,width=4,joint="curve")
        d.line((x+18,y+28,x+26,y+36,x+40,y+19),fill=color,width=4)
    elif name=="flow":
        d.line((x+10,y+16,x+44,y+16,x+44,y+7),fill=color,width=4)
        d.line((x+44,y+16,x+36,y+24),fill=color,width=4)
        d.line((x+46,y+43,x+12,y+43,x+12,y+52),fill=color,width=4)
        d.line((x+12,y+43,x+20,y+35),fill=color,width=4)
    elif name=="value":
        for j,height in enumerate((17,30,45)):
            d.rounded_rectangle((x+10+14*j,y+52-height,x+20+14*j,y+52),radius=3,fill=color)
    elif name=="review":
        d.rounded_rectangle((x+12,y+11,x+48,y+57),radius=4,outline=color,width=4)
        d.rounded_rectangle((x+22,y+5,x+38,y+18),radius=3,outline=color,width=3)
        for j in range(3):
            d.line((x+20,y+27+j*9,x+24,y+31+j*9,x+30,y+24+j*9),fill=color,width=2)
            d.line((x+34,y+27+j*9,x+43,y+27+j*9),fill=color,width=2)
def head(im,mobile=False):
    d=ImageDraw.Draw(im);w=im.width;h=393 if mobile else 330
    gradient(d,w,N,N2,0,h)
    for i in range(6):
        y=91+i*21
        d.arc((-220,y-150,w+190,y+230),192,345,fill="#1E5571",width=2)
    d.rounded_rectangle((32,37,39,125),radius=2,fill=P)
    txt(d,57,40,"EXECUTIVE AI BRIEFING / DATA READINESS",16,C,True)
    if mobile:
        txt(d,37,103,"AI CAN SCALE.",55,W,True)
        txt(d,37,178,"CAN ITS DATA?",55,W,True)
        para(d,40,283,"Data readiness is a release condition for each AI workflow.",22,w-80,"#D6E6EF",limit=2)
    else:
        txt(d,60,105,"AI CAN SCALE.",75,W,True)
        txt(d,60,188,"CAN ITS DATA?",75,W,True)
        para(d,63,283,"A use-case data contract connects quality, authority and value.",21,w-125,"#D6E6EF",limit=1)
def stat(im,rect,eyebrow,big,detail,source,mobile=False):
    d=ImageDraw.Draw(im);x,y,x2,y2=rect;box(d,rect)
    d.rounded_rectangle((x+13,y+17,x+20,y2-17),radius=3,fill=T)
    tx=x+38
    txt(d,tx,y+15,eyebrow.upper(),14,M,True)
    txt(d,tx,y+43,big,39,P,True)
    para(d,tx,y+96,detail,18 if mobile else 16,x2-tx-17,I,limit=3)
    txt(d,tx,y2-26,source,12,T,True)
def contract(im,rect,mobile=False):
    d=ImageDraw.Draw(im);x,y,x2,y2=rect
    box(d,rect,"#E4F4F7",22,"#BCDDE3")
    d.rounded_rectangle((x+18,y+18,x+26,y2-18),radius=3,fill=C)
    txt(d,x+47,y+26,"THE USE-CASE DATA CONTRACT",27 if mobile else 32,N,True)
    para(d,x+47,y+76,"The agreed data, permitted use, accountable owner and evidence required before release.",20,x2-x-85,M,limit=3)
def check(im,rect,number,heading,description,ico,mobile=False):
    d=ImageDraw.Draw(im);x,y,x2,y2=rect;box(d,rect,W,20,E)
    d.rounded_rectangle((x,y+21,x+7,y2-21),radius=3,fill=T if number%2 else P)
    d.ellipse((x+20,y+20,x+75,y+75),fill=N)
    txt(d,x+36,y+29,str(number),25,W,True)
    ix=x2-90;iy=y+26
    d.rounded_rectangle((ix-7,iy-8,ix+65,iy+67),radius=13,fill="#E8F5F8")
    emblem(d,ico,ix,iy)
    header_size=23 if mobile else 23
    para(d,x+94,y+24,heading,header_size,ix-x-110,N,True,limit=2)
    para(d,x+25,y+96,description,19,x2-x-50,M,limit=3)
def gate(im,rect,mobile=False):
    d=ImageDraw.Draw(im);x,y,x2,y2=rect
    box(d,rect,N,20,N);txt(d,x+23,y+17,"EXECUTIVE RELEASE GATE",18,C,True)
    choices=[
        ("PROCEED","The receiving team owns the tested workflow."),
        ("REPAIR","Fix the gaps and test the evidence again."),
        ("STOP","Do not extend unjustified AI authority.")]
    if mobile:
        for i,(label,desc) in enumerate(choices):
            yy=y+62+i*73
            if i:d.line((x+23,yy-13,x2-23,yy-13),fill="#28546F",width=2)
            txt(d,x+24,yy,label,22,C if i==0 else P,True)
            para(d,x+186,yy+2,desc,18,x2-x-214,W,limit=2)
    else:
        ww=(x2-x-48)//3
        for i,(label,desc) in enumerate(choices):
            xx=x+21+ww*i
            if i:d.line((xx-11,y+61,xx-11,y2-17),fill="#28546F",width=2)
            txt(d,xx,y+63,label,23,C if i==0 else P,True)
            para(d,xx,y+103,desc,16,ww-21,W,limit=3)
def author(im,start,mobile=False):
    d=ImageDraw.Draw(im);w,h=im.size
    gradient(d,w,N,N2,start,h);d.rectangle((0,start,w,start+4),fill=C)
    r=35 if mobile else 40;cx=62 if mobile else 80;cy=start+66
    d.ellipse((cx-r-4,cy-r-4,cx+r+4,cy+r+4),fill=W)
    source=ROOT/"images"/"profile_red_bg.jpg.jpg"
    if source.exists():
        with Image.open(source) as photo:
            tw,th=photo.size
            photo=photo.crop((int(tw*.4225),int(th*.169),int(tw*.695),int(th*.578))).convert("RGB").resize((r*2,r*2),Image.Resampling.LANCZOS)
        mask=Image.new("L",(r*2,r*2),0)
        ImageDraw.Draw(mask).ellipse((0,0,r*2-1,r*2-1),fill=255)
        im.paste(photo,(cx-r,cy-r),mask)
    else:txt(d,cx-r+12,cy-r+14,"JR",25,N,True)
    d=ImageDraw.Draw(im);tx=cx+r+24
    txt(d,tx,start+26,"Jair Ribeiro",26,W,True)
    txt(d,tx,start+68,"AI LEADER",17,C,True)
    if mobile:para(d,32,start+117,"Enterprise AI Adoption · Governance · Business Transformation",15,w-60,"#D7E6EF",limit=2)
    else:txt(d,tx,start+105,"Enterprise AI Adoption · Governance · Business Transformation",16,"#D7E6EF")
def render(mobile):
    w,h=(720,3180) if mobile else (1200,1810)
    im=Image.new("RGB",(w,h),F)
    head(im,mobile)
    stats=[
      ("ACCESS","+50%","Relative annual increase in access to sanctioned AI tools.","DELOITTE 2026"),
      ("READINESS","40%","Globally report high preparedness in AI data management.","DELOITTE 2026"),
      ("AT RISK","60%","Forecast AI projects without AI-ready data abandoned through 2026.","GARTNER 2025")]
    if mobile:
        for i,item in enumerate(stats):
            stat(im,(25,411+i*184,w-25,577+i*184),*item,mobile=True)
        contract(im,(25,977,w-25,1140),True)
    else:
        for i,item in enumerate(stats):
            stat(im,(30+i*390,349,400+i*390,526),*item)
        contract(im,(30,549,1170,698))
    cards=[
       ("Define the decision","Specify the business result and the data it needs.","target"),
       ("Prove data fitness","Check quality, freshness, lineage and exceptions.","data"),
       ("Name authority","Assign the owner, approved use and stop rights.","rights"),
       ("Test continuous use","Check repeated retrieval, handoffs and monitoring.","flow"),
       ("Measure the result","Connect defects and data investment to cost, quality and service.","value"),
       ("Renew permission","Release in stages; reassess drift, changes and failures.","review")]
    if mobile:
        for i,(a,b,c) in enumerate(cards):
            top=1170+i*235
            check(im,(25,top,w-25,top+219),i+1,a,b,c,True)
        gate(im,(25,2610,w-25,2895),True)
        author(im,2960,True)
    else:
        for i,(a,b,c) in enumerate(cards):
            col=i%2;row=i//2
            check(im,(30+col*585,720+row*206,584+col*585,911+row*206),i+1,a,b,c)
        gate(im,(30,1360,1170,1589))
        txt(ImageDraw.Draw(im),40,1615,"No named owner, no tested data, no wider AI authority.",23,N,True)
        author(im,1660)
    return im
def run(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    for name,mobile in (("desktop",False),("mobile",True)):
        im=render(mobile)
        im.save(folder/(name+".png"),optimize=True)
        im.save(folder/(name+".webp"),format="WEBP",quality=85,method=6)
        print(name,im.size)
    pdf=canvas.Canvas(str(folder/"infographic.pdf"),pagesize=A4)
    w,h=A4;im=Image.open(folder/"desktop.png")
    ratio=min(w/im.width,h/im.height);ww=im.width*ratio;hh=im.height*ratio
    pdf.drawImage(str(folder/"desktop.png"),(w-ww)/2,(h-hh)/2,width=ww,height=hh)
    pdf.setTitle("AI-ready data: the use-case data contract")
    pdf.setAuthor("Jair Ribeiro");pdf.showPage();pdf.save()
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True)
    run(p.parse_args().output)
