// ALLSTT: officer face photo source switch.
// One tap: direct phone camera. Fast double tap: password prompt, then Android image picker.
(function setupOfficerFaceGallery(){
  const btn = document.getElementById('takeOfficerPhotoBtn');
  const cameraInput = document.getElementById('officerPhotoInput');
  const galleryInput = document.getElementById('officerGalleryInput');
  if(!btn || !cameraInput || !galleryInput) return;
  if(btn.dataset.officerFaceGalleryReady === '1') return;
  btn.dataset.officerFaceGalleryReady = '1';

  // Remove the old standalone gallery-password panel from the officer card.
  ['officerGalleryPassword','unlockOfficerGalleryBtn','officerGalleryAccess'].forEach(id=>{
    const el=document.getElementById(id);
    if(el){
      const box=el.closest('div[style*="border-top"]') || el.parentElement;
      if(box) box.remove(); else el.remove();
    }
  });

  const PASSWORD = 'mbahpritampan';
  const SINGLE_TAP_DELAY = 280;
  let timer = null;
  let doubleTap = false;

  function openCamera(){
    cameraInput.setAttribute('capture','user');
    cameraInput.value='';
    cameraInput.click();
  }

  function openProtectedGallery(){
    const pw = window.prompt('🔐 Masukkan password untuk upload foto wajah dari galeri:');
    if(pw !== PASSWORD){
      if(pw !== null) window.alert('❌ Password salah.');
      return;
    }
    // No capture attribute here: Android uses its normal image picker/provider list.
    galleryInput.removeAttribute('capture');
    galleryInput.value='';
    galleryInput.click();
  }

  // Capture phase + stopImmediatePropagation prevents the original single-click
  // listener from opening the camera before the double-tap decision is made.
  btn.addEventListener('click', function(e){
    e.preventDefault();
    e.stopImmediatePropagation();
    if(timer) clearTimeout(timer);
    timer=setTimeout(()=>{
      if(!doubleTap) openCamera();
      doubleTap=false;
      timer=null;
    }, SINGLE_TAP_DELAY);
  }, true);

  btn.addEventListener('dblclick', function(e){
    e.preventDefault();
    e.stopImmediatePropagation();
    if(timer) clearTimeout(timer);
    timer=null;
    doubleTap=true;
    openProtectedGallery();
    setTimeout(()=>doubleTap=false,50);
  }, true);

  galleryInput.addEventListener('change', async function(e){
    const file=e.target.files?.[0];
    galleryInput.value='';
    if(!file) return;
    try{
      showOverlay('Memproses foto wajah dari galeri...');
      setOverlayProgress(25);
      await saveOfficerPhoto(file);
      setOverlayProgress(100);
      hideOverlay();
      alert('✅ Foto wajah dari galeri berhasil dipasang.');
    }catch(err){
      hideOverlay();
      alert('❌ Foto wajah dari galeri gagal diproses: '+(err?.message||err));
    }
  });
})();
