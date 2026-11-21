"""Privacy-first analytics: opt-in rich reporting, aggregate-only basic traffic."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class PrivacyControlsTests(unittest.TestCase):
    def test_modified_modules_parse(self):
        for name in ("src/site_analytics.py", "src/page_public_services.py",
                     "src/page_advisory_portal.py", "src/page_reader_native.py", "main.py"):
            ast.parse((ROOT / name).read_text(encoding="utf-8"), filename=name)

    def test_registration_has_notice_but_no_forced_acknowledgment(self):
        source = (ROOT / "src/page_advisory_portal.py").read_text()
        self.assertIn("PRIVACY_NOTICE_URL", source)
        self.assertIn("https://jairribeiro.com", (ROOT / "src/site_campaign_links.py").read_text())
        self.assertNotIn('st.checkbox("I have read the Privacy & Data notice.")', source)
        self.assertNotIn('"privacy_notice_ack": True', source)

    def test_optional_collectors_mounted_and_individually_consent_gated(self):
        main = (ROOT / "main.py").read_text()
        self.assertIn('inject_analytics(PAGE, source="streamlit")', main)
        self.assertIn("mount_behavior_telemetry(PAGE", main)
        self.assertIn("inject_article_analytics(PAGE", main)
        self.assertIn("inject_weekly_audio_telemetry()", main)
        for module in ("site_article_analytics.py", "site_behavior_telemetry_v2.py",
                       "site_weekly_audio_telemetry.py"):
            source = (ROOT / "src" / module).read_text()
            self.assertIn("jair_statistics_choice_v1", source, module)
            self.assertIn("if (!statisticsAllowed()) return", source, module)
            self.assertIn("const statisticsAllowed =", source, module)

    def test_server_counter_is_separate_from_opt_in_browser_tracking(self):
        server = (ROOT / "src/site_aggregate_traffic.py").read_text()
        self.assertIn("careersite_aggregate_page_load_v1", server)
        self.assertIn("PUBLIC_PAGES", server)
        self.assertNotIn("user_agent", server)
        self.assertNotIn("request.headers", server)
        self.assertNotIn("session_id", server)
        self.assertNotIn("ip_address", server)
        self.assertIn("record_page_load(PAGE", (ROOT / "main.py").read_text())

    def test_basic_page_loads_appear_before_detailed_metric_cards(self):
        source = (ROOT / "src/page_public_portfolio_overview.py").read_text()
        page = source.split("def render_public_portfolio_overview()", 1)[1]
        self.assertEqual(page.count("render_basic_page_loads(str(window))"), 1)
        self.assertLess(
            page.index("render_basic_page_loads(str(window))"),
            page.index("report = _selected_portfolio_report(str(window))"),
        )
        self.assertLess(
            page.index("render_basic_page_loads(str(window))"),
            page.index("st.html(portfolio_metric_grid(cards))"),
        )

    def test_lifetime_report_uses_retained_monthly_counts(self):
        portfolio = (ROOT / "src/page_public_portfolio_overview.py").read_text()
        aggregate = (ROOT / "src/site_aggregate_traffic.py").read_text()
        self.assertIn("monthly_content_rollup()", portfolio)
        self.assertIn('quality["site_views"] = max(', portfolio)
        self.assertIn('quality["article_views"] = max(', portfolio)
        self.assertIn("careersite_analytics_monthly_public_v1", aggregate)
        self.assertIn("careersite_analytics_lifetime_content_public_v1", aggregate)
        self.assertIn("render_monthly_optin_trend()", portfolio)

    def test_notice_is_concise_and_supports_changing_choice(self):
        notice = (ROOT / "src/page_public_services.py").read_text().split("def privacy() -> str:", 1)[1]
        self.assertIn("data-jair-privacy-settings", notice)
        self.assertIn("Last updated: 20 November 2026", notice)
        self.assertIn("after 90 days", notice)
        self.assertIn("United States", notice)
        self.assertNotIn("answer records remain private", notice.lower())

    @unittest.skipUnless(shutil.which("node"), "Node is required for browser execution")
    def test_article_and_audio_do_not_access_storage_before_consent(self):
        from types import SimpleNamespace
        import site_article_analytics
        import site_weekly_audio_telemetry
        article = SimpleNamespace(slug="public-test", title="Public test", kind="Article")
        with patch.object(site_article_analytics.components, "html") as html:
            site_article_analytics.inject_article_analytics("thinking", article)
        article_js = html.call_args.args[0].replace("<script>", "").replace("</script>", "")
        with patch.object(site_weekly_audio_telemetry.components, "html") as html:
            site_weekly_audio_telemetry.inject_weekly_audio_telemetry()
        audio_js = html.call_args.args[0].replace("<script>", "").replace("</script>", "")
        harness = r"""
const vm = require('node:vm');
const assert = require('node:assert/strict');
let browserAccesses = 0, sends = 0;
const win = {
  document: {},
  localStorage: {getItem: () => null},
  sessionStorage: {getItem: () => {browserAccesses++; throw Error('storage');},
                   setItem: () => {browserAccesses++; throw Error('storage');}},
};
const context = vm.createContext({
  window: {parent: win}, URL,
  fetch: () => {sends++; throw Error('network');},
});
vm.runInContext(ARTICLE, context);
vm.runInContext(AUDIO, context);
assert.equal(browserAccesses, 0);
assert.equal(sends, 0);
console.log('Independent collectors default off');
""".replace("ARTICLE", json.dumps(article_js)).replace("AUDIO", json.dumps(audio_js))
        result = subprocess.run(["node", "-"], input=harness, capture_output=True,
                                text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node is required for browser execution")
    def test_browser_is_default_off_and_opted_in_rich_events_are_constrained(self):
        import site_analytics
        with patch.object(site_analytics.components, "html") as html:
            site_analytics.inject_analytics("home")
        script = html.call_args.args[0].replace("<script>", "").replace("</script>", "")
        harness = r"""
const vm = require('node:vm');
const assert = require('node:assert/strict');
const choice = new Map(), temporary = new Map(), events = [], installed = [];
const doc = {
  referrer:'', readyState:'complete', visibilityState:'visible',
  documentElement:{clientWidth:1200, clientHeight:800, scrollHeight:1600},
  body:{appendChild:x=>installed.push(x)},
  getElementById:()=>null,
  createElement:()=>({style:{},setAttribute:()=>{},addEventListener:()=>{},
                     querySelector:()=>({textContent:''}),remove:()=>{}}),
  querySelector:()=>null, addEventListener:()=>{},
};
const win = {
  document:doc,
  location:{href:'https://jairribeiro-ai.streamlit.app/?page=home',
            hostname:'jairribeiro-ai.streamlit.app',origin:'https://jairribeiro-ai.streamlit.app',
            reload:()=>{}},
  navigator:{userAgent:'Chrome/123',platform:'Linux',language:'en'},
  innerWidth:1200, innerHeight:800, scrollY:0,
  performance:{now:()=>1000},
  crypto:{randomUUID:()=> 'aaaaaaaa-2222-4444-8888-aaaaaaaaaaaa'},
  localStorage:{getItem:k=>choice.get(k)||null,setItem:(k,v)=>choice.set(k,v)},
  sessionStorage:{getItem:k=>temporary.get(k)||null,
                  setItem:(k,v)=>temporary.set(k,v),
                  removeItem:k=>temporary.delete(k)},
  setTimeout:()=>{},setInterval:()=>{},addEventListener:()=>{},dispatchEvent:()=>{}
};
win.top=win;
const sandbox=vm.createContext({window:{parent:win},URL,Intl,Date,CustomEvent:class {},
  fetch:(url,options)=>{events.push(JSON.parse(options.body));return Promise.resolve({ok:true})}});
vm.runInContext(SCRIPT,sandbox);
assert.equal(events.length,0,'statistics sent before consent');
assert.equal(temporary.size,0,'analytics session storage before consent');
assert.equal(installed.length,1,'statistics choice must be visible');
choice.set('jair_statistics_choice_v1','yes');
vm.runInContext(SCRIPT,sandbox);
assert.equal(events.filter(x=>x.event_name==='page_view').length,1);
const view=events.find(x=>x.event_name==='page_view');
for (const field of ['device_type','browser_family','os_family',
                      'session_elapsed_ms','page_engaged_ms','scroll_depth']) {
  assert.equal(Object.hasOwn(view,field),true,field+' must be available after consent');
}
for (const field of ['viewport_width','screen_width','hardware_concurrency',
                      'device_memory_gb','timezone','referrer_host']) {
  assert.equal(Object.hasOwn(view,field),false,field+' should not be collected');
}
win.__jairAnalyticsSend('section_attention', {section_key:'hero',attention_ms:15000});
assert.equal(events.at(-1).event_name,'section_attention');
assert.equal(events.at(-1).attention_ms,15000);
win.__jairAnalyticsSend('audio_complete', {element_key:'ended',attention_ms:80000});
assert.equal(events.at(-1).event_name,'audio_complete');
choice.set('jair_statistics_choice_v1','no');
vm.runInContext(SCRIPT,sandbox);
win.__jairAnalyticsSend('page_view');
assert.equal(events.filter(x=>x.event_name==='page_view').length,1,'opt-out did not stop tracking');
assert.equal(events.at(-1).event_name,'audio_complete','opt-out cannot transmit more events');
console.log('Privacy controls verified');
""".replace("SCRIPT", json.dumps(script))
        result = subprocess.run(["node", "-"], input=harness, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Privacy controls verified", result.stdout)


if __name__ == "__main__":
    unittest.main()
