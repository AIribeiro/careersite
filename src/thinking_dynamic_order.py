"""Hourly browser-side ordering of the three Thinking landing collections.

Read-only public RPC returns three aggregate article-view metric vectors.
The client compares the hour, then calendar periods to break ties, and moves
the EXISTING section nodes while preserving event wiring, content and anchors.
Runs on initial load, on each clock-hour boundary and when the tab returns.
No visitor identifiers, per-article data or third-party tracking are sent.
"""

from __future__ import annotations

import json

import streamlit.components.v1 as components

from site_analytics import ANALYTICS_PUBLISHABLE_KEY, ANALYTICS_URL


def mount_thinking_hourly_order() -> None:
    """Mount a small iframe controller, consistent with existing site analytics."""
    endpoint = ANALYTICS_URL.rstrip("/") + "/rest/v1/rpc/careersite_thinking_rank_windows_v2"
    script = r"""
<script>
(() => {
  const win = window.parent;
  const doc = win.document;
  const endpoint = __ENDPOINT__;
  const key = __KEY__;
  const kinds = ['weekly_ai', 'briefings', 'articles'];
  // Lexicographic priority. These are Stockholm calendar periods except
  // for the rolling last hour. Do not sum overlapping calendar windows.
  const metrics = [
    'last_hour', 'today', 'yesterday', 'this_week',
    'last_week', 'this_month', 'last_month', 'this_year'
  ];
  const selectors = {
    weekly_ai: '#weekly-ai',
    briefings: '#thinking-briefings',
    articles: '#thinking-articles',
  };

  // Streamlit reruns can remount this iframe; stop the previous controller.
  if (win.__jairThinkingOrderV1 && typeof win.__jairThinkingOrderV1.dispose === 'function') {
    win.__jairThinkingOrderV1.dispose();
  }
  let stopped = false;
  let timer = null;
  let inFlight = null;
  let lastHourSlot = -1;

  const isLanding = () => {
    const params = new URLSearchParams(win.location.search);
    return params.get('page') === 'thinking' && !params.get('article') &&
      params.get('weekly_ai') !== 'archive';
  };
  const main = () => {
    const all = doc.querySelectorAll('.site main');
    for (let i = all.length - 1; i >= 0; i--) {
      if (all[i].querySelector('#thinking-briefings') && all[i].querySelector('#thinking-articles')) {
        return all[i];
      }
    }
    return null;
  };
  // Retain the element under the reader's eye when moving long sections.
  const reorder = (ordered) => {
    const root = main();
    if (!root) return false;
    const nodes = ordered.map(kind => root.querySelector(selectors[kind])).filter(Boolean);
    if (nodes.length < 2) return false;
    const parent = nodes[0].parentNode;
    if (!nodes.every(node => node.parentNode === parent)) return false;
    // The Premium Reader invitation is a fixed part of Thinking, not a
    // collection to rank. Anchor the editorial group immediately after it,
    // including when Streamlit restores the DOM or analytics is unavailable.
    const fixedReader = root.querySelector('#premium-reader-library');
    if (!fixedReader || fixedReader.parentNode !== parent) return false;
    const currently = Array.from(parent.children).filter(node => nodes.includes(node));
    if (currently.every((node, i) => node === nodes[i]) &&
        fixedReader.nextElementSibling === nodes[0]) return true;

    const observed = doc.elementFromPoint(
      Math.floor(win.innerWidth / 2), Math.floor(win.innerHeight / 2)
    );
    const inMovedSection = observed && nodes.some(node => node.contains(observed));
    const offset = inMovedSection ? observed.getBoundingClientRect().top : 0;
    const marker = doc.createComment('thinking-collection-order');
    parent.insertBefore(marker, fixedReader.nextSibling);
    nodes.forEach(node => parent.insertBefore(node, marker));
    marker.remove();
    if (inMovedSection && observed.isConnected) {
      const delta = observed.getBoundingClientRect().top - offset;
      if (Math.abs(delta) > 1) win.scrollBy(0, delta);
    }
    return true;
  };

  const waitForDOM = (ordered, remaining) => {
    if (stopped || !isLanding()) return;
    if (reorder(ordered)) return;
    if (remaining > 0) win.setTimeout(() => waitForDOM(ordered, remaining - 1), 250);
  };

  const schedule = () => {
    if (timer !== null) win.clearTimeout(timer);
    if (stopped) return;
    const untilHour = 3600000 - (Date.now() % 3600000) + 1500;
    timer = win.setTimeout(refresh, Math.max(1500, untilHour));
  };

  const refresh = async () => {
    if (stopped) return;
    if (!isLanding()) { controller.dispose(); return; }
    if (doc.hidden) { schedule(); return; }
    const slot = Math.floor(Date.now() / 3600000);
    const request = new win.AbortController();
    inFlight = request;
    try {
      const response = await win.fetch(endpoint, {
        method: 'GET',
        mode: 'cors',
        credentials: 'omit',
        cache: 'no-store',
        headers: { apikey: key, Authorization: 'Bearer ' + key, Accept: 'application/json' },
        signal: request.signal
      });
      if (!response.ok) throw new Error('Aggregate readership unavailable');
      const rows = await response.json();
      if (!Array.isArray(rows) || rows.length !== 3) throw new Error('Invalid readership response');
      const counts = new Map();
      for (const row of rows) {
        if (!kinds.includes(row.section_key) || counts.has(row.section_key)) {
          throw new Error('Invalid section key');
        }
        const vector = {};
        for (const metric of metrics) {
          if (row[metric] === null || row[metric] === undefined || row[metric] === '') {
            throw new Error('Missing readership metric');
          }
          const value = Number(row[metric]);
          if (!Number.isSafeInteger(value) || value < 0) {
            throw new Error('Invalid readership metric');
          }
          vector[metric] = value;
        }
        counts.set(row.section_key, vector);
      }
      if (counts.size !== 3) throw new Error('Missing section counts');
      // Compare one period at a time. The next period is considered only
      // if the previous period is tied, including the all-zero case.
      const sorted = [...kinds].sort((a, b) => {
        for (const metric of metrics) {
          const difference = counts.get(b)[metric] - counts.get(a)[metric];
          if (difference !== 0) return difference;
        }
        return kinds.indexOf(a) - kinds.indexOf(b);
      });
      if (stopped || !isLanding()) return;
      waitForDOM(sorted, 24);
      lastHourSlot = slot;
    } catch (err) {
      if (stopped || request.signal.aborted) return;
      waitForDOM(kinds, 24);
    } finally {
      if (inFlight === request) inFlight = null;
      schedule();
    }
  };

  const onVisibility = () => {
    if (stopped || doc.hidden || !isLanding()) return;
    if (Math.floor(Date.now() / 3600000) !== lastHourSlot) {
      if (timer !== null) win.clearTimeout(timer);
      refresh();
    }
  };
  const controller = {
    dispose: () => {
      stopped = true;
      if (timer !== null) win.clearTimeout(timer);
      if (inFlight) inFlight.abort();
      doc.removeEventListener('visibilitychange', onVisibility);
    }
  };
  win.__jairThinkingOrderV1 = controller;
  doc.addEventListener('visibilitychange', onVisibility);
  refresh();
})();
</script>
"""
    script = script.replace("__ENDPOINT__", json.dumps(endpoint))
    script = script.replace("__KEY__", json.dumps(ANALYTICS_PUBLISHABLE_KEY))
    components.html(script, height=0, width=0)
