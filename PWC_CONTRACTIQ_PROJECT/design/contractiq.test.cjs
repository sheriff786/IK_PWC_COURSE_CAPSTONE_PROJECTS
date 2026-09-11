const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {test} = require('node:test');

function workspace() {
  const node = {addEventListener(){},focus(){},scrollHeight:100,scrollTop:0};
  const context = vm.createContext({console,TextEncoder,URL,Blob,crypto:require('node:crypto').webcrypto,setTimeout,clearTimeout,window:{addEventListener(){}},document:{addEventListener(){},getElementById(){return node;}}});
  for(const file of ['contractiq.js','contractiq-sources.js','contractiq-uploads.js','contractiq-assistant.js']) vm.runInContext(fs.readFileSync(path.join(__dirname,file),'utf8'),context,{filename:file});
  vm.runInContext('render = () => {};',context);
  return code => vm.runInContext(code,context);
}

test('payment answer cites the exact source clause',()=>{
  const run=workspace();run("answer('What are the payment terms?')");
  assert.equal(run('state.chat[1].sources[0].key'),'7.2');
  assert.match(run('state.chat[1].text'),/forty-five/);
});
test('register expiry uses a register location, not a fabricated clause',()=>{
  const run=workspace();run("answer('Which agreements expire in 90 days?')");
  assert.equal(run('state.chat[1].sources[0].key'),'record:expiry');
  assert.match(run("getSourceRecord('acme').entries.find(entry=>entry.key==='record:expiry').label"),/Sample register/);
});
test('uploaded search retains CSV record identity and scope',()=>{
  const run=workspace();run("documents.push({id:'csv',name:'rates.csv',contract:false});sourceStore.set('csv',{kind:'csv',entries:[{key:'row:1',label:'Data record 1',text:'Acme Net 45'},{key:'row:2',label:'Data record 2',text:'CloudCorp Net 30'}]});state.chatScope='csv';answer('CloudCorp');");
  assert.equal(run('state.chat[1].sources.length'),1);
  assert.equal(run('state.chat[1].sources[0].key'),'row:2');
});
test('unknown questions do not invent evidence',()=>{
  const run=workspace();run("answer('volcano spectroscopy')");
  assert.equal(run('state.chat[1].sources.length'),0);
  assert.match(run('state.chat[1].text'),/No matching extracted evidence/);
});
test('comparison requires sufficient scope',()=>{
  const run=workspace();run("answer('Compare payment terms')");
  assert.equal(run('state.chat[1].table'),undefined);
  run("state.chatScope='all';answer('Compare payment terms')");
  assert.equal(run('state.chat[3].table.rows.length'),5);
});
test('negotiation template identifies draft status and sources',()=>{
  const run=workspace();run("answer('Draft a negotiation email')");
  assert.match(run('state.chat[1].label'),/Not sent/);
  assert.equal(run('state.chat[1].sources.length'),3);
});
test('source citation escapes untrusted filenames',()=>{
  const run=workspace();run("documents.push({id:'test',name:'<img src=x onerror=alert(1)>',contract:false});");
  const markup=run("citationButton({id:'test'})");
  assert.ok(!markup.includes('<img'));
  assert.match(markup,/&lt;img/);
});
test('calendar export contains assigned date and source identity',()=>{
  const run=workspace();run("reviewTasks.push({id:'task-1',title:'Review, payment',owner:'Reviewer',due:'2026-09-25',source:{id:'acme',key:'7.2'},done:false});download=(name,text)=>{globalThis.exported={name,text}};calendarExport();");
  assert.equal(run('exported.name'),'contractiq-review-tasks.ics');
  assert.match(run('exported.text'),/DTSTART;VALUE=DATE:20260925/);
  assert.match(run('exported.text'),/SUMMARY:Review\\, payment/);
});
test('standalone source reader highlights section 5.3 and shows available documents',()=>{
  const run=workspace();run("selectSourceLocation('acme','5.3');");
  assert.equal(run('sourceSelection.key'),'5.3');
  const markup=run('documentSources()');
  assert.match(markup,/Available documents/);
  assert.match(markup,/CloudCorp SOW-04/);
  assert.match(markup,/<mark>Service availability<\/mark>/);
  assert.match(markup,/<mark>The Supplier shall maintain monthly service availability of 99.9%/);
  assert.equal((markup.match(/aria-current="location"/g)||[]).length,1);
});
test('selecting a different source clears the previous citation highlight',()=>{
  const run=workspace();run("selectSourceLocation('acme','5.3');selectSourceLocation('cloud','4.2');");
  const markup=run('sourceReader()');
  assert.match(markup,/<mark>Delivery and acceptance<\/mark>/);
  assert.ok(!markup.includes('99.9%'));
});
test('missing citation does not silently highlight another passage',()=>{
  const run=workspace();
  const citation=run("citationButton({id:'acme',key:'missing'})");
  assert.match(citation,/data-location="missing"/);
  run("selectSourceLocation('acme','missing')");
  const markup=run('sourceReader()');
  assert.match(markup,/no substitute has been chosen/);
  assert.ok(!markup.includes('<mark>'));
});