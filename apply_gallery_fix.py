from pathlib import Path
import re
p=Path('stt.html')
s=p.read_text(encoding='utf-8')
for sid in ['ALLSTT-STT-FACE-GALLERY-V7','ALLSTT-STT-RUNTIME-FIX-V5','ALLSTT-STT-FACE-GALLERY-V6','ALLSTT-STT-FACE-GALLERY-V5','ALLSTT-STT-FACE-GALLERY-FINAL']:
    s=re.sub(r'<script[^>]*id=["\']'+re.escape(sid)+r'["\'][^>]*>.*?</script>','',s,flags=re.I|re.S)
s=s.replace('galleryAccessGranted ?', '(galleryAccessGranted || window.allsttGalleryUnlocked) ?')
s=s.replace('if (!galleryAccessGranted)', 'if (!(galleryAccessGranted || window.allsttGalleryUnlocked))')
s=s.replace('if(!galleryAccessGranted)', 'if(!(galleryAccessGranted || window.allsttGalleryUnlocked))')
company_patch=r'''<script id="ALLSTT-COMPANY-IDENTITY-DUAL-SAVE">
(function(){
  'use strict';
  function install(){
    const protectedBtn=document.getElementById('saveCompanyHeaderBtn');
    if(!protectedBtn || document.getElementById('saveCompanyIdentityNoPasswordBtn')) return;
    const btn=document.createElement('button');
    btn.id='saveCompanyIdentityNoPasswordBtn';
    btn.type='button';
    btn.className='btn btn-success';
    btn.style.cssText='margin-top:8px;width:100%';
    btn.innerHTML='<i class="fas fa-save"></i> SIMPAN IDENTITAS PERUSAHAAN (TANPA PASSWORD)';
    protectedBtn.parentNode.insertBefore(btn,protectedBtn.nextSibling);
    btn.addEventListener('click',function(){
      const name=(document.getElementById('companyName')?.value||'').trim();
      const address=(document.getElementById('companyAddress')?.value||'').trim();
      try{
        localStorage.setItem('patrol_company_name_v1',name);
        localStorage.setItem('patrol_company_address_v1',address);
        localStorage.setItem('ALLSTT_GLOBAL_COMPANY_IDENTITY_V1',JSON.stringify({name,address,leftLogo:localStorage.getItem('patrol_logo_left_v1')||'',rightLogo:localStorage.getItem('patrol_logo_right_v1')||''}));
        if(typeof companyName!=='undefined') companyName=name;
        if(typeof companyAddress!=='undefined') companyAddress=address;
        if(window.ALLSTT_COMPANY_IDENTITY) window.ALLSTT_COMPANY_IDENTITY.name=name,window.ALLSTT_COMPANY_IDENTITY.address=address;
        alert('✅ Nama dan alamat perusahaan berhasil disimpan tanpa password.');
      }catch(e){ alert('❌ Gagal menyimpan identitas perusahaan: '+(e?.message||e)); }
    });
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',install,{once:true}); else install();
  window.addEventListener('load',install);
  [300,800,1500].forEach(ms=>setTimeout(install,ms));
})();
</script>'''
face_patch=r'''<script id="ALLSTT-STT-FACE-GALLERY-FINAL">
(function(){
  'use strict';
  const PASSWORD_FALLBACK='mbahpritampan';
  const DOUBLE_TAP_MS=380;
  function expectedPassword(){try{return typeof getGalleryPassword==='function'?getGalleryPassword():PASSWORD_FALLBACK}catch(_){return PASSWORD_FALLBACK}}
  function unlock(){window.allsttGalleryUnlocked=true;try{renderAreas()}catch(_){}try{updateAreaSelector()}catch(_){} }
  function install(){
    const face=document.getElementById('takeOfficerPhotoBtn');
    const cam=document.getElementById('officerPhotoInput');
    const gal=document.getElementById('officerGalleryInput');
    const section=document.getElementById('officerSection');
    if(!face||!cam||!gal||!section||face.dataset.faceFinal==='1')return;
    const btn=face.cloneNode(true);btn.dataset.faceFinal='1';face.replaceWith(btn);
    cam.removeAttribute('multiple');cam.setAttribute('accept','image/*');cam.setAttribute('capture','user');
    gal.removeAttribute('capture');gal.setAttribute('accept','image/*');gal.removeAttribute('multiple');gal.style.display='none';
    let waiting=false,timer=null;
    function reset(){waiting=false;if(timer){clearTimeout(timer);timer=null}}
    function openCamera(){reset();cam.value='';cam.click()}
    function openGallery(){
      reset();
      if(!window.allsttGalleryUnlocked){
        const pw=window.prompt('Masukkan password untuk membuka Upload Foto dari Galeri:');
        if(pw===null)return;
        if(pw!==expectedPassword()){window.alert('❌ Password salah. Akses galeri ditolak.');return}
        unlock();
      }
      gal.value='';gal.click();
    }
    btn.addEventListener('click',function(e){
      e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();
      if(waiting){openGallery();return}
      waiting=true;timer=setTimeout(function(){if(waiting)openCamera()},DOUBLE_TAP_MS);
    },true);
    btn.addEventListener('dblclick',function(e){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();openGallery()},true);
    gal.addEventListener('change',async function(){
      const file=gal.files&&gal.files[0]; if(!file)return;
      try{
        if(typeof saveOfficerPhoto!=='function')throw new Error('Fungsi foto wajah tidak tersedia.');
        await saveOfficerPhoto(file);
        const st=document.getElementById('officerPhotoStatus');if(st)st.textContent='✅ Foto wajah dari galeri siap dimasukkan ke PDF.';
      }catch(err){window.alert('❌ Foto galeri gagal diproses: '+(err?.message||err))}
      finally{gal.value=''}
    },true);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
  window.addEventListener('load',install);[300,800,1500,2500].forEach(ms=>setTimeout(install,ms));
})();
</script>'''
s=s.replace('</body>',company_patch+'\n'+face_patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
