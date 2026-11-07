#!/usr/bin/env python3
"""Publish source-locked v2 Policy Is Not Permission artwork.
Preserves the reviewed six-card desktop/mobile figures; corrects brand footer,
makes a 16:9 cover, renews PDF, and writes content-fingerprint manifest.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader
import hashlib, io, json, math, sys

ROOT=Path(__file__).resolve().parents[1]
SLUG='policy-is-not-permission-executive-ai-governance'
ART=ROOT/'static'/'briefing-artwork'/SLUG
SOURCE=ROOT/'docs'/'briefing_revisions'/'policy-is-not-permission-v2.json'
REV='2026-11-07-r3'
NAVY=(4,31,54); CYAN=(4,199,236); COPPER=(191,137,101)
FONTS=['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']
BOLDS=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf']
def font(size,bold=False):
    paths=BOLDS if bold else FONTS
    for p in paths:
        if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()
def digest(raw): return hashlib.sha256(raw).hexdigest()
def portrait_from_art(im,box):
    crop=im.crop(box)
    w,h=crop.size; mask=Image.new('L',(w,h),0)
    ImageDraw.Draw(mask).ellipse((1,1,w-2,h-2),fill=255)
    return crop,mask
def footer(im,mobile=False):
    w,h=im.size
    height=155 if mobile else 125
    y=h-height
    original=im.copy()
    if mobile:
        # The existing approved image already holds Jair's authentic portrait.
        circ,mask=portrait_from_art(original,(32,h-132,116,h-48))
        px,py=34,h-133; text_x=143
    else:
        circ,mask=portrait_from_art(original,(63,h-121,153,h-31))
        px,py=67,h-122; text_x=175
    d=ImageDraw.Draw(im)
    d.rectangle((0,y,w,h),fill=NAVY)
    for k in range(5):
        pts=[(x,int(y+26+k*8+10*math.sin(x/118.0+k*.7))) for x in range(0,w,6)]
        d.line(pts,fill=(4,64+5*k,91+4*k),width=1)
    if mobile:
        d.ellipse((px-4,py-4,px+circ.width+4,py+circ.height+4),fill='white')
        im.paste(circ,(px,py),mask)
        d.text((text_x,y+13),'Jair Ribeiro',fill='white',font=font(29,True))
        d.text((text_x,y+52),'AI LEADER',fill=CYAN,font=font(18,True))
        d.text((text_x,y+83),'Enterprise AI Adoption • Governance',fill='#DEEBF3',font=font(16))
        d.text((text_x,y+108),'Business Transformation',fill='#DEEBF3',font=font(16))
    else:
        d.ellipse((px-4,py-4,px+circ.width+4,py+circ.height+4),fill='white')
        im.paste(circ,(px,py),mask)
        d.text((text_x,y+28),'Jair Ribeiro',fill='white',font=font(32,True))
        d.text((text_x,y+78),'AI LEADER',fill=CYAN,font=font(20,True))
        line='Enterprise AI Adoption • Governance • Business Transformation'
        size=20
        while d.textbbox((0,0),line,font=font(size))[2]>w-375 and size>14: size-=1
        d.text((365,y+79),line,fill='#E6F2F7',font=font(size))
    return im
def create_cover(path):
    w,h=1600,900
    cover=Image.new('RGB',(w,h)); d=ImageDraw.Draw(cover)
    for yy in range(h):
        t=yy/h
        d.line((0,yy,w,yy),fill=(int(2+7*t),int(23+24*t),int(45+28*t)))
    for k in range(14):
        pts=[]
        for x in range(0,w,7):
            y=660+k*8+int(40*math.sin(x/190+k*.22))
            pts.append((x,y))
        d.line(pts,fill=(6,58+k*3,91+k*4),width=2)
    d.line((82,108,234,108),fill=CYAN,width=5)
    d.text((86,67),'EXECUTIVE AI BRIEFING',font=font(29,True),fill=CYAN)
    d.text((84,210),'POLICY IS NOT',font=font(82,True),fill='white')
    d.text((84,317),'PERMISSION',font=font(97,True),fill=CYAN)
    d.text((88,488),'Six proofs before AI can act',font=font(40),fill='#F1F5F8')
    d.text((88,542),'for your business.',font=font(40),fill='#F1F5F8')
    d.text((88,803),'Jair Ribeiro  |  AI LEADER',font=font(25,True),fill='#D9E9F0')
    # Six linked, meaningful checks converge at a single execution boundary.
    cx,cy=1230,406
    for rad,col in ((290,(9,85,122)),(235,(8,122,155)),(182,(19,139,168))):
        d.ellipse((cx-rad,cy-rad,cx+rad,cy+rad),outline=col,width=3)
    centers=[]
    for i in range(6):
        a=math.pi*i/3-math.pi/2
        x=int(cx+275*math.cos(a));y=int(cy+275*math.sin(a))
        centers.append((x,y));d.line((cx,cy,x,y),fill=(5,142,178),width=3)
    for i,(x,y) in enumerate(centers):
        d.ellipse((x-49,y-49,x+49,y+49),fill=(8,58,88),outline=(24,183,211),width=4)
        d.text((x-15,y-25),str(i+1),font=font(42,True),fill='#F2FAFC')
    # Shield + working-control mark at the heart of permission.
    shield=[(cx,cy-142),(cx+115,cy-89),(cx+96,cy+81),(cx,cy+156),(cx-96,cy+81),(cx-115,cy-89)]
    d.polygon(shield,fill=(8,64,88),outline=(4,213,240),width=9)
    d.line([(cx-53,cy+7),(cx-10,cy+44),(cx+67,cy-38)],fill=(215,162,113),width=16,joint='curve')
    cover.save(path,format='WEBP',quality=84,method=6)
    return cover.size
def main():
    data=json.loads(SOURCE.read_text(encoding='utf-8'))
    fingerprint=digest((data['title']+'|'+data['subtitle']+'|'+data['content_html']).encode('utf-8'))
    ART.mkdir(parents=True,exist_ok=True)
    files={}
    for kind in ('desktop','mobile'):
        p=ART/(kind+'.webp')
        im=Image.open(p).convert('RGB')
        # Use a full-resolution original; never shrink a desktop sheet for mobile.
        assert (im.width,im.height)==((1200,1820) if kind=='desktop' else (720,2910)),im.size
        footer(im,mobile=(kind=='mobile'))
        im.save(p,format='WEBP',quality=87,method=6)
        with Image.open(p) as check: check.verify()
        files[kind]={'file':p.name,'sha256':digest(p.read_bytes()),'width':im.width,'height':im.height,'bytes':p.stat().st_size}
        assert p.stat().st_size<1500000
    cover_path=ART/'cover.webp'
    cw,ch=create_cover(cover_path)
    with Image.open(cover_path) as check: check.verify()
    files['cover']={'file':'cover.webp','sha256':digest(cover_path.read_bytes()),'width':cw,'height':ch,'bytes':cover_path.stat().st_size}
    pdf=ART/'infographic.pdf'
    with Image.open(ART/'desktop.webp') as art:
        art=art.convert('RGB');out=io.BytesIO();art.save(out,'JPEG',quality=91,subsampling=0)
        c=canvas.Canvas(str(pdf),pagesize=A4)
        c.setTitle('Policy Is Not Permission | Jair Ribeiro');c.setAuthor('Jair Ribeiro')
        pw,ph=A4;sc=min((pw-24)/art.width,(ph-24)/art.height)
        iw,ih=art.width*sc,art.height*sc
        c.drawImage(ImageReader(io.BytesIO(out.getvalue())),(pw-iw)/2,(ph-ih)/2,width=iw,height=ih)
        c.showPage();c.save()
    reader=PdfReader(str(pdf),strict=True);assert len(reader.pages)==1
    assert 589<float(reader.pages[0].mediabox.width)<601 and 836<float(reader.pages[0].mediabox.height)<848
    files['pdf']={'file':'infographic.pdf','sha256':digest(pdf.read_bytes()),'pages':1,'bytes':pdf.stat().st_size}
    manifest={'schema_version':1,'slug':SLUG,'article_fingerprint':fingerprint,'revision':REV,
      'heading':'Policy is not permission','deck':'Six operating proofs, bounded autonomy and enforceable action-time control.',
      **files,'release_note':'Approved source-matched revision: article, responsive artwork, authentic author footer and A4 PDF.'}
    (ART/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'revision':REV,'fingerprint':fingerprint,'files':files},indent=2))
    return 0
if __name__=='__main__': sys.exit(main())
