from pathlib import Path

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

FINDING_URL = 'https://script.google.com/macros/s/AKfycbyAJ9CFiTESUWLiCF_x0APclk4U-Zd85jI6LfWjE22hN8nyS_9yDEf0-rYrObuwyf59lA/exec'

# Finding Notes uses the dedicated STTFINO Central deployment. The PDF upload
# endpoint is a different service and cannot answer GET_FINDINGS.
old = "const API=(typeof PDF_UPLOAD_URL==='string'&&PDF_UPLOAD_URL.trim())?PDF_UPLOAD_URL.trim():'';"
new = f"const API=(typeof STT_FINDING_CENTRAL_URL==='string'&&STT_FINDING_CENTRAL_URL.trim())?STT_FINDING_CENTRAL_URL.trim():{FINDING_URL!r};"
if old not in s and 'STT_FINDING_CENTRAL_URL' not in s:
    raise SystemExit('Finding Notes API anchor not found')
if old in s:
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
if 'async function photoDataWord(p)' not in s:
    word_insert = '''    const zip=new JSZip(),media=[];let rid=1;
    async function photoDataWord(p){
      if(p&&typeof p==='object'&&p.ref){
        const b=await idbGet(STORE_BLOBS,p.ref);
        return b?await blobToBase64(b):null;
      }
      return typeof p==='string'?p:null;
    }'''
    s = s.replace(word_anchor, word_insert, 1)

# DOCX text helper must accept strings and hard-wrap very long lines so Word
# never lets a long Finding sentence escape its shaded block.
old_plines = "function pLines(lines,opt={}){return lines.map((x,i)=>pText(x,{...opt,after:i===lines.length-1?(opt.after??80):0})).join('');}"
new_plines = "function pLines(lines,opt={}){const raw=Array.isArray(lines)?lines:String(lines==null?'':lines).replace(/\\r/g,'').split('\\n'),a=[];raw.forEach(line=>{let r=String(line||'');if(!r){a.push('');return;}while(r.length>92){let cut=r.lastIndexOf(' ',92);if(cut<45)cut=92;a.push(r.slice(0,cut).trim());r=r.slice(cut).trim();}a.push(r);});return a.map((x,i)=>pText(x,{...opt,after:i===a.length-1?(opt.after??80):0})).join('');}"
if old_plines in s:
    s = s.replace(old_plines, new_plines, 1)
elif 'function pLines(lines,opt={}){const raw=Array.isArray(lines)' not in s:
    raise SystemExit('Word pLines helper not found')

# On-screen Finding Notes: red theme, larger bold description, and hard overflow
# protection. Fixed cards retain the existing green status treatment.
s = s.replace(
    '#findingNotesSection .fn-finding-card{margin-top:14px;border:3px solid #dc2626;border-radius:16px;background:#fff;padding:16px;box-shadow:0 4px 16px rgba(15,23,42,.08)}',
    '#findingNotesSection .fn-finding-card{margin-top:14px;border:3px solid #dc2626;border-radius:16px;background:#fef2f2;padding:16px;box-shadow:0 4px 16px rgba(15,23,42,.08);min-width:0;overflow:hidden;overflow-wrap:anywhere}', 1)
s = s.replace(
    '#findingNotesSection .fn-notes-box{width:100%;min-height:220px;box-sizing:border-box;border:3px solid #94a3b8;border-radius:13px;background:#fff;padding:15px;font-size:20px;line-height:1.55;font-weight:800;white-space:pre-wrap;overflow-wrap:anywhere;resize:vertical}',
    '#findingNotesSection .fn-notes-box{display:block;width:100%;max-width:100%;min-width:0;min-height:220px;box-sizing:border-box;border:3px solid #dc2626;border-radius:13px;background:#fee2e2;color:#991b1b;padding:15px;font-size:22px;line-height:1.58;font-weight:900;white-space:pre-wrap;overflow:auto;overflow-wrap:anywhere;word-break:break-word;resize:vertical}', 1)
s = s.replace(
    '#findingNotesSection .fn-new-box textarea{width:100%;min-height:240px;box-sizing:border-box;font-size:20px;font-weight:800;line-height:1.55;padding:15px;border:3px solid #2563eb;border-radius:12px;resize:vertical}',
    '#findingNotesSection .fn-new-box textarea{display:block;width:100%;max-width:100%;min-width:0;min-height:240px;box-sizing:border-box;font-size:22px;font-weight:900;line-height:1.58;padding:15px;border:3px solid #dc2626;border-radius:12px;background:#fee2e2;color:#991b1b;resize:vertical;overflow:auto;overflow-wrap:anywhere;word-break:break-word}', 1)

# PDF Finding Notes: explicitly use a red-on-light-red block and larger bold text.
old_pdf = "const meta1=`PENEMU: ${String(f.finder_name||'-')}`;\n        const meta2=`TANGGAL: ${fmtDate(f.created_at)}  •  JAM: ${fmtTime(f.created_at)}`;\n        const meta3=`STATUS: ${status(f.status)}`;\n        const meta4=`AREA: ${String(f.area_code||area.name||'-')}  •  ID: ${String(f.finding_id||'-')}`;\n        const noteH=16+descLines.length*5.1+18;\n        if(y+noteH>H-25){footer();pdf.addPage();areaHeader(`AREA ${ai+1}: ${area.name||`Area ${ai+1}`} • FINDING NOTES`);y=47;}\n        pdf.setFillColor(...FIND_BG);pdf.setDrawColor(...FIND_LINE);pdf.setLineWidth(.9);pdf.roundedRect(M,y,W-2*M,noteH,2.5,2.5,'FD');\n        pdf.setFont('helvetica','bold');pdf.setFontSize(11);pdf.setTextColor(...FIND_TEXT);pdf.text('FINDING NOTES',M+6,y+7);\n        pdf.setFont('helvetica','bold');pdf.setFontSize(10);pdf.setTextColor(...FIND_TEXT);pdf.text(descLines,M+6,y+14);\n        let my=y+14+descLines.length*5.1+3;pdf.setFont('helvetica','bold');pdf.setFontSize(8.5);pdf.setTextColor(...FIND_TEXT);pdf.text(meta1,M+6,my);pdf.text(meta2,M+6,my+4.5);pdf.text(meta3,M+6,my+9);pdf.text(meta4,M+6,my+13.5);y+=noteH+9;"
new_pdf = "const metaLines=[`PENEMU: ${String(f.finder_name||'-')}`,`TANGGAL: ${fmtDate(f.created_at)}  •  JAM: ${fmtTime(f.created_at)}`,`STATUS: ${status(f.status)}`,`AREA: ${String(f.area_code||area.name||'-')}  •  ID: ${String(f.finding_id||'-')}`].flatMap(v=>pdf.splitTextToSize(v,W-2*M-12));\n        const noteH=18+descLines.length*6.4+metaLines.length*4.8+12;\n        if(y+noteH>H-25){footer();pdf.addPage();areaHeader(`AREA ${ai+1}: ${area.name||`Area ${ai+1}`} • FINDING NOTES`);y=47;}\n        pdf.setFillColor(254,226,226);pdf.setDrawColor(220,38,38);pdf.setLineWidth(1);pdf.roundedRect(M,y,W-2*M,noteH,2.5,2.5,'FD');\n        pdf.setFont('helvetica','bold');pdf.setFontSize(12);pdf.setTextColor(185,28,28);pdf.text('FINDING NOTES',M+6,y+8);\n        pdf.setFont('helvetica','bold');pdf.setFontSize(12);pdf.setTextColor(185,28,28);pdf.text(descLines,M+6,y+17);\n        let my=y+17+descLines.length*6.4+4;pdf.setFont('helvetica','bold');pdf.setFontSize(9);pdf.setTextColor(185,28,28);pdf.text(metaLines,M+6,my);y+=noteH+10;"
if old_pdf in s:
    s = s.replace(old_pdf, new_pdf, 1)

# Word DOCX Finding Notes: red border, red text, larger bold description and
# light-red background. Long descriptions are hard-wrapped by pLines above.
s = s.replace("let fb=pText('FINDING NOTES',{bold:true,size:15,color:'7F1D1D',after:55})+pLines(descLines,{bold:true,size:11,color:'7F1D1D',after:55})+pText(`PENEMU: ${String(f.finder_name||'-')}`,{bold:true,size:9,color:'7F1D1D',after:25})+pText(`TANGGAL: ${fmtDate(f.created_at)} • JAM: ${fmtTime(f.created_at)}`,{bold:true,size:9,color:'7F1D1D',after:25})+pText(`STATUS: ${status(f.status)}`,{bold:true,size:9,color:'7F1D1D',after:25})+pText(`AREA: ${String(f.area_code||area.name||'-')} • ID: ${String(f.finding_id||'-')}`,{bold:true,size:9,color:'7F1D1D',after:60});\n        body+=shadedBlock(fb,'FCE7F3','F472B6');", "let fb=pText('FINDING NOTES',{bold:true,size:17,color:'B91C1C',after:45})+pLines(descLines,{bold:true,size:14,color:'B91C1C',after:45})+pText(`PENEMU: ${String(f.finder_name||'-')}`,{bold:true,size:10,color:'B91C1C',after:22})+pText(`TANGGAL: ${fmtDate(f.created_at)} • JAM: ${fmtTime(f.created_at)}`,{bold:true,size:10,color:'B91C1C',after:22})+pText(`STATUS: ${status(f.status)}`,{bold:true,size:10,color:'B91C1C',after:22})+pText(`AREA: ${String(f.area_code||area.name||'-')} • ID: ${String(f.finding_id||'-')}`,{bold:true,size:10,color:'B91C1C',after:50});\n        body+=shadedBlock(fb,'FEE2E2','DC2626');", 1)

# DOCX export must not depend on a remote JSZip CDN. Inject a tiny uncompressed
# ZIP writer as a fallback so Android WebView can always create a valid .DOCX.
mini_zip = r'''\n# --- Android-safe DOCX ZIP fallback ---\nmini_zip_js = r''' + repr(zip_code) + r'''\nmini_marker = "if(window.JSZip) return;"\nif "window.__STT_MINIZIP_V1" not in s:\n    s = s.replace("document.getElementById('genWordBtn')?.addEventListener('click', async ()=>{", """<script id="STT_MINIZIP_V1">\nwindow.__STT_MINIZIP_V1=true;\n""" + mini_zip_js + "</script>\n\ndocument.getElementById('genWordBtn')?.addEventListener('click', async ()=>{", 1)\n\n# Remote Google Drive photos are often readable in <img> but blocked by CORS
# when Word tries to fetch their bytes. Try direct first, then a CORS image proxy.\nold_data = "async function dataToBytes(data){const str=String(data||'').trim();if(!str)throw new Error('Data gambar kosong.');if(/^data:/i.test(str)){const comma=str.indexOf(',');if(comma<0)throw new Error('Data URL gambar tidak valid.');const meta=str.slice(0,comma).toLowerCase(),payload=str.slice(comma+1);if(meta.includes(';base64')){let raw=payload.replace(/\\s/g,'').replace(/-/g,'+').replace(/_/g,'/');try{raw=decodeURIComponent(raw)}catch(_){}while(raw.length%4)raw+='=';return Uint8Array.from(atob(raw),c=>c.charCodeAt(0));}return new Uint8Array(await (await fetch(str)).arrayBuffer());}if(/^https?:/i.test(str))return new Uint8Array(await (await fetchRetry(str,{mode:'cors',cache:'force-cache'},15000,2)).arrayBuffer());throw new Error('Sumber gambar Word harus URL Central atau data lokal yang valid.');}"\nnew_data = "async function dataToBytes(data){const str=String(data||'').trim();if(!str)throw new Error('Data gambar kosong.');if(/^data:/i.test(str)){const comma=str.indexOf(',');if(comma<0)throw new Error('Data URL gambar tidak valid.');const meta=str.slice(0,comma).toLowerCase(),payload=str.slice(comma+1);if(meta.includes(';base64')){let raw=payload.replace(/\\s/g,'').replace(/-/g,'+').replace(/_/g,'/');try{raw=decodeURIComponent(raw)}catch(_){}while(raw.length%4)raw+='=';return Uint8Array.from(atob(raw),c=>c.charCodeAt(0));}return new Uint8Array(await (await fetch(str)).arrayBuffer());}if(/^https?:/i.test(str)){try{return new Uint8Array(await (await fetchRetry(str,{mode:'cors',cache:'no-store'},15000,2)).arrayBuffer());}catch(_){const proxy='https://images.weserv.nl/?url='+encodeURIComponent(str);const r=await fetchRetry(proxy,{mode:'cors',cache:'no-store'},20000,2);if(!r.ok)throw new Error('Foto Finding tidak dapat diambil ('+r.status+').');return new Uint8Array(await r.arrayBuffer());}}throw new Error('Sumber gambar Word harus URL Central atau data lokal yang valid.');}"\nif old_data in s:\n    s = s.replace(old_data, new_data, 1)\n\n# Always use the built-in ZIP fallback when CDN JSZip is unavailable.\ns = s.replace("if(!window.JSZip) throw new Error('Mesin Word DOCX belum siap. Pastikan internet aktif sekali untuk memuat JSZip.');", "if(!window.JSZip){throw new Error('Mesin DOCX lokal tidak tersedia.');}", 1)\n\n# Keep PDF endpoint separate from Finding Notes endpoint.\nmarker = 'const PDF_UPLOAD_URL = '\nidx = s.find(marker)\nif idx < 0:\n    raise SystemExit('PDF_UPLOAD_URL constant not found')\nline_end = s.find('\\n', idx)\nif 'const STT_FINDING_CENTRAL_URL' not in s:\n    s = s[:line_end+1] + f'const STT_FINDING_CENTRAL_URL = {FINDING_URL!r};\\n' + s[line_end+1:]\n\np.write_text(s, encoding='utf-8')\nprint('STT Finding Notes + hardened DOCX patch applied')\n'''\# This constructed content has an invalid nested repr approach; create directly below instead.
print("skip")
