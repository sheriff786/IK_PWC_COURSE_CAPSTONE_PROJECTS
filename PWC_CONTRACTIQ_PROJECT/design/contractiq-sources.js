const sourceStore = new Map();
let sourceSelection = null;
let sourceRenderVersion = 0;
let sourceDocumentQuery = '';
let sourceReturnView = 'chat';

function getSourceRecord(id) {
  if (sourceStore.has(id)) return sourceStore.get(id);
  const item = documents.find(document => document.id === id);
  if (!item) return null;
  const entries = (findings[id] || []).map(finding => ({
    key: finding.section, label: `Section ${finding.section}`, title: finding.heading, text: finding.quote
  }));
  for (const [key, title] of [['payment','Payment terms'],['liability','Liability'],['sla','Availability'],['expiry','Expiry date'],['value','Value (USD)']]) {
    if (item[key] !== undefined && item[key] !== null) entries.push({key:`record:${key}`, label:`Sample register / ${title}`, title, text:String(item[key])});
  }
  const record = {kind:'sample', entries, status:'Illustrative source', name:item.name};
  sourceStore.set(id, record);
  return record;
}

function citationButton(source) {
  const record = getSourceRecord(source.id);
  const requestedKey = source.key || source.section || '';
  const entry = record?.entries.find(item => item.key === requestedKey);
  const name = documents.find(item => item.id === source.id)?.name || 'Unavailable source';
  return `<button class="citation" data-source="${escapeHtml(source.id)}" data-location="${escapeHtml(requestedKey)}">${icon('file-text')}${escapeHtml(name)} · ${escapeHtml(entry?.label || (requestedKey?'Location unavailable':'Document details'))}${icon('arrow-up-right')}</button>`;
}

function sourceDocumentList() {
  const matches = documents.filter(item => item.name.toLowerCase().includes(sourceDocumentQuery.toLowerCase()));
  return matches.map(item => {
    const record = getSourceRecord(item.id);
    return `<button class="source-document-item ${sourceSelection?.id===item.id?'selected':''}" data-source="${escapeHtml(item.id)}" aria-pressed="${sourceSelection?.id===item.id}">${icon(record.kind==='image'?'image':record.kind==='csv'?'table-2':'file-text')}<span><strong>${escapeHtml(item.name)}</strong><small>${record.kind.toUpperCase()} · ${record.entries.length} locations</small></span>${sourceSelection?.id===item.id?icon('check'):''}</button>`;
  }).join('') || '<p class="source-list-empty">No matching documents.</p>';
}

function selectSourceLocation(id, key = '') {
  const record = getSourceRecord(id);
  if (!record) return false;
  const index = key ? record.entries.findIndex(entry => entry.key === key) : 0;
  sourceSelection = {id, key:key || record.entries[index]?.key || '', index};
  return true;
}

function documentSources() {
  if (!sourceSelection) selectSourceLocation(documents[0]?.id);
  return `${heading('CITATIONS & EVIDENCE','Document sources','Available documents and their cited locations.',`<button class="button" data-action="return-from-source">${icon('arrow-left')}Back to ${sourceReturnView==='chat'?'conversation':sourceReturnView==='review'?'risk review':'previous view'}</button>`)}
    <div class="sources-workspace"><aside class="source-library" aria-label="Available documents"><div class="section-title"><h2>Available documents</h2><span class="count">${documents.length}</span></div><label class="search-field">${icon('search')}<input id="source-document-search" aria-label="Search source documents" placeholder="Find a document" value="${escapeHtml(sourceDocumentQuery)}"></label><div id="source-document-list">${sourceDocumentList()}</div></aside><section class="source-reader" aria-label="Selected document">${sourceReader()}</section></div>`;
}

function sourceReader() {
  const record = getSourceRecord(sourceSelection?.id);
  if (!record) return '<div class="empty-state">No source document available.</div>';
  const {key,index} = sourceSelection;
  const entry = record.entries[index];
  const locationControl = record.entries.length ? `<label>Location <select id="source-location" aria-label="Source location">${index<0?'<option value="" disabled selected>Location unavailable</option>':''}${record.entries.map(item => `<option value="${escapeHtml(item.key)}" ${entry===item?'selected':''}>${escapeHtml(item.label)}</option>`).join('')}</select></label>` : '';
  return `<div class="source-reader-heading"><div><h2>${escapeHtml(record.name)}</h2><p>${escapeHtml(record.kind==='sample'?'Sample excerpts and register':'Uploaded original and extracted content')}</p></div><span class="highlight-label">${icon('highlighter')}Yellow highlight</span></div>
    <div class="source-toolbar"><span class="source-format">${record.kind.toUpperCase()}</span>${locationControl}<div class="source-navigation">${iconButton('chevron-left','Previous source location','source-prev',index<=0?'disabled':'')}${iconButton('chevron-right','Next source location','source-next',index<0||index>=record.entries.length-1?'disabled':'')}</div></div>
    <p class="source-status">${escapeHtml(record.status)}${record.kind==='sample'?' · Example excerpts and register values, not the original dataset.':''}</p>
    <div class="source-layout ${record.kind==='pdf'||record.kind==='image'?'with-preview':''}">
      ${record.kind==='pdf'&&index>=0?'<div class="source-original"><canvas id="source-pdf" aria-label="Original PDF page"></canvas><p id="pdf-preview-status" role="status">Rendering original page...</p></div>':record.kind==='image'?`<div class="source-original"><img src="${record.url}" alt="${escapeHtml(record.name)}"></div>`:''}
      <section class="source-passages" aria-label="Source passages">
        ${key && index<0?'<p class="field-error">This citation location is unavailable. Select another location; no substitute has been chosen.</p>':''}
        ${record.entries.length?record.entries.map(item => `<article id="source-passage-${escapeHtml(item.key.replaceAll(':','-').replaceAll('.','-'))}" class="source-passage ${entry===item?'active':''}" data-source-key="${escapeHtml(item.key)}" ${entry===item?'tabindex="-1" aria-current="location"':''}><span>${escapeHtml(item.label)}</span><h3>${entry===item?`<mark>${escapeHtml(item.title || item.label)}</mark>`:escapeHtml(item.title || item.label)}</h3><p>${entry===item?`<mark>${escapeHtml(item.text)}</mark>`:escapeHtml(item.text)}</p></article>`).join(''):'<div class="empty-state"><h3>No extracted text</h3><p>There is no citable text available for this document yet.</p></div>'}
      </section>
    </div><div class="source-actions">${record.file?`<button class="button" data-action="download-original">${icon('download')}Download original</button>`:''}${record.kind==='image'?`<button class="button primary" data-action="run-ocr" ${record.ocrBusy?'disabled':''}>${icon('scan-text')}${record.ocrBusy?'OCR running...':'Extract text (English OCR)'}</button>`:''}<button class="button" data-action="ask-source">${icon('messages-square')}Ask this document</button><span>${record.kind==='pdf'?'Original page + extracted passage; PDF coordinates are not highlighted.':record.kind==='image'?'Original image; OCR text must be verified.':'Highlighted location in extracted source text.'}</span></div>`;
}

function openSource(id, key = '') {
  if (!selectSourceLocation(id, key)) return notify('Source document is no longer available.');
  if (state.view!=='sources') sourceReturnView=state.view;
  sourceDocumentQuery='';
  document.getElementById('dialog').close();
  navigate('sources');
}

async function activateSourceReader() {
  const version=++sourceRenderVersion;
  const record=getSourceRecord(sourceSelection?.id);
  const entry=record?.entries[sourceSelection.index];
  const highlighted=document.querySelector('.source-passage.active');
  highlighted?.scrollIntoView({block:'nearest'});
  highlighted?.focus({preventScroll:true});
  if (record?.kind === 'pdf' && record.pdf && sourceSelection.index>=0) {
    const canvas=document.getElementById('source-pdf');
    const status=document.getElementById('pdf-preview-status');
    try {
      const pageNumber = entry?.page || 1;
      const pdfPage = await record.pdf.getPage(pageNumber);
      if (version !== sourceRenderVersion || state.view!=='sources' || !canvas?.isConnected) return;
      const viewport = pdfPage.getViewport({scale:1.2});
      canvas.width = viewport.width; canvas.height = viewport.height;
      await pdfPage.render({canvasContext:canvas.getContext('2d'), viewport}).promise;
      if (version === sourceRenderVersion && status.isConnected) status.textContent = `Original page ${pageNumber} of ${record.pdf.numPages}`;
    } catch (error) {
      if (version === sourceRenderVersion && status?.isConnected) status.textContent = 'Original page preview unavailable. Download the original to verify the source.';
    }
  }
}

document.addEventListener('click', event => {
  const target = event.target.closest('button');
  if (!target) return;
  if (target.dataset.source) openSource(target.dataset.source, target.dataset.location);
  if (target.dataset.action==='return-from-source') navigate(sourceReturnView);
  if (target.dataset.action === 'source-prev' || target.dataset.action === 'source-next') {
    const record = getSourceRecord(sourceSelection.id);
    const next = sourceSelection.index + (target.dataset.action === 'source-next' ? 1 : -1);
    if (record.entries[next]) openSource(sourceSelection.id, record.entries[next].key);
  }
  if (target.dataset.action === 'ask-source') {
    if(state.chatScope!==sourceSelection.id)state.chat=[];
    state.chatScope = sourceSelection.id;
    document.getElementById('dialog').close(); navigate('chat');
  }
  if (target.dataset.action === 'download-original') {
    const record = getSourceRecord(sourceSelection.id);
    const anchor = document.createElement('a');
    anchor.href = record.url; anchor.download = record.name;
    document.body.append(anchor); anchor.click(); anchor.remove();
  }
});
document.addEventListener('change', event => {
  if (event.target.id === 'source-location') openSource(sourceSelection.id, event.target.value);
});
document.addEventListener('input',event=>{
  if(event.target.id!=='source-document-search')return;
  sourceDocumentQuery=event.target.value;
  document.getElementById('source-document-list').innerHTML=sourceDocumentList();
  refreshIcons();
});