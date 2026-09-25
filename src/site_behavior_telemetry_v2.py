from __future__ import annotations

"""Advanced browser telemetry built with Streamlit Components v2.

This collector is intentionally first-party and session-scoped. It measures
attention and UX signals without cookies, persistent visitor IDs, cursor
recordings, raw coordinates, form values, or free-text capture.
"""

import streamlit as st


BEHAVIOR_TELEMETRY_JS = r"""
export default function({ data }) {
  const win = window;
  const doc = document;
  const page = String(data?.page || 'home').slice(0, 64);
  const articleSlug = String(data?.article_slug || '').slice(0, 160);

  const safeText = (value, limit = 240) =>
    String(value || '').replace(/\s+/g, ' ').trim().slice(0, limit);
  const keyify = (value) =>
    safeText(value, 160).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 160);

  const contextSignature = () =>
    [page, articleSlug, win.location.pathname, win.location.search].join('|');

  const existing = win.__jairBehaviorTelemetryV5;
  if (existing && existing.version === 5) {
    existing.setContext({ page, articleSlug, signature: contextSignature() });
    return;
  }

  const state = {
    version: 5,
    active: true,
    page,
    articleSlug,
    signature: contextSignature(),
    contextStartedPerf: win.performance ? win.performance.now() : Date.now(),
    sectionRecords: new Map(),
    elementRecords: new Map(),
    sectionObserver: null,
    elementObserver: null,
    mutationObserver: null,
    refreshTimer: null,
    flushTimer: null,
    articleTimer: null,
    performanceTimer: null,
    firstInteractionSent: false,
    firstInteractionType: null,
    focusLossCount: 0,
    resizeCount: 0,
    orientationChangeCount: 0,
    maxScrollVelocity: 0,
    maxReverseScrollVelocity: 0,
    lastScrollY: Number(win.scrollY || 0),
    lastScrollAt: win.performance ? win.performance.now() : Date.now(),
    recentClicks: [],
    signalKeys: new Set(),
    currentArticleRegionKey: null,
    currentArticleRegionAt: null,
    currentArticleRegionSeen: new Set(),
    inpByInteraction: new Map(),
    fcpSent: false,
    inpSentValue: null,
  };

  win.__jairBehaviorTelemetryV5 = state;

  const nowPerf = () => win.performance ? win.performance.now() : Date.now();
  const sessionId = () => win.sessionStorage.getItem('jair_hq_session_v1') || '';

  const send = (eventName, extra = {}) => {
    if (!win.__jairAnalyticsSend) return false;
    win.__jairAnalyticsSend(eventName, extra);
    return true;
  };

  const sectionDescriptor = (section) => {
    if (win.__jairAnalyticsDescribeSection) {
      try {
        const value = win.__jairAnalyticsDescribeSection(section);
        if (value) return value;
      } catch (_) {}
    }
    if (!section) return null;
    let label = '';
    try {
      const heading = section.querySelector('.eyebrow, h1, h2, h3');
      label = safeText(heading && heading.textContent);
    } catch (_) {}
    const sections = Array.from(doc.querySelectorAll('.site main section'));
    const index = Math.max(0, sections.indexOf(section));
    const key = keyify(section.dataset?.analyticsSection) || keyify(label) || `section-${index + 1}`;
    return { key, label: label || key.replace(/-/g, ' ') };
  };

  const currentSectionDescriptor = () => {
    if (state.articleSlug) {
      const article = doc.querySelector('.article-body');
      if (article) {
        const headings = Array.from(article.querySelectorAll('h2, h3'));
        const marker = Math.max(80, win.innerHeight * 0.38);
        let chosen = null;
        for (const heading of headings) {
          const rect = heading.getBoundingClientRect();
          if (rect.top <= marker) chosen = heading;
          else break;
        }
        if (chosen) {
          const label = safeText(chosen.textContent) || 'Article section';
          return { key: `article-${keyify(label) || 'section'}`, label };
        }
        return { key: 'article-opening', label: 'Article opening' };
      }
    }

    const center = win.innerHeight * 0.5;
    const sections = Array.from(doc.querySelectorAll('.site main section'));
    for (const section of sections) {
      const rect = section.getBoundingClientRect();
      if (rect.top <= center && rect.bottom >= center) return sectionDescriptor(section);
    }
    return null;
  };

  const ensureSectionRecord = (key, label) => {
    let record = state.sectionRecords.get(key);
    if (!record) {
      record = {
        key,
        label: safeText(label) || key.replace(/-/g, ' '),
        isVisible: false,
        visibleSince: null,
        attentionMs: 0,
        exposureCount: 0,
      };
      state.sectionRecords.set(key, record);
    }
    return record;
  };

  const ensureElementRecord = (descriptor) => {
    const id = [
      descriptor.element_kind || 'element',
      descriptor.element_key || 'unknown',
      descriptor.element_placement || state.page,
    ].join('|');
    let record = state.elementRecords.get(id);
    if (!record) {
      record = {
        id,
        ...descriptor,
        isVisible: false,
        visibleSince: null,
        firstSeenAt: null,
        attentionMs: 0,
        hoverMs: 0,
        hoverSince: null,
        exposureCount: 0,
      };
      state.elementRecords.set(id, record);
    }
    return record;
  };

  const accrueSection = (record, at = nowPerf()) => {
    if (record.visibleSince != null && doc.visibilityState === 'visible') {
      record.attentionMs += Math.max(0, Math.min(30000, at - record.visibleSince));
    }
    record.visibleSince = record.isVisible && doc.visibilityState === 'visible' ? at : null;
  };

  const accrueElement = (record, at = nowPerf()) => {
    if (record.visibleSince != null && doc.visibilityState === 'visible') {
      record.attentionMs += Math.max(0, Math.min(30000, at - record.visibleSince));
    }
    record.visibleSince = record.isVisible && doc.visibilityState === 'visible' ? at : null;
    if (record.hoverSince != null) {
      record.hoverMs += Math.max(0, Math.min(30000, at - record.hoverSince));
      record.hoverSince = record.isVisible ? at : null;
    }
  };

  const flushAttention = () => {
    const at = nowPerf();
    for (const record of state.sectionRecords.values()) {
      accrueSection(record, at);
      if (record.attentionMs >= 250 || record.exposureCount > 0) {
        send('section_attention', {
          section_key: record.key,
          section_label: record.label,
          attention_ms: Math.round(record.attentionMs),
          exposure_count: record.exposureCount,
        });
        record.attentionMs = 0;
        record.exposureCount = 0;
      }
    }

    for (const record of state.elementRecords.values()) {
      accrueElement(record, at);
      if (record.attentionMs >= 250 || record.hoverMs >= 100 || record.exposureCount > 0) {
        send('element_attention', {
          element_kind: record.element_kind,
          element_key: record.element_key,
          element_label: record.element_label,
          element_placement: record.element_placement,
          attention_ms: Math.round(record.attentionMs),
          hover_ms: Math.round(record.hoverMs),
          exposure_count: record.exposureCount,
        });
        record.attentionMs = 0;
        record.hoverMs = 0;
        record.exposureCount = 0;
      }
    }
  };

  const sendSectionViewOnce = (descriptor) => {
    if (!descriptor) return;
    const sid = sessionId();
    const seenKey = `jair_hq_behavior_section_v5:${sid}:${state.page}:${state.articleSlug}:${descriptor.key}`;
    if (win.sessionStorage.getItem(seenKey)) return;
    win.sessionStorage.setItem(seenKey, '1');
    send('section_view', {
      section_key: descriptor.key,
      section_label: descriptor.label,
      element_placement: state.articleSlug ? 'article_body' : state.page,
    });
  };

  const tickArticleRegion = () => {
    if (!state.articleSlug || doc.visibilityState !== 'visible') return;
    const descriptor = currentSectionDescriptor();
    if (!descriptor) return;
    const at = nowPerf();

    if (state.currentArticleRegionKey && state.currentArticleRegionAt != null) {
      const previous = ensureSectionRecord(
        state.currentArticleRegionKey,
        state.sectionRecords.get(state.currentArticleRegionKey)?.label || state.currentArticleRegionKey
      );
      previous.attentionMs += Math.max(0, Math.min(5000, at - state.currentArticleRegionAt));
    }

    state.currentArticleRegionKey = descriptor.key;
    state.currentArticleRegionAt = at;
    const record = ensureSectionRecord(descriptor.key, descriptor.label);
    if (!state.currentArticleRegionSeen.has(descriptor.key)) {
      state.currentArticleRegionSeen.add(descriptor.key);
      record.exposureCount += 1;
      sendSectionViewOnce(descriptor);
    }
  };

  const describeElement = (el) => {
    try {
      const article = win.__jairAnalyticsDescribeArticleCard
        ? win.__jairAnalyticsDescribeArticleCard(el)
        : null;
      if (article) return article;
      return win.__jairAnalyticsDescribeCta
        ? win.__jairAnalyticsDescribeCta(el)
        : null;
    } catch (_) {
      return null;
    }
  };

  const bindHover = (el, record) => {
    if (el.dataset?.hqBehaviorHoverBound === '1') return;
    try { el.dataset.hqBehaviorHoverBound = '1'; } catch (_) {}

    el.addEventListener('pointerenter', () => {
      if (!record.isVisible || record.hoverSince != null) return;
      record.hoverSince = nowPerf();
    }, { passive: true });

    el.addEventListener('pointerleave', () => {
      if (record.hoverSince == null) return;
      const at = nowPerf();
      record.hoverMs += Math.max(0, Math.min(30000, at - record.hoverSince));
      record.hoverSince = null;
    }, { passive: true });
  };

  const refreshObservers = () => {
    if (!win.__jairAnalyticsSend) return;

    if (state.sectionObserver) state.sectionObserver.disconnect();
    if (state.elementObserver) state.elementObserver.disconnect();

    state.sectionObserver = new IntersectionObserver((entries) => {
      const at = nowPerf();
      for (const entry of entries) {
        const descriptor = sectionDescriptor(entry.target);
        if (!descriptor) continue;
        const record = ensureSectionRecord(descriptor.key, descriptor.label);
        const visible = Boolean(entry.isIntersecting && entry.intersectionRatio >= 0.15);
        if (visible === record.isVisible) continue;
        accrueSection(record, at);
        record.isVisible = visible;
        record.visibleSince = visible && doc.visibilityState === 'visible' ? at : null;
        if (visible) record.exposureCount += 1;
      }
    }, { threshold: [0, 0.15, 0.5] });

    for (const section of doc.querySelectorAll('.site main section')) {
      state.sectionObserver.observe(section);
    }

    state.elementObserver = new IntersectionObserver((entries) => {
      const at = nowPerf();
      for (const entry of entries) {
        const descriptor = describeElement(entry.target);
        if (!descriptor) continue;
        const record = ensureElementRecord(descriptor);
        const visible = Boolean(entry.isIntersecting && entry.intersectionRatio >= 0.5);
        if (visible === record.isVisible) continue;
        accrueElement(record, at);
        record.isVisible = visible;
        record.visibleSince = visible && doc.visibilityState === 'visible' ? at : null;
        if (visible) {
          record.exposureCount += 1;
          if (record.firstSeenAt == null) record.firstSeenAt = Date.now();
        }
        bindHover(entry.target, record);
      }
    }, { threshold: [0, 0.5, 1] });

    const selector = [
      'a[href*="article="]',
      'a.recent-card',
      'a.article',
      '.featured-thinking a',
      '.decision-note a',
      'a.btn',
      'a.contactlink',
      'footer a[data-hq-event]',
      'a[data-hq-event^="cv_download"]',
      'a[data-hq-event^="contact_"]',
      'a[data-hq-event^="email_"]',
      'a[data-hq-event^="linkedin_"]',
      'a[data-hq-event^="impact_"]',
    ].join(',');

    for (const el of doc.querySelectorAll(selector)) {
      const descriptor = describeElement(el);
      if (descriptor) {
        const record = ensureElementRecord(descriptor);
        bindHover(el, record);
        state.elementObserver.observe(el);
      }
    }
  };

  const scheduleRefresh = () => {
    if (state.refreshTimer) win.clearTimeout(state.refreshTimer);
    state.refreshTimer = win.setTimeout(refreshObservers, 120);
  };

  const recordFirstInteraction = (type) => {
    if (state.firstInteractionSent) return;
    state.firstInteractionSent = true;
    state.firstInteractionType = type;
    send('first_interaction', {
      interaction_type: type,
      latency_ms: Math.max(0, Math.round(nowPerf() - state.contextStartedPerf)),
    });
  };

  const handleScroll = () => {
    recordFirstInteraction('scroll');
    const at = nowPerf();
    const y = Number(win.scrollY || 0);
    const delta = y - state.lastScrollY;
    const dt = Math.max(16, at - state.lastScrollAt);
    const velocity = Math.min(1000000, Math.abs(delta) * 1000 / dt);
    state.maxScrollVelocity = Math.max(state.maxScrollVelocity, velocity);
    if (delta < 0) state.maxReverseScrollVelocity = Math.max(state.maxReverseScrollVelocity, velocity);
    state.lastScrollY = y;
    state.lastScrollAt = at;
  };

  const isInteractive = (target) => {
    if (!target || !target.closest) return true;
    return Boolean(target.closest(
      'a,button,input,select,textarea,summary,[role="button"],[role="link"],[contenteditable="true"],[data-copy-url]'
    ));
  };

  const signalSectionPayload = () => {
    const section = currentSectionDescriptor();
    return section ? { section_key: section.key, section_label: section.label } : {};
  };

  const handleClick = (event) => {
    const target = event.target;
    if (!target || !target.closest) return;

    const actionable = target.closest('[data-hq-event], a[href], button');
    const cta = actionable && win.__jairAnalyticsDescribeCta
      ? win.__jairAnalyticsDescribeCta(actionable)
      : null;

    if (cta) {
      const record = ensureElementRecord(cta);
      if (record.firstSeenAt != null) {
        send('cta_hesitation', {
          ...cta,
          hesitation_ms: Math.max(0, Date.now() - record.firstSeenAt),
          attention_ms: Math.round(record.attentionMs),
          hover_ms: Math.round(record.hoverMs),
        });
      }
    }

    const section = currentSectionDescriptor();
    const targetKey = [
      cta?.element_key || '',
      section?.key || '',
      safeText(target.tagName, 20).toLowerCase(),
    ].join('|');
    const now = Date.now();
    const x = Number(event.clientX || 0);
    const y = Number(event.clientY || 0);
    state.recentClicks = state.recentClicks.filter((item) => now - item.t <= 1200);
    state.recentClicks.push({ t: now, x, y, key: targetKey });

    const clustered = state.recentClicks.filter((item) =>
      item.key === targetKey &&
      Math.abs(item.x - x) <= 50 &&
      Math.abs(item.y - y) <= 50
    );
    if (clustered.length >= 3) {
      const signalKey = `rage:${state.signature}:${targetKey}`;
      if (!state.signalKeys.has(signalKey)) {
        state.signalKeys.add(signalKey);
        send('ux_signal', {
          interaction_type: 'rage_click',
          target: safeText(target.tagName, 20).toLowerCase(),
          ...signalSectionPayload(),
        });
      }
    }

    if (!isInteractive(target)) {
      const cardLike = target.closest('.card,.principle,.proofitem,.case,.box,.presence-card,.format-card,.upcoming-item');
      let pointerLike = false;
      try { pointerLike = win.getComputedStyle(target).cursor === 'pointer'; } catch (_) {}
      if (cardLike || pointerLike) {
        const signalKey = `dead:${state.signature}:${targetKey}`;
        if (!state.signalKeys.has(signalKey)) {
          state.signalKeys.add(signalKey);
          send('ux_signal', {
            interaction_type: 'dead_click',
            target: safeText(target.tagName, 20).toLowerCase(),
            ...signalSectionPayload(),
          });
        }
      }
    }
  };

  const sendAbandonment = () => {
    const section = currentSectionDescriptor();
    send('scroll_abandonment', {
      section_key: section?.key || 'unknown',
      section_label: section?.label || 'Unknown region',
      max_scroll_velocity: Math.round(state.maxScrollVelocity),
      max_reverse_scroll_velocity: Math.round(state.maxReverseScrollVelocity),
    });
  };

  const sendSummary = () => {
    send('behavior_summary', {
      focus_loss_count: state.focusLossCount,
      resize_count: state.resizeCount,
      orientation_change_count: state.orientationChangeCount,
      max_scroll_velocity: Math.round(state.maxScrollVelocity),
      max_reverse_scroll_velocity: Math.round(state.maxReverseScrollVelocity),
    });
  };

  const sendFcp = (value) => {
    if (state.fcpSent || value == null || !Number.isFinite(Number(value))) return;
    state.fcpSent = true;
    send('performance_metric', { metric_name: 'fcp_ms', metric_value: Math.round(Number(value)) });
  };

  const currentInpEstimate = () => {
    const values = Array.from(state.inpByInteraction.values()).filter((value) => Number.isFinite(value));
    if (!values.length) return null;
    values.sort((a, b) => a - b);
    const index = Math.min(values.length - 1, Math.max(0, Math.ceil(values.length * 0.98) - 1));
    return values[index];
  };

  const sendInp = () => {
    const value = currentInpEstimate();
    if (value == null) return;
    const rounded = Math.round(value);
    if (state.inpSentValue === rounded) return;
    state.inpSentValue = rounded;
    send('performance_metric', { metric_name: 'inp_ms', metric_value: rounded });
  };

  const bindPerformance = () => {
    try {
      const fcp = win.performance?.getEntriesByName?.('first-contentful-paint')?.[0];
      if (fcp) sendFcp(fcp.startTime);
    } catch (_) {}

    if (!win.PerformanceObserver) return;

    try {
      const paintObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.name === 'first-contentful-paint') sendFcp(entry.startTime);
        }
      });
      paintObserver.observe({ type: 'paint', buffered: true });
      state.paintObserver = paintObserver;
    } catch (_) {}

    try {
      const eventObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          const id = Number(entry.interactionId || 0);
          if (!id) continue;
          const duration = Number(entry.duration || 0);
          state.inpByInteraction.set(id, Math.max(state.inpByInteraction.get(id) || 0, duration));
        }
      });
      eventObserver.observe({ type: 'event', buffered: true, durationThreshold: 40 });
      state.eventObserver = eventObserver;
    } catch (_) {}

    state.performanceTimer = win.setInterval(sendInp, 15000);
  };

  const flushContext = ({ abandonment = false } = {}) => {
    tickArticleRegion();
    flushAttention();
    sendInp();
    sendSummary();
    if (abandonment) sendAbandonment();
  };

  state.setContext = (next) => {
    const nextSignature = String(next?.signature || '');
    if (nextSignature === state.signature) {
      state.page = String(next?.page || state.page).slice(0, 64);
      state.articleSlug = String(next?.articleSlug || state.articleSlug).slice(0, 160);
      scheduleRefresh();
      return;
    }

    flushContext({ abandonment: true });
    state.page = String(next?.page || 'home').slice(0, 64);
    state.articleSlug = String(next?.articleSlug || '').slice(0, 160);
    state.signature = nextSignature;
    state.contextStartedPerf = nowPerf();
    state.sectionRecords.clear();
    state.elementRecords.clear();
    state.firstInteractionSent = false;
    state.firstInteractionType = null;
    state.focusLossCount = 0;
    state.resizeCount = 0;
    state.orientationChangeCount = 0;
    state.maxScrollVelocity = 0;
    state.maxReverseScrollVelocity = 0;
    state.lastScrollY = Number(win.scrollY || 0);
    state.lastScrollAt = nowPerf();
    state.recentClicks = [];
    state.signalKeys.clear();
    state.currentArticleRegionKey = null;
    state.currentArticleRegionAt = null;
    state.currentArticleRegionSeen.clear();
    scheduleRefresh();
  };

  const boot = () => {
    if (!win.__jairAnalyticsSend) {
      state.bootTimer = win.setTimeout(boot, 100);
      return;
    }

    refreshObservers();
    bindPerformance();

    state.mutationObserver = new MutationObserver(scheduleRefresh);
    const site = doc.querySelector('.site') || doc.body;
    if (site) state.mutationObserver.observe(site, { childList: true, subtree: true });

    state.flushTimer = win.setInterval(flushAttention, 15000);
    state.articleTimer = win.setInterval(tickArticleRegion, 750);

    win.addEventListener('scroll', handleScroll, { passive: true });
    win.addEventListener('pointerdown', () => recordFirstInteraction('pointer'), { passive: true, capture: true });
    win.addEventListener('keydown', () => recordFirstInteraction('keyboard'), { capture: true });
    win.addEventListener('click', handleClick, { capture: true });

    doc.addEventListener('visibilitychange', () => {
      const at = nowPerf();
      if (doc.visibilityState === 'hidden') {
        state.focusLossCount += 1;
        for (const record of state.sectionRecords.values()) accrueSection(record, at);
        for (const record of state.elementRecords.values()) accrueElement(record, at);
      } else {
        for (const record of state.sectionRecords.values()) {
          if (record.isVisible) record.visibleSince = at;
        }
        for (const record of state.elementRecords.values()) {
          if (record.isVisible) record.visibleSince = at;
        }
        state.currentArticleRegionAt = at;
      }
    });

    win.addEventListener('resize', () => {
      state.resizeCount += 1;
      scheduleRefresh();
    }, { passive: true });

    try {
      win.screen?.orientation?.addEventListener?.('change', () => {
        state.orientationChangeCount += 1;
        scheduleRefresh();
      });
    } catch (_) {}

    win.addEventListener('error', (event) => {
      const type = safeText(event?.error?.name || (event?.target !== win ? 'ResourceError' : 'Error'), 64);
      send('ux_signal', {
        interaction_type: 'js_error',
        error_type: type || 'Error',
        ...signalSectionPayload(),
      });
    }, true);

    win.addEventListener('unhandledrejection', (event) => {
      const type = safeText(event?.reason?.name || event?.reason?.constructor?.name || 'PromiseRejection', 64);
      send('ux_signal', {
        interaction_type: 'promise_rejection',
        error_type: type || 'PromiseRejection',
        ...signalSectionPayload(),
      });
    });

    win.addEventListener('pagehide', () => {
      flushContext({ abandonment: true });
    });
  };

  boot();
}
"""


_behavior_component = st.components.v2.component(
    "careersite_behavior_telemetry_v5",
    html="<span hidden aria-hidden='true'></span>",
    css=":host { display:none !important; width:0 !important; height:0 !important; }",
    js=BEHAVIOR_TELEMETRY_JS,
)


def mount_behavior_telemetry(page: str, article: object | None = None) -> None:
    """Mount the invisible Components-v2 behavioral telemetry collector."""
    slug = str(getattr(article, "slug", "") or "")[:160]
    _behavior_component(
        key="careersite_behavior_telemetry",
        data={"page": str(page)[:64], "article_slug": slug},
    )
