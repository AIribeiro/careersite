const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');

// Run the actual script emitted by inject_live_home_update(), with a small
// mocked DOM and two published CMS records. No external services are called.
const html = fs.readFileSync(0, 'utf8');
const match = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(match, 'Injected live feed script must exist');
const elements = {
  '[data-news-meta]': {textContent: ''},
  '[data-news-title]': {textContent: ''},
  '[data-news-summary]': {textContent: ''},
  '[data-news-link]': {
    href: '', textContent: '', attrs: {},
    setAttribute(key, value) {this.attrs[key] = value;}
  },
};
const root = {querySelector(selector){return elements[selector] || null;}};
const listeners = {};
const doc = {
  visibilityState: 'visible',
  querySelector(selector){return selector === '#home-whats-new' ? root : null;},
  addEventListener(event, callback){listeners[event] = callback;},
};
const requests = [];
let intervalMs;
globalThis.window = {parent: {document: doc}, addEventListener() {}};
globalThis.fetch = async (url, opts) => {
  requests.push({url, opts});
  return {ok: true, async json() {return [
    {
      title: 'Older article', slug: 'older-article',
      kind: 'Article', published_at: '2026-10-01T00:00:00+00:00'
    },
    {
      title: 'AI Adoption Is Not One Problem: Four Leadership Responses',
      slug: 'ai-adoption-four-leadership-responses',
      kind: 'Executive Briefing', published_at: '2026-11-04T12:40:21.959975+00:00',
      subtitle: 'Four separate leadership decisions.'
    }
  ];}};
};
globalThis.setTimeout = () => 1;
globalThis.clearTimeout = () => {};
globalThis.setInterval = (_callback, ms) => {intervalMs = ms; return 2;};
globalThis.AbortController = class {signal = {}; abort() {}};
vm.runInThisContext(match[1]);
setImmediate(() => {
  try {
    assert.equal(requests.length, 1, 'Must fetch immediately on page load');
    assert.match(requests[0].url, /status=eq\.published/);
    assert.equal(elements['[data-news-meta]'].textContent.startsWith('Executive briefing · '), true);
    assert.equal(elements['[data-news-title]'].textContent,
      'AI Adoption Is Not One Problem: Four Leadership Responses');
    assert.equal(elements['[data-news-summary]'].textContent, 'Four separate leadership decisions.');
    assert.equal(elements['[data-news-link]'].href,
      '?page=briefing&article=ai-adoption-four-leadership-responses');
    assert.equal(elements['[data-news-link]'].textContent, 'Read the briefing →');
    assert.equal(elements['[data-news-link]'].attrs['data-hq-content-type'], 'briefing');
    assert.equal(intervalMs, 120000);
    assert.equal(typeof listeners.visibilitychange, 'function');
    process.stdout.write('Executive Briefing automatic homepage refresh: passed\n');
  } catch (err) {
    console.error(err);
    process.exitCode = 1;
  }
});
