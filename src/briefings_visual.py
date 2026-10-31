from __future__ import annotations

"""First-party, responsive vector artwork for the executive briefing experience."""

ICON_PATHS = {
    "target": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><path d="M12 10v4m-2-2h4"/>',
    "shield": '<path d="m12 2 8 4v6c0 5-3.4 8.3-8 10-4.6-1.7-8-5-8-10V6z"/><path d="m9 12 2 2 4-4"/>',
    "users": '<circle cx="9" cy="8" r="3"/><path d="M3 20v-2a6 6 0 0 1 12 0v2"/><path d="M17 5a3 3 0 0 1 0 6m2 9v-2a5 5 0 0 0-3-4.6"/>',
    "chart": '<path d="M4 20V5m0 15h17"/><path d="m7 16 5-5 3 2 5-7"/>',
    "layers": '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 12 9 5 9-5m-18 5 9 5 9-5"/>',
    "spark": '<path d="m12 2 2.5 7.5L22 12l-7.5 2.5L12 22l-2.5-7.5L2 12l7.5-2.5z"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
    "workflow": '<rect x="2" y="3" width="7" height="6" rx="1"/><rect x="15" y="15" width="7" height="6" rx="1"/><path d="M9 6h5a4 4 0 0 1 4 4v5M2 18h13"/>',
    "check": '<path d="m4 12 5 5L20 6"/>',
    "compass": '<circle cx="12" cy="12" r="9"/><path d="m15 9-2 5-4 1 2-5z"/>',
}

# Text-first icons survive Streamlit's HTML sanitizer. Inline SVGs did not:
# removing an SVG node collapsed adjacent CSS grid text into a 31px column.
ICON_GLYPHS = {
    "target": "◎", "shield": "◇", "users": "◉", "chart": "↗",
    "layers": "▤", "spark": "✦", "search": "⌕", "workflow": "⇢",
    "check": "✓", "compass": "◈",
}


def briefing_icon(name: str) -> str:
    """A stable decorative HTML element (not an SVG or remote icon)."""
    from html import escape
    safe_name = name if name in ICON_GLYPHS else "compass"
    return (
        f'<span class="briefing-icon briefing-icon-{safe_name}" aria-hidden="true">'
        f'{escape(ICON_GLYPHS[safe_name])}</span>'
    )


def briefing_visual() -> str:
    """Self-contained visual: no SVG sanitization, image fetch, or CDN dependency.

    The executive decision artwork is native HTML/CSS because Streamlit's
    st.html renderer may sanitize inline SVG and image routes may be intercepted.
    """
    return '''<div class="briefing-visual" role="img"
       aria-label="An executive AI decision at the center of four tests: business value, exposure and risk, accountability, and adoption.">
      <div class="bv-kicker"><span>THE EXECUTIVE LENS</span><span>BUSINESS · AI · OUTCOME</span></div>
      <div class="bv-board" aria-hidden="true">
        <div class="bv-cross bv-cross-h"></div><div class="bv-cross bv-cross-v"></div>
        <div class="bv-node bv-value"><span>01 / OUTCOME</span><strong>Business value</strong><small>What must improve?</small></div>
        <div class="bv-node bv-risk"><span>02 / JUDGMENT</span><strong>Exposure &amp; risk</strong><small>What is acceptable?</small></div>
        <div class="bv-node bv-owner"><span>03 / OWNERSHIP</span><strong>Accountability</strong><small>Who owns the result?</small></div>
        <div class="bv-node bv-adoption"><span>04 / EXECUTION</span><strong>Adoption</strong><small>What changes in work?</small></div>
        <div class="bv-hub"><div class="bv-hub-core"><span class="bv-check"></span><strong>DECISION</strong></div></div>
      </div>
      <div class="bv-foot"><span>BUSINESS FIRST</span><span>INVEST WITH EVIDENCE</span></div>
    </div>'''


PROMO_CSS = r'''<style>
/* Pure HTML/CSS artwork: independent of blocked SVG or external image requests. */
.site .briefing-visual{position:relative;isolation:isolate;display:flex;flex-direction:column;justify-content:space-between;box-sizing:border-box;width:100%;aspect-ratio:16/9;min-width:0;min-height:0;overflow:hidden;padding:clamp(12px,2.5vw,21px) clamp(14px,2.5vw,24px);background:radial-gradient(ellipse at 51% 51%,#264e61 0%,#18374d 44%,#0c2034 90%);color:#f3f5f5;font-family:Arial,sans-serif}
.site .briefing-visual:before{content:"";position:absolute;inset:0;z-index:-1;background-image:linear-gradient(rgba(158,188,203,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(158,188,203,.07) 1px,transparent 1px);background-size:29px 29px}
.site .briefing-visual:after{content:"";position:absolute;inset:6%;z-index:-1;border:1px solid rgba(226,179,142,.14);pointer-events:none}
.site .bv-kicker,.site .bv-foot{position:relative;z-index:2;display:flex;align-items:center;justify-content:space-between;gap:12px;font-size:clamp(6px,.87vw,9px);font-weight:800;letter-spacing:.13em;line-height:1.35;color:#e4b790}
.site .bv-kicker span:last-child,.site .bv-foot span:last-child{color:#aebfc8;font-weight:650}
.site .bv-board{position:relative;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));grid-template-rows:repeat(2,minmax(0,1fr));gap:clamp(30px,5vw,57px) clamp(72px,13vw,124px);width:88%;height:69%;margin:auto}
.site .bv-cross{position:absolute;z-index:0;background:rgba(223,175,136,.55)}
.site .bv-cross-h{left:13%;right:13%;top:50%;height:1px}
.site .bv-cross-v{top:8%;bottom:8%;left:50%;width:1px}
.site .bv-node{position:relative;z-index:1;display:flex;flex-direction:column;justify-content:center;min-width:0;min-height:0;padding:clamp(7px,1.3vw,12px) clamp(8px,1.5vw,15px);background:linear-gradient(125deg,rgba(26,58,76,.98),rgba(20,41,59,.98));border:1px solid rgba(159,184,196,.58);box-shadow:0 5px 20px rgba(3,11,20,.16)}
.site .bv-node:before{content:"";position:absolute;left:0;top:0;bottom:0;width:2px;background:#c89671}
.site .bv-node span{display:block;color:#e2b18e;font-size:clamp(6px,.8vw,9px);font-weight:850;letter-spacing:.10em}
.site .bv-node strong{display:block;color:#f9f6f2;font-size:clamp(10px,1.45vw,16px);font-weight:750;line-height:1.15;margin:clamp(3px,.55vw,6px) 0 0}
.site .bv-node small{display:block;color:#b8c9d2;font-size:clamp(7px,.94vw,10px);line-height:1.3;margin-top:clamp(3px,.55vw,6px)}
.site .bv-hub{position:absolute;z-index:3;top:50%;left:50%;width:clamp(74px,20%,112px);aspect-ratio:1;transform:translate(-50%,-50%);border:1px solid #c99772;border-radius:50%;padding:7px;background:rgba(13,32,48,.97);box-shadow:0 0 0 12px rgba(222,182,145,.08),0 0 0 24px rgba(199,157,120,.06)}
.site .bv-hub-core{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:9px;width:100%;height:100%;border:1px solid rgba(225,188,156,.28);border-radius:50%;background:#102638}
.site .bv-check{display:block;width:18px;height:11px;border-left:3px solid #eec6a5;border-bottom:3px solid #eec6a5;transform:translateY(-3px) rotate(-45deg)}
.site .bv-hub strong{color:#fff7ef;font-size:clamp(8px,1vw,11px);font-weight:850;letter-spacing:.1em}
.site .thinking-briefing-card{display:grid;grid-template-columns:minmax(0,1.06fr) minmax(325px,.94fr);background:#0e1d2d;color:#f8f6f2;border:1px solid #324355;overflow:hidden;box-shadow:0 24px 60px rgba(11,18,32,.13)}
.site .thinking-briefing-copy{padding:clamp(30px,4.3vw,58px);display:flex;flex-direction:column;align-items:flex-start;justify-content:center;min-width:0}
.site .thinking-briefing-copy .eyebrow{color:#ecb990}
.site .thinking-briefing-copy h2{font:500 clamp(34px,4vw,54px)/1.07 Georgia,serif;letter-spacing:-.026em;margin:9px 0 19px}
.site .thinking-briefing-copy p{margin:0;color:#cdd6df;font-size:16px;line-height:1.67;max-width:640px}
.site .thinking-briefing-points{list-style:none;padding:0;margin:24px 0 0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;width:100%}
.site .thinking-briefing-points li{padding-top:12px;border-top:1px solid rgba(225,186,152,.43);font:750 12px/1.4 Arial,sans-serif;color:#f4e4d5}
.site .thinking-briefing-ctas{display:flex;flex-wrap:wrap;gap:12px;margin-top:31px}
.site .thinking-briefing-ctas a{display:inline-flex;align-items:center;min-height:46px;text-decoration:none!important;font:750 12px/1.3 Arial,sans-serif;padding:12px 17px;border:1px solid #d6a47e}
.site .thinking-briefing-ctas a:first-child{background:#e4b48e;color:#101f30!important}
.site .thinking-briefing-ctas a:last-child{color:#f9f1ea!important}
.site .thinking-briefing-art{margin:0;position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;min-width:0;min-height:0;padding:22px 17px;background:radial-gradient(ellipse at center,#24445b 0%,#132c40 72%);overflow:hidden}
.site .thinking-briefing-art .briefing-visual{display:flex;flex:0 0 auto;width:min(100%,560px);max-width:100%;height:auto;aspect-ratio:16/9;box-shadow:0 12px 38px rgba(0,0,0,.24);border:1px solid rgba(238,191,151,.24)}
.site .briefings-feature-art .briefing-visual{display:flex;width:100%;height:100%;aspect-ratio:auto;box-shadow:none;border:0}
.site .thinking-briefing-art figcaption{position:static;box-sizing:border-box;display:block;width:min(100%,560px);padding:0;background:transparent;color:#e3c0a6;font:750 10px/1.5 Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase}
@media(max-width:980px){.site .thinking-briefing-card{grid-template-columns:minmax(0,1.08fr) minmax(0,.92fr)}.site .thinking-briefing-art{padding:16px;min-height:0}.site .thinking-briefing-copy{padding:clamp(22px,3vw,32px)}.site .thinking-briefing-copy p{font-size:14px}.site .thinking-briefing-points{gap:7px}}
@media(max-width:700px){.site .thinking-briefing-card{grid-template-columns:minmax(0,1fr)}.site .thinking-briefing-art{order:-1;padding:14px 14px 16px}}
@media(max-width:650px){.site .thinking-briefing-copy{padding:27px 24px}.site .thinking-briefing-copy p{font-size:14px}.site .thinking-briefing-points{gap:10px}.site .thinking-briefing-points li{font-size:10px}.site .thinking-briefing-art{padding:11px 11px 15px}.site .thinking-briefing-art figcaption{font-size:8px}.site .thinking-briefing-ctas{display:grid;width:100%}.site .thinking-briefing-ctas a{justify-content:center}.site .bv-board{width:92%;height:72%;gap:25px 62px}.site .bv-node small{display:none}.site .bv-node strong{font-size:10px}.site .bv-hub{width:72px}.site .bv-hub strong{font-size:8px}.site .bv-kicker,.site .bv-foot{font-size:6px}}
@media(prefers-reduced-motion:reduce){.site .thinking-briefing-ctas a{transition:none}}
</style>'''