#!/usr/bin/env python3
"""Premium source-locked AI Portfolio Renewal Challenge edition (original diagram)."""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

SLUG='would-you-fund-the-same-ai-initiatives-today'
FINGERPRINT='b9e255ca0e7ac9fdf7504e98fe07dd9e8f642c96c4e492d6aac4adf511c27bd5'
NAVY='#081E32'; DEEP='#0B2E48'; TEAL='#0F8194'; CYAN='#48C6DB'; COPPER='#B77F59'; GOLD='#D8A879'; WHITE='#FFFFFF'; INK='#18344B'; GRAY='#526675'; PAPER='#F6F8F6'; PALE='#E6F2F3'; LIGHT='#DAE5E8'
FONTS=Path('/usr/share/fonts/truetype/lato'); SERIFS=Path('/usr/share/fonts/truetype/noto')
FONT_B=FONTS/'Lato-Heavy.ttf'; FONT_R=FONTS/'Lato-Regular.ttf'; FONT_SB=FONTS/'Lato-Semibold.ttf'; FONT_SE=SERIFS/'NotoSerifDisplay-SemiBold.ttf'
if not FONT_SE.is_file():FONT_SE=Path('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf')
if not FONT_B.is_file():FONT_B=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
if not FONT_R.is_file():FONT_R=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
if not FONT_SB.is_file():FONT_SB=FONT_B

def f(n,weight='r'):
    p={'r':FONT_R,'b':FONT_B,'sb':FONT_SB,'serif':FONT_SE}[weight]
    return ImageFont.truetype(str(p),int(n))

def txt(d,xy,s,n,c=INK,weight='r',anchor=None):
    d.text(xy,s,font=f(n,weight),fill=c,anchor=anchor,stroke_width=0)

def lines(d,s,w,n,weight='r'):
    words=s.split(); parts=[]; line=''
    for word in words:
        nxt=(line+' '+word).strip()
        if line and d.textbbox((0,0),nxt,font=f(n,weight))[2]>w:
            parts.append(line);line=word
        else:line=nxt
    if line:parts.append(line)
    return parts

def para(d,x,y,s,w,n,c=GRAY,leading=None,weight='r'):
    leading=leading or int(n*1.35)
    for line in lines(d,s,w,n,weight):txt(d,(x,y),line,n,c,weight);y+=leading
    return y

def rr(d,xy,rad,fill,outline=None,width=2):d.rounded_rectangle(xy,radius=rad,fill=fill,outline=outline,width=width)

def vertical_gradient(im,area,start,end):
    import PIL.ImageColor
    c1=PIL.ImageColor.getrgb(start);c2=PIL.ImageColor.getrgb(end)
    x0,y0,x1,y1=area
    for y in range(y0,y1):
        r=(y-y0)/max(1,y1-y0)
        c=tuple(int(a+(b-a)*r) for a,b in zip(c1,c2))
        ImageDraw.Draw(im).line((x0,y,x1,y),fill=c)

def shadow_card(im,box,r=25,fill=WHITE,outline=LIGHT,blur=12,alpha=24):
    x0,y0,x1,y1=map(int,box)
    sh=Image.new('RGBA',im.size,(0,0,0,0));sd=ImageDraw.Draw(sh)
    sd.rounded_rectangle((x0+1,y0+9,x1+1,y1+9),radius=r,fill=(7,32,54,alpha))
    im.paste(Image.alpha_composite(im.convert('RGBA'),sh.filter(ImageFilter.GaussianBlur(blur))).convert('RGB'))
    d=ImageDraw.Draw(im);rr(d,box,r,fill,outline,2)
    return d

def arrow(d,cx,y,size=23,c=TEAL):
    d.line((cx,y-size,cx,y+size-8),fill=c,width=6)
    d.polygon([(cx-size//2,y+size-8),(cx+size//2,y+size-8),(cx,y+size+10)],fill=c)

def accent_line(d,x,y,w,c=CYAN):d.rounded_rectangle((x,y,x+w,y+5),radius=2,fill=c)

def portrait_footer(im,y,portrait,mobile=False):
    d=ImageDraw.Draw(im);w,h=im.size
    d.rectangle((0,y,w,h),fill=NAVY)
    dx=44 if mobile else 92;size=94 if mobile else 88
    if portrait.exists():
        ph=Image.open(portrait).convert('RGB').resize((size,size),Image.Resampling.LANCZOS)
        mask=Image.new('L',(size,size),0);ImageDraw.Draw(mask).ellipse((2,2,size-3,size-3),fill=255)
        d.ellipse((dx-5,y+38-5,dx+size+5,y+38+size+5),outline='#E8B38B',width=4)
        im.paste(ph,(dx,y+38),mask)
    tx=dx+size+27
    txt(d,(tx,y+51),'Jair Ribeiro',29 if mobile else 30,WHITE,'b')
    txt(d,(tx,y+99),'AI LEADER  •  ENTERPRISE AI ADOPTION  •  GOVERNANCE',15 if mobile else 19,'#B8CCD7','sb')
    if not mobile:txt(d,(w-390,y+76),'JAIRRIBEIRO.COM',22,'#E7B18D','b')

def cover(im,mobile):
    d=ImageDraw.Draw(im);w,h=im.size
    hero_h=640 if mobile else 580
    vertical_gradient(im,(0,0,w,hero_h),NAVY,'#173C55')
    d=ImageDraw.Draw(im)
    # Quiet flowing geometry, not decorative noise.
    # Fine curved rules stay INSIDE the dark cover; never overlap body copy.
    overlay=Image.new('RGBA',(w,hero_h),(0,0,0,0))
    od=ImageDraw.Draw(overlay)
    for k in range(5):
        y=90+k*68
        od.arc((int(w*.61),y-int(w*.18),int(w*1.13),y+int(w*.34)),10,155,fill=(78,131,150,105),width=3)
    im.paste(overlay,(0,0),overlay)
    mx=43 if mobile else 91
    d.rounded_rectangle((mx,53,mx+10,77),radius=3,fill=CYAN)
    txt(d,(mx+31,47),'EXECUTIVE AI BRIEFING   /   PORTFOLIO & VALUE',22 if mobile else 25,'#8CDCE6','b')
    if mobile:
        txt(d,(mx,126),'Would you fund',73,'#FFFFFF','serif')
        txt(d,(mx,216),'the same AI initiatives',52,'#FFFFFF','serif')
        txt(d,(mx,292),'today?',74,'#E8AE81','serif')
        para(d,mx,407,'A renewal test for the next investment, not another ranking of AI ideas.',w-mx*2,28,'#D5E5EB',39)
        rr(d,(mx,540,w-mx,597),22,'#164864','#4588A0',2)
        txt(d,(mx+26,552),'THE AI PORTFOLIO RENEWAL CHALLENGE',24,'#FFE1C6','b')
    else:
        txt(d,(mx,143),'Would you fund the same',80,'#FFFFFF','serif')
        txt(d,(mx,248),'AI initiatives today?',99,'#E8AE81','serif')
        para(d,mx,387,'Existing commitments should have to earn the next investment.',w-mx*2,36,'#D5E5EB',49)
        rr(d,(mx,490,mx+690,550),25,'#164864','#4588A0',2)
        txt(d,(mx+24,502),'THE AI PORTFOLIO RENEWAL CHALLENGE',26,'#FFE1C6','b')
    return hero_h

def stage(d,x,y,index,title,desc,width,mobile=False):
    accent_line(d,x,y+11,24,COPPER)
    txt(d,(x+38,y),f'0{index}',27 if mobile else 30,COPPER,'b')
    txt(d,(x+103,y),title,33 if mobile else 34,INK,'b')
    para(d,x+103,y+50,desc,width-110,23 if mobile else 26,GRAY,37)

def choice_card(im,x,y,w,h,primary,name,tag,title,desc,accent):
    d=shadow_card(im,(x,y,x+w,y+h),r=24,fill=WHITE,outline='#D4E3E7',blur=11)
    d.rectangle((x+25,y+29,x+37,y+66),fill=accent)
    txt(d,(x+60,y+28),tag,21,COPPER if primary else TEAL,'b')
    txt(d,(x+42,y+101),name,42,INK,'b')
    para(d,x+42,y+170,title,w-80,30,INK,43,'sb')
    para(d,x+42,y+(239 if h<340 else 277),desc,w-80,23 if h<340 else 25,GRAY,32)

def two_pass(im,x,y,w,mobile=False):
    d=ImageDraw.Draw(im)
    txt(d,(x,y),'THE TWO-PASS TEST',42 if mobile else 49,INK,'serif')
    para(d,x,y+67,'A clean-sheet choice. Then a realistic commitment.',w,26 if mobile else 30,GRAY)
    p1=y+150;ph=320 if mobile else 320
    d=shadow_card(im,(x,p1,x+w,p1+ph),r=23,fill=WHITE)
    rr(d,(x+28,p1+31,x+200,p1+82),21,'#D8EFF0')
    txt(d,(x+53,p1+40),'PASS 01',28,TEAL,'b')
    txt(d,(x+232,p1+38),'REMOVE THE ADVANTAGE',30 if mobile else 32,INK,'b')
    para(d,x+36,p1+114,'Which option wins on future value, real evidence and scarce capacity?',w-72,27 if mobile else 30,INK,43)
    for i,t in enumerate(['Forward value','Observed evidence','Shared resources']):
        span=(w-78)/3;xx=x+30+i*span
        rr(d,(xx,p1+244,xx+span-12,p1+292),15,'#E8F4F4')
        txt(d,(xx+13,p1+255),t,20 if mobile else 24,TEAL,'b')
    arrow(d,x+w//2,p1+ph+36,16,TEAL)
    p2=p1+ph+84
    d=shadow_card(im,(x,p2,x+w,p2+ph),r=23,fill=WHITE)
    rr(d,(x+28,p2+31,x+200,p2+82),21,'#F2E7DE')
    txt(d,(x+53,p2+40),'PASS 02',28,COPPER,'b')
    txt(d,(x+232,p2+38),'RESTORE REALITY',30 if mobile else 32,INK,'b')
    para(d,x+36,p2+114,'What changes after transition costs, operating duties and risk are included?',w-72,27 if mobile else 30,INK,43)
    for i,t in enumerate(['Switching costs','Continuity duties','Decision rights']):
        span=(w-78)/3;xx=x+30+i*span
        rr(d,(xx,p2+244,xx+span-12,p2+292),15,'#F6EDE7')
        txt(d,(xx+13,p2+255),t,20 if mobile else 24,'#A86E4B','b')
    return p2+ph

def outcomes(im,x,y,w,mobile=False):
    d=ImageDraw.Draw(im)
    txt(d,(x,y),'THE NEXT COMMITMENT',41 if mobile else 49,INK,'serif')
    para(d,x,y+63,'The meeting ends with a choice and an owner.',w,26 if mobile else 29,GRAY)
    names=['RENEW','REPLACE','TEST','STOP']
    desc=['Continue only when the forward case still wins.',
          'Redirect capacity to the better route.',
          'Resolve a material uncertainty with bounded evidence.',
          'Release spend when no next investment is justified.']
    accents=[TEAL,COPPER,'#517F99','#607382']
    # Outcome rows are more legible than dense mini-cards on phones.
    yy=y+142
    for i,(name,sub,c) in enumerate(zip(names,desc,accents)):
        h=94 if mobile else 105
        d=shadow_card(im,(x,yy,x+w,yy+h),18,WHITE,'#D9E5E7',7,16)
        rr(d,(x+17,yy+19,x+30,yy+h-19),6,c)
        txt(d,(x+51,yy+27),name,31 if mobile else 34,c,'b')
        desc_x=x+(225 if mobile else 275)
        para(d,desc_x,yy+24,sub,w-(desc_x-x)-28,24 if mobile else 28,INK,31)
        yy+=h+19
    return yy

def make_desktop(portrait):
    w,h=1800,2550
    im=Image.new('RGB',(w,h),PAPER);d=ImageDraw.Draw(im)
    cover(im,False);d=ImageDraw.Draw(im)
    x=91
    stage(d,x,650,1,'MAKE THE INCUMBENT COMPETE',
          'Every funding request should face its strongest credible alternative.',w-2*x)
    # Two comparable investment choices with a central VS counter.
    y=790;cw=744;gap=130
    choice_card(im,x,y,cw,404,True,'INCUMBENT','EXISTING AI INITIATIVE',
                'What will continuing deliver?',
                'Count the next stage, not the money already spent.',TEAL)
    choice_card(im,x+cw+gap,y,cw,404,False,'ALTERNATIVE','BEST CREDIBLE ROUTE',
                'What could deliver more?',
                'Another AI approach, a workflow change, or no new spend.',COPPER)
    d=ImageDraw.Draw(im);cx=x+cw+gap//2;cy=y+210
    d.ellipse((cx-53,cy-53,cx+53,cy+53),fill=NAVY,outline='#BBD3DA',width=3)
    txt(d,(cx,cy),'VS',35,'#FFFFFF','b',anchor='mm')
    stage(d,x,1277,2,'CHALLENGE THE NEXT COMMITMENT',
          'Two passes make the comparison fair without pretending that switching is free.',w-2*x)
    p_end=two_pass(im,x,1427,w-2*x,False)
    # The decision is a visible gate, not a fourth hidden checklist.
    d=ImageDraw.Draw(im)
    rr(d,(x,2300,w-x,2390),23,NAVY)
    txt(d,(x+31,2321),'DECIDE:  RENEW   /   REPLACE   /   TEST   /   STOP',34,WHITE,'b')
    txt(d,(x+32,2361),'Commit resources, name the owner and set the review trigger.',21,'#C5DDE3','r')
    portrait_footer(im,2402,portrait,False)
    return im

def make_mobile(portrait):
    w,h=900,3560;im=Image.new('RGB',(w,h),PAPER);d=ImageDraw.Draw(im)
    cover(im,True);d=ImageDraw.Draw(im);x=43;cw=w-2*x
    stage(d,x,695,1,'MAKE THE INCUMBENT COMPETE',
          'Compare a current project with the best credible alternative.',cw,True)
    choice_card(im,x,845,cw,300,True,'INCUMBENT','EXISTING AI INITIATIVE',
                'What will continuing deliver?',
                'Judge the next stage, not the sunk cost.',TEAL)
    d=ImageDraw.Draw(im);cx=w//2;cy=1189
    d.ellipse((cx-44,cy-44,cx+44,cy+44),fill=NAVY)
    txt(d,(cx,cy),'VS',29,WHITE,'b','mm')
    choice_card(im,x,1250,cw,300,False,'ALTERNATIVE','BEST CREDIBLE ROUTE',
                'What could deliver more?',
                'Another AI route or a simpler process fix.',COPPER)
    stage(d,x,1620,2,'CHALLENGE THE NEXT COMMITMENT',
          'Remove the incumbent advantage. Then put reality back.',cw,True)
    two_pass(im,x,1780,cw,True)
    outcomes(im,x,2690,cw,True)
    portrait_footer(im,3410,portrait,True)
    return im

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',default='static/briefing-artwork')
    ap.add_argument('--portrait',default='static/briefing-roi-portrait.webp')
    args=ap.parse_args();folder=Path(args.root)/SLUG;folder.mkdir(parents=True,exist_ok=True)
    portrait=Path(args.portrait);variants={}
    for kind,fn in [('desktop',make_desktop),('mobile',make_mobile)]:
        im=fn(portrait);source=folder/(kind+'.png');im.save(source,'PNG',optimize=True)
        dest=folder/(kind+'.webp');im.save(dest,'WEBP',quality=92,method=6)
        variants[kind]={'file':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'width':im.width,'height':im.height}
    im=make_desktop(portrait)
    pdf_file=folder/'infographic.pdf'
    with pdf_file.open('wb') as stream:
        pdf=canvas.Canvas(stream,pagesize=A4,pageCompression=1)
        pdf.setTitle('Would You Fund the Same AI Initiatives Today? — Executive Infographic')
        pdf.setAuthor('Jair Ribeiro')
        pdf.drawImage(ImageReader(im),0,0,width=A4[0],height=A4[1]);pdf.showPage();pdf.save()
    variants['pdf']={'file':'infographic.pdf','sha256':hashlib.sha256(pdf_file.read_bytes()).hexdigest(),'pages':1}
    manifest={
        'schema_version':1,'slug':SLUG,'revision':'v3-premium-editorial-20261116',
        'article_fingerprint':FINGERPRINT,
        'heading':'Would you fund the same AI initiatives today?',
        'deck':'Existing commitments must compete for the next investment.',
        **variants,
        'alt_text':'The AI Portfolio Renewal Challenge. Compare the existing AI initiative with the best credible alternative for the same business result. Pass one removes prior-approval bias and compares future value, observed evidence, and shared capacity; pass two restores switching costs, continuity, and decision rights. Leaders then renew, replace, test, or stop.',
        'caption':'AI Portfolio Renewal Challenge: make the incumbent compete, evaluate in two passes, then record an accountable next commitment. Original framework and infographic by Jair Ribeiro.',
    }
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for k in ['desktop','mobile','pdf']:
        p=folder/manifest[k]['file'];print(k, p.stat().st_size,manifest[k]['sha256'])

if __name__=='__main__':main()