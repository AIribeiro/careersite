"""Execute the real browser-persistence JS in Node to test storage transitions."""
from __future__ import annotations

import base64
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from site_owner_device_persistence import _DEVICE_JS


class BrowserDeviceJsTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js runtime unavailable")
    def test_store_restore_rotation_stale_tab_guard_and_logout(self):
        script = r"""
const vm = require('node:vm');
const source = Buffer.from(process.argv[1], 'base64').toString('utf8')
  .replace('export default function', 'function runComponent');
const store = new Map();
const storage = {
  getItem: key => store.has(key) ? store.get(key) : null,
  setItem: (key, value) => store.set(key, value),
  removeItem: key => store.delete(key)
};
function run(window, data) {
  const state = {};
  const sandbox = { window, Date, JSON, Number, String };
  vm.runInNewContext(source + '\nthis.render = runComponent', sandbox);
  sandbox.render({ data, setStateValue: (key, value) => { state[key] = value; } });
  return state;
}
const open = () => ({localStorage: storage});
const owner1 = open();
const alpha = 'first-valid-refresh-credential';
const beta = 'new-rotated-refresh-credential';
const saved = run(owner1, {mode:'write', refresh_token:alpha,
                            expires_at:1000,force:true});
if (saved.status !== 'stored') throw new Error('Initial persistence failed');
const reopened = open();
const restored = run(reopened, {mode:'read',read_nonce:4});
if (restored.restored.refresh_token !== alpha || restored.restored.read_nonce !== 4)
  throw new Error('New browser session did not recover stored refresh token');
const newTab = open();
const later = run(newTab,{mode:'write',refresh_token:beta,expires_at:2000,force:false});
if (later.status !== 'stored') throw new Error('Rotated session not written');
const stale = open();
const rejected = run(stale,{mode:'write',refresh_token:alpha,expires_at:1000,force:false});
if (rejected.status !== 'newer_saved_session')
  throw new Error('Stale tab was allowed to clobber current session');
const confirmed = run(open(),{mode:'read',read_nonce:5});
if (confirmed.restored.refresh_token !== beta)
  throw new Error('Latest token was overwritten');
const cleared = run(open(),{mode:'clear'});
if (cleared.status !== 'cleared') throw new Error('Sign out did not clear storage');
if (run(open(),{mode:'read'}).status !== 'empty')
  throw new Error('Sign out left behind credential');
process.stdout.write('device JS lifecycle passed');
"""
        result = subprocess.run(
            ["node","-e",script,base64.b64encode(_DEVICE_JS.encode()).decode()],
            capture_output=True,text=True,timeout=12,check=False,
        )
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("device JS lifecycle passed",result.stdout)


if __name__=="__main__":
    unittest.main()
