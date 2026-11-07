#!/usr/bin/env python3
"""Original source-matched executive decision infographic: Policy Is Not Permission."""
from pathlib import Path
from math import sin
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[1]
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
NAVY=(4,34,60); SKY=(3,201,232); INK=(19,47,68)
MUTED=(78,102,116); TEAL=(29,115,136); COPPER=(196,131,89)
ITEMS=[
 ("01","BUSINESS CASE",("Value at stake and named owner","Benefit net of oversight cost"),"target"),
 ("02","COMPLETE DISCOVERY",("Agents, embedded AI and suppliers","Actions and data access mapped"),"search"),
 ("03","RULES & RISK",("Applicable duties and exposure","Impact and cost of reversal"),"scale"),
 ("04","BOUNDED AUTHORITY",("Specific action, identity and duration","Approver and revocation right"),"shield"),
 ("05","ENFORCEMENT AT EXECUTION",("Policy checked when the action occurs","Prohibited actions tested and blocked"),"lock"),
 ("06","OPERATING EVIDENCE",("Tests, overrides, incidents and logs","Net value after control costs"),"doc"),
]
def ft(size,bold=False): return ImageFont.truetype(BOLD if bold else FONT,size)
def txt(d,x,y,s,size,fill,bold=False): d.text((x,y),s,font=ft(size,bold),fill=fill)
def gradient(im,top,bottom,y0,y1):
 d=ImageDraw.Draw(im)
 for y in range(y0,y1):
  a=(y-y0)/max(1,y1-y0)
  c=tuple(round(top[i]*(1-a)+bottom[i]*a) for i in range(3))
  d.line((0,y,im.width,y),fill=c)
def portrait(im,x,y,r):
 path=ROOT/"static/briefing-roi-portrait.webp"
 if not path.is_file(): return
 source=Image.open(path).convert("RGB")
 crop=ImageOps.fit(source,(2*r,2*r),method=Image.Resampling.LANCZOS,centering=(.5,.35))
 mask=Image.new("L",(2*r,2*r),0)
 ImageDraw.Draw(mask).ellipse((0,0,2*r-1,2*r-1),fill=255)
 dr=ImageDraw.Draw(im)
 dr.ellipse((x-r-4,y-r-4,x+r+4,y+r+4),fill=(245,250,254))
 im.paste(crop,(x-r,y-r),mask)
def icon(d,x,y,name,color):
 s=4
 if name=="target":
  for r in (32,19,6): d.ellipse((x-r,y-r,x+r,y+r),outline=color,width=s)
  d.line((x,y,x+34,y-37),fill=COPPER,width=6)
 if name=="search":
  d.ellipse((x-28,y-32,x+22,y+18),outline=color,width=5)
  d.line((x+20,y+17,x+48,y+45),fill=color,width=7)
 if name=="scale":
  d.line((x,y-41,x,y+42),fill=color,width=5)
  d.line((x-39,y-26,x+39,y-26),fill=color,width=5)
  d.line((x-43,y+41,x+43,y+41),fill=color,width=5)
  d.line((x-31,y-26,x-46,y+12),fill=color,width=4)
  d.line((x+31,y-26,x+46,y+12),fill=color,width=4)
 if name=="shield":
  d.line([(x,y-46),(x+40,y-30),(x+35,y+20),(x,y+49),(x-35,y+20),(x-40,y-30),(x,y-46)],fill=color,width=5,joint="curve")
  d.line([(x-20,y+2),(x-3,y+19),(x+25,y-18)],fill=COPPER,width=5,joint="curve")
 if name=="lock":
  d.rounded_rectangle((x-39,y-6,x+39,y+51),8,outline=color,width=5)
  d.arc((x-28,y-54,x+28,y+20),180,360,fill=color,width=6)
 if name=="doc":
  d.rounded_rectangle((x-38,y-43,x+38,y+48),5,outline=color,width=5)
  for k in range(3): d.line((x-24,y-14+k*20,x+24,y-14+k*20),fill=color,width=4)
def card(im,coords,item,side=False):
 x,y,w,h=coords;number,name,lines,symbol=item
 d=ImageDraw.Draw(im)
 high=number=="05"
 d.rounded_rectangle((x+5,y+9,x+w+5,y+h+9),26,fill=(230,237,241))
 d.rounded_rectangle((x,y,x+w,y+h),26,fill=NAVY if high else (255,255,255),outline=SKY if high else (215,228,233),width=4 if high else 2)
 fg=(255,255,255) if high else INK
 sub=(208,228,236) if high else MUTED
 d.rounded_rectangle((x+25,y+22,x+105,y+72),12,fill=(0,83,107) if high else (227,241,245))
 txt(d,x+42,y+28,number,30,SKY if high else TEAL,True)
 if side:
  fs=29 if len(name)>20 else 33
  while d.textlength(name,font=ft(fs,True)) > w-168: fs-=1
  txt(d,x+141,y+27,name,fs,fg,True)
  d.line((x+142,y+86,x+w-28,y+86),fill=COPPER,width=3)
  icon(d,x+83,y+163,symbol,SKY if high else TEAL)
  for j,line in enumerate(lines): txt(d,x+146,y+115+j*47,line,25,sub)
 else:
  icon(d,x+w//2,y+132,symbol,SKY if high else TEAL)
  words=name.split()
  if name=="ENFORCEMENT AT EXECUTION": title=["ENFORCEMENT","AT EXECUTION"]
  elif name=="COMPLETE DISCOVERY": title=["COMPLETE","DISCOVERY"]
  elif name=="OPERATING EVIDENCE": title=["OPERATING","EVIDENCE"]
  elif name=="BOUNDED AUTHORITY": title=["BOUNDED","AUTHORITY"]
  else: title=[name]
  for j,t in enumerate(title): txt(d,x+22,y+198+j*38,t,25 if len(t)>15 else 29,fg,True)
  d.line((x+21,y+276,x+w-22,y+276),fill=COPPER,width=2)
  for j,line in enumerate(lines):
   # Compact, human-reviewed wording for graphic, not an article substitute.
   brief={
    "Value at stake and named owner":"Value and accountable owner",
    "Benefit net of oversight cost":"Benefit after oversight cost",
    "Agents, embedded AI and suppliers":"Embedded AI, agents, suppliers",
    "Actions and data access mapped":"Actions and data access",
    "Applicable duties and exposure":"Applicable duties, impact",
    "Impact and cost of reversal":"Cost to reverse",
    "Specific action, identity and duration":"Action, identity and duration",
    "Approver and revocation right":"Approver and revocation",
    "Policy checked when the action occurs":"Check policy at execution",
    "Prohibited actions tested and blocked":"Test attempted violations",
    "Tests, overrides, incidents and logs":"Tests, incidents and logs",
    "Net value after control costs":"Net value after control cost",
   }.get(line,line)
   txt(d,x+21,y+292+j*33,brief,17,sub)
def desktop(out):
 W,H=1200,1820;im=Image.new("RGB",(W,H),(250,252,252))
 gradient(im,(3,29,52),(9,58,85),0,415);d=ImageDraw.Draw(im)
 for j in range(10):
  pts=[(x,250+j*8+int(19*sin(x/128+j*.49))) for x in range(-10,W+11,4)]
  d.line(pts,fill=(14,104+3*j,143+3*j),width=1)
 txt(d,70,59,"A I   G O V E R N A N C E",26,SKY,True)
 d.line((69,105,275,105),fill=SKY,width=3)
 txt(d,65,130,"POLICY IS NOT",94,(255,255,255),True)
 txt(d,65,236,"PERMISSION",109,SKY,True)
 txt(d,70,355,"Six proofs before AI can act for your business.",31,(236,246,250))
 txt(d,69,450,"A signed policy is not proof of a working control.",31,INK,True)
 txt(d,70,501,"Connect business purpose, authority, runtime enforcement and evidence.",24,MUTED)
 card_w=342
 for i,it in enumerate(ITEMS):
  col,row=i%3,i//3
  card(im,(49+col*389,564+row*382,card_w,363),it)
 d=ImageDraw.Draw(im)
 d.line((70,1393,1130,1393),fill=(205,221,230),width=3)
 txt(d,69,1339,"AUTONOMY IS A BUSINESS DECISION",33,INK,True)
 tiers=[("OBSERVE",(220,234,243)),("RECOMMEND + REVIEW",(213,235,237)),("ACT WITHIN LIMITS",(240,223,209))]
 for i,(label,col) in enumerate(tiers):
  x=69+i*365
  d.rounded_rectangle((x,1420,x+333,1520),20,fill=col)
  txt(d,x+20,1455,label,23 if i==1 else 26,INK,True)
 d.rounded_rectangle((48,1555,1150,1680),33,fill=(17,57,85))
 txt(d,81,1573,"THE EXECUTIVE DECISION",27,(220,173,135),True)
 txt(d,81,1618,"Continue • restrict • repair • stop — with evidence.",33,(255,255,255))
 gradient(im,(4,34,60),(3,27,48),1690,H)
 portrait(im,117,1753,38)
 d=ImageDraw.Draw(im)
 txt(d,179,1714,"Jair Ribeiro",35,(255,255,255),True)
 txt(d,180,1762,"AI LEADER",24,SKY,True)
 txt(d,388,1768,"Enterprise AI Adoption  •  Governance  •  Business Value",20,(220,235,243))
 im.save(out/"desktop.png",optimize=True)
 return im
def mobile(out):
 W,H=720,2910;im=Image.new("RGB",(W,H),(250,252,252))
 gradient(im,(3,29,52),(8,57,82),0,450);d=ImageDraw.Draw(im)
 for j in range(9):
  pts=[(x,290+j*8+int(22*sin(x/121+j*.5))) for x in range(-10,W+11,4)]
  d.line(pts,fill=(11,100+j*4,144+j*3),width=1)
 txt(d,40,45,"A I   G O V E R N A N C E",24,SKY,True)
 txt(d,35,125,"POLICY IS NOT",65,(255,255,255),True)
 txt(d,35,211,"PERMISSION",75,SKY,True)
 txt(d,40,337,"Six proofs before AI can act.",31,(235,246,251))
 d.rounded_rectangle((29,467,691,608),20,fill=(229,240,244))
 txt(d,47,493,"FROM POLICY TO OPERATING PROOF",25,INK,True)
 txt(d,47,540,"The permission must still be valid",27,MUTED)
 txt(d,47,572,"when the action occurs.",27,MUTED)
 for i,it in enumerate(ITEMS):
  card(im,(30,638+i*279,660,256),it,side=True)
 d=ImageDraw.Draw(im)
 txt(d,39,2340,"AUTONOMY IS A BUSINESS DECISION",29,INK,True)
 for j,(label,bg) in enumerate([
  ("OBSERVE",(220,234,243)),("RECOMMEND + REVIEW",(215,234,237)),("ACT IN LIMITS",(241,224,209))]):
  x=30+j*223
  d.rounded_rectangle((x,2415,x+212,2515),18,fill=bg)
  if j==1:
   txt(d,x+15,2432,"RECOMMEND",20,INK,True)
   txt(d,x+15,2470,"+ REVIEW",22,INK,True)
  else: txt(d,x+18,2446,label,24 if j==2 else 27,INK,True)
 d.rounded_rectangle((29,2572,690,2741),29,fill=(16,58,87))
 txt(d,53,2596,"EXECUTIVE DECISION",27,(235,184,141),True)
 txt(d,53,2650,"Continue  •  restrict",34,(255,255,255),True)
 txt(d,53,2692,"Repair  •  stop — with evidence.",25,(221,240,248))
 gradient(im,(4,34,60),(3,27,48),2780,H)
 portrait(im,84,2842,39)
 d=ImageDraw.Draw(im)
 txt(d,147,2803,"Jair Ribeiro",33,(255,255,255),True)
 txt(d,148,2851,"AI LEADER",22,SKY,True)
 txt(d,312,2860,"Governance  •  Enterprise AI  •  Value",17,(220,236,244))
 im.save(out/"mobile.png",optimize=True)
 return im
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--output",required=True);args=ap.parse_args()
 out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
 im=desktop(out);mobile(out)
 # A4 one-page source-identical layout, with an embedded high-resolution JPEG.
 jpeg=out/"print-master.jpg"; im.save(jpeg,"JPEG",quality=92,subsampling=0,optimize=True)
 c=canvas.Canvas(str(out/"infographic.pdf"),pagesize=A4)
 c.setAuthor("Jair Ribeiro");c.setTitle("Policy Is Not Permission — Executive AI Governance")
 w,h=A4
 scale=min((w-22)/im.width,(h-24)/im.height)
 iw,ih=im.width*scale,im.height*scale
 c.drawImage(ImageReader(str(jpeg)),(w-iw)/2,(h-ih)/2,width=iw,height=ih)
 c.showPage();c.save()
 print("Source-locked desktop, reflowed mobile and one-page A4 written",out)
if __name__=="__main__":main()
