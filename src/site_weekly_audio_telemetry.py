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

  const STORAGE_KEY = 'jair_hq_weekly_audio_v1';
  const SESSION_KEY = 'jair_hq_session_v1';
  const mediaState = new WeakMap();
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
    if (!win.__jairAnalyticsSend) return;
    win.__jairAnalyticsSend(name, {
      element_key: milestone || null,
      element_placement: 'thinking:weekly-ai-audio',
      element_label: 'WEEKLY AI audio · ' + slug,
      attention_ms: Math.max(0, Math.min(86400000, Math.round(listenedMs || 0)))
    });
  };
  const now = () => (win.performance ? win.performance.now() : Date.now());
  const sync = (audio, slug, countMedia) => {
    const live = mediaState.get(audio) || { lastPosition: null, lastTick: null };
    const clock = now();
    const position = Number(audio.currentTime);
    const store = getStore();
    const state = store.editions[slug] || {
      started: false, listenedMs: 0, milestones: {}, completed: false
    };
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
          state.milestones[percent] = true;
          record(slug, 'audio_progress', String(percent), state.listenedMs);
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
    const state = sync(item.audio, item.slug, false);
    if (!state.started) {
      state.started = true;
      const store = getStore();
      store.editions[item.slug] = state;
      persist(store);
      record(item.slug, 'audio_start', 'start', state.listenedMs);
    }
  }, true);

  doc.addEventListener('timeupdate', event => {
    const item = mediaFor(event);
    if (item) sync(item.audio, item.slug, true);
  }, true);

  for (const name of ['seeking', 'seeked', 'pause', 'ratechange']) {
    doc.addEventListener(name, event => {
      const item = mediaFor(event);
      if (item) sync(item.audio, item.slug, false);
    }, true);
  }

  doc.addEventListener('ended', event => {
    const item = mediaFor(event);
    if (!item) return;
    const state = sync(item.audio, item.slug, true);
    const durationMs = Number.isFinite(item.audio.duration) ? item.audio.duration * 1000 : 0;
    // Completion requires both natural 'ended' and substantial measured playback.
    if (state.started && !state.completed && durationMs > 0
        && state.listenedMs >= durationMs * 0.85) {
      state.completed = true;
      const store = getStore();
      store.editions[item.slug] = state;
      persist(store);
      record(item.slug, 'audio_complete', 'ended', state.listenedMs);
    }
  }, true);
})();
</script>
"""
    components.html(script, height=0, width=0)
