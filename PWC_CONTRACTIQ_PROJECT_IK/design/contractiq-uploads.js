let uploadProcessing = false;
let uploadQueue = [];
const uploadTypes = ['pdf','docx','csv','png','jpg','jpeg','webp'];
const uploadLimits = {files:10, bytes:10*1024*1024, pages:100, records:2000, text:1000000};

function openUploadManager() {
  uploadQueue = []; state.uploads = [];
  showDialog('Upload documents', `<form id="upload-form">
    <label class="dropzone" id="dropzone" for="file-input">${icon('cloud-upload')}<strong>Choose documents or images</strong><span>PDF, DOCX, CSV, PNG, JPG or WebP</span><small>Up to 10 files · 10 MB each</small><input id="file-input" type="file" accept=".pdf,.docx,.csv,.png,.jpg,.jpeg,.webp" multiple></label>
    <div class="upload-options"><label>Document category<select id="upload-category"><option>Unclassified</option><option>Master agreement</option><option>Statement of work</option><option>Financial document</option><option>Compliance document</option><option>Negotiation history</option></select></label><label>Counterparty<input id="upload-counterparty" maxlength="100" placeholder="Optional"></label></div>
    <div id="upload-list" aria-live="polite"></div>
    <p class="upload-note">Processed in this browser only. Up to 100 PDF pages / 2,000 CSV records / 1 million text characters. Images need English OCR; scanned PDFs may have no extractable text. Files and extracted text are lost on refresh.</p>
    <div class="dialog-actions"><button type="button" class="button" data-action="close-dialog">Cancel</button><button id="add-files" class="button primary" type="submit" disabled>Import & extract</button></div></form>`);
}

function queueFiles(files) {
  if (uploadProcessing) return;
  const errors = [];
  for (const file of Array.from(files)) {
    const extension = file.name.split('.').pop().toLowerCase();
    if (!uploadTypes.includes(extension)) errors.push(`${file.name}: unsupported file type.`);
    else if (!file.size) errors.push(`${file.name}: file is empty.`);
    else if (file.size > uploadLimits.bytes) errors.push(`${file.name}: exceeds 10 MB.`);
    else if (uploadQueue.length >= uploadLimits.files) errors.push('Maximum 10 files per batch.');
    else if (uploadQueue.some(item => item.file.name===file.name && item.file.size===file.size)) errors.push(`${file.name}: already queued.`);
    else if (documents.some(item => sourceStore.get(item.id)?.file?.name===file.name && sourceStore.get(item.id)?.file?.size===file.size)) errors.push(`${file.name}: matching name and size already imported.`);
    else uploadQueue.push({file, extension, status:'Ready', error:false});
  }
  state.uploads = uploadQueue.map(item => item.file);
  renderUploadQueue(errors);
}

function renderUploadQueue(errors = []) {
  const container = document.getElementById('upload-list');
  if (!container) return;
  container.innerHTML = uploadQueue.map((item,index) => `<div class="upload-file ${item.error?'upload-failed':''}">${icon(item.extension==='csv'?'table-2':['png','jpg','jpeg','webp'].includes(item.extension)?'image':'file-text')}<span><strong>${escapeHtml(item.file.name)}</strong><small>${escapeHtml(item.status)}</small></span><small>${Math.max(1,Math.round(item.file.size/1024))} KB</small>${!uploadProcessing?iconButton('x','Remove '+escapeHtml(item.file.name),'remove-upload',`data-index="${index}"`):''}</div>`).join('') + errors.map(error=>`<p class="field-error">${escapeHtml(error)}</p>`).join('');
  const submit = document.getElementById('add-files');
  submit.disabled = uploadProcessing || !uploadQueue.length;
  submit.textContent = uploadProcessing ? 'Extracting...' : 'Import & extract';
  refreshIcons();
}

async function extractFile(file, extension) {
  const record = {name:file.name,file,kind:extension,entries:[],status:'Text extracted locally'};
  if (['png','jpg','jpeg','webp'].includes(extension)) {
    const bitmap = await createImageBitmap(file);
    const pixels = bitmap.width*bitmap.height; bitmap.close();
    if (pixels > 25000000) throw new Error('Image exceeds 25 megapixels. Resize before importing.');
    record.kind='image'; record.status='Image preview ready · OCR not run';
  } else if (extension === 'csv') {
    if (!window.Papa) throw new Error('CSV parser unavailable. Check internet access and reload.');
    const result = Papa.parse(await file.text(), {skipEmptyLines:'greedy',preview:uploadLimits.records+2});
    if (result.errors.length) throw new Error('CSV could not be parsed: '+result.errors[0].message);
    if (!result.data.length) throw new Error('CSV contains no records.');
    const headers = result.data[0];
    if (headers.length>100) throw new Error('CSV exceeds 100 columns.');
    const data = result.data.slice(1,uploadLimits.records+1);
    record.entries = data.map((cells,index)=>({key:`row:${index+1}`, label:`Data record ${index+1}`,title:'CSV record (first record used as header)',text:cells.map((value,column)=>`${headers[column] || 'Column '+(column+1)}: ${value}`).join('\n'),cells}));
    record.headers=headers;
    if (!data.length) record.status='CSV header only · no data records';
    if (result.data.length>uploadLimits.records+1 || result.meta.truncated) record.status='Partial extraction · first 2,000 data records';
  } else if (extension === 'docx') {
    if (!window.mammoth) throw new Error('DOCX parser unavailable. Check internet access and reload.');
    const result = await mammoth.extractRawText({arrayBuffer:await file.arrayBuffer()});
    const text=result.value.slice(0,uploadLimits.text);
    record.entries = text.split(/\n\s*\n/).map(text=>text.trim()).filter(Boolean).slice(0,2000).map((text,index)=>({key:`paragraph:${index+1}`,label:`Extracted paragraph ${index+1}`,text}));
    if(result.value.length>uploadLimits.text || text.split(/\n\s*\n/).filter(text=>text.trim()).length>2000)record.status='Partial extraction · text limit reached';
    else if(result.messages.length)record.status='Text extracted with parser warnings · verify original';
    else if(!record.entries.length)record.status='No extractable DOCX text';
  } else if (extension === 'pdf') {
    if (!window.pdfjsLib) throw new Error('PDF parser unavailable. Check internet access and reload.');
    pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    record.pdf=await pdfjsLib.getDocument({data:await file.arrayBuffer(),isEvalSupported:false}).promise;
    const pages=Math.min(record.pdf.numPages,uploadLimits.pages);
    let characters=0;
    for(let pageNumber=1;pageNumber<=pages;pageNumber++) {
      const page=await record.pdf.getPage(pageNumber);
      const content=await page.getTextContent();
      const text=content.items.map(item=>item.str+(item.hasEOL?'\n':' ')).join('').trim();
      if(characters+text.length>uploadLimits.text){record.status='Partial extraction · text limit reached';break;}
      characters+=text.length;
      if(text)record.entries.push({key:`page:${pageNumber}`,label:`Page ${pageNumber}`,title:'Extracted page text',page:pageNumber,text});
    }
    if(record.pdf.numPages>pages)record.status='Partial extraction · first 100 PDF pages';
    if(!record.entries.length)record.status='No extractable PDF text · scanned or image-only PDF; OCR not available for PDF yet';
  }
  if(record.entries.reduce((sum,entry)=>sum+entry.text.length,0)>uploadLimits.text) {
    await record.pdf?.destroy();
    throw new Error('Extracted content exceeds the 1 million character limit.');
  }
  record.url=URL.createObjectURL(file);
  return record;
}

async function importQueuedFiles() {
  if(uploadProcessing || !uploadQueue.length)return;
  uploadProcessing=true;
  const category=document.getElementById('upload-category').value;
  const company=document.getElementById('upload-counterparty').value.trim() || 'Local upload';
  document.querySelectorAll('#dialog input, #dialog select').forEach(element=>element.disabled=true);
  renderUploadQueue();
  let imported=0;
  for(const item of uploadQueue) {
    item.status='Extracting...';renderUploadQueue();
    try {
      const record=await extractFile(item.file,item.extension);
      const id='upload-'+crypto.randomUUID();sourceStore.set(id,record);
      documents.push({id,name:item.file.name,company,initials:'UP',category,expiry:null,value:null,score:null,severity:'Not assessed',owner:'SM',contract:false,status:record.status});
      item.status=record.status;item.imported=true;imported++;
    } catch(error) {item.error=true;item.status=error.message || 'Extraction failed. File was not imported.';}
    renderUploadQueue();
  }
  uploadProcessing=false;
  traceEvents.unshift({time:new Date().toLocaleTimeString('en-GB'),title:'Local document import',detail:`${imported} imported; ${uploadQueue.length-imported} failed. No AI risk assessment.`,type:'files'});
  state.query='';state.severity='All';state.category='All';state.expiring=false;
  navigate('contracts');
  const summary=uploadQueue.map(item=>`<div class="upload-file ${item.error?'upload-failed':''}">${icon(item.error?'circle-alert':'check')}<span><strong>${escapeHtml(item.file.name)}</strong><small>${escapeHtml(item.status)}</small></span></div>`).join('');
  showDialog('Import results',`${summary}<div class="dialog-actions"><button class="button primary" data-action="close-dialog">Done</button></div>`);
  uploadQueue=[];state.uploads=[];
}

async function runImageOcr() {
  const id=sourceSelection?.id, record=sourceStore.get(id);
  if(!record || record.kind!=='image' || record.ocrBusy)return;
  if(!window.Tesseract)return notify('OCR library unavailable. Check internet access and reload.');
  record.ocrBusy=true;record.status='English OCR in progress';openSource(id);
  let worker;
  try {
    worker=await Tesseract.createWorker('eng');
    const result=await worker.recognize(record.file);
    const lines=result.data.text.split('\n').map(text=>text.trim()).filter(Boolean);
    record.entries=lines.slice(0,2000).map((text,index)=>({key:`ocr:${index+1}`,label:`OCR line ${index+1}`,text}));
    record.status=lines.length?`OCR extracted · confidence ${Math.round(result.data.confidence)}% · verify against image${lines.length>2000?' · first 2,000 lines only':''}`:'OCR found no text';
  } catch(error) {record.status='OCR failed. Try a clearer image or check network access to OCR assets.';}
  finally {await worker?.terminate();record.ocrBusy=false;}
  documents.find(item=>item.id===id).status=record.status;
  if(state.view==='sources' && sourceSelection?.id===id)openSource(id,record.entries[0]?.key);
  else notify(record.status);
}

document.addEventListener('click',event=>{
  const target=event.target.closest('button');if(!target)return;
  if(target.dataset.action==='remove-upload'&&!uploadProcessing){uploadQueue.splice(Number(target.dataset.index),1);state.uploads=uploadQueue.map(item=>item.file);renderUploadQueue();}
  if(target.dataset.action==='run-ocr')runImageOcr();
});
document.getElementById('dialog').addEventListener('cancel',event=>{if(uploadProcessing)event.preventDefault();});
window.addEventListener('beforeunload',()=>{for(const record of sourceStore.values())if(record.url)URL.revokeObjectURL(record.url);});