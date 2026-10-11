"""Exercise real WEEKLY AI browser event listeners with a minimal Node DOM harness."""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
NODE_HARNESS = r"""
const vm = require('vm');
const assert = require('node:assert/strict');
const listeners = new Map();
const storage = new Map([['jair_hq_session_v1', 'session-a']]);
let clock = 1000;
const events = [];
const win = {
  document: {
    addEventListener(name, fn) {
      const callbacks = listeners.get(name) || [];
      callbacks.push(fn);
      listeners.set(name, callbacks);
    }
  },
  performance: {now: () => clock},
  sessionStorage: {
    getItem: key => storage.get(key) || null,
    setItem: (key, value) => storage.set(key, value),
  },
};
const context = {window: {parent: win}, Promise, Number, Math, Date, Map, WeakMap, Set, JSON};
vm.runInNewContext(__SCRIPT__, context, {filename:'weekly_audio_telemetry.js'});
const audio = {
  tagName: 'AUDIO',
  paused: false,
  ended: false,
  seeking: false,
  currentTime: 0,
  duration: 100,
  playbackRate: 1,
  getAttribute(name) {
    return name === 'data-weekly-ai-audio' ? 'weekly-ai-2026-10-11' : null;
  },
};
const emit = name => {
  const callbacks = listeners.get(name) || [];
  for (const callback of callbacks) callback({target: audio});
};
const state = () => JSON.parse(storage.get('jair_hq_weekly_audio_v1')).editions['weekly-ai-2026-10-11'];
const tick = async (time) => {
  clock = 1000 + time * 1000;
  audio.currentTime = time;
  emit('timeupdate');
  await new Promise(setImmediate);
};
(async () => {
  // Explicit regression: a 'playing' event before the shared sender mounts
  // must NOT permanently claim a listener in session storage.
  emit('playing');
  assert.equal(state().started, false);
  assert.equal(events.length, 0);
  win.__jairAnalyticsSend = (name, payload) => {
    events.push({name, payload});
    return Promise.resolve(true);
  };
  await tick(2);
  assert.equal(state().started, true);
  assert.equal(events.filter(e=>e.name==='audio_start').length, 1);
  await tick(27);
  await tick(52);
  await tick(78);
  await tick(95);
  audio.paused = true; audio.ended = true;
  emit('ended');
  await new Promise(setImmediate);
  assert.equal(events.filter(e=>e.name==='audio_progress' && e.payload.element_key==='25').length, 1);
  assert.equal(events.filter(e=>e.name==='audio_progress' && e.payload.element_key==='50').length, 1);
  assert.equal(events.filter(e=>e.name==='audio_progress' && e.payload.element_key==='75').length, 1);
  assert.equal(events.filter(e=>e.name==='audio_complete').length, 1);
  emit('ended'); await new Promise(setImmediate);
  assert.equal(events.filter(e=>e.name==='audio_complete').length, 1, 'completed event must be unique');

  // A new browser session must not inherit the previous edition's starts.
  storage.set('jair_hq_session_v1', 'session-b');
  audio.currentTime = 0;
  audio.ended = false;
  audio.paused = false;
  clock += 6000;
  emit('playing');
  await new Promise(setImmediate);
  assert.equal(state().started, true);
  assert.equal(events.filter(e=>e.name==='audio_start').length, 2);

  // Seeking to the end may not produce completion without actual playback.
  audio.seeking = true;
  audio.currentTime = 99;
  clock += 1000;
  emit('seeking');
  audio.seeking = false;
  emit('seeked');
  emit('timeupdate');
  audio.paused = true; audio.ended = true;
  emit('ended');
  await new Promise(setImmediate);
  assert.equal(events.filter(e=>e.name==='audio_complete').length, 1);
  assert.ok(state().listenedMs < 85000);

  // A third session with a collector rejection must retry instead of being
  // marked as a confirmed listener or creating duplicate starts.
  storage.set('jair_hq_session_v1', 'session-c');
  audio.currentTime = 0; audio.ended = false; audio.paused = false;
  clock += 6000;
  let rejected = false;
  win.__jairAnalyticsSend = (name,payload) => {
    if (name === 'audio_start' && !rejected) {
      rejected = true; return Promise.resolve(false);
    }
    events.push({name,payload}); return Promise.resolve(true);
  };
  emit('playing');
  await new Promise(setImmediate);
  assert.equal(state().started, false);
  clock += 6000;
  audio.currentTime = 5;
  emit('timeupdate');
  await new Promise(setImmediate);
  assert.equal(state().started, true);
  assert.equal(events.filter(e=>e.name==='audio_start').length, 3);
  process.stdout.write('audio playback acknowledgement, progress, seeking, and retry passed');
})().catch(err=>{console.error(err);process.exitCode=1});
"""


class WeeklyAudioDeliveryAcknowledgementTests(unittest.TestCase):
    def test_sender_returns_a_delivery_result(self):
        source = (ROOT / "src" / "site_analytics.py").read_text(encoding="utf-8")
        self.assertIn("return delivery;", source)
        self.assertIn("response.ok", source)
        self.assertIn(".catch(() => false)", source)

    @unittest.skipUnless(shutil.which("node"), "Node not installed")
    def test_playback_and_network_failures(self):
        source = (ROOT / "src" / "site_weekly_audio_telemetry.py").read_text(encoding="utf-8")
        match = re.search(r"<script>(.*?)</script>", source, re.DOTALL)
        self.assertIsNotNone(match)
        script = NODE_HARNESS.replace("__SCRIPT__", json.dumps(match.group(1)))
        result = subprocess.run(
            ["node", "-e", script],
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertIn("acknowledgement", result.stdout)


if __name__ == "__main__":
    unittest.main()
