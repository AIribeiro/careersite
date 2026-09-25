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
    "element_impression",
    "article_card_click",
    "cta_click",
    "section_view",
    "performance_metric",
    "section_attention",
    "element_attention",
    "cta_hesitation",
    "scroll_abandonment",
    "ux_signal",
    "first_interaction",
    "behavior_summary",
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
  const page = {json.dumps(page)};
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
    // Page counter is reloaded below when a new session starts.
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

  const isExcludedTestTraffic = () => (
    String(attribution.source || '').toLowerCase() === 'application' &&
    String(attribution.role || '').toLowerCase() === 'test'
  );

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
      hardware_concurrency: Number(nav.hardwareConcurrency || 0) > 0
        ? Math.min(256, Math.max(1, Math.round(Number(nav.hardwareConcurrency))))
        : null,
      device_memory_gb: Number(nav.deviceMemory || 0) > 0
        ? Math.min(256, Number(nav.deviceMemory))
        : null,
      save_data: connection && typeof connection.saveData === 'boolean'
        ? Boolean(connection.saveData)
        : null,
      orientation: (() => {{
        try {{
          const value = String(win.screen && win.screen.orientation && win.screen.orientation.type || '');
          if (value.startsWith('portrait')) return 'portrait';
          if (value.startsWith('landscape')) return 'landscape';
        }} catch (_) {{}}
        return win.innerHeight >= win.innerWidth ? 'portrait' : 'landscape';
      }})(),
    }};
  }};

  // Counters are per content/session, retained across genuine revisits.
  let pageEngagedMs = 0;
  const pageTimeKey = () => `jair_hq_page_time:${{sessionId}}:${{page}}:${{win.__jairArticleContext?.slug || ''}}`;
  let currentPageTimeKey = pageTimeKey();
  pageEngagedMs = Number(win.sessionStorage.getItem(pageTimeKey()) || 0);
  let maxScrollDepth = Number(win.sessionStorage.getItem(pageTimeKey() + ':depth')) || null;
  const scrollDepth = () => {{
    const article = doc.querySelector('.article-body');
    const surface = article || doc.querySelector('.site main');
    if (!surface) return null;
    const rect = surface.getBoundingClientRect();
    if (rect.height <= 0) return null;
    const depth = Math.round(Math.max(0, Math.min(100, 100 * (win.innerHeight - rect.top) / rect.height)));
    maxScrollDepth = Math.max(maxScrollDepth || 0, depth);
    win.sessionStorage.setItem(pageTimeKey() + ':depth', String(maxScrollDepth));
    return maxScrollDepth;
  }};
  win.__jairAnalyticsScrollDepth = scrollDepth;
  win.__jairAnalyticsClientContext = clientContext;

  const safeText = (value, limit = 240) => String(value || '').replace(/\\s+/g, ' ').trim().slice(0, limit);
  const keyify = (value) => safeText(value, 160).toLowerCase()
    .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 160);

  const sectionDescriptor = (section) => {{
    if (!section) return null;
    let label = '';
    try {{
      const heading = section.querySelector('.eyebrow, h1, h2, h3');
      label = safeText(heading && heading.textContent);
    }} catch (_) {{}}
    let index = 0;
    try {{
      index = Math.max(0, Array.from(doc.querySelectorAll('main section')).indexOf(section));
    }} catch (_) {{}}
    const key = keyify(section.dataset && section.dataset.analyticsSection)
      || keyify(label)
      || `section-${{index + 1}}`;
    return {{ key, label: label || key.replace(/-/g, ' ') }};
  }};

  const placementFor = (el) => {{
    try {{
      if (el.closest('nav')) return 'header';
      if (el.closest('footer')) return 'footer';
      const section = el.closest('section');
      if (section) {{
        const className = String(section.className || '');
        if (win.__jairArticleContext && /(^|\\s)cta(\\s|$)/.test(className)) return 'article_footer';
        const desc = sectionDescriptor(section);
        if (desc) return `${{page}}:${{desc.key}}`;
      }}
    }} catch (_) {{}}
    return page;
  }};

  const articleCardDescriptor = (el) => {{
    if (!el || !el.getAttribute) return null;
    const raw = String((el.dataset && el.dataset.hqEvent) || '').toLowerCase();
    if (raw.startsWith('article_share_')) return null;
    const href = String(el.getAttribute('href') || '');
    let slug = '';
    try {{ slug = new URL(href, win.location.href).searchParams.get('article') || ''; }} catch (_) {{}}
    let isCard = Boolean(slug);
    try {{
      isCard = isCard || el.matches('a.recent-card, a.article') ||
        Boolean(el.closest('.featured-thinking, .decision-note') && raw.includes('open'));
    }} catch (_) {{}}
    if (!isCard) return null;
    let label = safeText(el.textContent);
    try {{
      const heading = el.querySelector('h2, h3') || (el.closest('article') && el.closest('article').querySelector('h2, h3'));
      label = safeText(heading && heading.textContent) || label;
    }} catch (_) {{}}
    return {{
      element_kind: 'article_card',
      element_key: safeText(slug,160) || keyify(label) || keyify(href) || 'article',
      element_label: label || safeText(slug,240) || 'Article',
      element_placement: placementFor(el),
    }};
  }};

  const ctaDescriptor = (el) => {{
    if (!el || !el.getAttribute || articleCardDescriptor(el)) return null;
    const raw = String((el.dataset && el.dataset.hqEvent) || '').toLowerCase();
    if (raw.startsWith('article_share_')) return null;
    const href = String(el.getAttribute('href') || '');
    let qualifies = false;
    try {{ qualifies = el.matches('a.btn, a.contactlink, footer a[data-hq-event]'); }} catch (_) {{}}
    qualifies = qualifies || /^(cv_download|contact_|email_|linkedin_|impact_|medium_)/.test(raw);
    if (!qualifies) return null;
    let key = raw || keyify(el.textContent) || 'cta';
    if (raw.startsWith('cv_download')) key = 'cv';
    else if (raw.startsWith('contact_') || raw.startsWith('email_') || href.toLowerCase().startsWith('mailto:')) key = 'contact';
    else if (raw.startsWith('linkedin_') || href.toLowerCase().includes('linkedin.com')) key = 'linkedin';
    else if (raw.startsWith('impact_')) key = 'impact';
    else if (raw.startsWith('medium_')) key = 'medium';
    return {{
      element_kind: 'cta',
      element_key: safeText(key,160),
      element_label: safeText(el.textContent) || key,
      element_placement: placementFor(el),
    }};
  }};

  win.__jairAnalyticsDescribeSection = sectionDescriptor;
  win.__jairAnalyticsDescribeArticleCard = articleCardDescriptor;
  win.__jairAnalyticsDescribeCta = ctaDescriptor;

  const markAndSendExposure = (eventName, descriptor) => {{
    if (!descriptor || !win.__jairAnalyticsSend) return;
    const kind = descriptor.element_kind || 'section';
    const elementKey = descriptor.element_key || descriptor.section_key || 'unknown';
    const placement = descriptor.element_placement || page;
    const seenKey = `jair_hq_seen_v4:${{sessionId}}:${{eventName}}:${{kind}}:${{elementKey}}:${{placement}}`;
    if (win.sessionStorage.getItem(seenKey)) return;
    win.sessionStorage.setItem(seenKey, '1');
    win.__jairAnalyticsSend(eventName, descriptor);
  }};

  const refreshExposures = () => {{
    if (win.__jairAnalyticsExposureObservers) {{
      for (const observer of win.__jairAnalyticsExposureObservers) {{
        try {{ observer.disconnect(); }} catch (_) {{}}
      }}
    }}
    win.__jairAnalyticsExposureObservers = [];
    if (!win.IntersectionObserver || !doc.querySelectorAll) return;

    const sectionObserver = new win.IntersectionObserver((entries) => {{
      for (const entry of entries) {{
        if (!entry.isIntersecting || entry.intersectionRatio < 0.15) continue;
        const desc = sectionDescriptor(entry.target);
        if (desc) markAndSendExposure('section_view', {{
          section_key: desc.key,
          section_label: desc.label,
          element_placement: page,
        }});
        sectionObserver.unobserve(entry.target);
      }}
    }}, {{ threshold: [0.15] }});
    for (const section of doc.querySelectorAll('main section')) sectionObserver.observe(section);
    win.__jairAnalyticsExposureObservers.push(sectionObserver);

    const elementObserver = new win.IntersectionObserver((entries) => {{
      for (const entry of entries) {{
        if (!entry.isIntersecting || entry.intersectionRatio < 0.5) continue;
        const article = articleCardDescriptor(entry.target);
        const cta = article ? null : ctaDescriptor(entry.target);
        if (article) markAndSendExposure('element_impression', article);
        else if (cta) markAndSendExposure('element_impression', cta);
        elementObserver.unobserve(entry.target);
      }}
    }}, {{ threshold: [0.5] }});

    const candidates = doc.querySelectorAll(
      'a[href*="article="], a.recent-card, a.article, .featured-thinking a, .decision-note a, ' +
      'a.btn, a.contactlink, footer a[data-hq-event], a[data-hq-event^="cv_download"], ' +
      'a[data-hq-event^="contact_"], a[data-hq-event^="email_"], a[data-hq-event^="linkedin_"], a[data-hq-event^="impact_"]'
    );
    for (const el of candidates) {{
      if (articleCardDescriptor(el) || ctaDescriptor(el)) elementObserver.observe(el);
    }}
    win.__jairAnalyticsExposureObservers.push(elementObserver);
  }};
  win.__jairAnalyticsRefreshExposures = refreshExposures;

  const updateEngagement = () => {{
    const state = win.__jairAnalyticsEngagementState;
    if (!state) return;
    if (currentPageTimeKey !== pageTimeKey()) {{
      currentPageTimeKey = pageTimeKey();
      pageEngagedMs = 0;
      maxScrollDepth = null;
    }};
    const nowPerf = win.performance ? win.performance.now() : Date.now();
    const delta = Math.max(0, Math.min(5000, nowPerf - state.lastTick));
    state.lastTick = nowPerf;
    if (doc.visibilityState === 'visible') {{
      scrollDepth();
      engagedMs = Math.min(86400000, engagedMs + delta);
      pageEngagedMs = Math.min(86400000, pageEngagedMs + delta);
      win.sessionStorage.setItem(pageTimeKey(), String(Math.round(pageEngagedMs)));
      lastActiveAt = Date.now();
      win.sessionStorage.setItem(engagedKey, String(Math.round(engagedMs)));
      win.sessionStorage.setItem(lastActiveKey, String(lastActiveAt));
    }}
  }};

  win.__jairAnalyticsUpdateEngagement = updateEngagement;
  win.__jairAnalyticsEnsureFreshSession = ensureFreshSession;

  win.__jairAnalyticsSend = (eventName, extra = {{}}) => {{
    if (!allowed.has(eventName) || isExcludedTestTraffic()) return;
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
      article_slug: win.__jairArticleContext ? win.__jairArticleContext.slug : null,
      content_kind: win.__jairArticleContext ? 'article' : 'page',
      tracking_version: 5,
      page_engaged_ms: Math.round(pageEngagedMs),
      scroll_depth: scrollDepth(),
      element_kind: extra.element_kind ? safeText(extra.element_kind, 32) : null,
      element_key: extra.element_key ? safeText(extra.element_key, 160) : null,
      element_label: extra.element_label ? safeText(extra.element_label, 240) : null,
      element_placement: extra.element_placement ? safeText(extra.element_placement, 160) : null,
      section_key: extra.section_key ? safeText(extra.section_key, 160) : null,
      section_label: extra.section_label ? safeText(extra.section_label, 240) : null,
      metric_name: extra.metric_name ? safeText(extra.metric_name, 32) : null,
      metric_value: extra.metric_value == null ? null : Math.max(0, Math.min(10000000, Number(extra.metric_value) || 0)),
      attention_ms: extra.attention_ms == null ? null : Math.max(0, Math.min(86400000, Math.round(Number(extra.attention_ms) || 0))),
      hover_ms: extra.hover_ms == null ? null : Math.max(0, Math.min(86400000, Math.round(Number(extra.hover_ms) || 0))),
      hesitation_ms: extra.hesitation_ms == null ? null : Math.max(0, Math.min(86400000, Math.round(Number(extra.hesitation_ms) || 0))),
      latency_ms: extra.latency_ms == null ? null : Math.max(0, Math.min(86400000, Math.round(Number(extra.latency_ms) || 0))),
      exposure_count: extra.exposure_count == null ? null : Math.max(0, Math.min(10000, Math.round(Number(extra.exposure_count) || 0))),
      interaction_type: extra.interaction_type ? safeText(extra.interaction_type, 32) : null,
      focus_loss_count: extra.focus_loss_count == null ? null : Math.max(0, Math.min(10000, Math.round(Number(extra.focus_loss_count) || 0))),
      resize_count: extra.resize_count == null ? null : Math.max(0, Math.min(10000, Math.round(Number(extra.resize_count) || 0))),
      orientation_change_count: extra.orientation_change_count == null ? null : Math.max(0, Math.min(10000, Math.round(Number(extra.orientation_change_count) || 0))),
      max_scroll_velocity: extra.max_scroll_velocity == null ? null : Math.max(0, Math.min(1000000, Number(extra.max_scroll_velocity) || 0)),
      max_reverse_scroll_velocity: extra.max_reverse_scroll_velocity == null ? null : Math.max(0, Math.min(1000000, Number(extra.max_reverse_scroll_velocity) || 0)),
      error_type: extra.error_type ? safeText(extra.error_type, 64) : null,
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
  if (win.__jairAnalyticsLastDocumentView !== viewSignature) {{
    win.__jairAnalyticsSend('page_view');
    if (win.__jairAnalyticsContext.page === 'impact') {{
      win.__jairAnalyticsSend('impact_view');
    }}
    if (lenses.has(win.__jairAnalyticsContext.page)) {{
      win.__jairAnalyticsSend('lens_view', {{ lens: win.__jairAnalyticsContext.page }});
    }}
    win.__jairAnalyticsLastDocumentView = viewSignature;
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

  if (win.__jairAnalyticsRefreshExposures) {{
    win.setTimeout(() => win.__jairAnalyticsRefreshExposures && win.__jairAnalyticsRefreshExposures(), 0);
  }}

  if (!win.__jairAnalyticsPerformanceBound) {{
    win.__jairAnalyticsPerformanceBound = true;
    const perf = {{ ttfb_ms: null, lcp_ms: null, cls: 0, interaction_ms: 0 }};
    win.__jairAnalyticsPerformanceState = perf;
    const sendMetric = (metricName, value) => {{
      if (value == null || !Number.isFinite(Number(value)) || !win.__jairAnalyticsSend) return;
      win.__jairAnalyticsSend('performance_metric', {{
        metric_name: metricName,
        metric_value: Number(value),
        element_placement: 'document',
      }});
    }};
    const sendPerformanceSnapshot = () => {{
      if (perf.ttfb_ms != null) sendMetric('ttfb_ms', Math.round(perf.ttfb_ms));
      if (perf.lcp_ms != null) sendMetric('lcp_ms', Math.round(perf.lcp_ms));
      sendMetric('cls', Number(perf.cls.toFixed(4)));
      if (perf.interaction_ms > 0) sendMetric('interaction_ms', Math.round(perf.interaction_ms));
    }};
    win.__jairAnalyticsSendPerformance = sendPerformanceSnapshot;

    try {{
      const navEntry = win.performance && win.performance.getEntriesByType
        ? win.performance.getEntriesByType('navigation')[0]
        : null;
      if (navEntry && Number.isFinite(navEntry.responseStart)) perf.ttfb_ms = Math.max(0, navEntry.responseStart);
    }} catch (_) {{}}

    if (win.PerformanceObserver) {{
      try {{
        const lcpObserver = new win.PerformanceObserver((list) => {{
          for (const entry of list.getEntries()) perf.lcp_ms = Math.max(perf.lcp_ms || 0, Number(entry.startTime || 0));
        }});
        lcpObserver.observe({{ type: 'largest-contentful-paint', buffered: true }});
      }} catch (_) {{}}
      try {{
        const clsObserver = new win.PerformanceObserver((list) => {{
          for (const entry of list.getEntries()) {{
            if (!entry.hadRecentInput) perf.cls += Number(entry.value || 0);
          }}
        }});
        clsObserver.observe({{ type: 'layout-shift', buffered: true }});
      }} catch (_) {{}}
      try {{
        const interactionObserver = new win.PerformanceObserver((list) => {{
          for (const entry of list.getEntries()) {{
            perf.interaction_ms = Math.max(perf.interaction_ms, Number(entry.duration || 0));
          }}
        }});
        interactionObserver.observe({{ type: 'event', buffered: true, durationThreshold: 40 }});
      }} catch (_) {{}}
    }}

    win.setTimeout(() => win.__jairAnalyticsSendPerformance && win.__jairAnalyticsSendPerformance(), 5000);
    win.addEventListener('pagehide', () => {{
      if (win.__jairAnalyticsSendPerformance) win.__jairAnalyticsSendPerformance();
    }});
  }}

  if (!win.__jairAnalyticsEngagementBound) {{
    win.__jairAnalyticsEngagementBound = true;
    const nowPerf = win.performance ? win.performance.now() : Date.now();
    win.__jairAnalyticsEngagementState = {{ lastTick: nowPerf }};

    win.setInterval(() => {{
      const ensure = win.__jairAnalyticsEnsureFreshSession;
      const update = win.__jairAnalyticsUpdateEngagement;
      const reset = ensure ? ensure() : false;
      if (reset && win.__jairAnalyticsRecordCurrentView) {{
        win.__jairAnalyticsRecordCurrentView();
      }}
      if (update) update();
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
      const ensure = win.__jairAnalyticsEnsureFreshSession;
      const update = win.__jairAnalyticsUpdateEngagement;
      if (doc.visibilityState === 'visible') {{
        const reset = ensure ? ensure() : false;
        if (reset && win.__jairAnalyticsRecordCurrentView) {{
          win.__jairAnalyticsRecordCurrentView();
        }}
        if (update) update();
      }} else {{
        if (update) update();
        if (win.__jairAnalyticsSend) win.__jairAnalyticsSend('engagement_ping');
      }}
    }});

    win.addEventListener('pagehide', () => {{
      const update = win.__jairAnalyticsUpdateEngagement;
      if (update) update();
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
      const articleDescriptor = win.__jairAnalyticsDescribeArticleCard
        ? win.__jairAnalyticsDescribeArticleCard(el)
        : null;
      const ctaDescriptor = win.__jairAnalyticsDescribeCta
        ? win.__jairAnalyticsDescribeCta(el)
        : null;
      if (articleDescriptor && win.__jairAnalyticsSend) {{
        win.__jairAnalyticsSend('article_card_click', articleDescriptor);
      }} else if (ctaDescriptor && win.__jairAnalyticsSend) {{
        win.__jairAnalyticsSend('cta_click', ctaDescriptor);
      }}
      if (raw.startsWith('article_share_')) return;
      try {{
        if (new URL(el.getAttribute('href') || '', win.location.href).searchParams.has('article')) return;
      }} catch (_) {{}}
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
      }} else if (raw.startsWith('article_') && !href.includes('article=')) {{
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
