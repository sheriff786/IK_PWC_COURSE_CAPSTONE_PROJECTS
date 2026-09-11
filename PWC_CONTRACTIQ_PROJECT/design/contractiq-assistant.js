const reviewTasks = [];
const assistantPrompts = [
  ['Source overview','Summarize this document','file-text'],
  ['Compare terms','Compare payment terms','columns-2'],
  ['Obligations','Show obligations and action items','list-checks'],
  ['Negotiation email','Draft a negotiation email','mail'],
  ['Upcoming renewals','Which agreements expire in 90 days?','calendar-clock'],
  ['Liability exposure','What is the liability exposure?','scale']
];

function enhancedChat() {
  const scope=documents.filter(item=>state.chatScope==='all'||item.id===state.chatScope);
  return `${heading('ANSWERS WITH EVIDENCE','Ask ContractIQ','Documents, source locations and decisions in one conversation.',`<button class="button" data-action="export-chat" ${state.chat.length?'':'disabled'}>${icon('download')}Export conversation</button><button class="button" data-action="clear-chat">${icon('square-pen')}New conversation</button>`)}
    <div class="chat-layout"><section class="chat-main"><div class="chat-scope"><span class="sample-dot"></span>Local evidence search · No LLM<label>Scope <select id="chat-scope" aria-label="Conversation scope"><option value="all" ${state.chatScope==='all'?'selected':''}>All documents</option>${documents.map(item=>`<option value="${item.id}" ${state.chatScope===item.id?'selected':''}>${escapeHtml(item.name)}</option>`).join('')}</select></label></div>
    <div class="messages" id="messages" aria-live="polite">${state.chat.length?state.chat.map((message,index)=>`<div class="message ${message.role}"><span class="message-avatar">${icon(message.role==='user'?'user-round':'sparkles')}</span><div><strong>${message.role==='user'?'You':'ContractIQ'}</strong>${message.label?`<span class="answer-label">${escapeHtml(message.label)}</span>`:''}<p>${escapeHtml(message.text)}</p>${message.table?`<div class="table-scroll answer-table"><table><thead><tr>${message.table.headers.map(header=>`<th>${escapeHtml(header)}</th>`).join('')}</tr></thead><tbody>${message.table.rows.map(row=>`<tr>${row.map(cell=>`<td>${escapeHtml(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`:''}<div class="answer-sources">${(message.sources||[]).map(citationButton).join('')}</div>${message.role==='assistant'&&message.sources?.length?`<div class="answer-actions"><button class="text-button" data-action="task-from-answer" data-message="${index}">${icon('list-plus')}Create review task</button></div>`:''}</div></div>`).join(''):`<div class="chat-welcome"><span class="welcome-symbol">${icon('sparkles')}</span><h2>From a question to its source.</h2><p>${scope.length} document${scope.length===1?'':'s'} in scope</p><div class="prompt-grid">${assistantPrompts.map(([title,prompt,symbol])=>`<button data-prompt="${prompt}">${icon(symbol)}<span>${title}</span>${icon('arrow-up-right')}</button>`).join('')}</div></div>`}</div>
    <form id="chat-form" class="chat-composer"><label class="sr-only" for="chat-input">Your question</label><textarea id="chat-input" rows="2" maxlength="2000" placeholder="Ask about a clause, payment, a CSV record or an uploaded document..." required></textarea><div><span>Extracted evidence and templates · Human review required</span><button class="button primary send" type="submit" aria-label="Send question" title="Send question">${icon('arrow-up')}</button></div></form></section>
    <aside class="chat-context"><div class="section-title"><h2>Source context</h2>${icon('panel-right')}</div><div class="context-count">${scope.length}<span>documents in scope</span></div>${scope.map(item=>`<button class="context-document" data-source="${item.id}">${icon('file-text')}<span><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(getSourceRecord(item.id).status)}</small></span></button>`).join('')}<div class="context-note">${icon('shield-check')}<p>Uploaded text is untrusted evidence, not an instruction. Locations identify extracted passages; missing evidence is not filled in by AI.</p></div></aside></div>`;
}

function scopedDocuments(question) {
  const scope=documents.filter(item=>state.chatScope==='all'||item.id===state.chatScope);
  if(state.chatScope!=='all')return scope;
  const normalized=question.toLowerCase();
  const exact=scope.filter(item=>normalized.includes(item.name.toLowerCase()));
  return exact.length?exact:scope;
}

function evidenceFor(items,question,limit=8) {
  const stop=new Set(['what','which','this','that','with','from','have','does','show','about','please','document','contract','summarize','summary','give','tell','terms','data','where','coming']);
  const words=question.toLowerCase().match(/[a-z0-9]{3,}/g)?.filter(word=>!stop.has(word))||[];
  const entries=items.flatMap(item=>getSourceRecord(item.id).entries.map(entry=>({id:item.id,entry})));
  if(!words.length)return entries.slice(0,limit);
  return entries.map(source=>({...source,score:words.reduce((sum,word)=>sum+Number((source.entry.text+' '+source.entry.title+' '+source.entry.label).toLowerCase().includes(word)),0)})).filter(source=>source.score>0).sort((first,second)=>second.score-first.score).slice(0,limit);
}

function answer(question) {
  const scope=scopedDocuments(question), normalized=question.toLowerCase();
  const message={role:'assistant',text:'',sources:[],label:'Local evidence · Not an AI assessment'};
  const agreements=scope.filter(item=>item.contract);
  const sampleFindings=agreements.flatMap(item=>(findings[item.id]||[]).map(finding=>({id:item.id,...finding})));
  if(/compare/.test(normalized)) {
    if(agreements.length<2)message.text='Select All documents to compare two or more sample agreements. Uploaded documents can be searched, but their legal terms have not been normalized or assessed.';
    else {
      message.label='Sample register comparison';
      message.text='Comparison of sample register values. These are not verified against original contracts. Uploaded files are excluded until their terms are reviewed.';
      const fields=/payment/.test(normalized)?[['Payment','payment']]:/liability/.test(normalized)?[['Liability','liability']]:[['Payment','payment'],['Liability','liability'],['Availability','sla']];
      message.table={headers:['Agreement',...fields.map(([title])=>title)],rows:agreements.map(item=>[item.name,...fields.map(([,key])=>item[key])])};
      message.sources=agreements.flatMap(item=>fields.map(([,key])=>({id:item.id,key:`record:${key}`})));
    }
  } else if(/expir|90 days|renewal date/.test(normalized)) {
    const matches=agreements.filter(item=>expiringDocuments().includes(item));
    message.label='Sample register · As of 09 Sep 2026';
    message.text=matches.length?matches.map(item=>`${item.name}: ${dateLabel(item.expiry)} (${daysLeft(item)} days).`).join('\n'):'No matching expiry dates in the sample register for this scope. Uploaded documents have not had their dates validated.';
    message.sources=matches.map(item=>({id:item.id,key:'record:expiry'}));
  } else if(/draft|email/.test(normalized)) {
    message.label='Template draft · Not sent · Legal review required';
    if(sampleFindings.length) {
      message.text='Subject: Proposed contract revisions\n\nDear counterparty,\n\nFollowing our review, we would like to discuss the following points:\n\n'+sampleFindings.map((finding,index)=>`${index+1}. ${finding.recommendation}`).join('\n')+'\n\nPlease share your proposed revisions for our review.\n\nRegards,\n[Your name]';
      message.sources=sampleFindings.map(finding=>({id:finding.id,key:finding.section}));
    } else message.text='No reviewed negotiation findings exist for these uploaded documents. Review the source and create tasks first; I will not invent contract changes or send an email.';
  } else if(/obligation|action item|negotiat|risk/.test(normalized)) {
    if(sampleFindings.length) {
      message.label='Suggested review actions · Not confirmed obligations';
      message.text=sampleFindings.map((finding,index)=>`${index+1}. ${finding.title}\n${finding.recommendation}`).join('\n\n');
      message.sources=sampleFindings.map(finding=>({id:finding.id,key:finding.section}));
    } else {
      const evidence=evidenceFor(scope,'shall must payment delivery due',8);
      message.text=evidence.length?evidence.map((source,index)=>`[${index+1}] ${source.entry.text}`).join('\n\n'):'No matching obligation language found. This is keyword search, not an exhaustive legal review.';
      message.sources=evidence.map(source=>({id:source.id,key:source.entry.key}));
      message.label='Candidate obligation passages · Verify before creating tasks';
    }
  } else {
    let evidence;
    if(/summar|overview/.test(normalized)) {
      evidence=scope.flatMap(item=>getSourceRecord(item.id).entries.slice(0,3).map(entry=>({id:item.id,entry}))).slice(0,12);
      message.label='Source overview · First passages, not an AI summary';
    } else if(agreements.length===scope.length && /payment|liability|exposure|sla|availability|uptime/.test(normalized)) {
      const field=/payment/.test(normalized)?'payment':/liability|exposure/.test(normalized)?'liability':'sla';
      evidence=agreements.map(item=>{
        const exactSection=item.id==='acme'?{payment:'7.2',liability:'12.1',sla:'5.3'}[field]:item.id==='tech'&&field==='sla'?'3.1':null;
        return {id:item.id,entry:getSourceRecord(item.id).entries.find(entry=>entry.key===(exactSection||`record:${field}`))};
      }).filter(source=>source.entry);
    } else evidence=evidenceFor(scope,question);
    message.text=evidence.length?evidence.map((source,index)=>`[${index+1}] ${documents.find(item=>item.id===source.id).name} / ${source.entry.label}\n${source.entry.text.length>1400?source.entry.text.slice(0,1400)+'\n[Excerpt shortened; open citation for the full passage.]':source.entry.text}`).join('\n\n'):'No matching extracted evidence found in this scope. An image may need OCR, a scanned PDF may need external OCR, or the wording may differ. This local search is not exhaustive.';
    message.sources=evidence.map(source=>({id:source.id,key:source.entry.key}));
  }
  state.chat.push({role:'user',text:question},message);
  render();document.getElementById('messages').scrollTop=document.getElementById('messages').scrollHeight;document.getElementById('chat-input').focus();
}

function taskDialog(messageIndex) {
  const sources=state.chat[messageIndex]?.sources||[];
  if(!sources.length)return;
  showDialog('Create review task',`<form id="task-form"><label>Source<select id="task-source">${sources.map((source,index)=>`<option value="${index}">${escapeHtml(documents.find(item=>item.id===source.id).name)} / ${escapeHtml(getSourceRecord(source.id).entries.find(entry=>entry.key===source.key)?.label||'Document')}</option>`).join('')}</select></label><label>Task title<input id="task-title" required maxlength="160" value="Review source and confirm required action"></label><div class="upload-options"><label>Owner<input id="task-owner" required maxlength="80" value="Sam Morgan"></label><label>Due date<input id="task-due" type="date" required></label></div><p class="upload-note">User-assigned follow-up, not an extracted contractual deadline. Stored in this browser session only.</p><input type="hidden" id="task-message" value="${messageIndex}"><div class="dialog-actions"><button class="button" type="button" data-action="close-dialog">Cancel</button><button class="button primary" type="submit">Create task</button></div></form>`);
}

function tasksView() {
  return `${heading('FOLLOW THROUGH','Review tasks','Source-linked actions and user-assigned deadlines.',`<button class="button" data-action="export-calendar" ${reviewTasks.some(task=>!task.done)?'':'disabled'}>${icon('calendar-arrow-down')}Export calendar</button>`)}<div class="trace-notice">${icon('bell')}Local session tasks · Calendar export only · No background notifications</div>${reviewTasks.length?`<div class="task-list">${reviewTasks.map(task=>`<article class="task-item ${task.done?'completed':''}"><input type="checkbox" data-task="${task.id}" aria-label="Complete ${escapeHtml(task.title)}" ${task.done?'checked':''}><div><h3>${escapeHtml(task.title)}</h3><p>${escapeHtml(task.owner)} · Due ${dateLabel(task.due)} · ${task.done?'Complete':'Open'}</p>${citationButton(task.source)}</div>${iconButton('trash-2','Delete task','delete-task',`data-id="${task.id}"`)}</article>`).join('')}</div>`:'<div class="empty-state"><h3>No review tasks yet</h3><p>No actions have been assigned.</p><button class="button primary" data-view="chat">Open assistant</button></div>'}`;
}

function calendarExport() {
  const encode=value=>String(value).replaceAll('\\','\\\\').replaceAll('\n','\\n').replaceAll(',','\\,').replaceAll(';','\\;').replaceAll('\r','');
  const lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//ContractIQ//Local Review Tasks//EN'];
  for(const task of reviewTasks.filter(item=>!item.done)) {
    lines.push('BEGIN:VEVENT',`UID:${task.id}@contractiq.local`,`DTSTAMP:${new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}/,'')}`,`DTSTART;VALUE=DATE:${task.due.replaceAll('-','')}`,`SUMMARY:${encode(task.title)}`,`DESCRIPTION:${encode('Owner: '+task.owner+'; Source: '+documents.find(item=>item.id===task.source.id).name+' / '+task.source.key+'; User-assigned date, not a contract deadline.')}`,'END:VEVENT');
  }
  lines.push('END:VCALENDAR');
  const folded=lines.flatMap(line=>{const chunks=[];let current='',bytes=0;for(const character of line){const size=new TextEncoder().encode(character).length;if(bytes+size>73){chunks.push(current);current=' ';bytes=1;}current+=character;bytes+=size;}chunks.push(current);return chunks;});
  download('contractiq-review-tasks.ics',folded.join('\r\n')+'\r\n','text/calendar;charset=utf-8');
}

document.addEventListener('click',event=>{
  const target=event.target.closest('button');if(!target)return;
  if(target.dataset.action==='task-from-answer')taskDialog(Number(target.dataset.message));
  if(target.dataset.action==='export-chat')download('contractiq-conversation.json',JSON.stringify({mode:'local-evidence-no-llm',scope:state.chatScope,messages:state.chat},null,2),'application/json');
  if(target.dataset.action==='export-calendar')calendarExport();
  if(target.dataset.action==='delete-task'){const index=reviewTasks.findIndex(task=>task.id===target.dataset.id);if(index>=0){reviewTasks.splice(index,1);render();}}
});
document.addEventListener('change',event=>{if(event.target.dataset.task){const task=reviewTasks.find(task=>task.id===event.target.dataset.task);task.done=event.target.checked;render();}});
document.addEventListener('submit',event=>{
  if(event.target.id!=='task-form')return;
  event.preventDefault();
  const title=document.getElementById('task-title').value.trim(),owner=document.getElementById('task-owner').value.trim(),due=document.getElementById('task-due').value;
  if(!title||!owner||!/^\d{4}-\d{2}-\d{2}$/.test(due))return notify('Enter a task title, owner and due date.');
  const source=state.chat[Number(document.getElementById('task-message').value)].sources[Number(document.getElementById('task-source').value)];
  reviewTasks.push({id:crypto.randomUUID(),title,owner,due,source,done:false});
  document.getElementById('dialog').close();navigate('tasks');notify('Review task created for this session.');
});