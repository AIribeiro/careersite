from __future__ import annotations

"""Minimal first-party behavioral analytics for the public career site.

The browser sends only a deliberately small event taxonomy to Supabase. There
are no cookies, persistent visitor identifiers, heatmaps, recordings, IP fields
or user-agent fields in the application-owned dataset. A random session UUID is
stored in sessionStorage so one tab visit can be reconstructed as a funnel.
"""

import json
import os

import streamlit.components.v1 as components

ANALYTICS_URL = os.getenv(
    "CAREERSITE_ANALYTICS_URL",
    "https://rnqweoxtynelfirffmlr.supabase.co",
)
ANALYTICS_PUBLISHABLE_KEY = os.getenv(
    "CAREERSITE_ANALYTICS_PUBLISHABLE_KEY",
    "sb_publishable_Hd24EkrnXK4kxb_VJ1KH-w_SN77LYkI",
)
ANALYTICS_TABLE = "careersite_analytics_events"

ALLOWED_EVENTS = (
    "page_view",
    "impact_view",
    "lens_view",
    "cv_download",
    "email_click",
    "linkedin_click",
    "article_click",
)
LENS_PAGES = ("enterprise", "transformation", "governance", "consulting")


def inject_analytics(page: str, source: str = "streamlit") -> None:
    """Inject the shared privacy-conscious analytics client into the browser."""
    if source not in {"streamlit", "lovable"}:
        raise ValueError(f"Unsupported analytics source: {source}")

    endpoint = f"{ANALYTICS_URL.rstrip('/')}/rest/v1/{ANALYTICS_TABLE}"
    script = f"""
<script>
(() => {{
  const win = window.parent;
  const doc = win.document;
  const endpoint = {json.dumps(endpoint)};
  const apiKey = {json.dumps(ANALYTICS_PUBLISHABLE_KEY)};
  const allowed = new Set({json.dumps(list(ALLOWED_EVENTS))});
  const lenses = new Set({json.dumps(list(LENS_PAGES))});

  win.__jairAnalyticsContext = {{
    page: {json.dumps(page)},
    source: {json.dumps(source)}
  }};

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

  const campaign = () => {{
    const params = new URL(win.location.href).searchParams;
    return {{
      utm_source: (params.get('utm_source') || params.get('src') || '').slice(0, 100) || null,
      utm_campaign: (params.get('utm_campaign') || '').slice(0, 100) || null,
    }};
  }};

  const referrerHost = () => {{
    try {{
      if (!doc.referrer) return null;
      const host = new URL(doc.referrer).hostname;
      return host && host !== win.location.hostname ? host.slice(0, 255) : null;
    }} catch (_) {{
      return null;
    }}
  }};

  win.__jairAnalyticsSend = (eventName, extra = {{}}) => {{
    if (!allowed.has(eventName)) return;
    const context = win.__jairAnalyticsContext || {{ page: 'home', source: 'streamlit' }};
    const c = campaign();
    const payload = {{
      event_name: eventName,
      page: String(context.page || 'home').slice(0, 64),
      lens: extra.lens ? String(extra.lens).slice(0, 64) : null,
      target: extra.target ? String(extra.target).slice(0, 500) : null,
      source: context.source,
      session_id: sessionId,
      referrer_host: referrerHost(),
      utm_source: c.utm_source,
      utm_campaign: c.utm_campaign,
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

    // Preserve the existing first-party browser event for local debugging or
    // future integrations; no external listener is required for measurement.
    win.dispatchEvent(new CustomEvent('hq-conversion', {{
      detail: {{ event: eventName, page: payload.page, lens: payload.lens, target: payload.target }}
    }}));
  }};

  // Streamlit can rerun a page without a genuine navigation. Suppress only
  // immediate duplicate view events while still counting a later revisit.
  const viewSignature = `${{win.__jairAnalyticsContext.source}}|${{win.__jairAnalyticsContext.page}}|${{win.location.href}}`;
  const now = Date.now();
  let lastView = null;
  try {{ lastView = JSON.parse(win.sessionStorage.getItem('jair_hq_last_view_v1') || 'null'); }} catch (_) {{}}
  if (!lastView || lastView.signature !== viewSignature || now - lastView.at > 3000) {{
    win.__jairAnalyticsSend('page_view');
    if (win.__jairAnalyticsContext.page === 'impact') {{
      win.__jairAnalyticsSend('impact_view');
    }}
    if (lenses.has(win.__jairAnalyticsContext.page)) {{
      win.__jairAnalyticsSend('lens_view', {{ lens: win.__jairAnalyticsContext.page }});
    }}
    win.sessionStorage.setItem('jair_hq_last_view_v1', JSON.stringify({{ signature: viewSignature, at: now }}));
  }}

  // Bind once using event delegation so links rendered after this component
  // are still measured. Internal page/lens transitions are measured on the
  // destination page rather than as duplicate click events.
  if (!win.__jairAnalyticsClickBound) {{
    win.__jairAnalyticsClickBound = true;
    doc.addEventListener('click', (event) => {{
      const el = event.target && event.target.closest
        ? event.target.closest('[data-hq-event], a[href]')
        : null;
      if (!el) return;

      const raw = String(el.dataset.hqEvent || '').toLowerCase();
      const href = String(el.getAttribute('href') || '');
      let eventName = null;
      let target = null;

      if (raw.startsWith('cv_download')) {{
        eventName = 'cv_download';
        target = 'cv';
      }} else if (raw.startsWith('email_') || href.toLowerCase().startsWith('mailto:')) {{
        eventName = 'email_click';
        target = 'email';
      }} else if (raw.startsWith('linkedin_') || href.toLowerCase().includes('linkedin.com')) {{
        eventName = 'linkedin_click';
        target = 'linkedin';
      }} else if (raw.startsWith('article_')) {{
        eventName = 'article_click';
        target = href || (el.textContent || '').trim();
      }}

      if (eventName && win.__jairAnalyticsSend) {{
        win.__jairAnalyticsSend(eventName, {{ target }});
      }}
    }}, true);
  }}
}})();
</script>
"""
    components.html(script, height=0, width=0)
