from pathlib import Path
import re

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

# Remove ONLY previous ADMIN patches. Never remove baseline face/gallery logic.
s = re.sub(r'<script[^>]+id=["\']ALLSTT-ADMIN-CONTROLLER["\'][^>]*>.*?</script>', '', s, flags=re.S|re.I)
s = re.sub(r'<style[^>]+id=["\']ALLSTT-ADMIN-CSS["\'][^>]*>.*?</style>', '', s, flags=re.S|re.I)

# Remove legacy company menu item. Company settings are available only from ADMIN.
s = re.sub(r'<button[^>]+data-target=["\']companySection["\'][^>]*>.*?</button>', '', s, count=1, flags=re.S|re.I)

# Make the requested company identity the immutable default for normal users.
s = s.replace("let companyName = localStorage.getItem('patrol_company_name_v1') || '';", "let companyName = localStorage.getItem('patrol_company_name_v1') || 'STT DATA CENTRES';")
s = s.replace("let companyAddress = localStorage.getItem('patrol_company_address_v1') || '';", "let companyAddress = localStorage.getItem('patrol_company_address_v1') || 'KAWASAN INDUSTRI DELTAMAS GIIC\\nCIKARANG PUSAT KABUPATEN BEKASI';")

# Expose the existing baseline face-photo processor so gallery double-tap can use the same safe path.
needle = "  document.getElementById('takeOfficerPhotoBtn')?.addEventListener('click', ()=>{"
if needle in s and 'window.__ALLSTT_SAVE_OFFICER_PHOTO' not in s:
    s = s.replace(needle, "  window.__ALLSTT_SAVE_OFFICER_PHOTO = saveOfficerPhoto;\n\n" + needle, 1)

# Replace the old double-tap patch with a corrected implementation.
s = re.sub(r'<script[^>]+id=["\']ALLSTT-STT-FACE-GALLERY-FINAL["\'][^>]*>.*?</script>', '', s, flags=re.S|re.I)
face_patch = r'''<script id="ALLSTT-STT-FACE-GALLERY-FINAL">
(function(){
'use strict';
const DOUBLE_TAP_MS=360;
function adminPassword(){
  try{return typeof getLogoUploadPassword==='function'?getLogoUploadPassword():(typeof getGalleryPassword==='function'?getGalleryPassword():'mbahpritampan');}
  catch(_){return 'mbahpritampan';}
}
function install(){
  const face=document.getElementById('takeOfficerPhotoBtn');
  const cam=document.getElementById('officerPhotoInput');
  const gal=document.getElementById('officerGalleryInput');
  if(!face||!cam||!gal||face.dataset.faceFinalV2==='1') return;
  face.dataset.faceFinalV2='1';
  gal.style.display='none';
  gal.removeAttribute('capture');

  let waiting=false,timer=null;
  function reset(){waiting=false;if(timer){clearTimeout(timer);timer=null;}}
  function openCamera(){
    reset();
    cam.value='';
    cam.setAttribute('accept','image/*');
    cam.setAttribute('capture','user');
    cam.click();
  }
  function openGalleryWithPassword(){
    reset();
    const entered=window.prompt('Masukkan password untuk Upload Foto dari Galeri:');
    if(entered===null) return;
    if(entered!==adminPassword()){
      window.alert('❌ Password salah. Akses galeri ditolak.');
      return;
    }
    window.__ALLSTT_FACE_GALLERY_AUTH=true;
    gal.value='';
    gal.click();
  }

  // 1 tap = camera. 2 taps = password -> gallery.
  face.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();
    if(waiting){openGalleryWithPassword();return;}
    waiting=true;
    timer=setTimeout(function(){if(waiting)openCamera();},DOUBLE_TAP_MS);
  },true);

  // IMPORTANT: do not transfer a gallery file into the camera <input>.
  // Android WebView can reject DataTransfer/files assignment, which caused the old error.
  // Use the exact same baseline saveOfficerPhoto() processor directly instead.
  gal.addEventListener('change',async function(e){
    const file=e.target.files&&e.target.files[0];
    e.target.value='';
    if(!file) return;
    if(!window.__ALLSTT_FACE_GALLERY_AUTH){
      window.alert('🔒 Password diperlukan.');
      return;
    }
    window.__ALLSTT_FACE_GALLERY_AUTH=false;
    try{
      if(typeof window.__ALLSTT_SAVE_OFFICER_PHOTO!=='function') throw new Error('Fungsi foto wajah belum siap.');
      showOverlay('Memproses foto wajah dari galeri...');
      setOverlayProgress(25);
      await window.__ALLSTT_SAVE_OFFICER_PHOTO(file);
      setOverlayProgress(100);
      hideOverlay();
    }catch(err){
      hideOverlay();
      window.alert('❌ Foto wajah dari galeri gagal diproses: '+(err&&err.message?err.message:err));
    }
  },true);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});
else install();
window.addEventListener('load',install);
[300,800,1500,2500].forEach(ms=>setTimeout(install,ms));
})();
</script>'''
s = s.replace('</body>', face_patch + '\n</body>', 1)

controller = r'''<style id="ALLSTT-ADMIN-CSS">
/* NORMAL USER: patrol dashboard only. Company/logo controls are invisible and inaccessible. */
#companySection,#logoUploadSection{display:none!important}
#allsttAdminGate{position:fixed;inset:0;background:rgba(0,0,0,.72);z-index:30000;display:none;align-items:center;justify-content:center;padding:20px}
#allsttAdminGate .box{background:#fff;border-radius:18px;padding:24px;max-width:420px;width:100%;box-shadow:0 20px 50px rgba(0,0,0,.35)}
#allsttAdminGate input{width:100%;padding:14px;border:2px solid #dbe2ea;border-radius:12px;font-size:16px;margin:10px 0}
body.allstt-admin-unlocked #companySection,body.allstt-admin-unlocked #logoUploadSection{display:block!important}
#allsttAdminPanel{display:none;margin:14px 0;padding:18px;border:2px solid #0b3d91;border-radius:16px;background:#fff}
body.allstt-admin-unlocked #allsttAdminPanel{display:block}
</style>
<script id="ALLSTT-ADMIN-CONTROLLER">(function(){
'use strict';
var unlocked=false;
function q(s){return document.querySelector(s)}
function qa(s){return Array.prototype.slice.call(document.querySelectorAll(s))}
function protect(){
  if(unlocked) return;
  ['#companySection','#logoUploadSection'].forEach(function(id){var e=q(id);if(e)e.style.display='none'});
  qa('input[type=file]').forEach(function(e){
    var id=(e.id||'').toLowerCase();
    if(id.indexOf('logo')>=0) e.style.display='none';
  });
}
function getAdminPassword(){
  try{return typeof getLogoUploadPassword==='function'?getLogoUploadPassword():(typeof getGalleryPassword==='function'?getGalleryPassword():'mbahpritampan');}
  catch(e){return 'mbahpritampan';}
}
function unlock(){
  var field=q('#allsttAdminPassword');
  var pass=field?field.value:'';
  if(pass!==getAdminPassword()){
    alert('❌ Password admin salah.');
    return;
  }
  unlocked=true;
  window.allsttAdminUnlocked=true;
  window.allsttGalleryUnlocked=true;
  document.body.classList.add('allstt-admin-unlocked');
  try{window.logoUnlocked=true;}catch(e){}
  var m=q('#allsttAdminGate');if(m)m.style.display='none';
  if(field)field.value='';
  protect();
  qa('input[type=file]').forEach(function(e){
    var id=(e.id||'').toLowerCase();
    if(id.indexOf('logo')>=0)e.style.display='';
  });
  var sec=q('#companySection');if(sec)sec.style.display='block';
  var logo=q('#logoUploadSection');if(logo)logo.style.display='block';
  try{renderAreas();}catch(e){}
  alert('✅ Password benar. Mode ADMIN aktif.');
}
function gate(){
  var m=q('#allsttAdminGate');
  if(!m){
    m=document.createElement('div');m.id='allsttAdminGate';
    m.innerHTML='<div class="box"><h2 style="margin:0 0 8px;color:#0b3d91"><i class="fas fa-user-shield"></i> ADMIN</h2><div style="color:#64748b">Fitur admin hanya dapat digunakan oleh pengguna yang mengetahui password admin.</div><input id="allsttAdminPassword" type="password" autocomplete="current-password" placeholder="Password admin"><div style="display:flex;gap:8px"><button id="allsttAdminCancel" type="button" class="btn btn-ghost" style="flex:1">BATAL</button><button id="allsttAdminLogin" type="button" class="btn btn-primary" style="flex:1">MASUK</button></div></div>';
    document.body.appendChild(m);
    q('#allsttAdminCancel').onclick=function(){m.style.display='none'};
    q('#allsttAdminLogin').onclick=unlock;
    q('#allsttAdminPassword').onkeydown=function(e){if(e.key==='Enter')unlock()};
  }
  m.style.display='flex';
  q('#allsttAdminPassword').value='';
  q('#allsttAdminPassword').focus();
}
function addAdmin(){
  if(q('[data-allstt-admin-menu="1"]'))return;
  var b=document.createElement('button');b.type='button';b.className='nav-item';b.setAttribute('data-allstt-admin-menu','1');b.innerHTML='<i class="fas fa-user-shield"></i><span>ADMIN</span>';b.onclick=function(e){e.preventDefault();gate()};
  var host=qa('.side-nav')[0];
  if(host)host.appendChild(b);
}
function addPanel(){
  if(q('#allsttAdminPanel'))return;
  var company=q('#companySection');
  if(!company)return;
  var panel=document.createElement('div');panel.id='allsttAdminPanel';
  panel.innerHTML='<div style="font-weight:900;color:#0b3d91"><i class="fas fa-user-shield"></i> MODE ADMIN AKTIF</div><div style="font-size:13px;color:#64748b;margin-top:5px">Identitas perusahaan, logo kiri/kanan, dan multiple upload galeri sekarang dapat digunakan.</div><button id="allsttAdminLock" type="button" class="btn btn-ghost" style="margin-top:10px;width:100%">KUNCI KEMBALI ADMIN</button>';
  company.parentNode.insertBefore(panel,company);
  q('#allsttAdminLock').onclick=function(){
    unlocked=false;window.allsttAdminUnlocked=false;window.allsttGalleryUnlocked=false;document.body.classList.remove('allstt-admin-unlocked');
    try{window.logoUnlocked=false;}catch(e){}
    protect();try{renderAreas();}catch(e){}
  };
}
function init(){protect();addAdmin();addPanel();setTimeout(function(){addAdmin();addPanel();if(!unlocked)protect()},500)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();</script>'''
s = s.replace('</head>', controller + '</head>', 1)

# Patrol multiple-upload controls are ADMIN-only. Do not alter the single face-photo double-tap flow.
s = s.replace("if (!(galleryAccessGranted || window.allsttGalleryUnlocked)) { alert('🔒 Masukkan password terlebih dahulu.'); return; }", "if (!window.allsttAdminUnlocked) { alert('🔒 Fitur multiple upload galeri hanya tersedia untuk ADMIN.'); return; }")
s = s.replace("if (!(galleryAccessGranted || window.allsttGalleryUnlocked)) { galleryInput.value=''; return; }", "if (!window.allsttAdminUnlocked) { galleryInput.value=''; return; }")
s = s.replace("const galleryButton = (galleryAccessGranted || window.allsttGalleryUnlocked) ?", "const galleryButton = window.allsttAdminUnlocked ?")
s = s.replace("if (galleryAccessGranted || window.allsttGalleryUnlocked) {", "if (window.allsttAdminUnlocked) {")

# Hide legacy password/change-password UI from normal users; ADMIN is the only password entry point.
s = re.sub(r'\s*<!-- PENGATURAN PASSWORD GALERI -->.*?</div>\s*<!-- Tombol Tambah Area untuk Camera Tab -->', '\n        <!-- ADMIN controls gallery access; normal users only have camera. -->\n        <!-- Tombol Tambah Area untuk Camera Tab -->', s, count=1, flags=re.S|re.I)

p.write_text(s, encoding='utf-8')
