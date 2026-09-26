from __future__ import annotations

import json
import streamlit.components.v1 as components

from site_assets import LINKEDIN, MEDIUM, EMAIL
from site_social_preview import PUBLIC_URL as SOCIAL_IMAGE, ensure_social_preview
from thinking_articles import ArticleMeta, article_social_image_url, article_url
from thinking_social import ensure_article_social_assets

try:
    ensure_social_preview()
except OSError:
    pass

DESCRIPTIONS = {
    "home": "Jair Ribeiro is an Enterprise AI & Data Leader. A curated portfolio of leadership cases, operating judgment, practical frameworks and selected writing across AI, Data and Analytics.",
    "impact": "Leadership cases from Jair Ribeiro showing situations, trade-offs, cross-functional leadership and decisions behind enterprise AI and Data work.",
    "thinking": "Selected writing by Jair Ribeiro on enterprise AI strategy, value, operating models, governance, data readiness, adoption and leadership judgment.",
    "about": "The professional story of Jair Ribeiro: from enterprise technology foundations into business-facing AI, Data and Analytics leadership across international organizations.",
    "certifications": "Selected credentials supporting Jair Ribeiro\'s enterprise AI and Data leadership across agentic AI, Responsible AI, GenAI strategy, data platforms, product and technical foundations.",
    "presence": "Selected speaking, publications and externally documented contributions by Jair Ribeiro across enterprise AI, Data, responsible adoption and leadership.",
    "contact": "Contact Jair Ribeiro about senior AI, Data and Analytics leadership where strategy, portfolio, governance, adoption and operating capability need to work together.",
    "enterprise": "Contextual view of Jair Ribeiro's Enterprise AI & Data leadership experience across strategy, portfolio, operating models, governance, adoption and technical judgment.",
    "transformation": "Contextual view of Jair Ribeiro's AI transformation and adoption experience, connecting experimentation with capability building, workflow change, governance and scale-readiness.",
    "governance": "Contextual view of Jair Ribeiro's AI governance and operating-model experience across decision rights, lifecycle ownership, Responsible AI, data trust and scale-readiness.",
    "ai-data-governance": "Jair Ribeiro's executive perspective on AI and Data Governance: accountability, decision rights, trusted data, evidence, traceability, monitoring and responsible scale.",
    "consulting": "Contextual view of Jair Ribeiro's business-driven AI and consulting experience, connecting problem framing and executive dialogue with enterprise operating reality.",
}


def _person_schema() -> dict[str, object]:
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": "Jair Ribeiro",
        "jobTitle": "Enterprise AI & Data Leader",
        "description": DESCRIPTIONS["home"],
        "email": f"mailto:{EMAIL}",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Gothenburg",
            "addressCountry": "SE",
        },
        "sameAs": [LINKEDIN, MEDIUM],
        "image": SOCIAL_IMAGE,
        "knowsAbout": [
            "Enterprise AI",
            "Data and Analytics",
            "AI Strategy",
            "AI Governance",
            "Responsible AI",
            "AI Adoption",
            "AI Operating Models",
            "Data Governance",
        ],
    }


def _article_schema(article: ArticleMeta) -> dict[str, object]:
    canonical = article_url(article)
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article.title,
        "description": article.seo_description,
        "datePublished": article.published_iso,
        "dateModified": article.published_iso,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "image": [article_social_image_url(article)],
        "author": {
            "@type": "Person",
            "name": "Jair Ribeiro",
            "url": "https://jairribeiro-ai.streamlit.app/",
            "sameAs": [LINKEDIN, MEDIUM],
        },
        "publisher": {
            "@type": "Person",
            "name": "Jair Ribeiro",
            "url": "https://jairribeiro-ai.streamlit.app/",
        },
        "articleSection": article.topic,
        "keywords": list(article.tags),
    }


def inject_metadata(page: str, title: str) -> None:
    """Add page metadata without third-party tracking."""
    description = DESCRIPTIONS.get(page, DESCRIPTIONS["home"])
    person = _person_schema()
    script = f"""
<script>
(() => {{
  const doc = window.parent.document;
  const page = {json.dumps(page)};
  const title = {json.dumps(title)};
  const description = {json.dumps(description)};
  const socialImage = {json.dumps(SOCIAL_IMAGE)};
  const socialAlt = "Jair Ribeiro — Enterprise AI & Data Leader";
  const base = window.parent.location.origin + window.parent.location.pathname;
  const canonical = page === 'home' ? base : base + '?page=' + encodeURIComponent(page);
  doc.title = title;

  const meta = (selector, attr, key, value) => {{
    let el = doc.head.querySelector(selector);
    if (!el) {{
      el = doc.createElement('meta');
      el.setAttribute(attr, key);
      doc.head.appendChild(el);
    }}
    el.setAttribute('content', value);
  }};

  meta('meta[name="description"]', 'name', 'description', description);
  meta('meta[name="robots"]', 'name', 'robots', 'index,follow,max-image-preview:large');
  meta('meta[property="og:title"]', 'property', 'og:title', title);
  meta('meta[property="og:description"]', 'property', 'og:description', description);
  meta('meta[property="og:type"]', 'property', 'og:type', 'profile');
  meta('meta[property="og:site_name"]', 'property', 'og:site_name', 'Jair Ribeiro');
  meta('meta[property="og:url"]', 'property', 'og:url', canonical);
  meta('meta[property="og:image"]', 'property', 'og:image', socialImage);
  meta('meta[property="og:image:secure_url"]', 'property', 'og:image:secure_url', socialImage);
  meta('meta[property="og:image:type"]', 'property', 'og:image:type', 'image/png');
  meta('meta[property="og:image:width"]', 'property', 'og:image:width', '1200');
  meta('meta[property="og:image:height"]', 'property', 'og:image:height', '630');
  meta('meta[property="og:image:alt"]', 'property', 'og:image:alt', socialAlt);
  meta('meta[name="twitter:card"]', 'name', 'twitter:card', 'summary_large_image');
  meta('meta[name="twitter:title"]', 'name', 'twitter:title', title);
  meta('meta[name="twitter:description"]', 'name', 'twitter:description', description);
  meta('meta[name="twitter:image"]', 'name', 'twitter:image', socialImage);
  meta('meta[name="twitter:image:alt"]', 'name', 'twitter:image:alt', socialAlt);

  doc.head.querySelectorAll('meta[property^="article:"]').forEach(el => el.remove());
  const oldArticleSchema = doc.head.querySelector('script[data-jair-article]');
  if (oldArticleSchema) oldArticleSchema.remove();

  let canonicalLink = doc.head.querySelector('link[rel="canonical"]');
  if (!canonicalLink) {{
    canonicalLink = doc.createElement('link');
    canonicalLink.setAttribute('rel', 'canonical');
    doc.head.appendChild(canonicalLink);
  }}
  canonicalLink.setAttribute('href', canonical);

  let schema = doc.head.querySelector('script[data-jair-person]');
  if (!schema) {{
    schema = doc.createElement('script');
    schema.setAttribute('type', 'application/ld+json');
    schema.setAttribute('data-jair-person', 'true');
    doc.head.appendChild(schema);
  }}
  const person = {json.dumps(person)};
  person.url = base;
  schema.textContent = JSON.stringify(person);
}})();
</script>
"""
    components.html(script, height=0, width=0)


def inject_article_metadata(article: ArticleMeta) -> None:
    """Inject article SEO metadata and bind footer sharing behavior."""
    try:
        ensure_article_social_assets(article)
    except OSError:
        pass

    canonical = article_url(article)
    social_image = article_social_image_url(article)
    person = _person_schema()
    article_schema = _article_schema(article)
    tags = ", ".join(article.tags)

    script = f"""
<script>
(() => {{
  const win = window.parent;
  const doc = win.document;
  const title = {json.dumps(article.seo_title)};
  const description = {json.dumps(article.seo_description)};
  const socialTitle = {json.dumps(article.social_title)};
  const socialDescription = {json.dumps(article.social_description)};
  const canonical = {json.dumps(canonical)};
  const socialImage = {json.dumps(social_image)};
  const socialAlt = {json.dumps(article.title + ' — Jair Ribeiro')};
  const tags = {json.dumps(tags)};
  doc.title = title;

  const meta = (selector, attr, key, value) => {{
    let el = doc.head.querySelector(selector);
    if (!el) {{
      el = doc.createElement('meta');
      el.setAttribute(attr, key);
      doc.head.appendChild(el);
    }}
    el.setAttribute('content', value);
  }};

  meta('meta[name="description"]', 'name', 'description', description);
  meta('meta[name="author"]', 'name', 'author', 'Jair Ribeiro');
  meta('meta[name="keywords"]', 'name', 'keywords', tags);
  meta('meta[name="robots"]', 'name', 'robots', 'index,follow,max-image-preview:large');
  meta('meta[property="og:title"]', 'property', 'og:title', socialTitle);
  meta('meta[property="og:description"]', 'property', 'og:description', socialDescription);
  meta('meta[property="og:type"]', 'property', 'og:type', 'article');
  meta('meta[property="og:site_name"]', 'property', 'og:site_name', 'Jair Ribeiro');
  meta('meta[property="og:url"]', 'property', 'og:url', canonical);
  meta('meta[property="og:image"]', 'property', 'og:image', socialImage);
  meta('meta[property="og:image:secure_url"]', 'property', 'og:image:secure_url', socialImage);
  meta('meta[property="og:image:type"]', 'property', 'og:image:type', 'image/png');
  meta('meta[property="og:image:width"]', 'property', 'og:image:width', '1200');
  meta('meta[property="og:image:height"]', 'property', 'og:image:height', '630');
  meta('meta[property="og:image:alt"]', 'property', 'og:image:alt', socialAlt);
  meta('meta[name="twitter:card"]', 'name', 'twitter:card', 'summary_large_image');
  meta('meta[name="twitter:title"]', 'name', 'twitter:title', socialTitle);
  meta('meta[name="twitter:description"]', 'name', 'twitter:description', socialDescription);
  meta('meta[name="twitter:image"]', 'name', 'twitter:image', socialImage);
  meta('meta[name="twitter:image:alt"]', 'name', 'twitter:image:alt', socialAlt);
  meta('meta[property="article:published_time"]', 'property', 'article:published_time', {json.dumps(article.published_iso)});
  meta('meta[property="article:modified_time"]', 'property', 'article:modified_time', {json.dumps(article.published_iso)});
  meta('meta[property="article:author"]', 'property', 'article:author', 'Jair Ribeiro');
  meta('meta[property="article:section"]', 'property', 'article:section', {json.dumps(article.topic)});

  let canonicalLink = doc.head.querySelector('link[rel="canonical"]');
  if (!canonicalLink) {{
    canonicalLink = doc.createElement('link');
    canonicalLink.setAttribute('rel', 'canonical');
    doc.head.appendChild(canonicalLink);
  }}
  canonicalLink.setAttribute('href', canonical);

  let personSchema = doc.head.querySelector('script[data-jair-person]');
  if (!personSchema) {{
    personSchema = doc.createElement('script');
    personSchema.setAttribute('type', 'application/ld+json');
    personSchema.setAttribute('data-jair-person', 'true');
    doc.head.appendChild(personSchema);
  }}
  const person = {json.dumps(person)};
  person.url = win.location.origin + win.location.pathname;
  personSchema.textContent = JSON.stringify(person);

  let articleSchema = doc.head.querySelector('script[data-jair-article]');
  if (!articleSchema) {{
    articleSchema = doc.createElement('script');
    articleSchema.setAttribute('type', 'application/ld+json');
    articleSchema.setAttribute('data-jair-article', 'true');
    doc.head.appendChild(articleSchema);
  }}
  articleSchema.textContent = JSON.stringify({json.dumps(article_schema)});

  if (!win.__jairCopyLinkBound) {{
    win.__jairCopyLinkBound = true;
    doc.addEventListener('click', async (event) => {{
      const button = event.target && event.target.closest
        ? event.target.closest('[data-copy-url]')
        : null;
      if (!button) return;
      event.preventDefault();
      const url = String(button.dataset.copyUrl || '');
      if (!url) return;
      let copied = false;
      try {{
        if (win.navigator && win.navigator.clipboard && win.navigator.clipboard.writeText) {{
          await win.navigator.clipboard.writeText(url);
          copied = true;
        }}
      }} catch (_) {{}}
      if (!copied) {{
        const temp = doc.createElement('textarea');
        temp.value = url;
        temp.setAttribute('readonly', '');
        temp.style.position = 'fixed';
        temp.style.opacity = '0';
        doc.body.appendChild(temp);
        temp.select();
        try {{ copied = doc.execCommand('copy'); }} catch (_) {{}}
        temp.remove();
      }}
      const scope = button.closest('.article-share');
      const status = scope ? scope.querySelector('[data-copy-status]') : null;
      if (status) {{
        status.textContent = copied ? 'Copied' : 'Copy failed';
        win.setTimeout(() => {{ status.textContent = ''; }}, 2200);
      }}
    }}, true);
  }}
}})();
</script>
"""
    components.html(script, height=0, width=0)
