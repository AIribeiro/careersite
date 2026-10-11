"""Client-side weekly audio listening telemetry using the existing first-party session.

No new cookies, identifiers, replay logs or separate page views. Milestones
measure cumulative media actually advanced while playback was active, not
the player's seek position. Events are session+edition unique across reruns.
"""
from __future__ import annotations

import streamlit.components.v1 as components


def inject_weekly_audio_telemetry() -> None:
    script = r"""
<script>
(() => {
  const win = window.parent;
  const doc = win.document;
  if (win.__jairWeeklyAudioTelemetryBound) return;
  win.__jairWeeklyAudioTelemetryBound = true;

  // Version 2 discards optimistic flags from the pre-acknowledgement client.
  const STORAGE_KEY = 'jair_hq_weekly_audio_v2';
  const SESSION_KEY = 'jair_hq_session_v1';
  const mediaState = new WeakMap();
  // Keep retries in memory; accepted milestones alone are saved in the current
  // browser session. This prevents failed requests being mistaken for listens.
  const pending = new Set();
  const retryAfter = new Map();
  const validSlug = /^weekly-ai-\d{4}-\d{2}-\d{2}$/;
  const mediaFor = (event) => {
    const audio = event.target;
    if (!audio || audio.tagName !== 'AUDIO') return null;
    const slug = String(audio.getAttribute('data-weekly-ai-audio') || '');
    return validSlug.test(slug) ? { audio, slug } : null;
  };
  const getStore = () => {
    const session = win.sessionStorage.getItem(SESSION_KEY) || '';
    let data = null;
    try { data = JSON.parse(win.sessionStorage.getItem(STORAGE_KEY) || 'null'); } catch (_) {}
    if (!data || data.session !== session) data = { session, editions: {} };
    return data;
  };
  const persist = (store) => {
    try { win.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(store)); } catch (_) {}
  };
  const record = (slug, name, milestone, listenedMs) => {
    if (typeof win.__jairAnalyticsSend !== 'function') return Promise.resolve(false);
    return Promise.resolve(win.__jairAnalyticsSend(name, {
      element_key: milestone || null,
      element_placement: 'thinking:weekly-ai-audio',
      element_label: 'WEEKLY AI audio · ' + slug,
      attention_ms: Math.max(0, Math.min(86400000, Math.round(listenedMs || 0)))
    })).then(ok => ok === true).catch(() => false);
  };
  const now = () => (win.performance ? win.performance.now() : Date.now());
  const freshState = () => ({
    started: false, listenedMs: 0, milestones: {}, completed: false
  });
  const recordOnce = (slug, marker, name, milestone, listenedMs) => {
    const key = slug + ':' + marker;
    if (pending.has(key) || now() < (retryAfter.get(key) || 0)) return;
    if (typeof win.__jairAnalyticsSend !== 'function') {
      retryAfter.set(key, now() + 1000);
      return;
    }
    const session = getStore().session;
    pending.add(key);
    record(slug, name, milestone, listenedMs).then(ok => {
      pending.delete(key);
      if (!ok) {
        retryAfter.set(key, now() + 5000);
        return;
      }
      const store = getStore();
      if (store.session !== session) return;
      const state = store.editions[slug] || freshState();
      if (marker === 'started') state.started = true;
      else if (marker === 'completed') state.completed = true;
      else if (marker === 'checkpoint') {
        state.lastCheckpointMs = Math.max(state.lastCheckpointMs || 0, listenedMs);
      } else if (marker.startsWith('milestone:')) {
        state.milestones[Number(milestone)] = true;
      }
      store.editions[slug] = state;
      persist(store);
    });
  };
  const tryStart = (audio, slug) => {
    if (audio.paused || audio.ended) return;
    const state = getStore().editions[slug] || freshState();
    if (!state.started) recordOnce(slug, 'started', 'audio_start', 'start', state.listenedMs);
  };
  const sync = (audio, slug, countMedia) => {
    const live = mediaState.get(audio) || { lastPosition: null, lastTick: null };
    const clock = now();
    const position = Number(audio.currentTime);
    const store = getStore();
    const state = store.editions[slug] || freshState();
    if (countMedia && live.lastPosition !== null && live.lastTick !== null
        && Number.isFinite(position) && !audio.seeking && !audio.paused) {
      const elapsed = Math.max(0, (clock - live.lastTick) / 1000);
      const advance = position - live.lastPosition;
      const speed = Math.min(2, Math.max(0.5, Number(audio.playbackRate) || 1));
      // Do not reward dragging the seek bar, clock changes or data jumps.
      if (advance > 0 && advance <= elapsed * speed + 0.7 && elapsed < 65) {
        const duration = Number.isFinite(audio.duration) && audio.duration > 0
          ? audio.duration : 0;
        state.listenedMs = Math.min(
          duration ? duration * 1000 : 86400000,
          Math.max(0, state.listenedMs || 0) + advance * 1000
        );
      }
    }
    live.lastPosition = position;
    live.lastTick = clock;
    mediaState.set(audio, live);

    const durationMs = Number.isFinite(audio.duration) && audio.duration > 0
      ? audio.duration * 1000 : 0;
    if (durationMs > 0 && state.started) {
      [25, 50, 75].forEach(percent => {
        if (!state.milestones[percent] && state.listenedMs >= durationMs * percent / 100) {
          recordOnce(slug, 'milestone:' + percent, 'audio_progress',
            String(percent), state.listenedMs);
        }
      });
    }
    store.editions[slug] = state;
    persist(store);
    return state;
  };

  doc.addEventListener('playing', event => {
    const item = mediaFor(event);
    if (!item) return;
    sync(item.audio, item.slug, false);
    tryStart(item.audio, item.slug);
  }, true);

  doc.addEventListener('timeupdate', event => {
    const item = mediaFor(event);
    if (item) {
      sync(item.audio, item.slug, true);
      // Also recover a start when playback began before the analytics sender
      // was mounted, or the previous collector request failed.
      tryStart(item.audio, item.slug);
    }
  }, true);

  for (const name of ['seeking', 'seeked', 'ratechange']) {
    doc.addEventListener(name, event => {
      const item = mediaFor(event);
      if (item) sync(item.audio, item.slug, false);
    }, true);
  }

  // A single checkpoint after a meaningful partial listen keeps listening
  // minutes accurate even when a visitor stops between quarter milestones.
  doc.addEventListener('pause', event => {
    const item = mediaFor(event);
    if (!item) return;
    const state = sync(item.audio, item.slug, false);
    if (!item.audio.ended && state.started &&
        state.listenedMs - (state.lastCheckpointMs || 0) >= 5000) {
      recordOnce(item.slug, 'checkpoint', 'audio_progress',
        'checkpoint', state.listenedMs);
    }
  }, true);

  doc.addEventListener('ended', event => {
    const item = mediaFor(event);
    if (!item) return;
    const state = sync(item.audio, item.slug, true);
    const durationMs = Number.isFinite(item.audio.duration) ? item.audio.duration * 1000 : 0;
    // Completion requires both natural 'ended' and substantial measured playback.
    if (state.started && !state.completed && durationMs > 0
        && state.listenedMs >= durationMs * 0.85) {
      recordOnce(item.slug, 'completed', 'audio_complete', 'ended', state.listenedMs);
    } else if (state.started && !state.completed && state.listenedMs > 0 &&
               state.listenedMs - (state.lastCheckpointMs || 0) >= 5000) {
      recordOnce(item.slug, 'checkpoint', 'audio_progress',
        'checkpoint', state.listenedMs);
    }
  }, true);
})();
</script>
"""
    components.html(script, height=0, width=0)
