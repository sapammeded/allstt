from pathlib import Path
import re

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

FINDING_URL = 'https://script.google.com/macros/s/AKfycbyAJ9CFiTESUWLiCF_x0APclk4U-Zd85jI6LfWjE22hN8nyS_9yDEf0-rYrObuwyf59lA/exec'

# 1) Finding Notes must use the Central Findings deployment, never the PDF service.
s = s.replace(
    "const API=(typeof PDF_UPLOAD_URL==='string'&&PDF_UPLOAD_URL.trim())?PDF_UPLOAD_URL.trim():'';",
    f"const API=(typeof STT_FINDING_CENTRAL_URL==='string'&&STT_FINDING_CENTRAL_URL.trim())?STT_FINDING_CENTRAL_URL.trim():{FINDING_URL!r};",
    1,
)

# 2) CENTRAL schema for the patrol-area Finding alert.
start = s.find('  function findingAlertHtml(areaName,areaKey){')
end = s.find('\n  // ==================== RENDER AREAS UI ====================', start)
if start >= 0 and end >= 0:
    block = '''  function findingAlertHtml(areaName,areaKey){
    const list=getActiveFindingNotesForArea(areaName,areaKey);
    if(!list.length) return '';
    const escLocal=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
    const photosLocal=f=>{
      const v=f?.photo_url;
      if(Array.isArray(v)) return v.map(x=>typeof x==='string'?x:String(x?.url||'')).filter(x=>/^https?:\\/\\//i.test(x));
      if(!v) return [];
      try{const a=JSON.parse(String(v));return Array.isArray(a)?a.map(x=>typeof x==='string'?x:String(x?.url||'')).filter(x=>/^https?:\\/\\//i.test(x)):[];}catch(_){return String(v).split(',').map(x=>x.trim()).filter(x=>/^https?:\\/\\//i.test(x));}
    };
    return `<div class="finding-area-alert"><div class="finding-area-title">⚠️ FINDING NOTES AKTIF (${list.length})</div>${list.map(f=>{const photos=photosLocal(f);return `<div class="finding-area-item"><div>${escLocal(f.description||'-')}</div>${photos.length?`<div class="finding-photo-strip">${photos.map(p=>`<img src="${escLocal(p)}" alt="Finding photo">`).join('')}</div>`:''}<div class="finding-area-meta">Status: ${escLocal(String(f.status||'OPEN').toUpperCase())} • Ditemukan: ${escLocal(f.created_at||'-')} • Petugas: ${escLocal(f.finder_name||'-')}</div></div>`;}).join('')}</div>`;
  }
'''
    s = s[:start] + block + s[end:]

# 3) FIXED is uppercase in Central.
s = s.replace(
    "return list.filter(f=>f&&f.status!=='fixed'&&((f.areaKey!=null&&String(f.areaKey)===key)||String(f.area||'').trim().toLowerCase()===target));",
    "return list.filter(f=>{const st=String(f?.status||'').toUpperCase();return f&&st!=='FIXED'&&((f.areaKey!=null&&String(f.areaKey)===key)||String(f.area_code||f.area||'').trim().toLowerCase()===target);});",
    1,
)

# 4) Correct Word helper for local photos and long text.
anchor = "    const zip=new JSZip(),media=[];let rid=1;"
if anchor not in s:
    raise SystemExit('DOCX anchor not found')
if 'async function photoDataWord(p)' not in s:
    s = s.replace(anchor, anchor + '''
    async function photoDataWord(p){
      if(p&&typeof p==='object'&&p.ref){const b=await idbGet(STORE_BLOBS,p.ref);return b?await blobToBase64(b):null;}
      return typeof p==='string'?p:null;
    }''', 1)

old_plines = "function pLines(lines,opt={}){return lines.map((x,i)=>pText(x,{...opt,after:i===lines.length-1?(opt.after??80):0})).join('');}"
new_plines = "function pLines(lines,opt={}){const raw=Array.isArray(lines)?lines:String(lines==null?'':lines).replace(/\\r/g,'').split('\\n'),a=[];raw.forEach(line=>{let r=String(line||'');if(!r){a.push('');return;}while(r.length>92){let cut=r.lastIndexOf(' ',92);if(cut<45)cut=92;a.push(r.slice(0,cut).trim());r=r.slice(cut).trim();}a.push(r);});return a.map((x,i)=>pText(x,{...opt,after:i===a.length-1?(opt.after??80):0})).join('');}"
if old_plines in s:
    s = s.replace(old_plines, new_plines, 1)

# 5) Finding Notes UI: larger, bold, red text, red-tinted background, no overflow.
s = s.replace(
    '#findingNotesSection .fn-finding-card{margin-top:14px;border:3px solid #dc2626;border-radius:16px;background:#fff;padding:16px;box-shadow:0 4px 16px rgba(15,23,42,.08)}',
    '#findingNotesSection .fn-finding-card{margin-top:14px;border:3px solid #dc2626;border-radius:16px;background:#fef2f2;padding:16px;box-shadow:0 4px 16px rgba(15,23,42,.08);min-width:0;overflow:hidden;overflow-wrap:anywhere}',
    1,
)
s = s.replace(
    '#findingNotesSection .fn-notes-box{width:100%;min-height:220px;box-sizing:border-box;border:3px solid #94a3b8;border-radius:13px;background:#fff;padding:15px;font-size:20px;line-height:1.55;font-weight:800;white-space:pre-wrap;overflow-wrap:anywhere;resize:vertical}',
    '#findingNotesSection .fn-notes-box{display:block;width:100%;max-width:100%;min-width:0;min-height:220px;box-sizing:border-box;border:3px solid #dc2626;border-radius:13px;background:#fee2e2;color:#991b1b;padding:15px;font-size:22px;line-height:1.58;font-weight:900;white-space:pre-wrap;overflow:auto;overflow-wrap:anywhere;word-break:break-word;resize:vertical}',
    1,
)
s = s.replace(
    '#findingNotesSection .fn-new-box textarea{width:100%;min-height:240px;box-sizing:border-box;font-size:20px;font-weight:800;line-height:1.55;padding:15px;border:3px solid #2563eb;border-radius:12px;resize:vertical}',
    '#findingNotesSection .fn-new-box textarea{display:block;width:100%;max-width:100%;min-width:0;min-height:240px;box-sizing:border-box;font-size:22px;font-weight:900;line-height:1.58;padding:15px;border:3px solid #dc2626;border-radius:12px;background:#fee2e2;color:#991b1b;resize:vertical;overflow:auto;overflow-wrap:anywhere;word-break:break-word}',
    1,
)

# 6) PDF Finding Notes: explicit red theme and dynamic wrapping/height.
old_pdf = """const meta1=`PENEMU: ${String(f.finder_name||'-')}`;
        const meta2=`TANGGAL: ${fmtDate(f.created_at)}  •  JAM: ${fmtTime(f.created_at)}`;
        const meta3=`STATUS: ${status(f.status)}`;
        const meta4=`AREA: ${String(f.area_code||area.name||'-')}  •  ID: ${String(f.finding_id||'-')}`;
        const noteH=16+descLines.length*5.1+18;
        if(y+noteH>H-25){footer();pdf.addPage();areaHeader(`AREA ${ai+1}: ${area.name||`Area ${ai+1}`} • FINDING NOTES`);y=47;}
        pdf.setFillColor(...FIND_BG);pdf.setDrawColor(...FIND_LINE);pdf.setLineWidth(.9);pdf.roundedRect(M,y,W-2*M,noteH,2.5,2.5,'FD');
        pdf.setFont('helvetica','bold');pdf.setFontSize(11);pdf.setTextColor(...FIND_TEXT);pdf.text('FINDING NOTES',M+6,y+7);
        pdf.setFont('helvetica','bold');pdf.setFontSize(10);pdf.setTextColor(...FIND_TEXT);pdf.text(descLines,M+6,y+14);
        let my=y+14+descLines.length*5.1+3;pdf.setFont('helvetica','bold');pdf.setFontSize(8.5);pdf.setTextColor(...FIND_TEXT);pdf.text(meta1,M+6,my);pdf.text(meta2,M+6,my+4.5);pdf.text(meta3,M+6,my+9);pdf.text(meta4,M+6,my+13.5);y+=noteH+9;"""
new_pdf = """const metaLines=[`PENEMU: ${String(f.finder_name||'-')}`,`TANGGAL: ${fmtDate(f.created_at)}  •  JAM: ${fmtTime(f.created_at)}`,`STATUS: ${status(f.status)}`,`AREA: ${String(f.area_code||area.name||'-')}  •  ID: ${String(f.finding_id||'-')}`].flatMap(v=>pdf.splitTextToSize(v,W-2*M-12));
        const noteH=18+descLines.length*6.4+metaLines.length*4.8+12;
        if(y+noteH>H-25){footer();pdf.addPage();areaHeader(`AREA ${ai+1}: ${area.name||`Area ${ai+1}`} • FINDING NOTES`);y=47;}
        pdf.setFillColor(254,226,226);pdf.setDrawColor(220,38,38);pdf.setLineWidth(1);pdf.roundedRect(M,y,W-2*M,noteH,2.5,2.5,'FD');
        pdf.setFont('helvetica','bold');pdf.setFontSize(12);pdf.setTextColor(185,28,28);pdf.text('FINDING NOTES',M+6,y+8);
        pdf.setFont('helvetica','bold');pdf.setFontSize(12);pdf.setTextColor(185,28,28);pdf.text(descLines,M+6,y+17);
        let my=y+17+descLines.length*6.4+4;pdf.setFont('helvetica','bold');pdf.setFontSize(9);pdf.setTextColor(185,28,28);pdf.text(metaLines,M+6,my);y+=noteH+10;"""
if old_pdf in s:
    s = s.replace(old_pdf, new_pdf, 1)

# 7) DOCX Finding Notes: larger red/bold text and red-tinted background.
old_word_block = """let fb=pText('FINDING NOTES',{bold:true,size:15,color:'7F1D1D',after:55})+pLines(descLines,{bold:true,size:11,color:'7F1D1D',after:55})+pText(`PENEMU: ${String(f.finder_name||'-')}`,{bold:true,size:9,color:'7F1D1D',after:25})+pText(`TANGGAL: ${fmtDate(f.created_at)} • JAM: ${fmtTime(f.created_at)}`,{bold:true,size:9,color:'7F1D1D',after:25})+pText(`STATUS: ${status(f.status)}`,{bold:true,size:9,color:'7F1D1D',after:25})+pText(`AREA: ${String(f.area_code||area.name||'-')} • ID: ${String(f.finding_id||'-')}`,{bold:true,size:9,color:'7F1D1D',after:60});
        body+=shadedBlock(fb,'FCE7F3','F472B6');"""
new_word_block = """let fb=pText('FINDING NOTES',{bold:true,size:17,color:'B91C1C',after:45})+pLines(descLines,{bold:true,size:14,color:'B91C1C',after:45})+pText(`PENEMU: ${String(f.finder_name||'-')}`,{bold:true,size:10,color:'B91C1C',after:22})+pText(`TANGGAL: ${fmtDate(f.created_at)} • JAM: ${fmtTime(f.created_at)}`,{bold:true,size:10,color:'B91C1C',after:22})+pText(`STATUS: ${status(f.status)}`,{bold:true,size:10,color:'B91C1C',after:22})+pText(`AREA: ${String(f.area_code||area.name||'-')} • ID: ${String(f.finding_id||'-')}`,{bold:true,size:10,color:'B91C1C',after:50});
        body+=shadedBlock(fb,'FEE2E2','DC2626');"""
if old_word_block in s:
    s = s.replace(old_word_block, new_word_block, 1)

# 8) Android WebView-safe DOCX writer. It is only a fallback; the CDN JSZip is
# still used when available. The fallback stores files uncompressed, which is
# fully valid for Office Open XML/DOCX.
mini_zip_js = r'''if(!window.JSZip){
  (function(){
    function crc32(u8){var c,t=crc32.t;if(!t){t=crc32.t=new Uint32Array(256);for(var n=0;n<256;n++){c=n;for(var k=0;k<8;k++)c=(c&1)?(0xEDB88320^(c>>>1)):(c>>>1);t[n]=c>>>0;}}var crc=0xFFFFFFFF;for(var i=0;i<u8.length;i++)crc=t[(crc^u8[i])&255]^(crc>>>8);return (crc^0xFFFFFFFF)>>>0;}
    function u16(n){return new Uint8Array([n&255,(n>>>8)&255]);}
    function u32(n){return new Uint8Array([n&255,(n>>>8)&255,(n>>>16)&255,(n>>>24)&255]);}
    function join(parts){var len=0;parts.forEach(function(p){len+=p.length;});var out=new Uint8Array(len),o=0;parts.forEach(function(p){out.set(p,o);o+=p.length;});return out;}
    function text(s){return new TextEncoder().encode(String(s));}
    async function toBytes(x){if(x instanceof Uint8Array)return x;if(x instanceof ArrayBuffer)return new Uint8Array(x);if(x instanceof Blob)return new Uint8Array(await x.arrayBuffer());return text(x);}
    function Zip(prefix,root){this.prefix=prefix||'';this.root=root||[];}
    Zip.prototype.folder=function(name){return new Zip(this.prefix+String(name).replace(/\/?$/,'/'),this.root);};
    Zip.prototype.file=function(name,data){this.root.push({name:this.prefix+String(name).replace(/^\/+/,''),data:data});return this;};
    Zip.prototype.generateAsync=async function(){var local=[],central=[],offset=0;for(var i=0;i<this.root.length;i++){var e=this.root[i],name=text(e.name),data=await toBytes(e.data),crc=crc32(data);var lh=join([u32(0x04034b50),u16(20),u16(0),u16(0),u16(0),u16(0),u32(crc),u32(data.length),u32(data.length),u16(name.length),u16(0),name,data]);local.push(lh);var ch=join([u32(0x02014b50),u16(20),u16(20),u16(0),u16(0),u16(0),u16(0),u32(crc),u32(data.length),u32(data.length),u16(name.length),u16(0),u16(0),u16(0),u16(0),u32(0),u32(offset),name]);central.push(ch);offset+=lh.length;}var cs=central.reduce(function(n,p){return n+p.length;},0),ls=local.reduce(function(n,p){return n+p.length;},0);var end=join([u32(0x06054b50),u16(0),u16(0),u16(this.root.length),u16(this.root.length),u32(cs),u32(ls),u16(0)]);return new Blob([join(local),join(central),end],{type:'application/vnd.openxmlformats-officedocument.wordprocessingml.document'});};
    window.JSZip=Zip;
  })();
}'''
if 'STT_MINI_ZIP_FALLBACK_V1' not in s:
    s = s.replace(
        "document.getElementById('genWordBtn')?.addEventListener('click', async ()=>{",
        "/* STT_MINI_ZIP_FALLBACK_V1 */\n" + mini_zip_js + "\ndocument.getElementById('genWordBtn')?.addEventListener('click', async ()=>{",
        1,
    )

# 9) Remote Drive images: direct CORS first, then CORS image proxy fallback.
old_data = "async function dataToBytes(data){const str=String(data||'').trim();if(!str)throw new Error('Data gambar kosong.');if(/^data:/i.test(str)){const comma=str.indexOf(',');if(comma<0)throw new Error('Data URL gambar tidak valid.');const meta=str.slice(0,comma).toLowerCase(),payload=str.slice(comma+1);if(meta.includes(';base64')){let raw=payload.replace(/\\s/g,'').replace(/-/g,'+').replace(/_/g,'/');try{raw=decodeURIComponent(raw)}catch(_){}while(raw.length%4)raw+='=';return Uint8Array.from(atob(raw),c=>c.charCodeAt(0));}return new Uint8Array(await (await fetch(str)).arrayBuffer());}if(/^https?:/i.test(str))return new Uint8Array(await (await fetchRetry(str,{mode:'cors',cache:'force-cache'},15000,2)).arrayBuffer());throw new Error('Sumber gambar Word harus URL Central atau data lokal yang valid.');}"
new_data = "async function dataToBytes(data){const str=String(data||'').trim();if(!str)throw new Error('Data gambar kosong.');if(/^data:/i.test(str)){const comma=str.indexOf(',');if(comma<0)throw new Error('Data URL gambar tidak valid.');const meta=str.slice(0,comma).toLowerCase(),payload=str.slice(comma+1);if(meta.includes(';base64')){let raw=payload.replace(/\\s/g,'').replace(/-/g,'+').replace(/_/g,'/');try{raw=decodeURIComponent(raw)}catch(_){}while(raw.length%4)raw+='=';return Uint8Array.from(atob(raw),c=>c.charCodeAt(0));}return new Uint8Array(await (await fetch(str)).arrayBuffer());}if(/^https?:/i.test(str)){try{return new Uint8Array(await (await fetchRetry(str,{mode:'cors',cache:'no-store'},15000,2)).arrayBuffer());}catch(_){const proxy='https://images.weserv.nl/?url='+encodeURIComponent(str);const r=await fetchRetry(proxy,{mode:'cors',cache:'no-store'},20000,2);if(!r.ok)throw new Error('Foto Finding tidak dapat diambil ('+r.status+').');return new Uint8Array(await r.arrayBuffer());}}throw new Error('Sumber gambar Word harus URL Central atau data lokal yang valid.');}"
if old_data in s:
    s = s.replace(old_data, new_data, 1)

# 10) Add the Finding Central URL constant once, next to the PDF URL.
marker = 'const PDF_UPLOAD_URL = '
idx = s.find(marker)
if idx < 0:
    raise SystemExit('PDF_UPLOAD_URL constant not found')
line_end = s.find('\n', idx)
if 'const STT_FINDING_CENTRAL_URL' not in s:
    s = s[:line_end+1] + f"const STT_FINDING_CENTRAL_URL = {FINDING_URL!r};\n" + s[line_end+1:]

p.write_text(s, encoding='utf-8')
print('STT hardening patch applied')
