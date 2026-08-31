from pathlib import Path
import re

p=Path('stt.html')
s=p.read_text(encoding='utf-8')
pat=re.compile(r'<script id="ALLSTT-STT-FACE-GALLERY-FINAL">.*?</script>',re.S)
script=r'''<script id="ALLSTT-STT-FACE-GALLERY-FINAL">
(function(){
'use strict';
const WAIT=360;
function mime(f){
 const t=(f&&f.type||'').toLowerCase();
 if(t.startsWith('image/')) return t;
 const n=((f&&f.name)||'').toLowerCase();
 if(n.endsWith('.png')) return 'image/png';
 if(n.endsWith('.webp')) return 'image/webp';
 return 'image/jpeg';
}
function normalized(f){
 if(!f)return null;
 const m=mime(f);
 if(f.type===m)return f;
 try{return new File([f],f.name||('photo-'+Date.now()+'.jpg'),{type:m,lastModified:f.lastModified||Date.now()})}catch(_){return f}
}
function install(){
 const face=document.getElementById('takeOfficerPhotoBtn'),cam=document.getElementById('officerPhotoInput'),gal=document.getElementById('officerGalleryInput');
 if(!face||!cam||!gal||face.dataset.faceAndroidFix==='1')return;
 const btn=face.cloneNode(true);btn.dataset.faceAndroidFix='1';face.replaceWith(btn);
 gal.removeAttribute('multiple');gal.removeAttribute('capture');gal.setAttribute('accept','image/*,.jpg,.jpeg,.png,.webp');gal.style.display='none';
 let waiting=false,timer=null;
 const reset=()=>{waiting=false;if(timer){clearTimeout(timer);timer=null}};
 const camera=()=>{reset();cam.value='';cam.setAttribute('capture','user');cam.click()};
 const gallery=()=>{reset();if(window.allsttAdminUnlocked){gal.value='';gal.click();return}if(window.ALLSTT_ADMIN_GATE)window.ALLSTT_ADMIN_GATE(()=>{gal.value='';gal.click()})};
 btn.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();if(waiting){gallery();return}waiting=true;timer=setTimeout(()=>{if(waiting)camera()},WAIT)},true);
 gal.addEventListener('change',async e=>{
  const f=normalized(e.target.files&&e.target.files[0]);
  if(!f)return;
  if(!window.allsttAdminUnlocked){e.target.value='';return}
  try{
   if(typeof saveOfficerPhoto!=='function')throw new Error('Fungsi foto wajah tidak tersedia.');
   if(typeof showOverlay==='function')showOverlay('Memproses foto wajah petugas...');
   if(typeof setOverlayProgress==='function')setOverlayProgress(30);
   await saveOfficerPhoto(f);
   if(typeof setOverlayProgress==='function')setOverlayProgress(100);
   if(typeof hideOverlay==='function')hideOverlay();
  }catch(err){if(typeof hideOverlay==='function')hideOverlay();alert('Foto galeri gagal diproses: '+(err&&err.message||String(err)))}
  finally{e.target.value=''}
 },true);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
window.addEventListener('load',install);
[300,800,1500,2500].forEach(ms=>setTimeout(install,ms));
})();
</script>'''
if not pat.search(s):raise SystemExit('FACE script not found')
s=pat.sub(script,s,count=1)
p.write_text(s,encoding='utf-8')
