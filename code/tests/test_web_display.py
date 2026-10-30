"""Exercise the mobile display controls without browser dependencies."""
import shutil
import subprocess
import unittest
from pathlib import Path


@unittest.skipUnless(shutil.which("node"), "Node is needed to exercise the web display controls")
class WebDisplayTest(unittest.TestCase):
    def test_fullscreen_success_exit_denial_and_unavailable_api(self):
        template = Path(__file__).resolve().parents[2] / "web/alexandria.tmpl"
        result = subprocess.run(["node", "-e", r'''
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync(process.argv[1], 'utf8');
const script = source.match(/<script id="mobile-display">([\s\S]*?)<\/script>/);
assert.ok(script, 'The mobile display controls must exist');
function setup({language='pt-BR', unavailable=false, denied=false, standalone=false}={}) {
    const events = {};
    const nodes = Object.fromEntries(['screen-controls','fullscreen-button','fullscreen-status','rotate-message','canvas'].map(id=>[id,{
        hidden:false, disabled:false, textContent:'', listeners:{},
        addEventListener(type, handler) { this.listeners[type]=handler; },
        focus() {},
        click() { return this.listeners.click(); },
    }]));
    const calls = [];
    const document = {
        fullscreenElement:null,
        documentElement:{},
        getElementById:id=>nodes[id],
        addEventListener:(event,handler)=>events[event]=handler,
    };
    if (!unavailable) document.documentElement.requestFullscreen = async function(options) {
        assert.equal(this,document.documentElement);
        assert.equal(options.navigationUI,'hide');
        calls.push('fullscreen');
        assert.equal(nodes['fullscreen-button'].disabled,true);
        if (denied) throw Error('denied');
        document.fullscreenElement=this;
        events.fullscreenchange();
    };
    const context=vm.createContext({document,navigator:{language,standalone},
        matchMedia:()=>({matches:false}),
        screen:{orientation:{lock:async value=>{calls.push(value);throw Error('orientation unsupported');}}},
    });
    vm.runInContext(script[1],context);
    return {nodes,document,events,calls};
}
(async()=>{
    const ok=setup();
    assert.equal(ok.nodes['fullscreen-button'].textContent,'Tela cheia');
    await ok.nodes['fullscreen-button'].listeners.click();
    assert.deepEqual(ok.calls,['fullscreen','landscape']);
    assert.equal(ok.nodes['screen-controls'].hidden,true);
    assert.equal(ok.nodes['fullscreen-status'].hidden,true);
    assert.equal(ok.nodes['fullscreen-button'].disabled,false);
    ok.document.fullscreenElement=null;
    ok.events.fullscreenchange();
    assert.equal(ok.nodes['screen-controls'].hidden,false);
    const keyboard=setup();
    assert.equal(typeof keyboard.nodes['fullscreen-button'].listeners.keydown,'function');
    let consumed=0;
    keyboard.nodes['fullscreen-button'].listeners.keydown({key:'Enter',preventDefault(){consumed++;},stopPropagation(){consumed++;}});
    await new Promise(setImmediate);
    assert.equal(consumed,2);
    assert.deepEqual(keyboard.calls,['fullscreen','landscape']);
    const denied=setup({denied:true});
    await denied.nodes['fullscreen-button'].listeners.click();
    assert.equal(denied.nodes['fullscreen-status'].hidden,false);
    assert.match(denied.nodes['fullscreen-status'].textContent,/tela cheia/i);
    assert.equal(denied.nodes['fullscreen-button'].disabled,false);
    const missing=setup({unavailable:true,language:'en-US'});
    assert.equal(missing.nodes['fullscreen-button'].textContent,'Fullscreen');
    await missing.nodes['fullscreen-button'].listeners.click();
    assert.equal(missing.nodes['fullscreen-status'].hidden,false);
    assert.equal(missing.calls.length,0);
    assert.equal(setup({standalone:true}).nodes['screen-controls'].hidden,true);
})().catch(error=>{console.error(error);process.exitCode=1;});
''', str(template)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
