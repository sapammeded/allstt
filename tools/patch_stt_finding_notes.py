from pathlib import Path

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

FINDING_URL = 'https://script.google.com/macros/s/AKfycbyAJ9CFiTESUWLiCF_x0APclk4U-Zd85jI6LfWjE22hN8nyS_9yDEf0-rYrObuwyf59lA/exec'

# Finding Notes uses the dedicated STTFINO Central deployment. The PDF upload
# endpoint is a different service and cannot answer GET_FINDINGS.
old = "const API=(typeof PDF_UPLOAD_URL==='string'&&PDF_UPLOAD_URL.trim())?PDF_UPLOAD_URL.trim():'';"
new = f"const API=(typeof STT_FINDING_CENTRAL_URL==='string'&&STT_FINDING_CENTRAL_URL.trim())?STT_FINDING_CENTRAL_URL.trim():{FINDING_URL!r};"
if old not in s:
    raise SystemExit('Finding Notes API anchor not found')
s = s.replace(old, new, 1)

# The patrol-area alert still expected the old local Finding schema.
start = s.find('  function findingAlertHtml(areaName,areaKey){')
end = s.find('\n  // ==================== RENDER AREAS UI ====================', start)
if start < 0 or end < 0:
    raise SystemExit('Legacy findingAlertHtml block not found')
new_block = '''  function findingAlertHtml(areaName,areaKey){
    const list=getActiveFindingNotesForArea(areaName,areaKey);
    if(!list.length) return '';
    const escLocal=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
    const photosLocal=f=>{
      const v=f?.photo_url;
      if(Array.isArray(v)) return v.map(x=>typeof x==='string'?x:String(x?.url||'')).filter(x=>/^https?:\\/\\//i.test(x));
      if(!v) return [];
      try{const a=JSON.parse(String(v));return Array.isArray(a)?a.map(x=>typeof x==='string'?x:String(x?.url||'')).filter(x=>/^https?:\\/\\//i.test(x)):[];}catch(_){return String(v).split(',').map(x=>x.trim()).filter(x=>/^https?:\\/\\//i.test(x));}
    };
    return `<div class="finding-area-alert"><div class="finding-area-title">⚠️ FINDING NOTES AKTIF (${list.length})</div>${list.map(f=>{const photos=photosLocal(f);return `<div class="finding-area-item"><div>${escLocal(f.description||f.content||'-')}</div>${photos.length?`<div class="finding-photo-strip">${photos.map(p=>`<img src="${escLocal(p)}" alt="Finding photo">`).join('')}</div>`:''}<div class="finding-area-meta">Status: ${escLocal(String(f.status||'OPEN').toUpperCase())} • Ditemukan: ${escLocal(f.created_at||f.foundAt||'-')} • Petugas: ${escLocal(f.finder_name||f.foundBy||'-')}</div></div>`;}).join('')}</div>`;
  }
'''
s = s[:start] + new_block + s[end:]

# Fixed findings must not appear in the active alert. CENTRAL uses uppercase
# status values, while the legacy code checked lowercase 'fixed'.
old_filter = "return list.filter(f=>f&&f.status!=='fixed'&&((f.areaKey!=null&&String(f.areaKey)===key)||String(f.area||'').trim().toLowerCase()===target));"
new_filter = "return list.filter(f=>{const st=String(f?.status||'').toUpperCase();return f&&st!=='FIXED'&&((f.areaKey!=null&&String(f.areaKey)===key)||String(f.area_code||f.area||'').trim().toLowerCase()===target);});"
if old_filter in s:
    s = s.replace(old_filter, new_filter, 1)

# Word export called photoDataWord(), but that helper did not exist.
word_anchor = "    const zip=new JSZip(),media=[];let rid=1;"
if word_anchor not in s:
    raise SystemExit('Word exporter anchor not found')
word_insert = '''    const zip=new JSZip(),media=[];let rid=1;
    async function photoDataWord(p){
      if(p&&typeof p==='object'&&p.ref){
        const b=await idbGet(STORE_BLOBS,p.ref);
        return b?await blobToBase64(b):null;
      }
      return typeof p==='string'?p:null;
    }'''
s = s.replace(word_anchor, word_insert, 1)

# DOCX text helper must accept strings as well as arrays.
old_plines = "function pLines(lines,opt={}){return lines.map((x,i)=>pText(x,{...opt,after:i===lines.length-1?(opt.after??80):0})).join('');}"
new_plines = "function pLines(lines,opt={}){const a=Array.isArray(lines)?lines:String(lines==null?'':lines).split(/\\r?\\n/);return a.map((x,i)=>pText(x,{...opt,after:i===a.length-1?(opt.after??80):0})).join('');}"
if old_plines not in s:
    raise SystemExit('Word pLines anchor not found')
s = s.replace(old_plines, new_plines, 1)

# Prevent long Finding Notes text from escaping its Android card.
s = s.replace(
    '#findingNotesSection .fn-finding-card{margin-top:14px;border:3px solid #dc2626;border-radius:16px;background:#fff;padding:16px;box-shadow:0 4px 16px rgba(15,23,42,.08)}',
    '#findingNotesSection .fn-finding-card{margin-top:14px;border:3px solid #dc2626;border-radius:16px;background:#fff;padding:16px;box-shadow:0 4px 16px rgba(15,23,42,.08);min-width:0;overflow:hidden;overflow-wrap:anywhere}', 1)
s = s.replace(
    '#findingNotesSection .fn-notes-box{width:100%;min-height:220px;box-sizing:border-box;border:3px solid #94a3b8;border-radius:13px;background:#fff;padding:15px;font-size:20px;line-height:1.55;font-weight:800;white-space:pre-wrap;overflow-wrap:anywhere;resize:vertical}',
    '#findingNotesSection .fn-notes-box{display:block;width:100%;max-width:100%;min-width:0;min-height:220px;box-sizing:border-box;border:3px solid #94a3b8;border-radius:13px;background:#fff;padding:15px;font-size:20px;line-height:1.55;font-weight:800;white-space:pre-wrap;overflow:auto;overflow-wrap:anywhere;word-break:break-word;resize:vertical}', 1)
s = s.replace(
    '#findingNotesSection .fn-new-box textarea{width:100%;min-height:240px;box-sizing:border-box;font-size:20px;font-weight:800;line-height:1.55;padding:15px;border:3px solid #2563eb;border-radius:12px;resize:vertical}',
    '#findingNotesSection .fn-new-box textarea{display:block;width:100%;max-width:100%;min-width:0;min-height:240px;box-sizing:border-box;font-size:20px;font-weight:800;line-height:1.55;padding:15px;border:3px solid #2563eb;border-radius:12px;resize:vertical;overflow:auto;overflow-wrap:anywhere;word-break:break-word}', 1)

# Wrap PDF metadata inside the Finding Notes box.
old_pdf = "const meta1=`PENEMU: ${String(f.finder_name||'-')}`;\n        const meta2=`TANGGAL: ${fmtDate(f.created_at)}  •  JAM: ${fmtTime(f.created_at)}`;\n        const meta3=`STATUS: ${status(f.status)}`;\n        const meta4=`AREA: ${String(f.area_code||area.name||'-')}  •  ID: ${String(f.finding_id||'-')}`;\n        const noteH=16+descLines.length*5.1+18;\n        if(y+noteH>H-25){footer();pdf.addPage();areaHeader(`AREA ${ai+1}: ${area.name||`Area ${ai+1}`} • FINDING NOTES`);y=47;}\n        pdf.setFillColor(...FIND_BG);pdf.setDrawColor(...FIND_LINE);pdf.setLineWidth(.9);pdf.roundedRect(M,y,W-2*M,noteH,2.5,2.5,'FD');\n        pdf.setFont('helvetica','bold');pdf.setFontSize(11);pdf.setTextColor(...FIND_TEXT);pdf.text('FINDING NOTES',M+6,y+7);\n        pdf.setFont('helvetica','bold');pdf.setFontSize(10);pdf.setTextColor(...FIND_TEXT);pdf.text(descLines,M+6,y+14);\n        let my=y+14+descLines.length*5.1+3;pdf.setFont('helvetica','bold');pdf.setFontSize(8.5);pdf.setTextColor(...FIND_TEXT);pdf.text(meta1,M+6,my);pdf.text(meta2,M+6,my+4.5);pdf.text(meta3,M+6,my+9);pdf.text(meta4,M+6,my+13.5);y+=noteH+9;"
new_pdf = "const metaLines=[`PENEMU: ${String(f.finder_name||'-')}`,`TANGGAL: ${fmtDate(f.created_at)}  •  JAM: ${fmtTime(f.created_at)}`,`STATUS: ${status(f.status)}`,`AREA: ${String(f.area_code||area.name||'-')}  •  ID: ${String(f.finding_id||'-')}`].flatMap(v=>pdf.splitTextToSize(v,W-2*M-12));\n        const noteH=16+descLines.length*5.1+metaLines.length*4.5+10;\n        if(y+noteH>H-25){footer();pdf.addPage();areaHeader(`AREA ${ai+1}: ${area.name||`Area ${ai+1}`} • FINDING NOTES`);y=47;}\n        pdf.setFillColor(...FIND_BG);pdf.setDrawColor(...FIND_LINE);pdf.setLineWidth(.9);pdf.roundedRect(M,y,W-2*M,noteH,2.5,2.5,'FD');\n        pdf.setFont('helvetica','bold');pdf.setFontSize(11);pdf.setTextColor(...FIND_TEXT);pdf.text('FINDING NOTES',M+6,y+7);\n        pdf.setFont('helvetica','bold');pdf.setFontSize(10);pdf.setTextColor(...FIND_TEXT);pdf.text(descLines,M+6,y+14);\n        let my=y+14+descLines.length*5.1+3;pdf.setFont('helvetica','bold');pdf.setFontSize(8.5);pdf.setTextColor(...FIND_TEXT);pdf.text(metaLines,M+6,my);y+=noteH+9;"
if old_pdf not in s:
    raise SystemExit('PDF Finding Notes block not found')
s = s.replace(old_pdf, new_pdf, 1)

# Keep PDF endpoint separate from Finding Notes endpoint.
marker = 'const PDF_UPLOAD_URL = '
idx = s.find(marker)
if idx < 0:
    raise SystemExit('PDF_UPLOAD_URL constant not found')
line_end = s.find('\n', idx)
if 'const STT_FINDING_CENTRAL_URL' not in s:
    s = s[:line_end+1] + f'const STT_FINDING_CENTRAL_URL = {FINDING_URL!r};\n' + s[line_end+1:]

p.write_text(s, encoding='utf-8')
print('STT Finding Notes patch applied')
