from pathlib import Path
import re

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

# Multiple gallery uploads should be silent; the existing processing overlay is enough feedback.
s = s.replace("      alert('✅ Foto berhasil ditambahkan ke '+area.name);\n", "", 1)

# Remove a prior generated copy so retries stay idempotent.
s = re.sub(r'<style id="ALLSTT-FINAL-ADMIN-GATE-CSS">.*?</script>\s*', '', s, count=1, flags=re.S)

script = r'''<style id="ALLSTT-FINAL-ADMIN-GATE-CSS">
/* Protected actions ask for ADMIN; ordinary UI remains visible. */
#companySection,
.nav-item[data-target="companySection"]{display:block !important;}
body:not(.allstt-admin-unlocked) #companyName,
body:not(.allstt-admin-unlocked) #companyAddress{
  background:#f8fafc !important;
  color:#64748b !important;
  cursor:pointer !important;
}
#logoPassword,#unlockLogoBtn,#changeLogoPasswordBtn{display:inline-flex !important;}
body:not(.allstt-admin-unlocked) #logoUploadSection{display:none !important;}
</style>
<script id="ALLSTT-FINAL-ADMIN-GATE-V1">
(function(){
  'use strict';
  var CAMERA_IDS={nativeCameraInput:true};
  function admin(){ return window.allsttAdminUnlocked===true; }
  function byId(id){ return document.getElementById(id); }
  function sync(){
    var ok=admin();
    document.body.classList.toggle('allstt-admin-unlocked',ok);
    var company=byId('companySection');
    if(company) company.style.display='block';
    ['companyName','companyAddress'].forEach(function(id){
      var x=byId(id); if(!x) return;
      x.readOnly=!ok; x.disabled=false;
      x.setAttribute('aria-readonly',String(!ok));
      x.style.cursor=ok?'text':'pointer';
    });
    var logo=byId('logoUploadSection');
    if(logo && !ok) logo.style.display='none';
    document.querySelectorAll('input[type="file"]').forEach(function(x){
      var isCamera=!!CAMERA_IDS[x.id||''];
      x.disabled=false;
      x.setAttribute('aria-disabled',String(!ok && !isCamera));
    });
  }
  function requestAdmin(after){
    if(admin()){ if(after) after(); return; }
    if(typeof window.ALLSTT_ADMIN_GATE==='function'){
      window.ALLSTT_ADMIN_GATE(function(){ sync(); if(after) after(); });
    } else alert('🔒 Masukkan password ADMIN terlebih dahulu.');
  }
  document.addEventListener('click',function(e){
    var t=e.target;
    if(!t || !t.id || admin()) return;
    if(t.id==='companyName' || t.id==='companyAddress'){
      e.preventDefault(); e.stopImmediatePropagation();
      requestAdmin(function(){ t.readOnly=false; try{t.focus();}catch(_){} });
    }
  },true);
  document.addEventListener('click',function(e){
    var t=e.target && e.target.closest ? e.target.closest('input[type="file"]') : null;
    if(!t || CAMERA_IDS[t.id] || admin()) return;
    e.preventDefault(); e.stopImmediatePropagation();
    requestAdmin(function(){ try{ t.click(); }catch(_){} });
  },true);
  document.addEventListener('change',function(e){
    var t=e.target;
    if(!t || t.type!=='file' || CAMERA_IDS[t.id] || admin()) return;
    try{t.value='';}catch(_){}
  },true);
  function boot(){ sync(); setInterval(sync,250); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();
</script>'''

if 'ALLSTT-FINAL-ADMIN-GATE-V1' not in s:
    s=s.replace('</body>',script+'\n</body>',1)

p.write_text(s,encoding='utf-8')
