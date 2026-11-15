"""Server-readable social metadata for the native Streamlit front door.

Client-side updates to `document.head` are useful for browsers but are too
late for LinkedIn's HTML fetcher. The Streamlit ASGI app serves this small
HTML document only to link-preview bots on public root URLs.
"""
from __future__ import annotations

from html import escape

SITE_IMAGE = "https://jairribeiro-ai.streamlit.app/app/static/jair-ribeiro-social-preview.png"
SITE_URL = "https://jairribeiro.com/"
HOME_TITLE = "Jair Ribeiro | Enterprise AI & Data Leadership"
HOME_DESCRIPTION = (
    "Jair Ribeiro explores how leaders turn enterprise AI and data strategy "
    "into business results. Executive briefings, governance perspectives "
    "and practical insights on AI adoption."
)

# Only pages safe for public sharing. Never expose owner/member routes,
# verification tokens or other sensitive query parameters in share metadata.
PAGE_META = {
    "home": (HOME_TITLE, HOME_DESCRIPTION),
    "thinking": ("Thinking | Jair Ribeiro", "Practical perspectives on enterprise AI leadership, governance, adoption and business value."),
    "briefings": ("Executive AI Briefings | Jair Ribeiro", "Executive briefings on AI investment, governance, organizational readiness and decision-making."),
    "about": ("About Jair Ribeiro | Enterprise AI & Data Leadership", "The professional experience and leadership perspective behind Jair Ribeiro's enterprise AI and data work."),
    "contact": ("Contact Jair Ribeiro | Enterprise AI & Data Leadership", "Discuss enterprise AI, data strategy, governance, adoption and executive leadership."),
    "advisory": ("Executive AI & Data Advisory | Jair Ribeiro", "Independent executive perspectives and practical advisory services on AI investment, adoption, governance and operating models."),
    "ai-data-governance": ("AI & Data Governance | Jair Ribeiro", "Leadership accountability, decision rights and responsible adoption of AI and data across the enterprise."),
    "impact": ("Enterprise AI & Data Experience | Jair Ribeiro", "Enterprise AI and data leadership experience, decisions and operating outcomes."),
    "enterprise": ("Enterprise AI Leadership | Jair Ribeiro", "Strategy, portfolios, operating models and enterprise adoption."),
    "transformation": ("AI Adoption & Organizational Change | Jair Ribeiro", "Organizational readiness, adoption and operating capability for enterprise AI."),
    "governance": ("Responsible AI & Governance | Jair Ribeiro", "Practical enterprise AI governance and accountable decision-making."),
    "consulting": ("Business-Driven AI | Jair Ribeiro", "Enterprise AI leadership bridging business needs, responsible adoption and operating decisions."),
    "privacy": ("Privacy | Jair Ribeiro", "Privacy information for the executive AI and data portfolio."),
}

SOCIAL_BOT_MARKERS = (
    "linkedinbot", "facebookexternalhit", "facebot", "twitterbot",
    "slackbot", "discordbot", "telegrambot", "whatsapp",
    "pinterest", "skypeuripreview", "embedly", "redditbot",
)


def is_social_crawler(user_agent: str) -> bool:
    agent = str(user_agent or "").lower()
    return any(marker in agent for marker in SOCIAL_BOT_MARKERS)


def homepage_social_html(page: str = "home") -> str | None:
    """Produce social tags in the first HTML response, never via JavaScript."""
    entry = PAGE_META.get(page)
    if entry is None:
        return None
    title, description = entry
    title = escape(title, quote=True)
    description = escape(description, quote=True)
    url = SITE_URL if page == "home" else f"{SITE_URL}?page={escape(page, quote=True)}"
    image = escape(SITE_IMAGE, quote=True)
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{url}">
<link rel="image_src" href="{image}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Jair Ribeiro">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image}">
<meta property="og:image:url" content="{image}">
<meta property="og:image:secure_url" content="{image}">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Jair Ribeiro — Enterprise AI &amp; Data Leadership">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{image}">
</head><body>
<main><h1>{title}</h1><p>{description}</p>
<p><a href="{url}">Open Jair Ribeiro's executive AI &amp; data portfolio</a></p></main>
</body></html>"""
