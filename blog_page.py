import html
import streamlit as st

ARTICLES = [
    ("01", "Strategy", "Strategy Alignment", "Why enterprise AI choices need to start with business priorities, portfolio trade-offs and clear ownership.", "https://lnkd.in/eFNiAX8M", "#0b1220", "#c56f3d"),
    ("02", "Value", "ROI", "Moving beyond activity metrics to value realization, evidence and the discipline of proving where AI is paying back.", "https://lnkd.in/ekQqQdgf", "#1b1d22", "#d89a4a"),
    ("03", "Organization", "Operating Model", "How roles, decision rights and team design determine whether successful AI work can become repeatable enterprise capability.", "https://lnkd.in/e7yrc6zh", "#132033", "#6f93b8"),
    ("04", "Governance", "AI Governance", "Governance as a practical system for ownership, evidence and escalation — not a collection of gates that slows useful work.", "https://lnkd.in/eJ8EHKHQ", "#11312f", "#d1a35f"),
    ("05", "Data", "Data Readiness", "Why access, quality, semantics and ownership of data often decide whether AI can scale long before model choice does.", "https://lnkd.in/ezmrefxC", "#162a33", "#5ca5b5"),
    ("06", "Work", "Workforce Redesign", "AI changes tasks before it changes job titles. The leadership work is redesigning how work, decisions and accountability fit together.", "https://lnkd.in/ebYBiuyH", "#302436", "#b77a9f"),
    ("07", "Capability", "Talent & Upskilling", "Building AI capability without replacing expert judgment: literacy, new skills, confidence and learning close to the work itself.", "https://lnkd.in/ez9xAzWb", "#332719", "#d6a95e"),
    ("08", "Adoption", "Change Management", "Training is not adoption. The real measure is whether workflows, decisions and everyday behavior actually change.", "https://lnkd.in/ew5mtJKv", "#1f2d24", "#79a77f"),
    ("09", "Leadership", "Board AI Literacy", "What boards need to understand about AI to ask better questions, govern risk and challenge value without micromanaging technology.", "https://lnkd.in/dSZXXP5i", "#25203c", "#8c7cc4"),
    ("10", "Autonomy", "Agentic AI", "What changes when AI systems can plan, coordinate and act — and why accountability has to evolve with that autonomy.", "https://lnkd.in/dYmKgQCi", "#102a3a", "#6ba9c7"),
    ("11", "Control", "Human Oversight", "Where human review genuinely improves outcomes, where it becomes symbolic, and how to design oversight around real decisions.", "https://lnkd.in/dJUbX98E", "#34231e", "#c98567"),
    ("12", "Regulation", "Regulation & Compliance", "Turning regulatory expectations into controls, ownership and evidence that teams can actually operate with day to day.", "https://lnkd.in/dzk9dQxK", "#27302f", "#8aa59d"),
    ("13", "Security", "Cybersecurity & AI", "AI introduces new attack surfaces across models, data, identities and workflows. Security has to become part of the operating model.", "https://lnkd.in/deKcUfeS", "#171d29", "#7c91b2"),
    ("14", "Risk", "Shadow AI", "Unsanctioned AI use is both a risk signal and a demand signal. Leaders need to understand why employees route around official tools.", "https://lnkd.in/emV6E-Qe", "#302c1b", "#c6a85e"),
    ("15", "Trust", "Responsible AI", "Trust, transparency and responsible practice matter most when they help teams make better decisions and scale AI with confidence.", "https://lnkd.in/e3-Qp9FT", "#213029", "#7ea389"),
    ("16", "Intelligence", "Competitive Intelligence", "AI can accelerate market sensing, but speed is not the same as signal quality. Judgment still determines what deserves attention.", "https://lnkd.in/ePdGggA3", "#222733", "#8898b6"),
    ("17", "Portfolio", "Tool Sprawl", "Without portfolio discipline, AI platforms multiply faster than value — bringing duplicated cost, fragmented data and inconsistent controls.", "https://lnkd.in/e6XN_wsn", "#302728", "#bd8584"),
    ("18", "Sourcing", "AI Procurement", "Buying AI requires more than feature comparison: value, architecture, data rights, security, governance and lock-in all belong in the decision.", "https://lnkd.in/eTZjFnbz", "#1d2c32", "#76a2a7"),
]


def _cards_html():
    cards = []
    for number, topic, title, description, url, c1, c2 in ARTICLES:
        cards.append(f"""
<a class="essay-card" href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">
  <div class="essay-thumb" style="--c1:{c1};--c2:{c2};">
    <span class="essay-number">{number}</span>
    <span class="essay-topic">{html.escape(topic)}</span>
    <div class="essay-mark"><i></i><i></i><i></i></div>
  </div>
  <div class="essay-copy">
    <span class="essay-series">Leading in the AI Enterprise</span>
    <h3>{html.escape(title)}</h3>
    <p>{html.escape(description)}</p>
    <span class="essay-read">Read article <b>↗</b></span>
  </div>
</a>""")
    return "".join(cards)


def render_blog(footer):
    cards = _cards_html()
    document = f"""<style>
:root {{ --paper:#f4f0e8; --ink:#10131a; --navy:#0b1220; --copper:#c56f3d; }}
.blog-shell {{ font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:var(--ink); }}
.blog-shell * {{ box-sizing:border-box; }}
.blog-hero {{ background:var(--navy); color:#fffdf9; padding:100px clamp(22px,5vw,70px) 86px; }}
.blog-inner {{ width:min(1180px,100%); margin:0 auto; }}
.blog-kicker {{ margin:0 0 18px; font-size:12px; line-height:1; letter-spacing:.16em; text-transform:uppercase; font-weight:800; color:#e7b780; }}
.blog-title {{ max-width:900px; margin:0; font-family:Georgia,serif; font-weight:500; font-size:clamp(48px,7vw,92px); line-height:.98; letter-spacing:-.035em; }}
.blog-deck {{ max-width:840px; margin:28px 0 0; color:#cbd1da; font-size:clamp(18px,2vw,23px); line-height:1.55; }}
.story-grid {{ display:grid; grid-template-columns:minmax(0,1.05fr) minmax(320px,.7fr); gap:clamp(42px,7vw,92px); margin-top:64px; padding-top:50px; border-top:1px solid rgba(255,255,255,.14); }}
.story-copy p {{ margin:0 0 18px; color:#d7dce4; font-size:17px; line-height:1.74; }}
.story-meta {{ margin-top:28px; color:#98a3b1; font-size:11px; font-weight:800; letter-spacing:.15em; text-transform:uppercase; }}
.question-stack {{ display:grid; gap:12px; }}
.question {{ padding:18px 20px; border:1px solid rgba(255,255,255,.14); background:rgba(255,255,255,.045); color:#fffdf9; font:500 18px/1.45 Georgia,serif; }}
.blog-series {{ background:var(--paper); padding:90px clamp(22px,5vw,70px) 110px; }}
.series-head {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(280px,420px); gap:40px; align-items:end; margin-bottom:42px; }}
.series-head .eyebrow {{ margin:0 0 12px; color:#8b5d3f; font-size:11px; font-weight:800; letter-spacing:.15em; text-transform:uppercase; }}
.series-head h2 {{ margin:0; max-width:780px; font:500 clamp(36px,5vw,62px)/1.02 Georgia,serif; letter-spacing:-.025em; }}
.series-head p {{ margin:0; color:#626863; font-size:16px; line-height:1.65; }}
.essay-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:22px; }}
.essay-card {{ min-width:0; display:flex; flex-direction:column; background:#fffdf9; border:1px solid rgba(16,19,26,.11); color:var(--ink) !important; text-decoration:none !important; overflow:hidden; transition:transform .22s ease,box-shadow .22s ease,border-color .22s ease; }}
.essay-card:hover {{ transform:translateY(-5px); box-shadow:0 22px 48px rgba(16,19,26,.11); border-color:rgba(16,19,26,.24); }}
.essay-thumb {{ position:relative; min-height:185px; padding:21px; overflow:hidden; display:flex; align-items:flex-end; justify-content:space-between; color:#fffdf9; background:radial-gradient(circle at 78% 24%, color-mix(in srgb,var(--c2) 82%, white 18%) 0 2px, transparent 3px),linear-gradient(135deg,var(--c1) 0%,var(--c1) 46%,var(--c2) 135%); }}
.essay-thumb:before {{ content:""; position:absolute; width:210px; height:210px; left:-82px; top:-112px; border:1px solid rgba(255,255,255,.18); border-radius:50%; }}
.essay-thumb:after {{ content:""; position:absolute; width:130px; height:130px; right:-48px; bottom:-64px; border:1px solid rgba(255,255,255,.17); border-radius:50%; }}
.essay-number,.essay-topic {{ position:relative; z-index:2; }}
.essay-number {{ font-size:13px; font-weight:900; letter-spacing:.16em; }}
.essay-topic {{ font-size:10px; font-weight:800; letter-spacing:.13em; text-transform:uppercase; border:1px solid rgba(255,255,255,.35); border-radius:999px; padding:7px 10px; }}
.essay-mark {{ position:absolute; z-index:1; width:130px; height:74px; left:50%; top:50%; transform:translate(-50%,-50%) rotate(-14deg); }}
.essay-mark i {{ position:absolute; display:block; height:1px; background:rgba(255,255,255,.34); transform-origin:left center; }}
.essay-mark i:nth-child(1) {{ width:126px; left:0; top:17px; transform:rotate(20deg); }}
.essay-mark i:nth-child(2) {{ width:96px; left:18px; top:39px; transform:rotate(-26deg); }}
.essay-mark i:nth-child(3) {{ width:72px; left:48px; top:57px; transform:rotate(11deg); }}
.essay-copy {{ display:flex; flex-direction:column; flex:1; padding:25px 24px 23px; }}
.essay-series {{ margin-bottom:14px; color:#8a8f8b; font-size:10px; font-weight:800; letter-spacing:.14em; text-transform:uppercase; }}
.essay-copy h3 {{ margin:0 0 14px; font:500 27px/1.08 Georgia,serif; letter-spacing:-.02em; }}
.essay-copy p {{ margin:0 0 25px; color:#5f6662; font-size:15px; line-height:1.62; }}
.essay-read {{ display:flex; justify-content:space-between; align-items:center; margin-top:auto; padding-top:18px; border-top:1px solid rgba(16,19,26,.10); color:#10131a; font-size:13px; font-weight:800; }}
.essay-read b {{ font-size:17px; font-weight:500; transition:transform .2s ease; }}
.essay-card:hover .essay-read b {{ transform:translate(3px,-3px); }}
@media (max-width:1000px) {{
  .story-grid,.series-head {{ grid-template-columns:1fr; }}
  .essay-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
}}
@media (max-width:650px) {{
  .blog-hero {{ padding-top:72px; }}
  .essay-grid {{ grid-template-columns:1fr; }}
  .essay-thumb {{ min-height:160px; }}
}}
</style>
<div class="blog-shell">
  <section class="blog-hero">
    <div class="blog-inner">
      <p class="blog-kicker">Blog & thought leadership</p>
      <h1 class="blog-title">Leading in the AI Enterprise</h1>
      <p class="blog-deck">A series about the leadership work behind enterprise AI — the decisions, structures and human choices that determine whether experimentation becomes measurable business value.</p>

      <div class="story-grid">
        <div class="story-copy">
          <p>Over the last few months, I have noticed something interesting: whether the conversation happens inside companies, industry forums, executive roundtables, or broader European discussions about competitiveness and digital transformation, the same questions keep surfacing.</p>
          <p>The technology is evolving rapidly. The leadership challenges are becoming clearer.</p>
          <p>Over the next weeks, I will share a series of 20 articles that I've been preparing to reflect on and explore what I believe are the most important AI topics senior leaders should be discussing in 2026.</p>
          <p>Not from the perspective of algorithms or tools, but from the perspective of strategy, governance, operating models, data, workforce transformation, and organizational readiness.</p>
          <div class="story-meta">18 published · 20 in the series</div>
        </div>
        <div class="question-stack">
          <div class="question">How do we move from AI experimentation to measurable business value?</div>
          <div class="question">How do we build trust without slowing innovation?</div>
          <div class="question">How do we prepare leaders and employees for a workplace increasingly shaped by AI?</div>
          <div class="question">How do we create the data foundations needed to scale responsibly?</div>
        </div>
      </div>
    </div>
  </section>

  <section class="blog-series">
    <div class="blog-inner">
      <div class="series-head">
        <div>
          <p class="eyebrow">The published series</p>
          <h2>18 essays. One connected leadership agenda.</h2>
        </div>
        <p>Each article stands on its own, but together they trace the path from strategy and value to governance, operating models, workforce, risk and responsible scale.</p>
      </div>
      <div class="essay-grid">{cards}</div>
    </div>
  </section>
</div>"""
    st.html(document)
    footer()
