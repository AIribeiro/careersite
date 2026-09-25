"""Run the actual injected JavaScript against a deterministic browser shell."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


@unittest.skipUnless(shutil.which('node'), 'Node required for browser collector contract')
class BrowserCollectorTests(unittest.TestCase):
    def test_collector_reruns_timing_scroll_and_share_exclusion(self):
        import site_analytics
        with patch.object(site_analytics.components, 'html') as html:
            site_analytics.inject_analytics('home')
        script = html.call_args.args[0].replace('<script>', '').replace('</script>', '')
        harness = r'''
const vm = require('node:vm');
const assert = require('node:assert/strict');
let clock=1000000, top=0;
const events=[], intervals=[], listeners={}, memory=new Map();
const doc={visibilityState:'visible',referrer:'',documentElement:{clientWidth:1200,clientHeight:800},
  querySelector:(s)=>s==='.site main'?{getBoundingClientRect:()=>({height:2000,top})}:null,
  addEventListener:(n,f)=>{listeners[n]=f}};
const win={document:doc,location:{href:'https://example.test/?page=home',hostname:'example.test'},
  navigator:{userAgent:'Chrome/123',platform:'Linux',language:'en'},innerWidth:1200,innerHeight:800,
  performance:{now:()=>clock},crypto:{randomUUID:()=> 'aaaaaaaa-2222-4444-8888-aaaaaaaaaaaa'},
  sessionStorage:{getItem:k=>memory.get(k)||null,setItem:(k,v)=>memory.set(k,v),removeItem:k=>memory.delete(k)},
  setInterval:(f,ms)=>intervals.push([f,ms]),setTimeout:()=>{},addEventListener:()=>{},dispatchEvent:()=>{}};
class FakeDate extends Date {static now(){return clock;}}
const ctx=vm.createContext({window:{parent:win},URL,Intl,Date:FakeDate,CustomEvent:class {},
  fetch:(url,options)=>{events.push(JSON.parse(options.body));return Promise.resolve({ok:true})}});
vm.runInContext(SCRIPT,ctx);
assert.equal(events.filter(e=>e.event_name==='page_view').length,1);
for(let i=0;i<15;i++){clock+=1000;intervals.find(x=>x[1]===1000)[0]();}
top=-1100;
win.__jairAnalyticsSend('engagement_ping');
assert.equal(events.at(-1).page_engaged_ms,15000);
assert.equal(events.at(-1).scroll_depth,95);
clock+=10000;
vm.runInContext(SCRIPT,ctx);
assert.equal(events.filter(e=>e.event_name==='page_view').length,1,'rerun must not create a view');
top=0;
win.__jairAnalyticsSend('engagement_ping');
assert.equal(events.at(-1).scroll_depth,95,'depth must survive rerun and scroll-up');
const count=events.length;
listeners.click({target:{closest:()=>({dataset:{hqEvent:'article_share_linkedin'},getAttribute:()=> 'https://linkedin.com/sharing/share-offsite/'})}});
assert.equal(events.length,count,'share is not a contact click');
console.log('collector behavior passed');
'''.replace('SCRIPT', json.dumps(script))
        result = subprocess.run(['node', '-e', harness], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
