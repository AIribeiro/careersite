#!/usr/bin/env python3
"""Original fifteen-outcome enterprise AI infographic; no copied formulas or third-party diagram."""
from pathlib import Path
import argparse, math
from PIL import Image, ImageDraw, ImageFont, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[1]
NAVY="#06213A"; NAVY2="#154362"; INK="#143149"; MUTED="#466071"
CREAM="#FCFAF7"; WHITE="#FFFFFF"; CYAN="#04C7EC"; COPPER="#BF8965"
EDGE="#DEE7EA"; PALE="#EDF5F5"; STEEL="#607F93"
REG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
GROUPS=[
("01","FINANCIAL PERFORMANCE","#247E7A","cash","Where the economics of the business change",[
("01","Incremental revenue","More contribution from qualified demand","Sales action with controlled recommendations","Matched-cohort contribution, not AI touches"),
("02","Recurring cost reduction","Fewer costs from work and rework","Redesigned process; expense actually retired","Finance-verified net run-cost change"),
("03","Investment payback","Recover the full AI investment","Lifecycle budget and realised cash effects","Cumulative net benefits versus investment"),
("04","Lower cost per transaction","Complete comparable work at lower unit cost","Reliable unit definition and exception control","Fully loaded cost per quality-adjusted case")]),
("02","OPERATIONAL PERFORMANCE","#BD8C61","clock","Where end-to-end work improves",[
("05","Faster cycle time","Less waiting from request to resolution","Remove bottlenecks across handoffs","End-to-end time, errors and escalation"),
("06","Repeatable automated work","Routine cases completed with less manual work","Permissions, test cases and recovery","Completed cases without rework"),
("07","More productive capacity","People do more useful work with released time","Redesign roles and allocate recovered hours","New work delivered; no double-counted cash"),
("08","Earlier first value","Useful results reach real operations sooner","Narrow scope and a clear release gate","Date of first verified sustained outcome")]),
("03","CUSTOMER OUTCOMES","#2E88BD","people","Where customers receive better results",[
("09","Higher sales conversion","More qualified prospects become customers","Reliable signals and seller judgment","Comparable conversion cohorts"),
("10","Stronger customer retention","Reduce avoidable churn and loss","Actionable signals, service ownership","Retention over a comparable renewal period"),
("11","Better customer experience","Clearer, more relevant and dependable service","Current knowledge, quality and feedback loops","Satisfaction with complaints and repeat contact"),
("12","First-contact resolution","Correctly solve more issues the first time","Bounded authority and reliable knowledge","Verified first-contact success and recontact")]),
("04","ENTERPRISE CAPABILITY","#8B7097","network","Where value survives beyond a pilot",[
("13","Pilots into owned services","Move useful tests into stable operations","Named owner, support and stop rights","Share of validated pilots operating reliably"),
("14","Cover priority value pools","Improve the work that matters most","Rank value, feasibility and risk","Material value addressed, not project count"),
("15","Employee experience","Remove friction while preserving judgment","Practitioner input and supported role changes","Experience, workload, quality and rework")])
]
def rgb(s):return tuple(int(s[i:i+2],16) for i in (1,3,5))
def F(size,bold=False):return ImageFont.truetype(BOLD if bold else REG,size)
def t(d,x,y,s,size,color,b=False):d.text((int(x),int(y)),str(s),font=F(size,b),fill=color)
def wrap(d,s,width,size,bold=False):
    a=[];line=""
    for word in s.split():
        trial=(line+" "+word).strip()
        if d.textbbox((0,0),trial,font=F(size,bold))[2] <= width:line=trial
        else:
            if line:a.append(line)
            line=word
    if line:a.append(line)
    return a
def paragraph(d,x,y,s,w,size,color,bold=False,limit=3,leading=1.28):
    lines=wrap(d,s,w,size,bold)
    if len(lines)>limit:raise ValueError("Overflow: "+repr((s,w,size,lines)))
    for line in lines:t(d,x,y,line,size,color,bold);y+=round(size*leading)
    return y
def rounded(d,box,fill,rad=15,edge=EDGE,width=2):
    d.rounded_rectangle(tuple(map(int,box)),radius=rad,fill=fill,outline=edge,width=width)
def gradient(im,box,a,b):
    d=ImageDraw.Draw(im);x0,y0,x1,y1=box;a=rgb(a);b=rgb(b)
    for y in range(y0,y1):
        k=(y-y0)/max(1,y1-y0)
        d.line((x0,y,x1,y),fill=tuple(round(a[i]*(1-k)+b[i]*k) for i in range(3)))
def emblem(d,kind,x,y,c):
    w=5
    if kind=="cash":
        d.ellipse((x+3,y+8,x+59,y+63),outline=c,width=w)
        d.line((x+30,y+18,x+30,y+53),fill=c,width=3)
        d.arc((x+16,y+18,x+48,y+49),70,255,fill=c,width=4)
    elif kind=="clock":
        d.ellipse((x+5,y+5,x+66,y+66),outline=c,width=w)
        d.line((x+35,y+35,x+35,y+16),fill=c,width=w)
        d.line((x+35,y+35,x+54,y+45),fill=c,width=w)
    elif kind=="people":
        d.ellipse((x+25,y+5,x+47,y+27),outline=c,width=4)
        d.arc((x+14,y+26,x+58,y+67),185,355,fill=c,width=4)
        d.ellipse((x+2,y+18,x+17,y+34),outline=c,width=3)
        d.ellipse((x+57,y+18,x+72,y+34),outline=c,width=3)
    else:
        for a,b in [(9,39),(35,12),(62,40)]:
            d.ellipse((x+a-9,y+b-9,x+a+9,y+b+9),outline=c,width=4)
        d.line((x+23,y+33,x+29,y+22),fill=c,width=4)
        d.line((x+44,y+23,x+55,y+33),fill=c,width=4)
def portrait(im,x,y,r):
    path=ROOT/"images"/"profile_red_bg.jpg.jpg"
    if not path.is_file():raise FileNotFoundError("Authentic brand portrait absent: "+str(path))
    with Image.open(path) as photo:
        photo=photo.convert("RGB")
        if photo.width>800:
            a,b=photo.size;photo=photo.crop((int(a*.42),int(b*.16),int(a*.70),int(b*.60)))
        photo=ImageOps.fit(photo,(2*r,2*r),centering=(.5,.4))
    mask=Image.new("L",(2*r,2*r),0);ImageDraw.Draw(mask).ellipse((0,0,2*r,2*r),fill=255)
    d=ImageDraw.Draw(im);d.ellipse((x-r-5,y-r-5,x+r+5,y+r+5),fill=WHITE)
    im.paste(photo,(x-r,y-r),mask)
def header(im,mobile):
    w=im.width;end=430 if mobile else 355;gradient(im,(0,0,w,end),NAVY,NAVY2)
    d=ImageDraw.Draw(im)
    for k in range(4):d.arc((-135,20+k*28,w+130,end+170+k*30),190,333,fill="#205477",width=3)
    x=40 if mobile else 64
    d.rectangle((x,44,x+9,108),fill=CYAN)
    t(d,x+28,56,"EXECUTIVE AI BRIEFING   /   BUSINESS VALUE",21 if mobile else 22,"#A4EAF3",True)
    if mobile:
        t(d,x,144,"15 WAYS AI CAN",54,WHITE,True)
        t(d,x,219,"CHANGE YOUR",54,WHITE,True)
        t(d,x,294,"BUSINESS",60,"#E7B488",True)
        paragraph(d,x,370,"What it takes to make the change measurable.",w-x*2,22,"#DFEDF3")
    else:
        t(d,x,130,"15 WAYS AI CAN CHANGE",67,WHITE,True)
        t(d,x,220,"YOUR BUSINESS",75,"#E7B488",True)
        t(d,x,314,"What changes. What it takes. What must be proved.",24,"#DFEDF3")
def intro(im,mobile):
    d=ImageDraw.Draw(im);x=42 if mobile else 64
    y=460 if mobile else 377
    t(d,x,y,"USAGE SHOWS ACTIVITY. OUTCOMES SHOW CHANGE.",22 if mobile else 25,INK,True)
    paragraph(d,x,y+(50 if mobile else 53),
      "Fifteen selected business outcomes across four executive dimensions. An AI feature is not a benefit until the business can demonstrate a change in real work.",
      im.width-2*x,20 if mobile else 22,MUTED,limit=4)
def band(im,y,g,mobile):
    n,label,color,kind,caption,_=g
    d=ImageDraw.Draw(im);x=34 if mobile else 55;right=im.width-x
    rounded(d,(x,y,right,y+(100 if mobile else 84)),color,18,color,2)
    emblem(d,kind,x+21,y+15,WHITE)
    tx=x+104
    t(d,tx,y+10,n+"   "+label,25 if mobile else 30,WHITE,True)
    paragraph(d,tx,y+54,caption,right-tx-18,18 if mobile else 20,"#FFFFFF",limit=1)
def card(im,x,y,w,h,item,color,mobile):
    number,title,change,takes,proof=item
    d=ImageDraw.Draw(im)
    rounded(d,(x,y,x+w,y+h),WHITE,18,EDGE,2)
    d.rounded_rectangle((x+18,y+17,x+79,y+65),radius=9,fill=color)
    t(d,x+25,y+24,number,25,WHITE,True)
    tx=x+95
    paragraph(d,tx,y+20,title,w-116,31 if mobile else 26,INK,True,limit=2,leading=1.12)
    first=y+(98 if mobile else 87)
    t(d,x+22,first,"CHANGE",20 if mobile else 15,color,True)
    paragraph(d,x+(170 if mobile else 119),first-2,change,w-(195 if mobile else 144),24 if mobile else 17,MUTED,limit=2)
    first+=79 if mobile else 49
    t(d,x+22,first,"REQUIRES",20 if mobile else 14,color,True)
    paragraph(d,x+(170 if mobile else 119),first-2,takes,w-(195 if mobile else 144),24 if mobile else 17,INK,limit=2)
    first+=79 if mobile else 49
    t(d,x+22,first,"PROOF",20 if mobile else 15,color,True)
    paragraph(d,x+(170 if mobile else 119),first-2,proof,w-(195 if mobile else 144),24 if mobile else 17,MUTED,limit=2)
def action(im,y,mobile):
    d=ImageDraw.Draw(im);x=34 if mobile else 55;right=im.width-x
    h=266 if mobile else 230
    gradient(im,(x,y,right,y+h),NAVY,NAVY2)
    d.rectangle((x,y,x+11,y+h),fill=CYAN)
    t(d,x+35,y+24,"THE LEADERSHIP DECISION",25 if mobile else 27,"#B9F4FC",True)
    paragraph(d,x+35,y+73,"Choose the outcome. Name the owner. Establish the baseline. Fund the change. Verify before scaling.",
        right-x-65,25 if mobile else 27,WHITE,True,limit=3)
    paragraph(d,x+35,y+(214 if mobile else 179),"Scale / repair / stop based on evidence, quality and full cost.",right-x-65,19,"#D9E9F1",limit=2)
def footer(im,y,mobile):
    gradient(im,(0,y,im.width,im.height),NAVY,NAVY2);d=ImageDraw.Draw(im)
    d.rectangle((0,y,im.width,y+5),fill=CYAN)
    px=98 if mobile else 105;py=y+83
    portrait(im,px,py,52);tx=px+82
    t(d,tx,y+29,"Jair Ribeiro",31,WHITE,True)
    t(d,tx,y+73,"AI LEADER",20,"#A5EBF5",True)
    paragraph(d,tx,y+111,"Enterprise AI Adoption · Governance · Business Transformation",
        im.width-tx-25,17,"#DAE8F1",limit=2)
def render(mobile=False):
    w=800 if mobile else 1400
    im=Image.new("RGB",(w,5200 if mobile else 3190),CREAM)
    header(im,mobile);intro(im,mobile)
    y=625 if mobile else 550
    for group in GROUPS:
        band(im,y,group,mobile);y+=112 if mobile else 100
        items=group[5]
        if mobile:
            for item in items:
                card(im,34,y,w-68,350,item,group[2],True);y+=365
        else:
            for j,item in enumerate(items):
                x=55+(j%2)*649
                row=j//2
                card(im,x,y+row*239,635,227,item,group[2],False)
            y+=math.ceil(len(items)/2)*239
        y+=20 if mobile else 20
    action(im,y+8,mobile);footer(im,y+308 if mobile else y+260,mobile)
    # No trailing empty canvas in release
    bottom=y+(308 if mobile else 260)+175
    return im.crop((0,0,w,bottom))
def build(dest):
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=True)
    assert len([x for g in GROUPS for x in g[5]])==15
    images=[]
    for name,mobile in [("desktop",False),("mobile",True)]:
        im=render(mobile);path=dest/(name+".png");im.save(path,optimize=True)
        wp=dest/(name+".webp");im.save(wp,format="WEBP",quality=85,method=6)
        assert wp.stat().st_size<1_500_000
        print(name,im.size,wp.stat().st_size);images.append(im)
    poster=images[0]
    pdf=canvas.Canvas(str(dest/"infographic.pdf"),pagesize=A4)
    page_w,page_h=A4
    # Three genuine A4 pages preserve legibility; each contains a contiguous band of the same infographic.
    cuts=[0,int(poster.height/3),int(poster.height*2/3),poster.height]
    for i in range(3):
        crop=poster.crop((0,cuts[i],poster.width,cuts[i+1]))
        ratio=min((page_w-36)/crop.width,(page_h-42)/crop.height)
        dw,dh=crop.width*ratio,crop.height*ratio
        pdf.drawImage(ImageReader(crop), (page_w-dw)/2, (page_h-dh)/2, dw,dh)
        pdf.setFont("Helvetica",8);pdf.setFillColorRGB(.3,.4,.5)
        pdf.drawRightString(page_w-20,15,f"Jair Ribeiro  |  Executive AI Briefing  |  {i+1}/3")
        pdf.showPage()
    pdf.save()
    assert (dest/"infographic.pdf").stat().st_size>1000
if __name__=="__main__":
    pa=argparse.ArgumentParser();pa.add_argument("--output",required=True)
    build(pa.parse_args().output)
