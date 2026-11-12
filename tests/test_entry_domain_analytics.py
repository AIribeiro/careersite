"""Entry address and referrer classification: browser code, not guessed server host."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class EntryDomainReportTests(unittest.TestCase):
    def test_historical_traffic_is_grouped_into_native_reporting_only(self):
        from page_entry_domain_analytics import entry_domain_rows, source_evidence_rows
        rows = entry_domain_rows({"domains": [
            {"domain_label": "jairribeiro.com", "sessions": 3, "views": 4,
             "verified_views": 4, "assigned_views": 0},
            {"domain_label": "jairribeiro-ai.streamlit.app",
             "sessions": 9, "views": 13, "verified_sessions": 0,
             "assigned_sessions": 9, "assigned_views": 13},
        ]})
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Sessions"], 3)
        self.assertEqual(rows[1]["Sessions"], 9)
        self.assertEqual(rows[1]["Assigned views"], 13)
        self.assertEqual(rows[1]["Assigned sessions"], 9)
        self.assertEqual(source_evidence_rows({"source_evidence": [{
            "domain_label": "jairribeiro-ai.streamlit.app",
            "source_evidence": "Direct / source unknown", "sessions": 9
        }]})[0]["Direct / unknown"], 9)

    @unittest.skipUnless(shutil.which("node"), "Node required for live browser collector contract")
    def test_both_browser_collectors_preserve_masked_entry_evidence(self):
        import site_analytics
        import site_article_analytics

        with patch.object(site_analytics.components, "html") as mock:
            site_analytics.inject_analytics("thinking")
        page_js = mock.call_args.args[0].replace("<script>", "").replace("</script>", "")

        article = SimpleNamespace(slug="test-article", title="Test article",
                                  kind="Article", topic="AI", published_iso="2026-11-12")
        with patch.object(site_article_analytics.components, "html") as mock:
            site_article_analytics.inject_article_analytics("thinking", article)
        article_js = mock.call_args.args[0].replace("<script>", "").replace("</script>", "")

        harness = r"""
const vm = require('node:vm');
const assert = require('node:assert/strict');
function run(host, framed, referrer, ancestors, expectedDomain, expectedEvidence, campaign) {
  const events=[], cache=new Map();
  const doc={
    referrer,visibilityState:'visible',
    documentElement:{clientWidth:1200,clientHeight:800},
    querySelector:()=>null,
    addEventListener:()=>{}
  };
  const url='https://'+host+'/?page=thinking&article=test-article'+(campaign?'&source=linkedin':'');
  const win={
    document:doc,
    location:{href:url,hostname:host,ancestorOrigins:ancestors||[]},
    navigator:{userAgent:'Chrome/123',platform:'Linux',language:'en'},
    innerWidth:1200,innerHeight:800,
    performance:{now:()=>1000},
    crypto:{randomUUID:()=> 'aaaaaaaa-2222-4444-8888-aaaaaaaaaaaa'},
    sessionStorage:{
      getItem:k=>cache.get(k)||null,setItem:(k,v)=>cache.set(k,v),
      removeItem:k=>cache.delete(k)
    },
    setInterval:()=>{},setTimeout:()=>{},
    addEventListener:()=>{},dispatchEvent:()=>{}
  };
  win.top=framed?{}:win;
  class FakeDate extends Date { static now(){return 1000000;} }
  const context=vm.createContext({
    window:{parent:win},URL,Intl,Date:FakeDate,CustomEvent:class {},
    fetch:(url,options)=>{events.push(JSON.parse(options.body));return Promise.resolve({ok:true});}
  });
  vm.runInContext(ARTICLE,context);
  vm.runInContext(PAGE,context);
  const views=events.filter(e=>['page_view','article_view'].includes(e.event_name));
  assert.equal(views.length,2);
  for(const event of views) {
    assert.equal(event.entry_domain,expectedDomain);
    assert.equal(event.entry_domain_evidence,expectedEvidence);
    if (expectedDomain==='jairribeiro.com') assert.equal(event.referrer_host,null);
    assert.equal(event.attribution_source,campaign?'linkedin':null);
  }
}
run('jairribeiro-ai.streamlit.app',false,'',[],
    'jairribeiro-ai.streamlit.app','direct_host',false);
run('jairribeiro-ai.streamlit.app',true,'https://jairribeiro.com/',[],
    'jairribeiro.com','embed_referrer',true);
run('jairribeiro-ai.streamlit.app',true,'',['https://jairribeiro.com'],
    'jairribeiro.com','embed_ancestor',false);
run('jairribeiro-ai.streamlit.app',true,'',[],
    null,'embedded_unresolved',false);
run('jairribeiro-ai.streamlit.app',false,'https://jairribeiro.com/',[],
    'jairribeiro-ai.streamlit.app','direct_host',false);
run('unknown.example',false,'',[],null,null,false);
console.log('entry domain behavior passed');
""".replace("ARTICLE", json.dumps(article_js)).replace("PAGE", json.dumps(page_js))
        result = subprocess.run(["node", "-e", harness], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
