from __future__ import annotations

"""Original, contextual presentation for the seven-question Executive AI Briefing.

The editorial article lives in Content Studio. The design stays in source control
so publishing the CMS entry retains consistent visuals across public readers.
"""
from html import escape
from io import BytesIO

SLUG = "seven-questions-for-better-ai-decisions"

QUESTIONS_STYLES = r'''<style>
.site .article-body .aiq-intro{padding:25px 28px;background:#e8e1d7;border-left:3px solid #bd794c;margin:0 0 26px}
.site .article-body .aiq-intro p{margin:0;color:#18283a;font:400 18px/1.62 Georgia,serif}
.site .article-body .aiq-overline{font:800 10px/1.4 Inter,Arial,sans-serif;letter-spacing:.17em;text-transform:uppercase;color:#a25c39}
.site .article-body .aiq-executive-rule{margin:28px 0 34px;padding:22px 26px;background:#12273b;color:#fff;border-top:2px solid #cf9873}
.site .article-body .aiq-executive-rule span{font:800 10px/1.4 Inter,Arial,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#e0b08c}
.site .article-body .aiq-executive-rule p{font:400 18px/1.5 Georgia,serif;color:#fff;margin:10px 0 0}
.site .article-body .aiq-flow{margin:27px 0 37px;padding:22px 20px 19px;background:#f9f7f2;border:1px solid #d8d9d7}
.site .article-body .aiq-flow-caption{font:800 10px/1.3 Inter,Arial,sans-serif;letter-spacing:.16em;color:#8c5235;text-transform:uppercase;margin:0 0 17px}
.site .article-body .aiq-flow-items{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;position:relative}
.site .article-body .aiq-flow-item{min-width:0;padding:14px 10px 13px;background:#fff;border-top:2px solid #24465c}
.site .article-body .aiq-flow-item span{display:block;font:800 10px/1.3 Inter,Arial,sans-serif;color:#956445;letter-spacing:.1em;margin-bottom:8px}
.site .article-body .aiq-flow-item strong{display:block;font:700 13px/1.35 Inter,Arial,sans-serif;color:#14273a}
.site .article-body .aiq-flow-note{font-size:12px;color:#65707a;margin:15px 0 0;line-height:1.55}
.site .article-body .aiq-section-title{margin:32px 0 9px;font:500 clamp(28px,3vw,38px)/1.17 Georgia,serif;color:#12263a}
.site .article-body .aiq-section-lead{font-size:15px;color:#5c6570;line-height:1.65;margin:0 0 22px}
.site .article-body .aiq-cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px;margin:22px 0 26px}
.site .article-body .aiq-card{background:#fffdf9;border:1px solid #d9dbda;min-width:0;padding:23px 22px 19px;display:flex;flex-direction:column;gap:0;box-shadow:0 6px 22px rgba(18,39,59,.035)}
.site .article-body .aiq-card:last-child{grid-column:span 2;background:#f0e9e0;border-color:#ddcfc2}
.site .article-body .aiq-card-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:15px}
.site .article-body .aiq-card-id{font:800 10px/1.3 Inter,Arial,sans-serif;letter-spacing:.14em;color:#8f6047}
.site .article-body .aiq-icon{display:inline-block;flex:0 0 37px;width:37px;height:37px;border:1px solid #d9bca6;background-color:#142d42;background-position:center;background-repeat:no-repeat;background-size:20px}
.site .article-body .aiq-icon-focus{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23d5a57f%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Ccircle%20cx%3D%2212%22%20cy%3D%2212%22%20r%3D%229%22%2F%3E%3Ccircle%20cx%3D%2212%22%20cy%3D%2212%22%20r%3D%224%22%2F%3E%3Cpath%20d%3D%22M12%202v4%20M12%2018v4%20M2%2012h4%20M18%2012h4%22%2F%3E%3C%2Fsvg%3E")}
.site .article-body .aiq-icon-clarify{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23d5a57f%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M4%207h16%20M4%2012h11%20M4%2017h8%22%2F%3E%3Ccircle%20cx%3D%2218%22%20cy%3D%2217%22%20r%3D%223%22%2F%3E%3C%2Fsvg%3E")}
.site .article-body .aiq-icon-test{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23d5a57f%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22m9%203-5%209%205%209%20M15%203l5%209-5%209%22%2F%3E%3Cpath%20d%3D%22M12%207v7%20M12%2018h.01%22%2F%3E%3C%2Fsvg%3E")}
.site .article-body .aiq-icon-evidence{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23d5a57f%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Crect%20x%3D%224%22%20y%3D%223%22%20width%3D%2216%22%20height%3D%2218%22%20rx%3D%222%22%2F%3E%3Cpath%20d%3D%22M8%208h8%20M8%2012h4%20m-4%204%202%202%205-5%22%2F%3E%3C%2Fsvg%3E")}
.site .article-body .aiq-icon-cause{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23d5a57f%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Ccircle%20cx%3D%226%22%20cy%3D%226%22%20r%3D%222%22%2F%3E%3Ccircle%20cx%3D%2218%22%20cy%3D%228%22%20r%3D%222%22%2F%3E%3Ccircle%20cx%3D%2218%22%20cy%3D%2218%22%20r%3D%222%22%2F%3E%3Cpath%20d%3D%22M6%208v8a2%202%200%200%200%202%202h8%20M8%206h8%22%2F%3E%3C%2Fsvg%3E")}
.site .article-body .aiq-icon-effect{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23d5a57f%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Ccircle%20cx%3D%2212%22%20cy%3D%224%22%20r%3D%222%22%2F%3E%3Ccircle%20cx%3D%225%22%20cy%3D%2218%22%20r%3D%222%22%2F%3E%3Ccircle%20cx%3D%2219%22%20cy%3D%2218%22%20r%3D%222%22%2F%3E%3Cpath%20d%3D%22M11%206%206%2016%20M13%206l5%2010%20M7%2018h10%22%2F%3E%3C%2Fsvg%3E")}
.site .article-body .aiq-icon-act{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23d5a57f%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Crect%20x%3D%223%22%20y%3D%224%22%20width%3D%2218%22%20height%3D%2217%22%20rx%3D%222%22%2F%3E%3Cpath%20d%3D%22M7%202v5%20M17%202v5%20M3%209h18%20m-12%206%202%202%204-4%22%2F%3E%3C%2Fsvg%3E")}
.site .article-body .aiq-card h3{font:500 22px/1.2 Georgia,serif;margin:0 0 13px;color:#11263b}
.site .article-body .aiq-card .aiq-primary{font:700 15px/1.47 Inter,Arial,sans-serif;color:#20384b;margin:0 0 13px}
.site .article-body .aiq-card .aiq-probe{font-size:13px;line-height:1.55;color:#5c646d;margin:0 0 17px}
.site .article-body .aiq-card .aiq-output{border-top:1px solid #e0dfda;padding-top:12px;margin-top:auto;font-size:12px;line-height:1.55;color:#374857}
.site .article-body .aiq-card .aiq-output strong{font:800 10px/1.5 Inter,Arial,sans-serif;color:#97593c;letter-spacing:.09em;text-transform:uppercase;margin-right:6px}
.site .article-body .aiq-example{margin:23px 0;padding:23px 25px;background:#f4f0ea;border-left:3px solid #31546b}
.site .article-body .aiq-example p{font-size:15px;line-height:1.65;color:#304357;margin:10px 0 0}
.site .article-body .aiq-example strong{color:#142c40}
.site .article-body .aiq-meeting{margin:29px 0 0;padding:26px;background:#12273b;color:#fff}
.site .article-body .aiq-meeting h3{color:#fff;font:500 27px/1.18 Georgia,serif;margin:12px 0}
.site .article-body .aiq-meeting p{color:#d7e0e6;font-size:15px;line-height:1.65;margin:0}
.site .article-body .aiq-meeting .aiq-checkpoints{display:flex;flex-wrap:wrap;gap:9px;margin:18px 0}
.site .article-body .aiq-meeting .aiq-checkpoints span{font:750 11px/1.3 Inter,Arial,sans-serif;color:#e8d5c4;border:1px solid #687b87;padding:9px 10px}
.site .article-body .aiq-meeting a{display:inline-block;margin-top:8px;padding:12px 17px;color:#13273a!important;background:#f0bb91;font:800 12px/1.35 Inter,Arial,sans-serif;text-decoration:none!important}
.site .article-body .aiq-meeting a:hover,.site .article-body .aiq-meeting a:focus-visible{background:#fff}
.site .article-body .aiq-credit{border-top:1px solid #c9c9c5;font-size:12px;line-height:1.65;color:#5d6469;padding-top:19px;margin-top:30px}
.site .article-body .aiq-credit a{color:#29546e}
.site .aiq-cover{position:relative;margin-top:26px;min-height:410px;overflow:hidden;background:radial-gradient(circle at 83% 42%,#28465b 0,#132c40 40%,#0c1e30 78%);border:1px solid #456172;color:#fff;box-shadow:0 20px 48px rgba(0,0,0,.20);display:flex;align-items:stretch}
.site .aiq-cover:before{content:"";position:absolute;inset:0;background-image:linear-gradient(90deg,rgba(235,242,241,.07) 1px,transparent 1px),linear-gradient(rgba(235,242,241,.07) 1px,transparent 1px);background-size:56px 56px;opacity:.6}
.site .aiq-cover-copy{position:relative;z-index:2;flex:1;display:flex;flex-direction:column;justify-content:space-between;padding:42px 0 38px 46px;max-width:55%}
.site .aiq-cover-copy span{font:800 11px/1.4 Inter,Arial,sans-serif;color:#f0ba94;letter-spacing:.18em;text-transform:uppercase}
.site .aiq-cover-copy strong{font:500 clamp(31px,4vw,57px)/1.07 Georgia,serif;letter-spacing:-.035em;margin:22px 0 18px}
.site .aiq-cover-copy small{font:500 13px/1.5 Inter,Arial,sans-serif;color:#b8cbd8}
.site .aiq-cover-graphic{position:relative;z-index:1;flex:1;min-width:0;display:flex;align-items:center;justify-content:center;padding:22px}
.site .aiq-cover-orbit{width:min(100%,330px);aspect-ratio:1;border:1px solid rgba(229,185,149,.45);border-radius:50%;position:relative;display:grid;place-items:center;box-shadow:0 0 0 32px rgba(229,185,149,.035),0 0 0 65px rgba(229,185,149,.025)}
.site .aiq-cover-orbit:after{content:"";position:absolute;inset:21%;border:1px dashed rgba(238,209,180,.35);border-radius:50%}
.site .aiq-cover-core{display:grid;place-items:center;z-index:1;width:110px;height:110px;border-radius:50%;border:1px solid #c99472;background:#10283b;color:#edc09e;font:500 72px/1 Georgia,serif}
.site .aiq-cover-node{position:absolute;z-index:2;display:grid;place-items:center;width:44px;height:44px;background:#173850;border:1px solid #b78966;color:#f6e3d3;font:800 13px/1 Inter,Arial,sans-serif}
.site .aiq-cover-node:nth-of-type(2){top:-17px;left:calc(50% - 22px)}
.site .aiq-cover-node:nth-of-type(3){top:13%;right:0}
.site .aiq-cover-node:nth-of-type(4){right:-15px;bottom:25%}
.site .aiq-cover-node:nth-of-type(5){bottom:-17px;right:25%}
.site .aiq-cover-node:nth-of-type(6){bottom:2%;left:5%}
.site .aiq-cover-node:nth-of-type(7){top:35%;left:-19px}
.site .aiq-cover-node:nth-of-type(8){top:4%;left:11%}
@media(max-width:760px){.site .article-body .aiq-cards{grid-template-columns:1fr}.site .article-body .aiq-card:last-child{grid-column:auto}.site .article-body .aiq-flow-items{grid-template-columns:repeat(2,minmax(0,1fr))}.site .aiq-cover{min-height:470px;display:block}.site .aiq-cover-copy{max-width:none;min-height:205px;padding:28px 28px 0}.site .aiq-cover-copy strong{max-width:540px;font-size:clamp(30px,6vw,44px);margin:10px 0}.site .aiq-cover-graphic{height:230px;max-width:280px;margin:0 auto;padding:12px}.site .aiq-cover-orbit{width:185px}.site .aiq-cover-core{width:73px;height:73px;font-size:48px}.site .aiq-cover-node{width:28px;height:28px;font-size:10px}.site .aiq-cover-node:nth-of-type(2){top:-12px;left:calc(50% - 14px)}}
@media(max-width:480px){.site .article-body .aiq-intro,.site .article-body .aiq-meeting,.site .article-body .aiq-executive-rule{padding:19px}.site .article-body .aiq-card{padding:19px}.site .article-body .aiq-flow{padding:16px}.site .article-body .aiq-flow-item{padding:12px 9px}}
</style>'''


def cover(article, css_class: str) -> str:
    nodes = ''.join(f'<span class="aiq-cover-node">{n:02d}</span>' for n in range(1, 8))
    return (
        f'<div class="{escape(css_class, quote=True)} aiq-cover" role="img" '
        f'aria-label="{escape(article.header_image_alt or "Seven connected executive questions around one AI decision", quote=True)}">'
        '<div class="aiq-cover-copy"><span>Executive field guide · 07 questions</span>'
        '<strong>Better questions.<br>Better AI decisions.</strong>'
        '<small>Business relevance · Evidence · Ownership · Value</small></div>'
        '<div class="aiq-cover-graphic" aria-hidden="true">'
        f'<div class="aiq-cover-orbit"><span class="aiq-cover-core">?</span>{nodes}</div>'
        '</div></div>'
    )


def social_image(article, social_font, wrap_social_text) -> bytes:
    """Contextual first-party social preview for the questions briefing."""
    from PIL import Image, ImageDraw
    width, height = 1200, 630
    im = Image.new("RGB", (width, height), "#0c1e30")
    draw = ImageDraw.Draw(im)
    for y in range(height):
        ratio = y / height
        draw.line((0, y, width, y), fill=(int(12 + 13 * ratio), int(30 + 25 * ratio), int(48 + 25 * ratio)))
    draw.line((64, 90, 1130, 90), fill="#8c9ba5", width=1)
    draw.text((66, 48), "EXECUTIVE AI BRIEFINGS   /   FIELD GUIDE", font=social_font(18, bold=True), fill="#dcb08c")
    title = "Seven questions for better AI decisions"
    y = 135
    for line in wrap_social_text(draw, title, social_font(58, serif=True), 640, 4):
        draw.text((66, y), line, font=social_font(58, serif=True), fill="#f9f7f2")
        y += 73
    draw.text((68, 494), "Ask for proof. Name the owner. Define the decision.", font=social_font(21), fill="#cbd7df")
    draw.text((68, 564), "Jair Ribeiro  ·  Enterprise AI & Data Leadership", font=social_font(20, serif=True), fill="#f9f7f2")
    cx, cy = 959, 318
    for radius in (175, 125):
        draw.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),outline="#526d80",width=2)
    for i in range(7):
        import math
        angle = -math.pi/2 + i*2*math.pi/7
        x = int(cx + 175*math.cos(angle)); yy = int(cy + 175*math.sin(angle))
        draw.ellipse((x-22,yy-22,x+22,yy+22),fill="#27485e",outline="#ddad86",width=2)
        n = f"{i+1:02d}"; bbox=draw.textbbox((0,0),n,font=social_font(14,bold=True))
        draw.text((x-(bbox[2]-bbox[0])/2,yy-(bbox[3]-bbox[1])/2-2),n,font=social_font(14,bold=True),fill="#fdf4eb")
    draw.ellipse((cx-55,cy-55,cx+55,cy+55),fill="#142f44",outline="#dfb28c",width=3)
    draw.text((cx-20,cy-42),"?",font=social_font(80,serif=True),fill="#f3c59b")
    data=BytesIO();im.save(data,format="PNG",optimize=True);return data.getvalue()
