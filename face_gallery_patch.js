(function(){
  'use strict';
  const PASSWORD = 'mbahpritampan';
  const SINGLE_DELAY = 280;

  function init(){
    const btn = document.getElementById('takeOfficerPhotoBtn');
    const cameraInput = document.getElementById('officerPhotoInput');
    const galleryInput = document.getElementById('officerGalleryInput');
    if(!btn || !cameraInput || !galleryInput) return false;

    ['officerGalleryPassword','unlockOfficerGalleryBtn','officerGalleryAccess'].forEach(id=>{
      const el=document.getElementById(id);
      if(el){
        const box=el.closest('div[style*="border-top"]') || el.parentElement;
        if(box) box.remove(); else el.remove();
      }
    });

    if(btn.dataset.faceGalleryPatch==='1') return true;
    btn.dataset.faceGalleryPatch='1';

    let timer=null;
    let double=false;

    const openCamera=()=>{
      // Keep capture="user" so one tap goes directly to the phone camera.
      cameraInput.setAttribute('capture','user');
      cameraInput.click();
    };

    const openGallery=()=>{
      const pw=window.prompt('🔐 Masukkan password untuk upload foto wajah dari galeri:');
      if(pw !== PASSWORD){
        if(pw !== null) window.alert('❌ Password salah.');
        return;
      }
      // No capture attribute: Android can present its normal image picker,
      // including available camera/gallery providers.
      galleryInput.removeAttribute('capture');
      galleryInput.click();
    };

    btn.addEventListener('click', function(e){
      e.preventDefault();
      e.stopImmediatePropagation();
      if(timer) clearTimeout(timer);
      timer=setTimeout(()=>{
        if(!double) openCamera();
        double=false;
        timer=null;
      }, SINGLE_DELAY);
    }, true);

    btn.addEventListener('dblclick', function(e){
      e.preventDefault();
      e.stopImmediatePropagation();
      if(timer) clearTimeout(timer);
      timer=null;
      double=true;
      openGallery();
      setTimeout(()=>double=false,50);
    }, true);

    galleryInput.addEventListener('change', async function(e){
      const file=e.target.files && e.target.files[0];
      if(!file) return;
      try{
        if(typeof showOverlay==='function') showOverlay('Memproses foto wajah dari galeri...');
        if(typeof setOverlayProgress==='function') setOverlayProgress(25);
        if(typeof saveOfficerPhoto==='function') await saveOfficerPhoto(file);
        if(typeof setOverlayProgress==='function') setOverlayProgress(100);
        if(typeof hideOverlay==='function') hideOverlay();
      }catch(err){
        if(typeof hideOverlay==='function') hideOverlay();
        window.alert('❌ Foto wajah dari galeri gagal diproses: '+(err&&err.message?err.message:'Kesalahan tidak diketahui.'));
      }finally{ galleryInput.value=''; }
    });

    return true;
  }

  if(!init()){
    const mo=new MutationObserver(()=>{ if(init()) mo.disconnect(); });
    mo.observe(document.documentElement,{childList:true,subtree:true});
    setTimeout(()=>mo.disconnect(),10000);
  }
})();
