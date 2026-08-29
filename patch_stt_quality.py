from pathlib import Path
import re

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

DEFAULT_DESC = 'Kegiatan patroli area tersebut telah selesai dilaksanakan dengan hasil situasi terpantau terkendali aman dan kondusif, temuan menonjol serta kendala operasional nihil.'

# Upgrade photo processing: keep substantially more source resolution and JPEG quality.
s = s.replace('function compressDataUrl(dataUrl, quality=0.9, maxSize=1920)', 'function compressDataUrl(dataUrl, quality=0.98, maxSize=4096)')
s = s.replace('const compressed = await compressDataUrl(raw, 0.88, 1200);', 'const compressed = await compressDataUrl(raw, 0.98, 2400);')
s = s.replace('const comp = await compressDataUrl(data,0.9,1920);', 'const comp = await compressDataUrl(data,0.98,4096);')
s = s.replace('const comp=await compressDataUrl(data,0.9,1920);', 'const comp=await compressDataUrl(data,0.98,4096);')
s = s.replace('const re = await compressDataUrl(p, 0.85, 1600);', 'const re = await compressDataUrl(p, 0.98, 4096);')

marker = 'const DEFAULT_LOGO_URL = "https://i.ibb.co.com/dJV2bjQR/IMG-20251123-001741.png";'
if 'const DEFAULT_PATROL_DESCRIPTION =' not in s:
    s = s.replace(marker, marker + '\n\nconst DEFAULT_PATROL_DESCRIPTION = ' + repr(DEFAULT_DESC) + ';', 1)

s = s.replace("area.descriptions.push('TERKENDALI AMAN');", "area.descriptions.push(DEFAULT_PATROL_DESCRIPTION);")
s = s.replace("patrolData[k].descriptions.push('TERKENDALI AMAN');", "patrolData[k].descriptions.push(DEFAULT_PATROL_DESCRIPTION);")
s = s.replace("const currentDesc = a.descriptions[idx] || 'TERKENDALI AMAN';", "const currentDesc = a.descriptions[idx] || DEFAULT_PATROL_DESCRIPTION;")
s = s.replace("a.descriptions[idx] = newDesc === '' ? 'TERKENDALI AMAN' : newDesc;", "a.descriptions[idx] = newDesc === '' ? DEFAULT_PATROL_DESCRIPTION : newDesc;")
s = s.replace("const desc = String(area.descriptions?.[i] || 'TERKENDALI AMAN').trim() || 'TERKENDALI AMAN';", "const desc = String(area.descriptions?.[i] || DEFAULT_PATROL_DESCRIPTION).trim() || DEFAULT_PATROL_DESCRIPTION;")

# Remove telephone and email inputs from the Company / Letterhead tab.
s = re.sub(r'\s*<div class="col">\s*<label class="small">EMAIL PERUSAHAAN</label>\s*<input id="companyEmail".*?</div>\s*', '\n', s, count=1, flags=re.S)
s = re.sub(r'\s*<div class="col">\s*<label class="small">TELEPON / HOTLINE</label>\s*<input id="companyPhone".*?</div>\s*', '\n', s, count=1, flags=re.S)

# Existing premium letterhead CSS is preserved. If an older STT does not have it, add it.
if 'ALLSTT premium letterhead editor' not in s:
    premium_css = '''\n<style id="ALLSTT premium letterhead editor">\n#companySection { background:linear-gradient(145deg,#fff,#f8fbff); border:1px solid #dbe5f0; border-left:6px solid #0b3d91; border-radius:20px; padding:24px; box-shadow:0 10px 28px rgba(15,23,42,.10); }\n#companySection > label:first-child { display:block; font-size:20px; font-weight:900; letter-spacing:.3px; color:#0b3d91; text-transform:none; }\n#companySection .small { line-height:1.55; }\n#companySection input,#companySection textarea { font-size:16px; }\n</style>\n'''
    s = s.replace('</head>', premium_css + '</head>', 1)

# Filename: Petugas_DD-MM-YYYY_SHIFT.pdf
old_filename = "const filename = `Laporan_Patroli_${safe(petugas)}_${safe(tanggal)}.pdf`;"
new_filename = """const filenameDate = /^\\d{4}-\\d{2}-\\d{2}$/.test(tanggal)\n        ? tanggal.split('-').reverse().join('-')\n        : safe(tanggal || new Date().toISOString().slice(0,10));\n      const filenameShift = safe((document.getElementById('shift')?.value || shift || '').trim()).replace(/_+/g,'_') || 'SHIFT';\n      const filename = `${safe(petugas || 'Petugas')}_${filenameDate}_${filenameShift}.pdf`;"""
s = s.replace(old_filename, new_filename)

# Robust autosave/recovery. Additive: preserves existing patrolData + IndexedDB photo storage.
autosave_patch = r'''
<!-- ALLSTT ROBUST AUTOSAVE V2 -->
<script id="ALLSTT-robust-autosave">
(function(){
  'use strict';
  const KEY='allstt_stt_draft_v2';
  let timer=null, restoring=false;
  function el(id){return document.getElementById(id)}
  function snapshot(){
    const fields={};
    document.querySelectorAll('input,select,textarea').forEach(e=>{
      if(!e.id || e.type==='file' || e.type==='password') return;
      fields[e.id]=(e.type==='checkbox'||e.type==='radio') ? !!e.checked : (e.value ?? '');
    });
    return {version:2,savedAt:Date.now(),fields};
  }
  function saveNow(){
    if(restoring) return;
    try{
      if(typeof persistMeta==='function') persistMeta();
      localStorage.setItem(KEY,JSON.stringify(snapshot()));
      localStorage.setItem('allstt_autosave_at',String(Date.now()));
    }catch(e){console.warn('ALLSTT autosave',e)}
  }
  function restore(){
    restoring=true;
    try{
      const raw=localStorage.getItem(KEY); if(!raw) return;
      const d=JSON.parse(raw); if(!d || d.version!==2 || !d.fields) return;
      Object.entries(d.fields).forEach(([id,v])=>{
        const e=el(id); if(!e || e.type==='file' || e.type==='password') return;
        if(e.type==='checkbox'||e.type==='radio') e.checked=!!v; else e.value=v;
      });
    }catch(e){console.warn('ALLSTT draft restore',e)}
    finally{restoring=false}
  }
  function schedule(){clearTimeout(timer);timer=setTimeout(saveNow,250)}
  function start(){
    restore();
    document.addEventListener('input',schedule,{passive:true});
    document.addEventListener('change',schedule,{passive:true});
    document.addEventListener('blur',schedule,true);
    window.addEventListener('pagehide',saveNow);
    window.addEventListener('beforeunload',saveNow);
    document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')saveNow()});
    setInterval(saveNow,15000);
    setTimeout(saveNow,800);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',start,{once:true}); else start();
})();
</script>
'''
if 'id="ALLSTT-robust-autosave"' not in s:
    s = s.replace('</body>', autosave_patch + '\n</body>', 1)

p.write_text(s, encoding='utf-8')
print('STT patch applied: letterhead, filename, default description, robust autosave.')
