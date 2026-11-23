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
const marketAt = new Date(Date.parse(revisedAt) + 30 * 60000).toISOString();
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
let cmsCalls = 0;
let marketCalls = 0;
globalThis.fetch = async (url, opts) => {
  requests.push({url, opts});
  if (url.includes('/rpc/portfolio_public_market_release_timestamp_v1')) {
    const call = ++marketCalls;
    return {ok: true, async json() {
      return call > 2 ? {
        type: 'New market review',
        title: 'Swedish AI & Data Market Review',
        description: 'The latest Executive and Jobseeker Editions are available.',
        href: '?page=advisory-market-signals', date: marketAt
      } : null;
    }};
  }
  const call = ++cmsCalls;
  return {ok: true, async json() {return [
    {
      title: 'Older article', slug: 'older-article',
      kind: 'Article', published_at: '2026-10-01T00:00:00+00:00'
    },
    {
      title: 'AI Adoption Is Not One Problem: Four Leadership Responses',
      slug: 'ai-adoption-four-leadership-responses',
      kind: 'Executive Briefing', published_at: publishedAt,
      updated_at: call > 1 ? revisedAt : publishedAt,
      subtitle: call > 1
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
Date.now = () => Date.parse(marketAt) + 3600000;
vm.runInThisContext(match[1]);
setImmediate(async () => {
  try {
    assert.equal(requests.length, 2, 'Must check CMS and approved market metadata immediately');
    assert.equal(elements['[data-news-title]'].textContent,
      'AI Adoption Is Not One Problem: Four Leadership Responses',
      'The latest publication should be visible immediately, even when the strip is onscreen');
    assert.equal(elements['[data-news-meta]'].textContent.startsWith('Executive briefing · '), true);
    bounds.top = 1350;
    bounds.bottom = 1600;
    await refreshInterval();
    assert.match(requests[0].url, /status=eq\.published/);
    assert.match(requests[0].url, /published_at=not.is.null/);
    assert.doesNotMatch(requests[0].url, /updated_at/);
    assert.equal(elements['[data-news-meta]'].textContent.startsWith('Executive briefing · '), true);
    assert.equal(elements['[data-news-summary]'].textContent, 'Four separate leadership decisions.',
      "Editing an already published briefing must not bump its What's New timestamp");
    assert.equal(elements['[data-news-title]'].textContent,
      'AI Adoption Is Not One Problem: Four Leadership Responses');
    // CMS updated_at is deliberately ignored until a new publication is made.
    assert.equal(elements['[data-news-link]'].href,
      '?page=briefing&article=ai-adoption-four-leadership-responses');
    assert.equal(elements['[data-news-link]'].textContent, 'Read the briefing →');
    assert.equal(elements['[data-news-link]'].attrs['data-hq-content-type'], 'briefing');
    assert.equal(requests.length, 4, 'Should check both sources on the next refresh');
    await refreshInterval();
    assert.equal(requests.length, 6, 'Third refresh checks both sources');
    assert.equal(elements['[data-news-meta]'].textContent.startsWith('New market review · '), true);
    assert.equal(elements['[data-news-title]'].textContent, 'Swedish AI & Data Market Review');
    assert.equal(elements['[data-news-summary]'].textContent,
      'The latest Executive and Jobseeker Editions are available.');
    assert.equal(elements['[data-news-link]'].href, '?page=advisory-market-signals');
    assert.equal(elements['[data-news-link]'].attrs['data-hq-content-type'], 'market_signals');
    assert.equal(intervalMs, 120000);
    assert.equal(typeof listeners.visibilitychange, 'function');
    process.stdout.write('Publication-only What's New guardrails and market release: passed\n');
  } catch (err) {
    console.error(err);
    process.exitCode = 1;
  }
});
