"""Lightweight Home-only Executive Briefings discovery strip.

Avoid importing the full 80 KB briefing reader and CMS orchestration just to
display one static homepage CTA. Preserve the original design and event name.
"""

HOME_BRIEFINGS_CSS = """<style>
.site .briefings-index{font:800 10px/1.45 Arial,sans-serif;letter-spacing:.15em;text-transform:uppercase;color:#ac663e}
.site .briefings-home-strip{background:#ede3d5;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:30px 0}
.site .briefings-home-inner{display:flex;justify-content:space-between;align-items:center;gap:28px}
.site .briefings-home-inner h2{font:500 25px/1.18 Georgia,serif;margin:6px 0 7px}
.site .briefings-home-inner p{font-size:13px;line-height:1.65;color:#535b64;margin:0}
.site .briefings-home-inner>a{flex:0 0 auto;font-size:12px;font-weight:750;text-decoration:none;border-bottom:1px solid var(--copper);padding:10px 0}
@media(max-width:650px){.site .briefings-home-inner{display:block}.site .briefings-home-inner>a{display:inline-block;margin-top:10px}}
</style>"""

def home_briefings_strip() -> str:
    return HOME_BRIEFINGS_CSS + """<section class="briefings-home-strip" data-analytics-section="home-executive-briefings">
    <div class="container briefings-home-inner"><div><span class="briefings-index">Executive AI Briefings</span>
    <h2>AI explained through the decisions leaders face.</h2>
    <p>Short operating perspectives on capability, ownership, risk and business value.</p></div>
    <a href="?page=briefings" target="_self" data-hq-event="briefings_home_open">Explore the briefings →</a>
    </div></section>"""
