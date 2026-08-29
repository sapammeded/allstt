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

if 'ALLSTT premium letterhead editor' not in s:
    premium_css = '''\n<style id="ALLSTT premium letterhead editor">\n#companySection { background:linear-gradient(145deg,#fff,#f8fbff); border:1px solid #dbe5f0; border-left:6px solid #0b3d91; border-radius:20px; padding:24px; box-shadow:0 10px 28px rgba(15,23,42,.10); }\n#companySection > label:first-child { display:block; font-size:20px; font-weight:900; letter-spacing:.3px; color:#0b3d91; text-transform:none; }\n#companySection .small { line-height:1.55; }\n#companySection input,#companySection textarea { font-size:16px; }\n</style>\n'''
    s = s.replace('</head>', premium_css + '</head>', 1)

old_filename = "const filename = `Laporan_Patroli_${safe(petugas)}_${safe(tanggal)}.pdf`;"
new_filename = """const filenameDate = /^\\d{4}-\\d{2}-\\d{2}$/.test(tanggal)\n        ? tanggal.split('-').reverse().join('-')\n        : safe(tanggal || new Date().toISOString().slice(0,10));\n      const filenameShift = safe((document.getElementById('shift')?.value || shift || '').trim()).replace(/_+/g,'_') || 'SHIFT';\n      const filename = `${safe(petugas || 'Petugas')}_${filenameDate}_${filenameShift}.pdf`;"""
s = s.replace(old_filename, new_filename)

# Password-protected officer photo gallery upload.
officer_html_marker = '<input id="officerPhotoInput" type="file" accept="image/*" capture="user" style="display:none">'
officer_html_add = '''<input id="officerPhotoInput" type="file" accept="image/*" capture="user" style="display:none">
        <input id="officerGalleryInput" type="file" accept="image/*" multiple style="display:none">
        <div style="width:100%;margin-top:14px;padding-top:14px;border-top:1px solid #e2e8f0">
          <div style="font-weight:800;margin-bottom:8px"><i class="fas fa-lock"></i> UPLOAD FOTO WAJAH DARI GALERI</div>
          <div class="small" style="margin-bottom:10px">Fitur ini hanya dapat digunakan setelah password galeri dimasukkan dengan benar.</div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            <input id="officerGalleryPassword" type="password" placeholder="Masukkan password..." style="flex:1;min-width:180px">
            <button id="unlockOfficerGalleryBtn" type="button" class="btn btn-primary"><i class="fas fa-unlock"></i> BUKA</button>
          </div>
          <div id="officerGalleryAccess" style="display:none;margin-top:10px">
            <div class="quality-notice"><i class="fas fa-check-circle"></i> Akses galeri foto wajah aktif.</div>
            <button id="uploadOfficerGalleryBtn" type="button" class="btn btn-info" style="width:100%;margin-top:10px"><i class="fas fa-images"></i> UPLOAD FOTO WAJAH DARI GALERI</button>
          </div>
        </div>'''
if 'id="officerGalleryInput"' not in s:
    if officer_html_marker in s:
        s = s.replace(officer_html_marker, officer_html_add, 1)
    else:
        print('Officer photo input marker not found; continuing without HTML gallery reinjection')

officer_js_marker = '''  document.getElementById('takeOfficerPhotoBtn')?.addEventListener('click',()=>{
    const input = document.getElementById('officerPhotoInput');
    if(input) input.click();
  });'''
officer_js_add = '''  document.getElementById('takeOfficerPhotoBtn')?.addEventListener('click',()=>{
    const input = document.getElementById('officerPhotoInput');
    if(input) input.click();
  });

  // Password-protected officer photo gallery upload.
  let officerGalleryAccessGranted = false;
  document.getElementById('unlockOfficerGalleryBtn')?.addEventListener('click', ()=>{
    const pw = document.getElementById('officerGalleryPassword')?.value || '';
    if (pw === getGalleryPassword()) {
      officerGalleryAccessGranted = true;
      const access = document.getElementById('officerGalleryAccess');
      const input = document.getElementById('officerGalleryPassword');
      if (access) access.style.display = 'block';
      if (input) input.value = '';
      alert('✅ Akses upload foto wajah dari galeri dibuka.');
    } else {
      officerGalleryAccessGranted = false;
      alert('❌ Password salah!');
    }
  });

  document.getElementById('uploadOfficerGalleryBtn')?.addEventListener('click', ()=>{
    if (!officerGalleryAccessGranted) {
      alert('🔒 Masukkan password terlebih dahulu.');
      return;
    }
    document.getElementById('officerGalleryInput')?.click();
  });

  document.getElementById('officerGalleryInput')?.addEventListener('change', (e)=>{
    if (!officerGalleryAccessGranted) {
      e.target.value = '';
      alert('🔒 Akses galeri belum dibuka.');
      return;
    }
    const file = e.target.files?.[0];
    if (!file) return;
    const cameraInput = document.getElementById('officerPhotoInput');
    try {
      const dt = new DataTransfer();
      dt.items.add(file);
      cameraInput.files = dt.files;
      cameraInput.dispatchEvent(new Event('change', { bubbles: true }));
    } catch (err) {
      alert('❌ Foto dari galeri gagal diproses.');
      console.error(err);
    } finally {
      e.target.value = '';
    }
  });'''
if 'id="uploadOfficerGalleryBtn"' not in s:
    if officer_js_marker in s:
        s = s.replace(officer_js_marker, officer_js_add, 1)
    else:
        print('Officer camera handler marker not found; continuing without JS gallery reinjection')

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

startup_fix = r'''
<!-- ALLSTT STARTUP + FACE CAMERA DOUBLE-TAP FIX -->
<script id="ALLSTT-startup-camera-fix">
(function(){
  'use strict';
  function install(){
    const modal=document.getElementById('notificationModal');
    const btn=document.getElementById('aamiinBtn');
    if(btn && !btn.dataset.allsttContinueFix){
      btn.dataset.allsttContinueFix='1';
      btn.addEventListener('click',function(e){
        e.preventDefault(); e.stopPropagation();
        if(modal) modal.style.display='none';
        try{localStorage.setItem('bangPriNotif','dilihat')}catch(_){ }
      },true);
    }

    const cameraBtn=document.getElementById('openCameraMenu');
    const nativeInput=document.getElementById('nativeCameraInput');
    const galleryInput=document.getElementById('galleryCameraInput');
    if(!cameraBtn || !nativeInput || cameraBtn.dataset.allsttCameraFix) return;
    cameraBtn.dataset.allsttCameraFix='1';

    let timer=null, waiting=false;
    const DOUBLE_TAP_MS=330;
    function openCamera(){
      nativeInput.value='';
      nativeInput.click();
    }
    function password(){
      const pw=window.prompt('Masukkan password galeri foto wajah:');
      if(pw===null) return false;
      let expected='';
      try{ expected=(typeof getGalleryPassword==='function') ? getGalleryPassword() : ''; }catch(_){ expected=''; }
      if(!expected || pw!==expected){ window.alert('❌ Password salah!'); return false; }
      return true;
    }
    function openCameraGalleryChooser(){
      if(!password()) return;
      if(galleryInput){
        galleryInput.removeAttribute('capture');
        galleryInput.value='';
        galleryInput.click();
      }
    }
    cameraBtn.addEventListener('click',function(e){
      e.preventDefault(); e.stopImmediatePropagation();
      if(waiting){
        waiting=false; if(timer) clearTimeout(timer); timer=null;
        openCameraGalleryChooser();
        return;
      }
      waiting=true;
      timer=setTimeout(function(){
        if(!waiting) return;
        waiting=false; timer=null;
        openCamera();
      },DOUBLE_TAP_MS);
    },true);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',install,{once:true});
  else install();
})();
</script>
'''
if 'id="ALLSTT-startup-camera-fix"' not in s:
    s = s.replace('</body>', startup_fix + '\n</body>', 1)

p.write_text(s, encoding='utf-8')
print('STT patch applied.')
