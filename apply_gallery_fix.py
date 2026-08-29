from pathlib import Path
import re

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

# Remove all previous injected face handlers so only this controller remains.
for sid in [
    'ALLSTT-STT-FACE-GALLERY-V7',
    'ALLSTT-STT-RUNTIME-FIX-V5',
    'ALLSTT-STT-FACE-GALLERY-V6',
    'ALLSTT-STT-FACE-GALLERY-V5',
    'ALLSTT-STT-FACE-GALLERY-FINAL',
]:
    s = re.sub(r'<script[^>]*id=["\\\']' + re.escape(sid) + r'["\\\'][^>]*>.*?</script>', '', s, flags=re.I | re.S)

# The original app keeps galleryAccessGranted inside its main async closure.
# Add a session flag that the existing render/change logic can safely consult.
s = s.replace('galleryAccessGranted ?', '(galleryAccessGranted || window.allsttGalleryUnlocked) ?')
s = s.replace('if (!galleryAccessGranted)', 'if (!(galleryAccessGranted || window.allsttGalleryUnlocked))')
s = s.replace('if(!galleryAccessGranted)', 'if(!(galleryAccessGranted || window.allsttGalleryUnlocked))')

patch = r'''<script id="ALLSTT-STT-FACE-GALLERY-FINAL">
(function(){
  'use strict';
  const PASSWORD='mbahpritampan';
  const DOUBLE_TAP_MS=380;

  function expectedPassword(){
    try { return typeof getGalleryPassword==='function' ? getGalleryPassword() : PASSWORD; }
    catch(_) { return PASSWORD; }
  }

  function unlockPatrolGallery(){
    // This session flag is consumed by the existing STT render/change logic.
    // It is never persisted, so the password is required again on a new session.
    window.allsttGalleryUnlocked=true;
    try { if(typeof renderAreas==='function') renderAreas(); } catch(_) {}
    try { if(typeof updateAreaSelector==='function') updateAreaSelector(); } catch(_) {}
  }

  function install(){
    const face=document.getElementById('takeOfficerPhotoBtn');
    const cam=document.getElementById('officerPhotoInput');
    const gal=document.getElementById('officerGalleryInput');
    if(!face || !cam || !gal || face.dataset.faceFinal==='1') return;
    face.dataset.faceFinal='1';

    // No standalone gallery/password card is visible before the protected gesture.
    ['officerGalleryAccess','officerGalleryPassword','unlockOfficerGalleryBtn','uploadOfficerGalleryBtn'].forEach(function(id){
      const el=document.getElementById(id);
      if(el){
        const card=el.closest('.card');
        if(card && card!==face.closest('.card')) card.remove();
        else el.remove();
      }
    });

    // Clone removes every legacy face-button handler so one tap and two taps
    // have exactly one deterministic meaning.
    const btn=face.cloneNode(true);
    btn.dataset.faceFinal='1';
    face.replaceWith(btn);

    cam.removeAttribute('multiple');
    cam.setAttribute('accept','image/*');
    gal.removeAttribute('capture');
    gal.setAttribute('accept','image/*');
    gal.removeAttribute('multiple');
    gal.style.display='none';

    let pending=false;
    let timer=null;
    function reset(){
      pending=false;
      if(timer){clearTimeout(timer);timer=null;}
    }

    function openCamera(){
      reset();
      cam.setAttribute('capture','user');
      cam.value='';
      cam.click();
    }

    function openProtectedGallery(){
      reset();
      const pw=window.prompt('Masukkan password mbahpritampan untuk upload foto wajah dari galeri:');
      if(pw===null) return;
      if(pw!==expectedPassword()){
        window.alert('❌ Password salah. Akses galeri ditolak.');
        return;
      }
      unlockPatrolGallery();
      gal.value='';
      gal.removeAttribute('capture');
      gal.setAttribute('accept','image/*');
      gal.click();
    }

    // 1x tap -> camera. Wait briefly so a second fast tap can be detected.
    btn.addEventListener('click',function(e){
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      if(pending){ openProtectedGallery(); return; }
      pending=true;
      timer=setTimeout(function(){ if(pending) openCamera(); },DOUBLE_TAP_MS);
    },true);

    // Native dblclick fallback for Android WebView/browser gesture handling.
    btn.addEventListener('dblclick',function(e){
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      openProtectedGallery();
    },true);

    // Gallery photo uses the same original officer-photo pipeline.
    gal.addEventListener('change',async function(){
      const file=gal.files && gal.files[0];
      if(!file) return;
      try{
        if(typeof saveOfficerPhoto==='function') await saveOfficerPhoto(file);
        else if(typeof window.saveOfficerPhoto==='function') await window.saveOfficerPhoto(file);
        else throw new Error('Fungsi penyimpanan foto wajah tidak tersedia.');
        const st=document.getElementById('officerPhotoStatus');
        if(st) st.textContent='✅ Foto wajah dari galeri siap dimasukkan ke PDF.';
      }catch(err){
        window.alert('❌ Foto galeri gagal diproses: '+(err && err.message ? err.message : err));
      }finally{
        gal.value='';
      }
    },true);
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',install,{once:true});
  else install();
  window.addEventListener('load',install);
  [300,800,1500,2500].forEach(function(ms){setTimeout(install,ms);});
})();
</script>'''

s = s.replace('</body>', patch + '\n</body>', 1)
p.write_text(s, encoding='utf-8')
