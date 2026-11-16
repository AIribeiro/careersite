#!/usr/bin/env python3
"""Create source-matched AI Portfolio Renewal Challenge graphics and a printable A4 PDF."""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

SLUG = 'would-you-fund-the-same-ai-initiatives-today'
FINGERPRINT = 'b9e255ca0e7ac9fdf7504e98fe07dd9e8f642c96c4e492d6aac4adf511c27bd5'
NAVY = '#06263e'; DARK = '#092f4d'; WHITE = '#fbfdfc'; BG = '#f6f8f8'
TEXT = '#14344c'; GRAY = '#4b6475'; LINE = '#c5d8dc'; CYAN = '#14b1ca'
TEAL = '#167e90'; COPPER = '#bf8461'; STEEL = '#7995a7'
FONT_ROOT = Path('/usr/share/fonts/truetype/dejavu')
REG = FONT_ROOT / 'DejaVuSans.ttf'; BOLD = FONT_ROOT / 'DejaVuSans-Bold.ttf'
if not REG.is_file():
    FONT_ROOT = Path('/usr/share/fonts/truetype/liberation2')
    REG = FONT_ROOT / 'LiberationSans-Regular.ttf'; BOLD = FONT_ROOT / 'LiberationSans-Bold.ttf'

def font(n: int, bold: bool = False):
    return ImageFont.truetype(str(BOLD if bold else REG), int(n))

def text(draw, x, y, s, size=26, color=TEXT, bold=False):
    draw.text((int(x), int(y)), str(s), font=font(size,bold), fill=color)

def wrap(draw, content, max_width, size, bold=False):
    words=content.split(); lines=[]; line=''
    for word in words:
        candidate=(line+' '+word).strip()
        if line and draw.textbbox((0,0),candidate,font=font(size,bold))[2]>max_width:
            lines.append(line);line=word
        else:line=candidate
    if line:lines.append(line)
    return lines

def paragraph(draw,x,y,s,max_width,size=25,color=GRAY,leading=None,bold=False):
    leading=leading or int(size*1.52)
    lines=wrap(draw,s,max_width,size,bold)
    for line in lines:
        text(draw,x,y,line,size,color,bold);y+=leading
    return y

def rect(draw,box,fill,outline=None,rad=18,width=2):
    draw.rounded_rectangle(tuple(map(int,box)),radius=rad,fill=fill,outline=outline,width=width)

def header(draw,w,h,mobile):
    h1=470 if mobile else 310
    draw.rectangle((0,0,w,h1),fill=NAVY)
    x=38 if mobile else 78
    draw.rectangle((x,44,x+12,60), fill=CYAN)
    text(draw,x+32,33,'EXECUTIVE AI BRIEFING  /  PORTFOLIO & VALUE',19 if mobile else 21,'#6ad6e5',True)
    if mobile:
        text(draw,x,100,'WOULD YOU FUND',53,WHITE,True)
        text(draw,x,170,'IT AGAIN?',53,WHITE,True)
        paragraph(draw,x,270,'A better AI priority is not always a new idea. It may be the decision to reconsider work already funded.',w-2*x,29,'#d5e4ea',42)
    else:
        text(draw,x,91,'WOULD YOU FUND IT AGAIN?',73,WHITE,True)
        text(draw,x,223,'A better AI priority is not always a new idea. It may be the decision to reconsider work already funded.',24,'#d5e4ea')
    return h1

def symbol(draw,cx,cy,k,color):
    # Intentional, consistent line-icons without external icon dependencies.
    import math
    if k==0:
        draw.arc((cx-23,cy-23,cx+23,cy+23),25,330,fill=color,width=4)
        draw.line([(cx+22,cy-16),(cx+22,cy-2),(cx+36,cy-8)],fill=color,width=4)
    elif k==1:
        draw.line([(cx-30,cy-10),(cx+30,cy-10)],fill=color,width=4)
        draw.polygon([(cx+30,cy-10),(cx+19,cy-20),(cx+19,cy)],fill=color)
        draw.line([(cx+30,cy+13),(cx-30,cy+13)],fill=color,width=4)
        draw.polygon([(cx-30,cy+13),(cx-19,cy+3),(cx-19,cy+23)],fill=color)
    else:
        draw.line([(cx-10,cy-24),(cx+10,cy-24)],fill=color,width=4)
        draw.line([(cx-5,cy-24),(cx-5,cy-6),(cx-24,cy+25),(cx+24,cy+25),(cx+5,cy-6),(cx+5,cy-24)],fill=color,width=4)
        draw.line([(cx-15,cy+8),(cx+15,cy+8)],fill=color,width=3)

def card(draw,x,y,w,h,kind,name,head,caption,mobile):
    colors=[TEAL,COPPER,STEEL];color=colors[kind]
    rect(draw,(x,y,x+w,y+h),WHITE,LINE,18)
    box_w=77 if mobile else 81
    rect(draw,(x+23,y+24,x+23+box_w,y+24+box_w),['#e0f1f2','#f4e7df','#e8eef2'][kind],rad=17)
    symbol(draw,x+23+box_w//2,y+24+box_w//2,kind,color)
    name_x=x+130
    text(draw,name_x,y+32,name,31 if mobile else 31,color,True)
    text(draw,x+28,y+133,head,25 if mobile else 23,TEXT,True)
    paragraph(draw,x+28,y+184,caption,w-50,22 if mobile else 23,GRAY)

def section_label(draw,x,y,number,name,mobile):
    text(draw,x,y,number+'  /  '+name,25 if mobile else 26,DARK,True)

def pass_card(draw,x,y,w,h,index,head,description,bullets,mobile):
    rect(draw,(x,y,x+w,y+h),WHITE,LINE,18)
    band='#e0f0f3' if index==1 else '#f5e8dc'
    label=CYAN if index==1 else COPPER
    draw.rounded_rectangle((x+1,y+1,x+w-1,y+72),radius=17,fill=band)
    draw.rectangle((x+1,y+48,x+w-1,y+72),fill=band)
    text(draw,x+22,y+21,'PASS '+('ONE' if index==1 else 'TWO'),22,label,True)
    text(draw,x+200 if mobile else x+193,y+19,head,22 if mobile else 19,TEXT,True)
    paragraph(draw,x+25,y+93,description,w-50,23 if mobile else 23,GRAY)
    y0=y+(172 if mobile else 169)
    for i,line in enumerate(bullets):
        yy=y0+i*(70 if mobile else 50)
        draw.ellipse((x+26,yy+12,x+42,yy+28),fill=label)
        text(draw,x+59,yy,line,22 if mobile else 21,TEXT)

def footer(img,draw,w,y,mobile,portrait):
    x=40 if mobile else 80
    draw.line((x,y,w-x,y),fill=LINE,width=2)
    if portrait and portrait.exists():
        photo=Image.open(portrait).convert('RGB').resize((82,82),Image.Resampling.LANCZOS)
        mask=Image.new('L',(82,82),0);ImageDraw.Draw(mask).ellipse((0,0,81,81),fill=255)
        img.paste(photo,(x+8,y+18),mask)
    text(draw,x+106,y+31,'Jair Ribeiro',24 if mobile else 22,TEXT,True)
    text(draw,x+106,y+67,'AI LEADER  ·  ENTERPRISE AI ADOPTION  ·  GOVERNANCE',15 if mobile else 16,GRAY,True)
    if not mobile:
        text(draw,w-330,y+43,'JAIRRIBEIRO.COM',21,COPPER,True)
    else:
        text(draw,x+106,y+104,'JAIRRIBEIRO.COM',19,COPPER,True)

def desktop(portrait):
    w,h=1800,1370;im=Image.new('RGB',(w,h),BG);d=ImageDraw.Draw(im)
    header(d,w,h,False)
    margin=80;section_label(d,margin,354,'01','MAKE THE NEXT COMMITMENT COMPETE',False)
    cw=(w-2*margin-48)//3
    for i,(label,head,cap) in enumerate([
        ('RENEW','Keep the existing initiative','Only if the future case still wins'),
        ('REPLACE','Redirect the investment','Count switching and continuity costs'),
        ('TEST','Buy evidence, not more runway','Limit spend, uncertainty and time')]):
        card(d,margin+i*(cw+24),402,cw,238,i,label,head,cap,False)
    section_label(d,margin,676,'02','TWO PASSES, ONE HONEST DECISION',False)
    half=(w-2*margin-34)//2
    pass_card(d,margin,725,half,318,1,'CLEAN-SHEET JUDGMENT','Temporarily remove the advantage of prior approval.',[
        'Compare future business value','Show evidence, not a polished demo','Price the same scarce capacity'],False)
    pass_card(d,margin+half+34,725,half,318,2,'RESTORE REAL-WORLD CONSEQUENCES','Put the transition and operating realities back.',[
        'Include exit and switching costs','Protect mandatory duties and continuity','Name the owner and next review'],False)
    rect(d,(margin,1074,w-margin,1217),DARK,rad=18)
    text(d,margin+31,1093,'THE LEADERSHIP CALL',20,'#70cdd9',True)
    text(d,margin+32,1136,'RENEW   /   REPLACE   /   TEST',41,WHITE,True)
    paragraph(d,margin+965,1112,'If no next investment is justified, stop discretionary spend and release the capacity.',535,24,WHITE,32)
    footer(im,d,w,1245,False,portrait)
    return im

def mobile(portrait):
    w,h=900,2470;im=Image.new('RGB',(w,h),BG);d=ImageDraw.Draw(im)
    header(d,w,h,True)
    margin=38;section_label(d,margin,511,'01','MAKE THE NEXT COMMITMENT COMPETE',True)
    for i,(label,head,cap) in enumerate([
        ('RENEW','Keep the existing initiative','Only if the future case still wins'),
        ('REPLACE','Redirect the investment','Count switching and continuity costs'),
        ('TEST','Buy evidence, not more runway','Limit spend, uncertainty and time')]):
        card(d,margin,566+i*262,w-2*margin,236,i,label,head,cap,True)
    section_label(d,margin,1385,'02','TWO PASSES, ONE HONEST DECISION',True)
    pass_card(d,margin,1439,w-2*margin,360,1,'CLEAN-SHEET JUDGMENT','Temporarily remove the advantage of prior approval.',[
        'Compare future business value','Show evidence, not a polished demo','Price the same scarce capacity'],True)
    pass_card(d,margin,1817,w-2*margin,360,2,'REAL-WORLD CONSEQUENCES','Put the transition and operating realities back.',[
        'Include exit and switching costs','Protect mandatory duties and continuity','Name the owner and next review'],True)
    rect(d,(margin,2190,w-margin,2331),DARK,rad=15)
    text(d,margin+22,2208,'THE LEADERSHIP CALL',19,'#70cdd9',True)
    text(d,margin+22,2240,'RENEW  /  REPLACE  /  TEST',31,WHITE,True)
    paragraph(d,margin+22,2285,'Stop discretionary spend if none of the options is justified.',w-2*margin-40,18,WHITE,25)
    footer(im,d,w,2350,True,portrait)
    return im

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',default='static/briefing-artwork')
    parser.add_argument('--portrait',default='static/briefing-roi-portrait.webp')
    args=parser.parse_args()
    folder=Path(args.root)/SLUG;folder.mkdir(parents=True,exist_ok=True)
    portrait=Path(args.portrait)
    versions={}
    for name,build in [('desktop',desktop),('mobile',mobile)]:
        image=build(portrait)
        p=folder/(name+'.webp')
        image.save(p,'WEBP',quality=87,method=6)
        versions[name]={'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(), 'width':image.width,'height':image.height}
    a4=mobile(portrait).resize((1654,2339),Image.Resampling.LANCZOS)
    out=folder/'infographic.pdf'
    with out.open('wb') as f:
        pdf=canvas.Canvas(f,pagesize=A4,pageCompression=1)
        pdf.setTitle('AI Portfolio Renewal Challenge - Executive infographic')
        pdf.setAuthor('Jair Ribeiro')
        pdf.drawImage(ImageReader(a4),0,0,width=A4[0],height=A4[1])
        pdf.showPage();pdf.save()
    versions['pdf']={'file':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'pages':1}
    manifest={
      'schema_version':1,'slug':SLUG,'revision':'v2-humanized-20261116-release',
      'article_fingerprint':FINGERPRINT,'heading':'Would you fund it again?',
      'deck':'Existing AI initiatives must compete for the next commitment.',
      **versions,
      'alt_text':'Original AI Portfolio Renewal Challenge map. Compare Renew, Replace and Test against future business value and evidence in a clean-sheet pass, then restore switching costs, continuity, mandatory safeguards and ownership before the executive decision.',
      'caption':'The AI Portfolio Renewal Challenge: review incumbent and alternative investments in two passes before renewing, replacing, testing or ending discretionary expenditure. Original decision illustration by Jair Ribeiro.'
    }
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Created artwork:',folder)
    for key in ['desktop','mobile','pdf']:
        p=folder/manifest[key]['file'];print(key,p.stat().st_size,manifest[key]['sha256'])

if __name__=='__main__':main()
