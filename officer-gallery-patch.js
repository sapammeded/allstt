// ALLSTT: protected officer face photo source switch.
// 1 tap = camera. 2 fast taps = password, then Android gallery/image chooser.
(function setupOfficerFaceGallery(){
  function install(){
    const oldBtn = document.getElementById('takeOfficerPhotoBtn');
    const cameraInput = document.getElementById('officerPhotoInput');
    const galleryInput = document.getElementById('officerGalleryInput');
    if(!oldBtn || !cameraInput || !galleryInput || oldBtn.dataset.officerFaceGalleryReady==='1') return;

    // Remove the visible standalone gallery/password controls. The hidden
    // gallery input stays available only for the protected double-tap flow.
    ['officerGalleryPassword','unlockOfficerGalleryBtn','officerGalleryAccess','uploadOfficerGalleryBtn'].forEach(function(id){
      const el=document.getElementById(id);
      if(!el)return;
      const card=el.closest('.card') || el.closest('[style*="border-top"]') || el.parentElement;
      if(card && card!==oldBtn && card!==document.body) card.remove(); else el.remove();
    });

    // Clone the button so every legacy click/double-click listener is removed.
    const btn=oldBtn.cloneNode(true);
    btn.dataset.officerFaceGalleryReady='1';
    oldBtn.replaceWith(btn);

    const PASSWORD='mbahpritampan';
    const DELAY=360;
    let timer=null;
    let secondTap=false;

    function clearTimer(){
      if(timer){clearTimeout(timer);timer=null;}
      secondTap=false;
    }

    function openCamera(){
      clearTimer();
      cameraInput.setAttribute('capture','user');
      cameraInput.value='';
      cameraInput.click();
    }

    function openProtectedGallery(){
      clearTimer();
      const pw=window.prompt('Masukkan password untuk upload foto wajah dari galeri:');
      if(pw===null)return;
      if(pw!==PASSWORD){
        window.alert('❌ Password salah. Akses ditolak.');
        return;
      }
      galleryInput.removeAttribute('capture');
      galleryInput.setAttribute('accept','image/*');
      galleryInput.value='';
      galleryInput.click();
    }

    // One tap waits briefly before opening camera. A second fast tap converts
    // the pending action into the protected gallery flow.
    btn.addEventListener('click',function(e){
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      if(timer){
        clearTimeout(timer);
        timer=null;
        secondTap=true;
        openProtectedGallery();
        return;
      }
      timer=setTimeout(function(){
        if(secondTap)return;
        openCamera();
      },DELAY);
    },true);

    galleryInput.addEventListener('change',function(){
      const file=galleryInput.files && galleryInput.files[0];
      if(!file)return;
      try{
        // Reuse the original officer camera input's existing change handler.
        // This preserves the app's current IndexedDB/preview/PDF pipeline.
        const dt=new DataTransfer();
        dt.items.add(file);
        cameraInput.files=dt.files;
        cameraInput.dispatchEvent(new Event('change',{bubbles:true}));
      }catch(err){
        window.alert('❌ Foto galeri gagal diproses: '+(err&&err.message||err));
      }finally{
        galleryInput.value='';
      }
    },true);
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',install,{once:true});
  else install();
  window.addEventListener('load',install);
  [300,800,1500,2500].forEach(function(ms){setTimeout(install,ms);});
})();
