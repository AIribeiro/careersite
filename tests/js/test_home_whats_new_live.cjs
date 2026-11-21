const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');

// Run the actual script emitted by inject_live_home_update(), with a small
// mocked DOM and two published CMS records. No external services are called.
const html = fs.readFileSync(0, 'utf8');
// The local published release advances during November; a fixed November 18
// mock eventually becomes older than the site's first frame. Keep the new
// fixture newer than that actual baseline without changing production code.
const baselineLiteral = html.match(/const localPublished = Date\.parse\(("[^"]+")\);/);
assert.ok(baselineLiteral, 'Injected script must declare the local release time');
const localTime = Date.parse(JSON.parse(baselineLiteral[1]));
assert.ok(Number.isFinite(localTime), 'Local release timestamp must be valid');
const publishedAt = new Date(Math.max(localTime, Date.parse('2026-11-18T12:40:21Z')) + 3600000).toISOString();
const revisedAt = new Date(Date.parse(publishedAt) + 30 * 60000).toISOString();
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
// The first CMS response arrives while the announcement is visible.
const bounds = {top: 110, bottom: 350};
const root = {
  querySelector(selector){return elements[selector] || null;},
  getBoundingClientRect(){return bounds;}
};
const listeners = {};
const doc = {
  visibilityState: 'visible',
  querySelector(selector){return selector === '#home-whats-new' ? root : null;},
  addEventListener(event, callback){listeners[event] = callback;},
};
const requests = [];
let intervalMs;
let refreshInterval;
globalThis.window = {parent: {document: doc, innerHeight: 850}, addEventListener() {}};
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
      kind: 'Executive Briefing', published_at: publishedAt,
      updated_at: requests.length > 1 ? revisedAt : publishedAt,
      subtitle: requests.length > 1
        ? 'The updated decision framework and practical considerations.'
        : 'Four separate leadership decisions.'
    }
  ];}};
};
globalThis.setTimeout = () => 1;
globalThis.clearTimeout = () => {};
globalThis.setInterval = (callback, ms) => {intervalMs = ms; refreshInterval = callback; return 2;};
globalThis.AbortController = class {signal = {}; abort() {}};
// Clock is fixed so future CMS issues can be tested against a published
// November 17 market research edition, irrespective of CI wall-clock time.
Date.now = () => Date.parse(revisedAt) + 3600000;
vm.runInThisContext(match[1]);
setImmediate(async () => {
  try {
    assert.equal(requests.length, 1, 'Must fetch immediately on page load');
    assert.equal(elements['[data-news-title]'].textContent,
      'AI Adoption Is Not One Problem: Four Leadership Responses',
      'The latest publication should be visible immediately, even when the strip is onscreen');
    assert.equal(elements['[data-news-meta]'].textContent.startsWith('Executive briefing · '), true);
    bounds.top = 1350;
    bounds.bottom = 1600;
    await refreshInterval();
    assert.match(requests[0].url, /status=eq\.published/);
    assert.match(requests[0].url, /updated_at/);
    assert.equal(elements['[data-news-meta]'].textContent.startsWith('Updated executive briefing · '), true);
    assert.equal(elements['[data-news-title]'].textContent,
      'AI Adoption Is Not One Problem: Four Leadership Responses');
    assert.equal(elements['[data-news-summary]'].textContent, 'The updated decision framework and practical considerations.');
    assert.equal(elements['[data-news-link]'].href,
      '?page=briefing&article=ai-adoption-four-leadership-responses');
    assert.equal(elements['[data-news-link]'].textContent, 'Read the briefing →');
    assert.equal(elements['[data-news-link]'].attrs['data-hq-content-type'], 'briefing');
    assert.equal(requests.length, 2, 'Should refresh only when the next scheduled check runs');
    assert.equal(intervalMs, 120000);
    assert.equal(typeof listeners.visibilitychange, 'function');
    process.stdout.write('Executive Briefing publication and revision homepage refresh: passed\n');
  } catch (err) {
    console.error(err);
    process.exitCode = 1;
  }
});
