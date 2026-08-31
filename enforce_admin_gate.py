from pathlib import Path

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

marker = 'ALLSTT-FINAL-ADMIN-GATE-V1'
if marker in s:
    raise SystemExit('final admin gate already present')

script = r'''<style id="ALLSTT-FINAL-ADMIN-GATE-CSS">
/* FINAL POLICY: baseline UI remains; only privileged actions are locked. */
body:not(.allstt-admin-unlocked) #companySection,
body:not(.allstt-admin-unlocked) .nav-item[data-target="companySection"]{
  display:none !important;
}
body:not(.allstt-admin-unlocked) #logoUploadSection{
  display:none !important;
}
body:not(.allstt-admin-unlocked) #companyName,
body:not(.allstt-admin-unlocked) #companyAddress{
  pointer-events:none !important;
  opacity:.72;
}
</style>
<script id="ALLSTT-FINAL-ADMIN-GATE-V1">
(function(){
  'use strict';
  var CAMERA_IDS={nativeCameraInput:true, officerPhotoInput:true};

  function admin(){ return window.allsttAdminUnlocked===true; }
  function byId(id){ return document.getElementById(id); }

  function sync(){
    var ok=admin();
    document.body.classList.toggle('allstt-admin-unlocked',ok);

    var company=byId('companySection');
    if(company) company.style.display=ok ? '' : 'none';
    var logo=byId('logoUploadSection');
    if(logo && !ok) logo.style.display='none';

    ['companyName','companyAddress'].forEach(function(id){
      var x=byId(id); if(!x) return;
      x.disabled=!ok;
      x.readOnly=!ok;
      x.setAttribute('aria-disabled',String(!ok));
    });

    document.querySelectorAll('input[type="file"]').forEach(function(x){
      var id=x.id||'';
      var isCamera=!!CAMERA_IDS[id];
      /* Camera is public. Every gallery/file upload is ADMIN-only. */
      x.disabled=(!ok && !isCamera);
      x.setAttribute('aria-disabled',String(!ok && !isCamera));
    });

    /* Existing gallery access panels are visible only to ADMIN. */
    ['cameraGalleryAccess','galleryAccess','logoUploadSection'].forEach(function(id){
      var x=byId(id); if(x && !ok) x.style.display='none';
    });
  }

  function watchAdmin(){
    var last=null;
    setInterval(function(){
      var now=admin();
      if(now!==last){ last=now; sync(); }
      else sync();
    },250);
  }

  /* Never let an ordinary user open a protected file chooser by script. */
  document.addEventListener('click',function(e){
    var t=e.target && e.target.closest ? e.target.closest('input[type="file"]') : null;
    if(!t || CAMERA_IDS[t.id]) return;
    if(!admin()){
      e.preventDefault();
      e.stopImmediatePropagation();
      alert('Akses galeri hanya setelah ADMIN berhasil login.');
    }
  },true);

  document.addEventListener('change',function(e){
    var t=e.target;
    if(!t || t.type!=='file' || CAMERA_IDS[t.id] || admin()) return;
    try{t.value='';}catch(_){ }
    alert('Akses galeri hanya setelah ADMIN berhasil login.');
  },true);

  function boot(){
    sync();
    watchAdmin();
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();
</script>'''

s=s.replace('</body>',script+'\n</body>',1)
p.write_text(s,encoding='utf-8')
