// Renderer regression tests: existing fictional fixtures only, no browser simulation claim.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const front = path.join(__dirname, '../frontend/monitoring');

function renderer() {
  const context = vm.createContext({
    document: {getElementById: () => ({addEventListener() {}})},
    fetch: () => new Promise(() => {}),
    fixture: JSON.parse(fs.readFileSync(path.join(front, 'demo.json'), 'utf8')),
  });
  vm.runInContext(fs.readFileSync(path.join(front, 'app.js'), 'utf8'), context);
  vm.runInContext('data=fixture', context);
  return expression => vm.runInContext(expression, context);
}

test('measurement text is escaped before HTML rendering', () => {
  const run = renderer();
  const html = run('data.readings[0].unit="<b>TEST</b>"; dataQuality()');
  assert.ok(html.includes('&lt;b&gt;TEST&lt;/b&gt;'));
  assert.ok(!html.includes('<b>TEST</b>'));
});

test('platform measurement text is escaped', () => {
  const run = renderer();
  const html = run('data.runs[0].latency_ms="<b>TEST</b>"; platform()');
  assert.ok(html.includes('&lt;b&gt;TEST&lt;/b&gt;'));
  assert.ok(!html.includes('<b>TEST</b>'));
});

test('site filter applies to all four fixture collections', () => {
  const run = renderer();
  for (const site of ['Site démo A', 'Site démo B']) {
    run(`chosenSite=${JSON.stringify(site)}`);
    for (const name of ['devices', 'readings', 'actions', 'runs']) {
      assert.equal(run(`selected(data.${name}).length`), name === 'devices' || name === 'readings' ? 2 : 1);
      assert.equal(run(`selected(data.${name}).every(x=>x.site===chosenSite)`), true);
    }
  }
});
