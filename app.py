from pathlib import Path
import base64
import io
import zipfile

ROOT = Path(__file__).resolve().parent
encoded = "".join(p.read_text(encoding="ascii") for p in sorted((ROOT / "payload_parts").glob("part_*.b64")))
with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as bundle:
    source = bundle.read("site.py").decode("utf-8")
    ASSET_BYTES = {Path(name).name: bundle.read(name) for name in bundle.namelist() if name.startswith("assets/")}

# Replace the original Blog page as one complete block. This avoids Markdown
# indentation artefacts and keeps every essay as a distinct, clickable card.
BLOG_BRANCH = r'''elif page == "blog":
    blog_articles = [
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

    article_cards = "".join(
        f"""<a class="essay-card" href="{url}" target="_blank" rel="noopener noreferrer">
          <div class="essay-thumb" style="background:linear-gradient(135deg,{c1} 0%,{c1} 52%,{c2} 150%);">
            <div class="essay-orbit"></div>
            <span class="essay-number">{number}</span>
            <span class="essay-topic">{topic}</span>
          </div>
          <div class="essay-copy">
            <span class="essay-series">Leading in the AI Enterprise</span>
            <h3>{title}</h3>
            <p>{description}</p>
            <span class="essay-read">Read article <b>↗</b></span>
          </div>
        </a>"""
        for number, topic, title, description, url, c1, c2 in blog_articles
    )

    blog_html = """<style>
.blog-hero {background:#0b1220;color:#fffdf9;padding:clamp(92px,10vw,150px) var(--pad) clamp(72px,8vw,116px);}
.blog-hero-inner,.blog-series-inner {max-width:var(--max);margin:0 auto;}
.blog-hero .kicker {color:#e7b780;}
.blog-hero h1 {max-width:980px;margin-bottom:28px;}
.blog-hero .body-lg {max-width:860px;color:#cbd1da;}
.series-story {display:grid;grid-template-columns:minmax(0,1.05fr) minmax(300px,.65fr);gap:clamp(40px,7vw,96px);align-items:start;margin-top:58px;padding-top:48px;border-top:1px solid rgba(255,255,255,.14);}
.series-story-copy p {font-size:17px;line-height:1.75;color:#d7dce4;margin-bottom:18px;}
.series-questions {display:grid;gap:12px;}
.series-question {padding:18px 20px;border:1px solid rgba(255,255,255,.13);background:rgba(255,255,255,.045);font-family:Georgia,serif;font-size:18px;line-height:1.45;color:#fffdf9;}
.series-meta {margin-top:26px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#95a0af;}
.blog-series {background:#f4f0e8;padding:clamp(72px,9vw,126px) var(--pad);}
.series-head {display:flex;justify-content:space-between;gap:28px;align-items:end;margin-bottom:38px;}
.series-head h2 {max-width:760px;margin:0;}
.series-head p {max-width:460px;margin:0;color:#6f746f;font-size:16px;line-height:1.65;}
.essay-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px;}
.essay-card {display:flex;flex-direction:column;min-height:100%;background:#fffdf9;border:1px solid rgba(16,19,26,.11);color:#10131a !important;overflow:hidden;transition:transform .22s ease,box-shadow .22s ease,border-color .22s ease;}
.essay-card:hover {transform:translateY(-5px);box-shadow:0 20px 45px rgba(16,19,26,.10);border-color:rgba(16,19,26,.22);}
.essay-thumb {position:relative;min-height:180px;padding:20px;overflow:hidden;display:flex;align-items:flex-end;justify-content:space-between;color:#fffdf9;}
.essay-thumb:before {content:"";position:absolute;inset:-40% 48% 34% -18%;border:1px solid rgba(255,255,255,.18);border-radius:50%;transform:rotate(22deg);}
.essay-thumb:after {content:"";position:absolute;width:120px;height:120px;right:-30px;top:-26px;border:1px solid rgba(255,255,255,.16);border-radius:50%;}
.essay-orbit {position:absolute;left:50%;top:48%;width:140px;height:1px;background:rgba(255,255,255,.25);transform:translate(-50%,-50%) rotate(-24deg);}
.essay-orbit:after {content:"";position:absolute;right:-3px;top:-3px;width:7px;height:7px;border-radius:50%;background:#fffdf9;}
.essay-number {position:relative;z-index:1;font-size:13px;letter-spacing:.16em;font-weight:800;}
.essay-topic {position:relative;z-index:1;font-size:11px;letter-spacing:.14em;text-transform:uppercase;border:1px solid rgba(255,255,255,.34);border-radius:999px;padding:7px 10px;}
.essay-copy {display:flex;flex-direction:column;flex:1;padding:24px 24px 22px;}
.essay-series {font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:#8a8f8b;font-weight:800;margin-bottom:14px;}
.essay-copy h3 {font-family:Georgia,serif;font-size:27px;line-height:1.08;font-weight:500;letter-spacing:-.02em;margin:0 0 14px;}
.essay-copy p {color:#5f6662;font-size:15px;line-height:1.62;margin:0 0 24px;}
.essay-read {margin-top:auto;font-size:13px;font-weight:800;color:#10131a;display:flex;justify-content:space-between;align-items:center;padding-top:18px;border-top:1px solid rgba(16,19,26,.10);}
.essay-read b {font-size:17px;font-weight:500;transition:transform .2s ease;}
.essay-card:hover .essay-read b {transform:translate(3px,-3px);}
@media (max-width:1000px){.essay-grid{grid-template-columns:repeat(2,minmax(0,1fr));}.series-story{grid-template-columns:1fr;}.series-head{align-items:start;flex-direction:column;}}
@media (max-width:650px){.essay-grid{grid-template-columns:1fr;}.essay-thumb{min-height:155px;}.blog-hero,.blog-series{padding-left:22px;padding-right:22px;}.series-question{font-size:17px;}}
</style>
<main class="page">
  <section class="blog-hero">
    <div class="blog-hero-inner">
      <p class="kicker">Blog & thought leadership</p>
      <h1 class="title">Leading in the AI Enterprise</h1>
      <p class="body-lg">A series about the leadership work behind enterprise AI — the decisions, structures and human choices that determine whether experimentation becomes measurable business value.</p>

      <div class="series-story">
        <div class="series-story-copy">
          <p>Over the last few months, I have noticed something interesting: whether the conversation happens inside companies, industry forums, executive roundtables, or broader European discussions about competitiveness and digital transformation, the same questions keep surfacing.</p>
          <p>The technology is evolving rapidly. The leadership challenges are becoming clearer.</p>
          <p>Over the next weeks, I will share a series of 20 articles that I've been preparing to reflect on and explore what I believe are the most important AI topics senior leaders should be discussing in 2026.</p>
          <p>Not from the perspective of algorithms or tools, but from the perspective of strategy, governance, operating models, data, workforce transformation, and organizational readiness.</p>
          <div class="series-meta">18 published · 20 in the series</div>
        </div>
        <div class="series-questions">
          <div class="series-question">How do we move from AI experimentation to measurable business value?</div>
          <div class="series-question">How do we build trust without slowing innovation?</div>
          <div class="series-question">How do we prepare leaders and employees for a workplace increasingly shaped by AI?</div>
          <div class="series-question">How do we create the data foundations needed to scale responsibly?</div>
        </div>
      </div>
    </div>
  </section>

  <section class="blog-series">
    <div class="blog-series-inner">
      <div class="series-head">
        <div>
          <p class="kicker">The published series</p>
          <h2 class="title">18 essays. One connected leadership agenda.</h2>
        </div>
        <p>Each article stands on its own, but together they trace the path from strategy and value to governance, operating models, workforce, risk and responsible scale.</p>
      </div>
      <div class="essay-grid">__ARTICLE_CARDS__</div>
    </div>
  </section>
</main>"""

    st.markdown(blog_html.replace("__ARTICLE_CARDS__", article_cards), unsafe_allow_html=True)
    footer()
'''

blog_start = source.find('elif page == "blog":')
contact_start = source.find('elif page == "contact":')
if blog_start != -1 and contact_start != -1 and contact_start > blog_start:
    source = source[:blog_start] + BLOG_BRANCH + "\n" + source[contact_start:]

exec(compile(source, "site_app.py", "exec"), globals(), globals())
