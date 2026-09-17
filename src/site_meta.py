from __future__ import annotations

import json
import streamlit.components.v1 as components

from site_assets import LINKEDIN, MEDIUM, EMAIL
from site_social_preview import PUBLIC_URL as SOCIAL_IMAGE, ensure_social_preview

try:
    ensure_social_preview()
except OSError:
    # Metadata remains valid even if a constrained runtime cannot write the
    # derivative during import; the public URL is stable across deployments.
    pass

DESCRIPTIONS = {
    "home": "Jair Ribeiro is an Enterprise AI & Data Leader. A curated portfolio of leadership cases, operating judgment, practical frameworks and selected writing across AI, Data and Analytics.",
    "impact": "Leadership cases from Jair Ribeiro showing situations, trade-offs, cross-functional leadership and decisions behind enterprise AI and Data work.",
    "thinking": "Selected writing by Jair Ribeiro on enterprise AI strategy, value, operating models, governance, data readiness, adoption and leadership judgment.",
    "about": "The professional story of Jair Ribeiro: from enterprise technology foundations into business-facing AI, Data and Analytics leadership across international organizations.",
    "contact": "Contact Jair Ribeiro about senior AI, Data and Analytics leadership where strategy, portfolio, governance, adoption and operating capability need to work together.",
    "enterprise": "Contextual view of Jair Ribeiro's Enterprise AI & Data leadership experience across strategy, portfolio, operating models, governance, adoption and technical judgment.",
    "transformation": "Contextual view of Jair Ribeiro's AI transformation and adoption experience, connecting experimentation with capability building, workflow change, governance and scale-readiness.",
    "governance": "Contextual view of Jair Ribeiro's AI governance and operating-model experience across decision rights, lifecycle ownership, Responsible AI, data trust and scale-readiness.",
    "consulting": "Contextual view of Jair Ribeiro's business-driven AI and consulting experience, connecting problem framing and executive dialogue with enterprise operating reality.",
}


def inject_metadata(page: str, title: str) -> None:
    """Add page metadata without third-party tracking."""
    description = DESCRIPTIONS.get(page, DESCRIPTIONS["home"])
    person = {
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
