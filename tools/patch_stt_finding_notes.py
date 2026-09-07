from pathlib import Path
import re

p = Path('stt.html')
s = p.read_text(encoding='utf-8')
FINDING_URL = 'https://script.google.com/macros/s/AKfycbyAJ9CFiTESUWLiCF_x0APclk4U-Zd85jI6LfWjE22hN8nyS_9yDEf0-rYrObuwyf59lA/exec'

# Dedicated CENTRAL endpoint for Finding Notes.
if 'STT_FINDING_CENTRAL_URL' not in s:
    s = s.replace('const PDF_UPLOAD_URL = ', f"const STT_FINDING_CENTRAL_URL = {FINDING_URL!r};\n    const PDF_UPLOAD_URL = ", 1)
s = s.replace("const API=(typeof PDF_UPLOAD_URL==='string'&&PDF_UPLOAD_URL.trim())?PDF_UPLOAD_URL.trim():'';", f"const API=(typeof STT_FINDING_CENTRAL_URL==='string'&&STT_FINDING_CENTRAL_URL.trim())?STT_FINDING_CENTRAL_URL.trim():{FINDING_URL!r};", 1)

# CENTRAL schema for the area warning.
start = s.find('  function findingAlertHtml(areaName,areaKey){')
end = s.find('\n  // ==================== RENDER AREAS UI ====================', start)
if start >= 0 and end >= 0:
    s = s[:start] + '''  function findingAlertHtml(areaName,areaKey){
    const list=getActiveFindingNotesForArea(areaName,areaKey); if(!list.length) return '';
    const escLocal=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
    const photosLocal=f=>{const v=f?.photo_url;if(Array.isArray(v))return v.map(x=>typeof x==='string'?x:String(x?.url||'')).filter(x=>/^https?:\\/\\//i.test(x));if(!v)return [];try{const a=JSON.parse(String(v));return Array.isArray(a)?a.map(x=>typeof x==='string'?x:String(x?.url||'')).filter(x=>/^https?:\\/\\//i.test(x)):[];}catch(_){return String(v).split(',').map(x=>x.trim()).filter(x=>/^https?:\\/\\//i.test(x));}};
    return `<div class="finding-area-alert"><div class="finding-area-title">⚠️ FINDING NOTES AKTIF (${list.length})</div>${list.map(f=>{const photos=photosLocal(f);return `<div class="finding-area-item"><div class="finding-note-description">${escLocal(f.description||f.content||'-')}</div>${photos.length?`<div class="finding-photo-strip">${photos.map(q=>`<img src="${escLocal(q)}" alt="Finding photo">`).join('')}</div>`:''}<div class="finding-area-meta">Status: ${escLocal(String(f.status||'OPEN').toUpperCase())} • Ditemukan: ${escLocal(f.created_at||f.foundAt||'-')} • Petugas: ${escLocal(f.finder_name||f.foundBy||'-')}</div></div>`;}).join('')}</div>`;
  }
''' + s[end:]

# FIXED is not an active warning.
s = re.sub(r"return list\.filter\(f=>f&&f\.status!=='fixed'&&\(\(f\.areaKey!=null&&String\(f\.areaKey\)===key\)\|\|String\(f\.area\|\|'\'\)\.trim\(\)\.toLowerCase\(\)===target\)\);", "return list.filter(f=>{const st=String(f?.status||'').toUpperCase();return f&&st!=='FIXED'&&((f.areaKey!=null&&String(f.areaKey)===key)||String(f.area_code||f.area||'').trim().toLowerCase()===target);});", s, count=1)

# Android-safe DOCX ZIP fallback. No CDN dependency is required for export.
if 'window.STTMiniZip' not in s:
    marker='// ==================== WORD EXPORT — CENTRAL FINDING NOTES CONTRACT ===================='
    mini=r'''// ==================== WORD EXPORT ZIP ENGINE (ANDROID SAFE) ====================
(function(){
  if(window.STTMiniZip)return;
  function crc32(b){let c=0xffffffff;for(let i=0;i<b.length;i++){c^=b[i];for(let k=0;k<8;k++)c=(c>>>1)^((c&1)?0xedb88320:0);}return(c^0xffffffff)>>>0;}
  function u16(a,n){a.push(n&255,(n>>>8)&255)} function u32(a,n){a.push(n&255,(n>>>8)&255,(n>>>16)&255,(n>>>24)&255)}
  function enc(v){return new TextEncoder().encode(String(v??''));}
  async function bytes(v){if(v instanceof Uint8Array)return v;if(v instanceof ArrayBuffer)return new Uint8Array(v);if(v instanceof Blob)return new Uint8Array(await v.arrayBuffer());return enc(v);}
  class MiniZip{
    constructor(prefix='',root=null){this.prefix=prefix;this.root=root||this;this.entries=this.root===this?[]:this.root.entries;}
    folder(name){return new MiniZip(this.prefix+String(name).replace(/\/?$/,'')+'/',this.root);}
    file(name,data){this.entries.push({name:this.prefix+String(name).replace(/^\//,''),data});return this;}
    async generateAsync(){const local=[],central=[],offs=[];let off=0;for(const e of this.entries){const n=enc(e.name),b=await bytes(e.data),c=crc32(b),h=[];u32(h,0x04034b50);u16(h,20);u16(h,0);u16(h,0);u16(h,0);u16(h,0);u32(h,c);u32(h,b.length);u32(h,b.length);u16(h,n.length);u16(h,0);local.push(new Uint8Array([...h,...n,...b]));offs.push(off);off+=h.length+n.length+b.length;}for(let i=0;i<this.entries.length;i++){const e=this.entries[i],n=enc(e.name),b=await bytes(e.data),c=crc32(b),h=[];u32(h,0x02014b50);u16(h,20);u16(h,20);u16(h,0);u16(h,0);u16(h,0);u16(h,0);u32(h,c);u32(h,b.length);u32(h,b.length);u16(h,n.length);u16(h,0);u16(h,0);u16(h,0);u16(h,0);u16(h,0);u32(h,0);u32(h,offs[i]);central.push(new Uint8Array([...h,...n]));}const cd=central.reduce((n,x)=>n+x.length,0),body=local.reduce((n,x)=>n+x.length,0),end=[];u32(end,0x06054b50);u16(end,0);u16(end,0);u16(end,this.entries.length);u16(end,this.entries.length);u32(end,cd);u32(end,body);u16(end,0);return new Blob([...local,...central,new Uint8Array(end)],{type:'application/zip'});}
  }
  window.STTMiniZip=MiniZip;
})();

'''
    pos=s.find(marker)
    if pos<0: raise SystemExit('Word export marker not found')
    s=s[:pos]+mini+s[pos:]

s=s.replace("    if(!window.JSZip) throw new Error('Mesin Word DOCX belum siap. Pastikan internet aktif sekali untuk memuat JSZip.');\n",'',1)
s=s.replace("const zip=new JSZip(),media=[];let rid=1;","const zip=new (window.JSZip||window.STTMiniZip)(),media=[];let rid=1;",1)

# Word images must be actual bytes, not remote URL strings.
old='''    async function photoDataWord(p){
      if(p&&typeof p==='object'&&p.ref){
        const b=await idbGet(STORE_BLOBS,p.ref);
        return b?await blobToBase64(b):null;
      }
      return typeof p==='string'?p:null;
    }'''
new='''    async function photoDataWord(p){
      if(p&&typeof p==='object'&&p.ref){const b=await idbGet(STORE_BLOBS,p.ref);return b?await blobToBase64(b):null;}
      const src=String(p||'').trim(); if(!src)return null; if(/^data:image\\//i.test(src))return src;
      if(/^https?:\\/\\//i.test(src)){
        try{const r=await fetchRetry(src,{mode:'cors',cache:'no-store'},15000,2);if(r.ok)return await blobToBase64(await r.blob());}catch(_){ }
        try{const img=new Image();img.crossOrigin='anonymous';await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=reject;img.src=src;});const c=document.createElement('canvas');c.width=img.naturalWidth||img.width;c.height=img.naturalHeight||img.height;c.getContext('2d').drawImage(img,0,0);return c.toDataURL('image/jpeg',0.9);}catch(_){return null;}
      }
      return null;
    }'''
if old in s:s=s.replace(old,new,1)

# Long Word descriptions are split into safe paragraphs.
old_pl="function pLines(lines,opt={}){const a=Array.isArray(lines)?lines:String(lines==null?'':lines).split(/\\r?\\n/);return a.map((x,i)=>pText(x,{...opt,after:i===a.length-1?(opt.after??80):0})).join('');}"
new_pl="function pLines(lines,opt={}){const raw=Array.isArray(lines)?lines:String(lines==null?'':lines).replace(/\\r/g,'').split('\\n'),a=[];raw.forEach(line=>{let r=String(line||'');if(!r){a.push('');return;}while(r.length>92){let cut=r.lastIndexOf(' ',92);if(cut<45)cut=92;a.push(r.slice(0,cut).trim());r=r.slice(cut).trim();}a.push(r);});return a.map((x,i)=>pText(x,{...opt,after:i===a.length-1?(opt.after??80):0})).join('');}"
if old_pl in s:s=s.replace(old_pl,new_pl,1)

# Screen Finding Notes style.
s=re.sub(r"#findingNotesSection \.fn-finding-card\{[^}]*\}","#findingNotesSection .fn-finding-card{margin-top:14px;border:3px solid #dc2626;border-radius:16px;background:#fef2f2;padding:16px;box-shadow:0 4px 16px rgba(15,23,42,.08);min-width:0;overflow:hidden;overflow-wrap:anywhere}",s,count=1)
s=re.sub(r"#findingNotesSection \.fn-notes-box\{[^}]*\}","#findingNotesSection .fn-notes-box{display:block;width:100%;max-width:100%;min-width:0;min-height:220px;box-sizing:border-box;border:3px solid #dc2626;border-radius:13px;background:#fee2e2;color:#991b1b;padding:15px;font-size:22px;line-height:1.58;font-weight:900;white-space:pre-wrap;overflow:auto;overflow-wrap:anywhere;word-break:break-word;resize:vertical}",s,count=1)
s=re.sub(r"#findingNotesSection \.fn-new-box textarea\{[^}]*\}","#findingNotesSection .fn-new-box textarea{display:block;width:100%;max-width:100%;min-width:0;min-height:240px;box-sizing:border-box;font-size:22px;font-weight:900;line-height:1.58;padding:15px;border:3px solid #dc2626;border-radius:12px;background:#fee2e2;color:#991b1b;resize:vertical;overflow:auto;overflow-wrap:anywhere;word-break:break-word}",s,count=1)

# PDF Finding Notes: dynamic height, wrapped metadata, larger bold red text on light-red block.
pat=re.compile(r"const descLines=pdf\.splitTextToSize\(findingText\(f\),W-2\*M-12\);\s*const metaLines=\[[\s\S]*?y\+=noteH\+9;")
m=pat.search(s)
if m:
    rep="""const descLines=pdf.splitTextToSize(findingText(f),W-2*M-12);\n        const metaLines=[`PENEMU: ${String(f.finder_name||'-')}`,`TANGGAL: ${fmtDate(f.created_at)}  •  JAM: ${fmtTime(f.created_at)}`,`STATUS: ${status(f.status)}`,`AREA: ${String(f.area_code||area.name||'-')}  •  ID: ${String(f.finding_id||'-')}`].flatMap(v=>pdf.splitTextToSize(v,W-2*M-12));\n        const noteH=20+descLines.length*6.4+metaLines.length*4.8+12;\n        if(y+noteH>H-25){footer();pdf.addPage();areaHeader(`AREA ${ai+1}: ${area.name||`Area ${ai+1}`} • FINDING NOTES`);y=47;}\n        pdf.setFillColor(254,226,226);pdf.setDrawColor(220,38,38);pdf.setLineWidth(1);pdf.roundedRect(M,y,W-2*M,noteH,2.5,2.5,'FD');\n        pdf.setFont('helvetica','bold');pdf.setFontSize(12);pdf.setTextColor(185,28,28);pdf.text('FINDING NOTES',M+6,y+8);\n        pdf.setFont('helvetica','bold');pdf.setFontSize(12);pdf.setTextColor(185,28,28);pdf.text(descLines,M+6,y+18);\n        let my=y+18+descLines.length*6.4+4;pdf.setFont('helvetica','bold');pdf.setFontSize(9);pdf.setTextColor(185,28,28);pdf.text(metaLines,M+6,my);y+=noteH+10;"""
    s=s[:m.start()]+rep+s[m.end():]

# DOCX Finding Notes: same red visual contract.
s=s.replace("let fb=pText('FINDING NOTES',{bold:true,size:15,color:'7F1D1D',after:55})+pLines(descLines,{bold:true,size:11,color:'7F1D1D',after:55})+pText(`PENEMU: ${String(f.finder_name||'-')}`,{bold:true,size:9,color:'7F1D1D',after:25})+pText(`TANGGAL: ${fmtDate(f.created_at)} • JAM: ${fmtTime(f.created_at)}`,{bold:true,size:9,color:'7F1D1D',after:25})+pText(`STATUS: ${status(f.status)}`,{bold:true,size:9,color:'7F1D1D',after:25})+pText(`AREA: ${String(f.area_code||area.name||'-')} • ID: ${String(f.finding_id||'-')}`,{bold:true,size:9,color:'7F1D1D',after:60});\n        body+=shadedBlock(fb,'FCE7F3','F472B6');","let fb=pText('FINDING NOTES',{bold:true,size:17,color:'B91C1C',after:45})+pLines(descLines,{bold:true,size:14,color:'B91C1C',after:45})+pText(`PENEMU: ${String(f.finder_name||'-')}`,{bold:true,size:10,color:'B91C1C',after:22})+pText(`TANGGAL: ${fmtDate(f.created_at)} • JAM: ${fmtTime(f.created_at)}`,{bold:true,size:10,color:'B91C1C',after:22})+pText(`STATUS: ${status(f.status)}`,{bold:true,size:10,color:'B91C1C',after:22})+pText(`AREA: ${String(f.area_code||area.name||'-')} • ID: ${String(f.finding_id||'-')}`,{bold:true,size:10,color:'B91C1C',after:50});\n        body+=shadedBlock(fb,'FEE2E2','DC2626');",1)

# Image conversion errors must not kill the whole Word document.
s=s.replace("for(const m of media){const bytes=await dataToBytes(m.raw);zip.folder('word').folder('media').file(m.path.split('/').pop(),bytes);}","for(const m of media){try{const bytes=await dataToBytes(m.raw);zip.folder('word').folder('media').file(m.path.split('/').pop(),bytes);}catch(err){console.warn('[WORD] Skipping image:',m.path,err);}}",1)

p.write_text(s,encoding='utf-8')
