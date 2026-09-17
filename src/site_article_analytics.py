from __future__ import annotations

import json

import streamlit.components.v1 as components

from site_analytics import ANALYTICS_PUBLISHABLE_KEY, ANALYTICS_TABLE, ANALYTICS_URL
from thinking_articles import ArticleMeta


def inject_article_analytics(
    page: str,
    article: ArticleMeta | None,
    *,
    source: str = "streamlit",
) -> None:
    """Track article opens, reads and shares without persistent visitor identity."""
    if source not in {"streamlit", "lovable"}:
        raise ValueError(f"Unsupported analytics source: {source}")

    endpoint = f"{ANALYTICS_URL.rstrip('/')}/rest/v1/{ANALYTICS_TABLE}"
    article_payload = None
    if article is not None:
        article_payload = {
            "slug": article.slug,
            "title": article.title,
            "kind": article.kind,
            "topic": article.topic,
        }

    script = f"""
<script>
(() => {{
  const win = window.parent;
  const doc = win.document;
  const endpoint = {json.dumps(endpoint)};
  const apiKey = {json.dumps(ANALYTICS_PUBLISHABLE_KEY)};
  const source = {json.dumps(source)};
  const page = {json.dumps(page)};
  const currentArticle = {json.dumps(article_payload)};

  const sessionKey = 'jair_hq_session_v1';
  let sessionId = win.sessionStorage.getItem(sessionKey);
  if (!sessionId) {{
    sessionId = (win.crypto && win.crypto.randomUUID)
      ? win.crypto.randomUUID()
      : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {{
          const r = Math.random() * 16 | 0;
          const v = c === 'x' ? r : (r & 0x3 | 0x8);
          return v.toString(16);
        }});
    win.sessionStorage.setItem(sessionKey, sessionId);
  }}

  const startedKey = 'jair_hq_started_v2';
  let startedAt = Number(win.sessionStorage.getItem(startedKey) || 0);
  if (!startedAt || startedAt > Date.now()) {{
    startedAt = Date.now();
    win.sessionStorage.setItem(startedKey, String(startedAt));
  }}

  const attributionKey = 'jair_hq_attribution_v1';
  const params = new URL(win.location.href).searchParams;
  let attribution = {{ source: null, role: null, utm_source: null, utm_campaign: null }};
  try {{
    attribution = JSON.parse(win.sessionStorage.getItem(attributionKey) || 'null') || attribution;
  }} catch (_) {{}}

  const incomingSource = (
    params.get('source') || params.get('utm_source') || params.get('src') || ''
  ).trim().slice(0, 100) || null;
  const incomingRole = (params.get('role') || '').trim().slice(0, 120) || null;
  const incomingUtmSource = (params.get('utm_source') || params.get('src') || '').trim().slice(0, 100) || null;
  const incomingCampaign = (params.get('utm_campaign') || '').trim().slice(0, 100) || null;
  if (incomingSource || incomingRole || incomingUtmSource || incomingCampaign) {{
    attribution = {{
      source: incomingSource || attribution.source || null,
      role: incomingRole || attribution.role || null,
      utm_source: incomingUtmSource || attribution.utm_source || null,
      utm_campaign: incomingCampaign || attribution.utm_campaign || null,
    }};
    win.sessionStorage.setItem(attributionKey, JSON.stringify(attribution));
  }}

  const referrerHost = () => {{
    try {{
      if (!doc.referrer) return null;
      const host = new URL(doc.referrer).hostname;
      return host && host !== win.location.hostname ? host.slice(0, 255) : null;
    }} catch (_) {{
      return null;
    }}
  }};

  win.__jairArticleContext = currentArticle;
  if (!win.__jairArticleAnalyticsState) {{
    win.__jairArticleAnalyticsState = {{
      slug: null,
      lastTick: win.performance ? win.performance.now() : Date.now(),
      engagedMs: 0,
    }};
  }}
  const state = win.__jairArticleAnalyticsState;

  const articleStorageKey = slug => `jair_hq_article_engaged_v1:${{slug}}`;
  const syncArticleState = () => {{
    const article = win.__jairArticleContext;
    const slug = article && article.slug ? String(article.slug) : null;
    if (state.slug === slug) return;
    state.slug = slug;
    state.lastTick = win.performance ? win.performance.now() : Date.now();
    state.engagedMs = slug
      ? Math.max(0, Number(win.sessionStorage.getItem(articleStorageKey(slug)) || 0))
      : 0;
  }};

  const updateArticleEngagement = () => {{
    syncArticleState();
    if (!state.slug) return;
    const nowPerf = win.performance ? win.performance.now() : Date.now();
    const delta = Math.max(0, Math.min(5000, nowPerf - state.lastTick));
    state.lastTick = nowPerf;
    if (doc.visibilityState === 'visible') {{
      state.engagedMs = Math.min(86400000, state.engagedMs + delta);
      win.sessionStorage.setItem(articleStorageKey(state.slug), String(Math.round(state.engagedMs)));
    }}
  }};

  const send = (eventName, {{ slug = null, action = null, target = null }} = {{}}) => {{
    updateArticleEngagement();
    const effectiveSlug = slug || (win.__jairArticleContext && win.__jairArticleContext.slug) || null;
    const articleMs = effectiveSlug && state.slug === effectiveSlug ? Math.round(state.engagedMs) : 0;
    const sessionEngagedMs = Math.max(0, Number(win.sessionStorage.getItem('jair_hq_engaged_v2') || 0));
    const payload = {{
      event_name: eventName,
      page: String(page || 'thinking').slice(0, 64),
      lens: null,
      target: target ? String(target).slice(0, 500) : (effectiveSlug ? String(effectiveSlug).slice(0, 500) : null),
      source,
      session_id: sessionId,
      referrer_host: referrerHost(),
      attribution_source: attribution.source,
      attribution_role: attribution.role,
      utm_source: attribution.utm_source,
      utm_campaign: attribution.utm_campaign,
      session_elapsed_ms: Math.round(Math.min(86400000, Math.max(0, Date.now() - startedAt))),
      engaged_ms: Math.round(Math.min(86400000, sessionEngagedMs)),
      article_slug: effectiveSlug ? String(effectiveSlug).slice(0, 160) : null,
      article_action: action ? String(action).slice(0, 32) : null,
      article_engaged_ms: effectiveSlug ? Math.min(86400000, Math.max(0, articleMs)) : null,
    }};

    fetch(endpoint, {{
      method: 'POST',
      mode: 'cors',
      keepalive: true,
      headers: {{
        'apikey': apiKey,
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
      }},
      body: JSON.stringify(payload)
    }}).catch(() => {{}});
  }};

  syncArticleState();
  if (currentArticle && currentArticle.slug) {{
    const signature = `${{currentArticle.slug}}|${{win.location.href}}`;
    const now = Date.now();
    let last = null;
    try {{ last = JSON.parse(win.sessionStorage.getItem('jair_hq_last_article_view_v1') || 'null'); }} catch (_) {{}}
    if (!last || last.signature !== signature || now - last.at > 3000) {{
      send('article_view', {{ slug: currentArticle.slug }});
      win.sessionStorage.setItem('jair_hq_last_article_view_v1', JSON.stringify({{ signature, at: now }}));
    }}
  }}

  if (!win.__jairArticleAnalyticsBound) {{
    win.__jairArticleAnalyticsBound = true;

    win.setInterval(() => {{
      updateArticleEngagement();
    }}, 1000);

    win.setInterval(() => {{
      const article = win.__jairArticleContext;
      if (article && article.slug && doc.visibilityState === 'visible') {{
        send('engagement_ping', {{ slug: article.slug }});
      }}
    }}, 30000);

    doc.addEventListener('visibilitychange', () => {{
      updateArticleEngagement();
      const article = win.__jairArticleContext;
      if (article && article.slug && doc.visibilityState === 'hidden') {{
        send('engagement_ping', {{ slug: article.slug }});
      }}
    }});

    win.addEventListener('pagehide', () => {{
      updateArticleEngagement();
      const article = win.__jairArticleContext;
      if (article && article.slug) send('engagement_ping', {{ slug: article.slug }});
    }});

    doc.addEventListener('click', (event) => {{
      const el = event.target && event.target.closest
        ? event.target.closest('[data-hq-event], a[href], button[data-copy-url]')
        : null;
      if (!el) return;

      const raw = String(el.dataset.hqEvent || '').toLowerCase();
      const href = String(el.getAttribute('href') || '');
      const article = win.__jairArticleContext;

      if (raw.startsWith('article_share_') && article && article.slug) {{
        const action = raw.replace('article_share_', '').slice(0, 32) || 'unknown';
        send('article_share', {{ slug: article.slug, action }});
        return;
      }}

      if (href) {{
        try {{
          const destination = new URL(href, win.location.href);
          const slug = destination.searchParams.get('article');
          if (slug) {{
            send('article_click', {{ slug: slug.toLowerCase().slice(0, 160) }});
          }}
        }} catch (_) {{}}
      }}
    }}, true);
  }}
}})();
</script>
"""
    components.html(script, height=0, width=0)
