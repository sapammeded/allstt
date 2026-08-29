// ALLSTT STT face-photo interaction patch
// 1 tap  -> direct camera
// 2 quick taps -> password prompt, then Android camera/gallery chooser
// Existing standalone face-gallery card is removed.
(function(){
  'use strict';
  const PASSWORD = 'mbahpritampan';
  const DOUBLE_TAP_MS = 320;
  let tapTimer = null;
  let busy = false;

  function findFaceButton(){
    const els = Array.from(document.querySelectorAll('button, .btn, input[type="button"], input[type="submit"]'));
    return els.find(el => /foto\s+wajah/i.test((el.textContent || el.value || '').trim())) || null;
  }

  function removeStandaloneGalleryCard(){
    const all = Array.from(document.querySelectorAll('body *'));
    const target = all.find(el => {
      if (!el.children || el.children.length > 8) return false;
      const txt = (el.textContent || '').replace(/\s+/g,' ').trim();
      return /UPLOAD\s+FOTO\s+WAJAH\s+DARI\s+GALERI/i.test(txt) && el !== document.body;
    });
    if(target){
      let card = target.closest('.card');
      if(!card) card = target;
      card.remove();
    }
  }

  function makeInput(id, capture){
    let input = document.getElementById(id);
    if(input) return input;
    input = document.createElement('input');
    input.type = 'file';
    input.id = id;
    input.accept = 'image/*';
    if(capture) input.setAttribute('capture', capture);
    input.style.cssText = 'position:fixed;left:-99999px;top:-99999px;width:1px;height:1px;opacity:0;pointer-events:none;';
    document.body.appendChild(input);
    return input;
  }

  function makeModal(){
    let modal = document.getElementById('sttFaceGalleryPasswordModal');
    if(modal) return modal;
    modal = document.createElement('div');
    modal.id = 'sttFaceGalleryPasswordModal';
    modal.style.cssText = 'position:fixed;inset:0;z-index:999999;background:rgba(0,0,0,.72);display:flex;align-items:center;justify-content:center;padding:20px;';
    modal.innerHTML = `
      <div style="width:min(430px,94vw);background:#fff;border-radius:22px;padding:26px;box-shadow:0 20px 60px rgba(0,0,0,.35);font-family:inherit">
        <div style="font-size:21px;font-weight:800;color:#0b3d91;margin-bottom:10px">🔐 AKSES GALERI FOTO WAJAH</div>
        <div style="font-size:15px;color:#64748b;margin-bottom:16px">Masukkan password untuk membuka kamera dan galeri HP.</div>
        <input id="sttFaceGalleryPassword" type="password" autocomplete="off" placeholder="Masukkan password..." style="width:100%;padding:15px 16px;border:2px solid #e2e8f0;border-radius:14px;font-size:17px;box-sizing:border-box;margin-bottom:14px">
        <div id="sttFaceGalleryPasswordError" style="display:none;color:#dc2626;font-weight:700;font-size:14px;margin-bottom:12px">Password salah.</div>
        <div style="display:flex;gap:10px;justify-content:flex-end">
          <button type="button" id="sttFaceGalleryCancel" style="border:0;border-radius:12px;padding:13px 18px;font-weight:700;background:#e2e8f0;color:#1e293b">BATAL</button>
          <button type="button" id="sttFaceGalleryOpen" style="border:0;border-radius:12px;padding:13px 20px;font-weight:800;background:linear-gradient(135deg,#0b3d91,#4f46e5);color:#fff">BUKA</button>
        </div>
      </div>`;
    document.body.appendChild(modal);
    const close=()=>{ modal.remove(); busy=false; };
    modal.querySelector('#sttFaceGalleryCancel').onclick=close;
    modal.querySelector('#sttFaceGalleryOpen').onclick=()=>{
      const val=modal.querySelector('#sttFaceGalleryPassword').value;
      if(val !== PASSWORD){
        modal.querySelector('#sttFaceGalleryPasswordError').style.display='block';
        modal.querySelector('#sttFaceGalleryPassword').focus();
        return;
      }
      close();
      makeInput('sttFaceChooser', false).click();
    };
    modal.querySelector('#sttFaceGalleryPassword').addEventListener('keydown',e=>{
      if(e.key==='Enter') modal.querySelector('#sttFaceGalleryOpen').click();
      if(e.key==='Escape') close();
    });
    setTimeout(()=>modal.querySelector('#sttFaceGalleryPassword').focus(),50);
    return modal;
  }

  function install(){
    removeStandaloneGalleryCard();
    const button=findFaceButton();
    if(!button || button.dataset.sttFacePatchInstalled) return false;
    button.dataset.sttFacePatchInstalled='1';
    const camera=makeInput('sttFaceDirectCamera','environment');
    const chooser=makeInput('sttFaceChooser',false);
    const faceCard = button.closest('.card, .photo-card, section, form') || button.parentElement;
    const existingFaceInput = faceCard ? faceCard.querySelector('input[type=file]') : null;

    function deliverFile(file){
      try{
        if(typeof window.handleFacePhotoFile==='function'){
          window.handleFacePhotoFile(file);
          return;
        }
      }catch(e){ console.warn(e); }
      document.dispatchEvent(new CustomEvent('allstt-face-photo-selected',{detail:{file}}));
      if(existingFaceInput){
        try{
          const dt=new DataTransfer();
          dt.items.add(file);
          existingFaceInput.files=dt.files;
          existingFaceInput.dispatchEvent(new Event('change',{bubbles:true}));
        }catch(e){ console.warn(e); }
      }
    }

    function forward(input){
      input.addEventListener('change',()=>{
        if(!input.files || !input.files[0]) return;
        const file=input.files[0];
        deliverFile(file);
        input.value='';
      });
    }
    forward(camera); forward(chooser);

    button.addEventListener('click',function(e){
      e.preventDefault();
      e.stopImmediatePropagation();
      if(busy) return;
      if(tapTimer){
        clearTimeout(tapTimer); tapTimer=null;
        busy=true;
        makeModal();
        return;
      }
      tapTimer=setTimeout(()=>{
        tapTimer=null;
        camera.click();
      },DOUBLE_TAP_MS);
    },true);
    button.addEventListener('dblclick',e=>{e.preventDefault();e.stopImmediatePropagation();},true);
    return true;
  }

  const observer=new MutationObserver(()=>{ if(install()) observer.disconnect(); else removeStandaloneGalleryCard(); });
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',install,{once:true}); else install();
  observer.observe(document.documentElement,{childList:true,subtree:true});
})();
