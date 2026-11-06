#!/usr/bin/env python3
"""Source-locked premium artwork for the nine AI governance blind spots briefing."""
from __future__ import annotations
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

ROOT = Path(__file__).resolve().parents[1]
NAVY = '#06213A'; BLUE = '#103E5F'; CYAN = '#04C7EC'; COPPER = '#BF8965'
TEAL = '#257E79'; STEEL = '#486C81'; BG = '#FCFAF7'; WHITE = '#FFFFFF'
INK = '#152D41'; MUTED = '#506779'; EDGE = '#DAE5E8'; LIGHT = '#ECF6F7'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

GROUPS = [
 ('01', 'DISCOVER', 'THE USE', 'Make AI use visible and its data routes accountable.', TEAL, [
  ('01', 'Unapproved AI use', 'Offer useful approved tools; define data rules, SSO and upload controls.', 'search'),
  ('02', 'Missing AI inventory', 'Register each workflow, owner, model, data, purpose and risk.', 'layers'),
  ('03', 'Vendor data exposure', 'Check retention, training terms, subprocessors and contracts.', 'cloud')]),
 ('02', 'AUTHORISE', 'THE WORK', 'Give only the authority the business can justify.', COPPER, [
  ('04', 'Unclear business owner', 'Name an accountable owner with exception and stop rights.', 'user'),
  ('05', 'No risk gate', 'Test accuracy, fairness, privacy, security and potential harm.', 'shield'),
  ('06', 'Missing human review', 'Give reviewers genuine power to challenge, reverse and offer recourse.', 'people')]),
 ('03', 'PROVE', 'IN USE', 'Keep the evidence and the ability to respond.', STEEL, [
  ('07', 'Missing traceability', 'Protect records of key inputs, outputs, versions and approvals.', 'log'),
  ('08', 'Silent drift', 'Monitor quality and re-test after material changes.', 'trend'),
  ('09', 'No incident readiness', 'Prepare pause, rollback, escalation and recovery drills.', 'alert')])]


def color(h): return tuple(int(h[j:j+2], 16) for j in (1,3,5))
def font(sz, bold=False): return ImageFont.truetype(BOLD if bold else FONT, sz)
def txt(d, xy, s, sz, fill, bold=False): d.text(xy, s, font=font(sz, bold), fill=fill)
def wrap(d, content, width, sz, bold=False):
    lines=[]; line=''
    for word in content.split():
        test=(line+' '+word).strip()
        if d.textbbox((0,0), test, font=font(sz, bold))[2] <= width: line=test
        else:
            if line: lines.append(line)
            line=word
    if line:lines.append(line)
    return lines

def para(d,x,y,s,width,sz,fill,bold=False,maxlines=5,spacing=1.29):
    lines=wrap(d,s,width,sz,bold)
    if len(lines)>maxlines: raise ValueError(f'Overflow {sz}px width {width}: {s} => {lines}')
    for line in lines:
        txt(d,(x,y),line,sz,fill,bold);y+=int(sz*spacing)
    return y

def rounded(d, rect, fill, r=18, outline=EDGE, stroke=2):
    d.rounded_rectangle(rect, radius=r, fill=fill, outline=outline, width=stroke)

def fade(d,rect,start,end):
    x1,y1,x2,y2=rect;ca,cb=color(start),color(end)
    for y in range(y1,y2):
        t=(y-y1)/max(y2-y1-1,1)
        cc=tuple(round(ca[i]*(1-t)+cb[i]*t) for i in range(3))
        d.line((x1,y,x2,y),fill=cc)

def icon(d,name,x,y,size=50,ink=INK):
    # Exact semantic line symbols are original; all share the same stroke and bounds.
    w=3;r=size/50
    q=lambda v:int(v*r)
    X=lambda v:x+q(v)
    Y=lambda v:y+q(v)
    if name=='search':
        d.ellipse((X(5),Y(5),X(33),Y(33)),outline=ink,width=w)
        d.line((X(28),Y(30),X(44),Y(46)),fill=ink,width=w+1)
    elif name=='layers':
        for yy in (7,20,33):
            d.line([(X(4),Y(yy+6)),(X(25),Y(yy-3)),(X(46),Y(yy+6)),(X(25),Y(yy+15)),(X(4),Y(yy+6))],fill=ink,width=w)
    elif name=='cloud':
        d.arc((X(5),Y(8),X(45),Y(36)),180,350,fill=ink,width=w)
        d.line((X(7),Y(31),X(27),Y(31)),fill=ink,width=w)
        d.line((X(28),Y(31),X(28),Y(44)),fill=ink,width=w)
        d.line((X(22),Y(38),X(28),Y(44),X(34),Y(38)),fill=ink,width=w)
    elif name=='user':
        d.ellipse((X(17),Y(3),X(33),Y(19)),outline=ink,width=w)
        d.arc((X(5),Y(21),X(45),Y(51)),180,360,fill=ink,width=w)
        d.ellipse((X(33),Y(30),X(47),Y(44)),outline=COPPER,width=w)
    elif name=='shield':
        d.line([(X(25),Y(3)),(X(44),Y(12)),(X(39),Y(37)),(X(25),Y(47)),(X(11),Y(37)),(X(6),Y(12)),(X(25),Y(3))],fill=ink,width=w)
        d.line([(X(15),Y(25)),(X(23),Y(32)),(X(36),Y(17))],fill=ink,width=w)
    elif name=='people':
        d.ellipse((X(18),Y(5),X(32),Y(19)),outline=ink,width=w)
        d.arc((X(8),Y(18),X(42),Y(53)),180,355,fill=ink,width=w)
        for xx in (3,36): d.ellipse((X(xx),Y(13),X(xx+10),Y(23)),outline=ink,width=2)
    elif name=='log':
        d.rounded_rectangle((X(8),Y(3),X(42),Y(47)),radius=3,outline=ink,width=w)
        for yy in (16,25,34):d.line((X(15),Y(yy),X(35),Y(yy)),fill=ink,width=2)
    elif name=='trend':
        d.line((X(6),Y(43),X(6),Y(7)),fill=ink,width=2);d.line((X(6),Y(43),X(46),Y(43)),fill=ink,width=2)
        d.line([(X(11),Y(35)),(X(21),Y(27)),(X(31),Y(31)),(X(43),Y(11))],fill=ink,width=w)
        for xx,yy in [(11,35),(21,27),(31,31),(43,11)]: d.ellipse((X(xx-3),Y(yy-3),X(xx+3),Y(yy+3)),fill=WHITE,outline=ink,width=2)
    elif name=='alert':
        d.arc((X(8),Y(7),X(42),Y(42)),180,360,fill=ink,width=w)
        d.line((X(9),Y(27),X(9),Y(37)),fill=ink,width=w)
        d.line((X(41),Y(27),X(41),Y(37)),fill=ink,width=w)
        d.line((X(9),Y(37),X(41),Y(37)),fill=ink,width=w)
        d.ellipse((X(23),Y(43),X(27),Y(47)),fill=ink)

def header(im,mobile):
    d=ImageDraw.Draw(im);w=im.width;h=340 if mobile else 320
    fade(d,(0,0,w,h),NAVY,BLUE)
    for j in range(4):
        d.arc((-70,20+j*14,w+80,275+j*7),196,343,fill='#1F5570',width=2)
    d.rectangle((32,40,40,109),fill=COPPER)
    txt(d,(60,39),'EXECUTIVE AI BRIEFING   /   GOVERNANCE',17 if mobile else 19,CYAN,True)
    if mobile:
        txt(d,(38,98),'WHO IS ACCOUNTABLE',39,WHITE,True)
        txt(d,(38,154),'FOR THE AI YOU',39,WHITE,True)
        txt(d,(38,207),'CANNOT SEE?',44,'#F0C19E',True)
        para(d,39,275,'Nine governance gaps. Three operating obligations.',w-70,20,'#E3EDF4',False,2)
    else:
        txt(d,(60,111),'WHO IS ACCOUNTABLE FOR',50,WHITE,True)
        txt(d,(60,179),'THE AI YOU CANNOT SEE?',48,'#F0C19E',True)
        txt(d,(63,263),'Nine governance gaps. Three executive obligations.',22,'#E3EDF4')

def desktop_section(im,y,group):
    n,h1,h2,sub,accent,items=group;d=ImageDraw.Draw(im)
    x0=27;x1=1173;height=374
    rounded(d,(x0,y,x1,y+height),WHITE,23,EDGE,2)
    # Left side with a decisive editorial domain panel.
    rgb=color(accent);side='#'+''.join(f'{min(255,int(x*.86)):02x}' for x in rgb)
    d.rounded_rectangle((x0+1,y+1,251,y+height-1),radius=21,fill=side)
    d.rectangle((231,y+4,251,y+height-4),fill=side)
    txt(d,(56,y+32),n,31,'#B8F2F0' if accent==TEAL else '#FCE4D4',True)
    d.line((55,y+90,172,y+90),fill='#F7EDE0',width=2)
    txt(d,(55,y+112),h1,28,WHITE,True)
    txt(d,(55,y+151),h2,27,WHITE,True)
    para(d,55,y+235,sub,170,18,'#E5F0F1',maxlines=5)
    for i,(number,title,detail,glyph) in enumerate(items):
        x=269+i*299;right=x+283
        rounded(d,(x,y+18,right,y+height-18),BG,16,EDGE,2)
        d.rounded_rectangle((x+16,y+28,x+82,y+94),radius=13,fill=LIGHT,outline='#CEE7E9',width=1)
        icon(d,glyph,x+25,y+38,48)
        txt(d,(x+93,y+40),number,26,accent,True)
        para(d,x+17,y+119,title,253,23,INK,True,2)
        d.line((x+18,y+202,right-18,y+202),fill='#C8D9DC',width=2)
        para(d,x+18,y+224,detail,247,19,MUTED,maxlines=5)

def mobile_section(im,y,group):
    n,h1,h2,sub,accent,items=group;d=ImageDraw.Draw(im);x=24;w=672
    rounded(d,(x,y,x+w,y+698),WHITE,23,EDGE)
    d.rounded_rectangle((x+3,y+3,x+w-3,y+119),radius=17,fill=accent)
    txt(d,(x+26,y+19),n,26,WHITE,True)
    txt(d,(x+89,y+18),h1+' '+h2,30,WHITE,True)
    para(d,x+89,y+70,sub,w-110,17,'#F4F9FA',maxlines=2)
    for i,(number,title,detail,glyph) in enumerate(items):
        cy=y+137+i*181
        rounded(d,(x+16,cy,x+w-16,cy+165),BG,15,EDGE)
        d.rounded_rectangle((x+32,cy+23,x+108,cy+99),radius=14,fill=LIGHT)
        icon(d,glyph,x+44,cy+34,53)
        txt(d,(x+124,cy+23),number+'  '+title,23,INK,True)
        para(d,x+124,cy+69,detail,w-164,19,MUTED,maxlines=3)

def control_record(im,y,mobile):
    d=ImageDraw.Draw(im);x=24 if mobile else 29;right=im.width-x;h=151 if mobile else 149
    rounded(d,(x,y,right,y+h),NAVY,20,NAVY)
    d.rounded_rectangle((x+14,y+17,x+21,y+h-18),radius=2,fill=CYAN)
    txt(d,(x+42,y+17),'LIVE AI CONTROL RECORD',29 if mobile else 35,WHITE,True)
    a='Purpose  •  Owner  •  Data  •  Authority  •  Risk  •  Proof  •  Stop right'
    para(d,x+44,y+82,a,right-x-65,16 if mobile else 19,'#D4EAF2',maxlines=2)

def actions(im,y,mobile):
    d=ImageDraw.Draw(im);x=24 if mobile else 30;w=im.width-2*x
    txt(d,(x+4,y),'THE EXECUTIVE DECISION',27 if mobile else 30,NAVY,True)
    pairs=[('CONTINUE',TEAL),('RESTRICT',COPPER),('REPAIR',STEEL),('STOP','#994F40')]
    gap=10 if mobile else 14;cw=(w-3*gap)//4
    for i,(label,accent) in enumerate(pairs):
        left=x+i*(cw+gap);top=y+56
        rounded(d,(left,top,left+cw,top+(63 if mobile else 68)),accent,12,accent,1)
        line=label;sz=19 if mobile else 23
        tw=d.textbbox((0,0),line,font=font(sz,True))[2]
        txt(d,(left+(cw-tw)//2,top+16),line,sz,WHITE,True)
    para(d,x+3,y+144,'Continue only where controls work; otherwise restrict, repair or stop.',w-6,17 if mobile else 19,MUTED,maxlines=2)

def footer(im,y,mobile):
    d=ImageDraw.Draw(im);fade(d,(0,y,im.width,im.height),NAVY,BLUE);d.rectangle((0,y,im.width,y+4),fill=CYAN)
    radius=37 if mobile else 42;cx=63 if mobile else 80;cy=y+69
    d.ellipse((cx-radius-4,cy-radius-4,cx+radius+4,cy+radius+4),fill=WHITE)
    candidates=[ROOT/'images'/'profile_red_bg.jpg.jpg',Path('/mnt/data/f5z4a.300-300_Original(1).jpeg')]
    path=next((p for p in candidates if p.exists()),None)
    if path:
        with Image.open(path) as photo:
            if 'profile_red' in path.name and photo.width>800:
                tw,th=photo.size;photo=photo.crop((int(tw*.42),int(th*.16),int(tw*.70),int(th*.60)))
            photo=ImageOps.fit(photo.convert('RGB'),(radius*2,radius*2),method=Image.Resampling.LANCZOS,centering=(.5,.4))
        mask=Image.new('L',(radius*2,radius*2));ImageDraw.Draw(mask).ellipse((0,0,radius*2,radius*2),fill=255)
        im.paste(photo,(cx-radius,cy-radius),mask)
    d=ImageDraw.Draw(im);x=cx+radius+23
    txt(d,(x,y+26),'Jair Ribeiro',24 if mobile else 28,WHITE,True)
    txt(d,(x,y+66),'AI LEADER',16 if mobile else 17,CYAN,True)
    para(d,x,y+97,'Enterprise AI Adoption · Governance · Business Transformation',im.width-x-19,14 if mobile else 15,'#DBE8F1',maxlines=2)

def render(mobile=False):
    if mobile:w,h=720,3200
    else:w,h=1200,2210
    im=Image.new('RGB',(w,h),BG)
    header(im,mobile)
    d=ImageDraw.Draw(im)
    if mobile:
        rounded(d,(23,360,697,492),'#E5F2F4',18,'#B7D9DF')
        para(d,46,378,'THE MANAGEMENT TEST',630,19,TEAL,True,1)
        para(d,46,420,'Can we explain who uses AI, who permits it and how we would stop it?',619,20,INK,maxlines=2)
        ys=[516,1227,1938]
        for y,group in zip(ys,GROUPS):mobile_section(im,y,group)
        control_record(im,2654,True);actions(im,2820,True);footer(im,3057,True)
    else:
        rounded(d,(30,340,1170,480),'#E5F2F4',19,'#B7D9DF')
        txt(d,(57,360),'THE MANAGEMENT TEST',18,TEAL,True)
        para(d,57,406,'Can we explain who uses AI, who permits it and how we would stop it?',1050,25,INK,maxlines=2)
        ys=[501,887,1273]
        for y,group in zip(ys,GROUPS):desktop_section(im,y,group)
        control_record(im,1692,False);actions(im,1873,False);footer(im,2061,False)
    return im

def run(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    for name,mobile in [('desktop',False),('mobile',True)]:
        im=render(mobile);im.save(folder/(name+'.png'),optimize=True)
        im.save(folder/(name+'.webp'),format='WEBP',quality=84,method=6)
        print(name,im.size)
    c=canvas.Canvas(str(folder/'infographic.pdf'),pagesize=A4)
    w,h=A4; im=Image.open(folder/'desktop.png');ratio=min(w/im.width,h/im.height)
    width,height=im.width*ratio,im.height*ratio
    c.drawImage(str(folder/'desktop.png'),(w-width)/2,(h-height)/2,width=width,height=height)
    c.setTitle('Who is accountable for the AI you cannot see?')
    c.setAuthor('Jair Ribeiro');c.showPage();c.save()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True)
    run(p.parse_args().output)
