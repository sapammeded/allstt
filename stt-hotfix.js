(function(){
  'use strict';
  const GALLERY_UNLOCK_KEY='allstt_gallery_unlock_until_v2';
  const GALLERY_TTL=30*60*1000;
  const getGalleryPw=()=>{
    try{ if(typeof getGalleryPassword==='function') return getGalleryPassword(); }catch(e){}
    try{return localStorage.getItem('patrol_gallery_password_v1')||'supangat505';}catch(e){return 'supangat505';}
  };
  const isUnlocked=()=>{try{return Number(localStorage.getItem(GALLERY_UNLOCK_KEY)||0)>Date.now();}catch(e){return false;}};
  const unlock=()=>{try{localStorage.setItem(GALLERY_UNLOCK_KEY,String(Date.now()+GALLERY_TTL));}catch(e){}};
  const showGallery=()=>{
    const a=document.getElementById('cameraGalleryAccess');
    if(a) a.style.display='block';
    const p=document.getElementById('cameraGalleryPassword');
    if(p) p.value='';
  };
  function installGalleryFix(){
    const camera=document.getElementById('nativeCameraInput');
    const gallery=document.getElementById('galleryCameraInput');
    const unlockBtn=document.getElementById('unlockCameraGalleryBtn');
    const pass=document.getElementById('cameraGalleryPassword');
    const upload=document.getElementById('uploadGalleryBtn');
    if(camera) camera.removeAttribute('capture');
    if(isUnlocked()) showGallery();
    unlockBtn?.addEventListener('click',function(e){
      e.preventDefault(); e.stopImmediatePropagation();
      if((pass?.value||'')===getGalleryPw()){
        unlock(); showGallery();
        try{alert('✅ Akses galeri dibuka selama 30 menit.');}catch(_){ }
      }else alert('❌ Password salah!');
    },true);
    upload?.addEventListener('click',function(e){
      e.preventDefault(); e.stopImmediatePropagation();
      if(!isUnlocked()){
        const p=document.getElementById('cameraGalleryPassword'); if(p) p.focus();
        alert('🔒 Masukkan password galeri terlebih dahulu.'); return;
      }
      if(gallery) gallery.click();
    },true);
  }
  function installCompanySettings(){
    const existing=document.getElementById('companyName');
    if(existing){
      const sec=document.getElementById('companySection');
      if(sec){sec.style.display='block';sec.classList.add('menu-section-open');}
      return;
    }
    const style=document.createElement('style');
    style.textContent='.allstt-company-settings{margin:16px 0;padding:18px;border-left:5px solid #0b3d91;background:#fff;border-radius:16px;box-shadow:0 5px 18px rgba(15,23,42,.08)} .allstt-company-settings input,.allstt-company-settings textarea{width:100%;padding:12px;border:2px solid #e2e8f0;border-radius:10px;margin:6px 0 10px}';
    document.head.appendChild(style);
    const card=document.createElement('section');
    card.className='allstt-company-settings';
    card.innerHTML='<h3 style="margin:0 0 12px;color:#0b3d91">🏢 SETTING PERUSAHAAN</h3><label>Nama Perusahaan</label><input id="allsttCompanyName" type="text" placeholder="Nama perusahaan"><label>Alamat Perusahaan</label><textarea id="allsttCompanyAddress" rows="2" placeholder="Alamat lengkap perusahaan"></textarea><button id="allsttSaveCompany" type="button" class="btn btn-primary" style="width:100%">💾 SIMPAN SETTING PERUSAHAAN</button>';
    const target=document.querySelector('.container')||document.body;
    target.insertBefore(card,target.firstChild);
    const name=document.getElementById('allsttCompanyName'), addr=document.getElementById('allsttCompanyAddress');
    try{name.value=localStorage.getItem('patrol_company_name_v1')||'';addr.value=localStorage.getItem('patrol_company_address_v1')||'';}catch(e){}
    document.getElementById('allsttSaveCompany').addEventListener('click',()=>{
      try{localStorage.setItem('patrol_company_name_v1',(name.value||'').trim());localStorage.setItem('patrol_company_address_v1',(addr.value||'').trim());window.companyName=(name.value||'').trim();window.companyAddress=(addr.value||'').trim();alert('✅ Nama dan alamat perusahaan berhasil disimpan.');}
      catch(e){alert('❌ Gagal menyimpan setting: '+e.message);}
    });
  }
  function boot(){installGalleryFix();installCompanySettings();}
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();
