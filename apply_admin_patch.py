from pathlib import Path
import re

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

# ---------------------------------------------------------------------------
# 1) Restore the baseline defaults without changing any baseline feature code.
# ---------------------------------------------------------------------------
s = s.replace(
    "let companyName = localStorage.getItem('patrol_company_name_v1') || '';",
    "let companyName = localStorage.getItem('patrol_company_name_v1') || 'STT DATA CENTRES';",
    1,
)
s = s.replace(
    "let companyAddress = localStorage.getItem('patrol_company_address_v1') || '';",
    "let companyAddress = localStorage.getItem('patrol_company_address_v1') || 'KAWASAN INDUSTRI DELTAMAS GIIC\\nCIKARANG PUSAT KABUPATEN BEKASI';",
    1,
)

# ---------------------------------------------------------------------------
# 2) Existing baseline unlock handlers remain the real owners of the state.
#    ADMIN simply authorizes them; no duplicate gallery/logo implementations.
# ---------------------------------------------------------------------------
old_gallery = """    unlockBtn?.addEventListener('click', () => {\n      const pw = passwordInput?.value || '';\n      if (pw === getGalleryPassword()) {"""
new_gallery = """    unlockBtn?.addEventListener('click', () => {\n      if (window.allsttAdminUnlocked) {\n        galleryAccessGranted = true;\n        if(access) access.style.display='block';\n        if(passwordInput) passwordInput.value='';\n        try { renderAreas(); } catch(_) {}\n        return;\n      }\n      const pw = passwordInput?.value || '';\n      if (pw === getGalleryPassword()) {"""
if old_gallery not in s:
    raise SystemExit('Baseline gallery unlock handler not found')
s = s.replace(old_gallery, new_gallery, 1)

old_logo = """  document.getElementById('unlockLogoBtn')?.addEventListener('click', ()=>{\n    const pw=document.getElementById('logoPassword')?.value || '';\n    if(pw === getLogoUploadPassword()){"""
new_logo = """  document.getElementById('unlockLogoBtn')?.addEventListener('click', ()=>{\n    if (window.allsttAdminUnlocked) {\n      logoUnlocked=true;\n      const sec=document.getElementById('logoUploadSection');\n      if(sec) sec.style.display='block';\n      updateLogoPreviews();\n      return;\n    }\n    const pw=document.getElementById('logoPassword')?.value || '';\n    if(pw === getLogoUploadPassword()){"""
if old_logo not in s:
    raise SystemExit('Baseline logo unlock handler not found')
s = s.replace(old_logo, new_logo, 1)

# ---------------------------------------------------------------------------
# 3) Replace ONLY the old face double-tap bridge.  The baseline saveOfficerPhoto
#    function is kept intact and is called directly for gallery files; no
#    DataTransfer/file-input trick is used.
# ---------------------------------------------------------------------------
face_pattern = re.compile(
    r'<script id="ALLSTT-STT-FACE-GALLERY-FINAL">.*?</script>',
    re.S,
)
face_script = r'''<script id="ALLSTT-STT-FACE-GALLERY-FINAL">
(function(){
  'use strict';
  const DOUBLE_TAP_MS = 360;

  function install(){
    const face = document.getElementById('takeOfficerPhotoBtn');
    const cam = document.getElementById('officerPhotoInput');
    const gal = document.getElementById('officerGalleryInput');
    if(!face || !cam || !gal || face.dataset.allsttUnifiedFace === '1') return;

    // Remove baseline click listeners from this one button only, then restore
    // the exact same visual button with the requested 1-tap/2-tap behavior.
    const btn = face.cloneNode(true);
    btn.dataset.allsttUnifiedFace = '1';
    face.replaceWith(btn);

    gal.removeAttribute('multiple');
    gal.removeAttribute('capture');
    gal.setAttribute('accept','image/*');
    gal.style.display='none';

    let waiting = false;
    let timer = null;

    function reset(){
      waiting = false;
      if(timer){ clearTimeout(timer); timer = null; }
    }

    function camera(){
      reset();
      cam.value='';
      cam.setAttribute('accept','image/*');
      cam.setAttribute('capture','user');
      cam.click();
    }

    function gallery(){
      reset();
      if(window.allsttAdminUnlocked){
        gal.value='';
        gal.click();
        return;
      }
      if(typeof window.ALLSTT_ADMIN_GATE === 'function'){
        window.ALLSTT_ADMIN_GATE(function(){
          gal.value='';
          gal.click();
        });
      }
    }

    btn.addEventListener('click',function(e){
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      if(waiting){
        gallery();
        return;
      }
      waiting=true;
      timer=setTimeout(function(){
        if(waiting) camera();
      },DOUBLE_TAP_MS);
    },true);

    btn.addEventListener('dblclick',function(e){
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      gallery();
    },true);

    // Process the selected gallery image through the original baseline
    // saveOfficerPhoto(file) function. This is the Android-safe path.
    gal.addEventListener('change',async function(e){
      const file=e.target.files && e.target.files[0];
      if(!file) return;
      if(!window.allsttAdminUnlocked){
        e.target.value='';
        return;
      }
      try{
        if(typeof saveOfficerPhoto !== 'function') throw new Error('Fungsi foto wajah tidak tersedia.');
        showOverlay('Memproses foto wajah petugas...');
        setOverlayProgress(25);
        await saveOfficerPhoto(file);
        setOverlayProgress(100);
        hideOverlay();
      }catch(err){
        hideOverlay();
        alert('❌ Foto galeri gagal diproses: '+(err && err.message ? err.message : err));
      }finally{
        e.target.value='';
      }
    },true);
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',install,{once:true});
  else install();
  window.addEventListener('load',install);
  [300,800,1500,2500].forEach(ms=>setTimeout(install,ms));
})();
</script>'''
if not face_pattern.search(s):
    raise SystemExit('Baseline face gallery script not found')
s = face_pattern.sub(face_script, s, count=1)

# ---------------------------------------------------------------------------
# 4) One ADMIN gate.  It is the only password UI.  Successful ADMIN unlock
#    authorizes every existing baseline password-gated handler at once.
# ---------------------------------------------------------------------------
admin_layer = r'''<style id="ALLSTT-UNIFIED-ADMIN-CSS">
/* Ordinary users never see password controls or company administration. */
body:not(.allstt-admin-unlocked) #companySection,
body:not(.allstt-admin-unlocked) .nav-item[data-target="companySection"]{display:none!important}
#logoPassword,#unlockLogoBtn,#changeLogoPasswordBtn,
#cameraGalleryPassword,#unlockCameraGalleryBtn,#cameraGalleryAccess,
#currentGalleryPassword,#newGalleryPassword,#confirmGalleryPassword,
#changeGalleryPasswordBtn{display:none!important}
#allsttAdminGate{position:fixed;inset:0;display:none;align-items:center;justify-content:center;z-index:60000;background:rgba(2,8,23,.78);backdrop-filter:blur(8px);padding:20px}
#allsttAdminGate .allstt-admin-box{width:min(430px,100%);background:#fff;border-radius:20px;padding:24px;box-shadow:0 24px 60px rgba(0,0,0,.30)}
#allsttAdminGate input{width:100%;box-sizing:border-box;padding:14px 16px;margin:14px 0;border:2px solid #dbe2ea;border-radius:12px;font-size:17px}
#allsttAdminMenuPanel{display:none;margin:4px 12px 10px 12px;padding:10px;border-radius:12px;background:#eef4ff;border:1px solid #cddcff}
#allsttAdminMenuPanel button{width:100%;margin:4px 0;text-align:left}
body.allstt-admin-unlocked #allsttAdminMenuPanel{display:block}
</style>
<script id="ALLSTT-UNIFIED-ADMIN">
(function(){
  'use strict';
  const ADMIN_KEY='patrol_admin_password_v1';
  const DEFAULT_ADMIN_PASSWORD='mbahpritampan';
  let adminUnlocked=false;

  function el(id){return document.getElementById(id)}
  function getAdminPassword(){
    try{
      return localStorage.getItem(ADMIN_KEY)
        || localStorage.getItem('patrol_logo_password_v1')
        || localStorage.getItem('patrol_gallery_password_v1')
        || DEFAULT_ADMIN_PASSWORD;
    }catch(_){return DEFAULT_ADMIN_PASSWORD}
  }
  function syncPasswords(pw){
    try{
      localStorage.setItem(ADMIN_KEY,pw);
      localStorage.setItem('patrol_logo_password_v1',pw);
      localStorage.setItem('patrol_gallery_password_v1',pw);
    }catch(_){}
  }

  function ensureDefaultIdentity(){
    const name='STT DATA CENTRES';
    const address='KAWASAN INDUSTRI DELTAMAS GIIC\nCIKARANG PUSAT KABUPATEN BEKASI';
    const n=el('companyName'), a=el('companyAddress');
    if(n && !(n.value||'').trim()) n.value=name;
    if(a && !(a.value||'').trim()) a.value=address;
  }

  function openGate(after){
    if(adminUnlocked || window.allsttAdminUnlocked){ if(after) after(); return; }
    let g=el('allsttAdminGate');
    if(!g){
      g=document.createElement('div');
      g.id='allsttAdminGate';
      g.innerHTML='<div class="allstt-admin-box">'
        +'<h2 style="margin:0;color:#0b3d91"><i class="fas fa-user-shield"></i> ADMIN</h2>'
        +'<div style="margin-top:8px;color:#64748b">Masukkan password Admin. Satu login membuka seluruh fitur yang dilindungi.</div>'
        +'<input id="allsttAdminPassword" type="password" autocomplete="current-password" placeholder="Password Admin">'
        +'<div style="display:flex;gap:10px">'
        +'<button type="button" id="allsttAdminCancel" class="btn btn-ghost" style="flex:1">BATAL</button>'
        +'<button type="button" id="allsttAdminEnter" class="btn btn-primary" style="flex:1">MASUK</button>'
        +'</div></div>';
      document.body.appendChild(g);
      el('allsttAdminCancel').onclick=function(){g.style.display='none'};
      el('allsttAdminEnter').onclick=function(){unlock(after)};
      el('allsttAdminPassword').onkeydown=function(e){if(e.key==='Enter')unlock(after)};
    }
    g.style.display='flex';
    const f=el('allsttAdminPassword');
    if(f){f.value='';f.focus()}
  }

  function authorizeBaseline(pw){
    adminUnlocked=true;
    window.allsttAdminUnlocked=true;
    try{sessionStorage.setItem('allstt_admin_unlocked','1')}catch(_){}
    document.body.classList.add('allstt-admin-unlocked');
    syncPasswords(pw);

    // Authorize the existing baseline gallery handler.
    const gp=el('cameraGalleryPassword'), gu=el('unlockCameraGalleryBtn');
    if(gp) gp.value=pw;
    if(gu) gu.click();

    // Authorize the existing baseline logo/company handler.
    const lp=el('logoPassword'), lu=el('unlockLogoBtn');
    if(lp) lp.value=pw;
    if(lu) lu.click();

    ensureDefaultIdentity();
    // The baseline save handler owns the companyName/companyAddress variables.
    // Trigger it only after logoUnlocked has been granted by the baseline handler.
    const save=el('saveCompanyHeaderBtn');
    if(save) save.click();

    try{ if(typeof renderAreas==='function') renderAreas(); }catch(_){}
    try{ if(typeof updateAreaSelector==='function') updateAreaSelector(); }catch(_){}
  }

  function unlock(after){
    const f=el('allsttAdminPassword');
    const entered=(f && f.value ? f.value : '').trim();
    if(!entered){alert('Masukkan password Admin.');return}
    if(entered!==getAdminPassword()){
      alert('❌ Password Admin salah.');
      return;
    }
    authorizeBaseline(entered);
    const g=el('allsttAdminGate');if(g)g.style.display='none';
    alert('✅ ADMIN aktif. Semua fitur galeri, upload multiple, foto wajah galeri, logo, dan identitas perusahaan terbuka.');
    if(after) after();
  }

  function lock(){
    adminUnlocked=false;
    window.allsttAdminUnlocked=false;
    try{sessionStorage.removeItem('allstt_admin_unlocked')}catch(_){}
    document.body.classList.remove('allstt-admin-unlocked');
    const sec=el('logoUploadSection');if(sec)sec.style.display='none';
    const access=el('cameraGalleryAccess');if(access)access.style.display='none';
    const lp=el('logoPassword');if(lp)lp.value='';
    const gp=el('cameraGalleryPassword');if(gp)gp.value='';
    try{ if(typeof galleryAccessGranted!=='undefined') galleryAccessGranted=false; }catch(_){}
    try{ if(typeof logoUnlocked!=='undefined') logoUnlocked=false; }catch(_){}
    try{ if(typeof renderAreas==='function') renderAreas(); }catch(_){}
  }

  function installMenu(){
    const nav=document.getElementById('sideNav');
    if(!nav || el('allsttAdminMenu')) return;
    const divider=document.createElement('div');
    divider.className='nav-divider';
    nav.appendChild(divider);
    const b=document.createElement('button');
    b.type='button';b.id='allsttAdminMenu';b.className='nav-item';
    b.innerHTML='<i class="fas fa-user-shield"></i><span>ADMIN</span>';
    b.onclick=function(e){e.preventDefault();openGate()};
    nav.appendChild(b);

    const panel=document.createElement('div');
    panel.id='allsttAdminMenuPanel';
    panel.innerHTML='<button type="button" id="allsttAdminIdentity" class="btn btn-ghost"><i class="fas fa-building"></i> Pengaturan Identitas & Logo</button>'
      +'<button type="button" id="allsttAdminLock" class="btn btn-danger"><i class="fas fa-lock"></i> Kunci ADMIN</button>';
    nav.appendChild(panel);
    el('allsttAdminIdentity').onclick=function(){
      const c=el('companySection');
      if(c){c.style.display='block';c.scrollIntoView({behavior:'smooth',block:'start'})}
    };
    el('allsttAdminLock').onclick=function(){lock()};
  }

  // Public entry point used by the face-photo double-tap handler.
  window.ALLSTT_ADMIN_GATE=function(after){openGate(after)};

  function boot(){
    installMenu();
    ensureDefaultIdentity();
    // Always start locked unless this exact page session was already unlocked.
    let restored=false;
    try{restored=sessionStorage.getItem('allstt_admin_unlocked')==='1'}catch(_){}
    if(restored){
      const pw=getAdminPassword();
      authorizeBaseline(pw);
    }else{
      adminUnlocked=false;
      window.allsttAdminUnlocked=false;
      document.body.classList.remove('allstt-admin-unlocked');
      const c=el('companySection');if(c)c.style.display='none';
      const sec=el('logoUploadSection');if(sec)sec.style.display='none';
    }
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
  window.addEventListener('load',installMenu);
})();
</script>'''
if 'ALLSTT-UNIFIED-ADMIN' not in s:
    s=s.replace('</body>', admin_layer+'\n</body>', 1)

p.write_text(s,encoding='utf-8')
