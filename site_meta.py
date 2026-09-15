from __future__ import annotations

import json
import streamlit.components.v1 as components

from site_assets import LINKEDIN, MEDIUM, EMAIL

SOCIAL_IMAGE = "https://avatars.githubusercontent.com/u/97567343?v=4"

DESCRIPTIONS = {
    "home": "Enterprise AI & Data leadership focused on strategy, operating models, governance, adoption and business value.",
    "impact": "Leadership evidence from Jair Ribeiro across enterprise AI and data: operating models, portfolio choices, adoption, governance, data readiness and decisions required to scale responsibly.",
    "thinking": "Selected writing by Jair Ribeiro on enterprise AI strategy, value, operating models, governance, data readiness, adoption and leadership judgment.",
    "about": "About Jair Ribeiro, a Senior AI & Data Leader based in Gothenburg with international experience across enterprise technology, data, analytics, AI adoption and governance.",
    "contact": "Contact Jair Ribeiro to discuss senior AI, Data and Analytics leadership mandates in Sweden and international environments.",
    "enterprise": "Enterprise AI & Data leadership profile for Jair Ribeiro: strategy, portfolio management, operating models, data foundations, governance, adoption and scale.",
    "transformation": "AI transformation and capability profile for Jair Ribeiro: prioritization, adoption, governance, operating models, data readiness and moving from pilots to scale.",
    "consulting": "Business-driven AI and consulting leadership profile for Jair Ribeiro, connecting executive priorities with technology choices, governance, adoption and delivery reality.",
}


def inject_metadata(page: str, title: str) -> None:
    """Add page metadata to the browser document without introducing third-party tracking."""
    description = DESCRIPTIONS.get(page, DESCRIPTIONS["home"])
    person = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": "Jair Ribeiro",
        "jobTitle": "Senior AI & Data Leader",
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
  meta('meta[property="og:url"]', 'property', 'og:url', canonical);
  meta('meta[property="og:image"]', 'property', 'og:image', socialImage);
  meta('meta[name="twitter:card"]', 'name', 'twitter:card', 'summary_large_image');
  meta('meta[name="twitter:title"]', 'name', 'twitter:title', title);
  meta('meta[name="twitter:description"]', 'name', 'twitter:description', description);
  meta('meta[name="twitter:image"]', 'name', 'twitter:image', socialImage);

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

  // Event names are deliberately attached without sending data anywhere.
  // They are ready for a privacy-conscious analytics provider if one is later configured.
  doc.querySelectorAll('[data-hq-event]').forEach((el) => {{
    if (el.dataset.hqBound === '1') return;
    el.dataset.hqBound = '1';
    el.addEventListener('click', () => {{
      window.parent.dispatchEvent(new CustomEvent('hq-conversion', {{
        detail: {{ event: el.dataset.hqEvent, page }}
      }}));
    }});
  }});
}})();
</script>
"""
    components.html(script, height=0, width=0)
