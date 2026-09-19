from __future__ import annotations

"""Privacy-conscious first-party behavioral analytics for the public career site.

The browser sends a deliberately small event taxonomy plus coarse session context
to Supabase. There are no analytics cookies, persistent visitor identifiers,
heatmaps, recordings, raw IP fields, or raw user-agent fields in the
application-owned dataset. A random session UUID, attribution, and engagement
state live only in sessionStorage so a single tab visit can be reconstructed
without creating a durable cross-session visitor profile.
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
    "engagement_ping",
)
LENS_PAGES = ("enterprise", "transformation", "governance", "consulting")
RECOMMENDED_ATTRIBUTION_SOURCES = (
    "linkedin",
    "email",
    "cv",
    "outreach",
    "application",
)


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

  const SESSION_TIMEOUT_MS = 30 * 60 * 1000;
  const FIRST_HEARTBEAT_MS = 5000;
  const HEARTBEAT_MS = 10000;
  const sessionKey = 'jair_hq_session_v1';
  const startedKey = 'jair_hq_started_v3';
  const engagedKey = 'jair_hq_engaged_v3';
  const lastActiveKey = 'jair_hq_last_active_v3';

  const makeSessionId = () => (win.crypto && win.crypto.randomUUID)
    ? win.crypto.randomUUID()
    : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {{
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      }});

  let sessionId = win.sessionStorage.getItem(sessionKey) || '';
  let startedAt = Number(win.sessionStorage.getItem(startedKey) || 0);
  let engagedMs = Math.max(0, Number(win.sessionStorage.getItem(engagedKey) || 0));
  let lastActiveAt = Number(win.sessionStorage.getItem(lastActiveKey) || 0);

  const startFreshSession = (now = Date.now()) => {{
    sessionId = makeSessionId();
    startedAt = now;
    engagedMs = 0;
    lastActiveAt = now;
    win.sessionStorage.setItem(sessionKey, sessionId);
    win.sessionStorage.setItem(startedKey, String(startedAt));
    win.sessionStorage.setItem(engagedKey, '0');
    win.sessionStorage.setItem(lastActiveKey, String(lastActiveAt));
    win.sessionStorage.removeItem('jair_hq_last_view_v1');
    const state = win.__jairAnalyticsEngagementState;
    if (state) {{
      state.lastTick = win.performance ? win.performance.now() : Date.now();
    }}
  }};

  const ensureFreshSession = () => {{
    const now = Date.now();
    const stale = !sessionId || !startedAt || startedAt > now || !lastActiveAt
      || now - lastActiveAt > SESSION_TIMEOUT_MS;
    if (stale) {{
      startFreshSession(now);
      return true;
    }}
    return false;
  }};

  ensureFreshSession();

  // Attribution describes the job-search activity that brought a visitor to
  // the site, never an individual. Persist it only for this browser tab so
  // internal navigation can drop query parameters without losing the funnel.
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

  const clientContext = () => {{
    const nav = win.navigator || {{}};
    const ua = String(nav.userAgent || '');
    const platform = String(nav.platform || '');
    const touchPoints = Number(nav.maxTouchPoints || 0);
    const width = Number(win.innerWidth || doc.documentElement.clientWidth || 0);
    const isIPadDesktopUa = platform === 'MacIntel' && touchPoints > 1;
    const isTablet = isIPadDesktopUa || /iPad|Tablet|PlayBook|Silk/i.test(ua) || (/Android/i.test(ua) && !/Mobile/i.test(ua));
    const isMobile = !isTablet && (/Mobi|iPhone|iPod|Android/i.test(ua) || width < 600);
    const deviceType = isTablet ? 'tablet' : (isMobile ? 'mobile' : 'desktop');

    let browserFamily = 'Other';
    if (ua.includes('Edg/')) browserFamily = 'Edge';
    else if (ua.includes('OPR/')) browserFamily = 'Opera';
    else if (ua.includes('Firefox/')) browserFamily = 'Firefox';
    else if (ua.includes('CriOS/')) browserFamily = 'Chrome iOS';
    else if (ua.includes('Chrome/')) browserFamily = 'Chrome';
    else if (ua.includes('FxiOS/')) browserFamily = 'Firefox iOS';
    else if (ua.includes('Safari/')) browserFamily = 'Safari';

    let osFamily = 'Other';
    if (/Windows NT/i.test(ua)) osFamily = 'Windows';
    else if (/Android/i.test(ua)) osFamily = 'Android';
    else if (/iPhone|iPad|iPod/i.test(ua) || isIPadDesktopUa) osFamily = 'iOS/iPadOS';
    else if (/Mac OS X|Macintosh/i.test(ua)) osFamily = 'macOS';
    else if (/Linux/i.test(ua)) osFamily = 'Linux';

    let timezone = null;
    try {{ timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || null; }} catch (_) {{}}
    const connection = nav.connection || nav.mozConnection || nav.webkitConnection || null;

    return {{
      device_type: deviceType,
      browser_family: browserFamily.slice(0, 32),
      os_family: osFamily.slice(0, 32),
      language: String(nav.language || '').slice(0, 35) || null,
      timezone: timezone ? String(timezone).slice(0, 64) : null,
      viewport_width: Math.min(20000, Math.max(1, Math.round(width || 1))),
      viewport_height: Math.min(20000, Math.max(1, Math.round(win.innerHeight || 1))),
      screen_width: Math.min(20000, Math.max(1, Math.round((win.screen && win.screen.width) || 1))),
      screen_height: Math.min(20000, Math.max(1, Math.round((win.screen && win.screen.height) || 1))),
      connection_type: connection && connection.effectiveType
        ? String(connection.effectiveType).slice(0, 20)
        : null,
    }};
  }};

  const updateEngagement = () => {{
    const state = win.__jairAnalyticsEngagementState;
    if (!state) return;
    const nowPerf = win.performance ? win.performance.now() : Date.now();
    const delta = Math.max(0, Math.min(5000, nowPerf - state.lastTick));
    state.lastTick = nowPerf;
    if (doc.visibilityState === 'visible') {{
      engagedMs = Math.min(86400000, engagedMs + delta);
      lastActiveAt = Date.now();
      win.sessionStorage.setItem(engagedKey, String(Math.round(engagedMs)));
      win.sessionStorage.setItem(lastActiveKey, String(lastActiveAt));
    }}
  }};

  win.__jairAnalyticsSend = (eventName, extra = {{}}) => {{
    if (!allowed.has(eventName)) return;
    ensureFreshSession();
    updateEngagement();
    const context = win.__jairAnalyticsContext || {{ page: 'home', source: 'streamlit' }};
    const elapsedMs = Math.min(86400000, Math.max(0, Date.now() - startedAt));
    const payload = {{
      event_name: eventName,
      page: String(context.page || 'home').slice(0, 64),
      lens: extra.lens ? String(extra.lens).slice(0, 64) : null,
      target: extra.target ? String(extra.target).slice(0, 500) : null,
      source: context.source,
      session_id: sessionId,
      referrer_host: referrerHost(),
      attribution_source: attribution.source,
      attribution_role: attribution.role,
      utm_source: attribution.utm_source,
      utm_campaign: attribution.utm_campaign,
      session_elapsed_ms: Math.round(elapsedMs),
      engaged_ms: Math.round(Math.min(86400000, Math.max(0, engagedMs))),
      ...clientContext(),
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

  win.__jairAnalyticsRecordCurrentView = () => {{
    if (!win.__jairAnalyticsSend) return;
    win.__jairAnalyticsSend('page_view');
    if (win.__jairAnalyticsContext.page === 'impact') {{
      win.__jairAnalyticsSend('impact_view');
    }}
    if (lenses.has(win.__jairAnalyticsContext.page)) {{
      win.__jairAnalyticsSend('lens_view', {{ lens: win.__jairAnalyticsContext.page }});
    }}
  }};

  if (!win.__jairAnalyticsEngagementBound) {{
    win.__jairAnalyticsEngagementBound = true;
    const nowPerf = win.performance ? win.performance.now() : Date.now();
    win.__jairAnalyticsEngagementState = {{ lastTick: nowPerf }};

    win.setInterval(() => {{
      const reset = ensureFreshSession();
      if (reset && win.__jairAnalyticsRecordCurrentView) {{
        win.__jairAnalyticsRecordCurrentView();
      }}
      updateEngagement();
    }}, 1000);

    win.setTimeout(() => {{
      if (doc.visibilityState === 'visible' && win.__jairAnalyticsSend) {{
        win.__jairAnalyticsSend('engagement_ping');
      }}
    }}, FIRST_HEARTBEAT_MS);

    win.setInterval(() => {{
      if (doc.visibilityState === 'visible' && win.__jairAnalyticsSend) {{
        win.__jairAnalyticsSend('engagement_ping');
      }}
    }}, HEARTBEAT_MS);

    doc.addEventListener('visibilitychange', () => {{
      if (doc.visibilityState === 'visible') {{
        const reset = ensureFreshSession();
        if (reset && win.__jairAnalyticsRecordCurrentView) {{
          win.__jairAnalyticsRecordCurrentView();
        }}
        updateEngagement();
      }} else {{
        updateEngagement();
        if (win.__jairAnalyticsSend) win.__jairAnalyticsSend('engagement_ping');
      }}
    }});

    win.addEventListener('pagehide', () => {{
      updateEngagement();
      if (win.__jairAnalyticsSend) win.__jairAnalyticsSend('engagement_ping');
    }});
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
