"""Privacy controls: default-off statistics, minimal payload and no forced read attestation."""
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

    def test_legacy_optional_collectors_are_not_mounted(self):
        main = (ROOT / "main.py").read_text()
        self.assertIn('inject_analytics(PAGE, source="streamlit")', main)
        self.assertNotIn("mount_behavior_telemetry(PAGE", main)
        self.assertNotIn("inject_article_analytics(PAGE", main)
        self.assertNotIn("inject_weekly_audio_telemetry()", main)

    def test_notice_is_concise_and_supports_changing_choice(self):
        notice = (ROOT / "src/page_public_services.py").read_text().split("def privacy() -> str:", 1)[1]
        self.assertIn("data-jair-privacy-settings", notice)
        self.assertIn("Last updated: 20 November 2026", notice)
        self.assertIn("after 90 days", notice)
        self.assertIn("United States", notice)
        self.assertNotIn("answer records remain private", notice.lower())

    @unittest.skipUnless(shutil.which("node"), "Node is required for browser execution")
    def test_browser_is_default_off_and_opted_in_events_are_minimal(self):
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
for (const field of ['device_type','browser_family','hover_ms','attention_ms',
                      'session_elapsed_ms','page_engaged_ms','scroll_depth','referrer_host']) {
  assert.equal(Object.hasOwn(view,field),false,field+' should not be collected');
}
choice.set('jair_statistics_choice_v1','no');
vm.runInContext(SCRIPT,sandbox);
win.__jairAnalyticsSend('page_view');
assert.equal(events.filter(x=>x.event_name==='page_view').length,1,'opt-out did not stop tracking');
console.log('Privacy controls verified');
""".replace("SCRIPT", json.dumps(script))
        result = subprocess.run(["node", "-e", harness], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Privacy controls verified", result.stdout)


if __name__ == "__main__":
    unittest.main()
