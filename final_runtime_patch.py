from pathlib import Path

p = Path('stt.html')
s = p.read_text(encoding='utf-8')
marker = '<!-- ALLSTT FINAL ADMIN/GALLERY RUNTIME v4 -->'
if marker in s:
    raise SystemExit(0)

patch = r'''<!-- ALLSTT FINAL ADMIN/GALLERY RUNTIME v4 -->
<style id="allstt-final-admin-css">
#companySection:not(.menu-section-open){display:none!important}
#saveCompanyIdentityNoPasswordBtn,#changeLogoPasswordBtn{display:none!important}
</style>
<script id="allstt-final-admin-runtime-v4">
(function(){
'use strict';
const SESSION_KEY='allstt_admin_unlocked_v4';
const DEFAULT_COMPANY='STT DATA CENTRES';
const DEFAULT_ADDRESS='KAWASAN INDUSTRI DELTAMAS GIIC\\nCIKARANG PUSAT KABUPATEN BEKASI';
let adminUnlocked=sessionStorage.getItem(SESSION_KEY)==='1';
function adminPassword(){
 try{if(typeof getLogoUploadPassword==='function')return String(getLogoUploadPassword())}catch(_){ }
 try{if(typeof getGalleryPassword==='function')return String(getGalleryPassword())}catch(_){ }
 return 'mbahpritampan';
}
function setAdmin(on){
 adminUnlocked=!!on;
 try{sessionStorage.setItem(SESSION_KEY,on?'1':'0')}catch(_){ }
 window.allsttGalleryUnlocked=adminUnlocked;
 document.documentElement.dataset.allsttAdmin=adminUnlocked?'1':'0';
 const c=document.getElementById('companySection');
 if(c&&!adminUnlocked){c.classList.remove('menu-section-open');c.style.display='none'}
 if(adminUnlocked){try{renderAreas()}catch(_){} try{updateAreaSelector()}catch(_){} }
}
function removeLegacyPasswordUI(){
 for(const el of [...document.querySelectorAll('body *')]){
  const t=(el.textContent||'').trim().toUpperCase();
  if(t.includes('GANTI PASSWORD GALERI')||t.includes('SIMPAN IDENTITAS PERUSAHAAN (TANPA PASSWORD)')){
   if(el.children.length<=4||el.id==='saveCompanyIdentityNoPasswordBtn')el.remove();
  }
 }
 document.getElementById('changeLogoPasswordBtn')?.remove();
 const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT),kill=[];let n;
 while(n=w.nextNode()){const v=(n.nodeValue||'').trim();if(/^\\n(?:\\n){0,3}$/.test(v))kill.push(n)}
 kill.forEach(x=>x.remove());
}
function defaults(){
 const n=document.getElementById('companyName'),a=document.getElementById('companyAddress');
 if(n&&!String(n.value||'').trim())n.value=DEFAULT_COMPANY;
 if(a&&!String(a.value||'').trim())a.value=DEFAULT_ADDRESS.replace(/\\n/g,'\n');
 try{if(typeof companyName!=='undefined'&&!String(companyName||'').trim())companyName=DEFAULT_COMPANY}catch(_){ }
 try{if(typeof companyAddress!=='undefined'&&!String(companyAddress||'').trim())companyAddress=DEFAULT_ADDRESS.replace(/\\n/g,'\n')}catch(_){ }
}
function adminButton(){
 const nav=document.getElementById('sideNav');if(!nav||document.getElementById('allsttAdminNav'))return;
 const b=document.createElement('button');b.id='allsttAdminNav';b.type='button';b.className='nav-item';
 b.innerHTML='<i class="fas fa-user-shield"></i><span>Admin</span>';
 const d=nav.querySelector('.nav-divider');nav.insertBefore(b,d||null);
 b.addEventListener('click',function(){
  if(!adminUnlocked){
   const pw=window.prompt('Masukkan password ADMIN:');if(pw===null)return;
   if(String(pw)!==adminPassword()){window.alert('❌ Password ADMIN salah.');return}
   setAdmin(true);
  }
  const c=document.getElementById('companySection');
  if(c){c.classList.add('menu-section-open');c.style.display='block';c.scrollIntoView({behavior:'smooth',block:'start'})}
  b.classList.add('active');document.getElementById('navOverlay')?.classList.remove('open');nav.classList.remove('open');
 });
}
function guardCompanyNav(){
 const nav=document.getElementById('sideNav');if(!nav||nav.dataset.adminGuardV4==='1')return;nav.dataset.adminGuardV4='1';
 nav.addEventListener('click',function(e){
  const item=e.target.closest('.nav-item[data-target="companySection"]');
  if(!item||adminUnlocked)return;
  e.preventDefault();e.stopImmediatePropagation();window.alert('🔒 Fitur Admin. Buka menu ADMIN dan masukkan password terlebih dahulu.');
 },true);
}
function robustOfficerPhoto(){
 window.saveOfficerPhoto=async function(file){
  if(!file)throw new Error('Tidak ada foto yang dipilih.');
  if(file.size&&file.size>8*1024*1024)throw new Error('Foto terlalu besar. Maksimal 8MB.');
  const raw=await new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(r.result);r.onerror=()=>reject(new Error('Gagal membaca foto dari galeri.'));r.readAsDataURL(file)});
  if(!raw)throw new Error('Foto tidak dapat dibaca.');
  let out=raw;try{if(typeof compressDataUrl==='function')out=await compressDataUrl(raw,0.96,2400)||raw}catch(_){out=raw}
  try{officerPhotoBlob=file}catch(_){ } try{officerPhotoDataUrl=out}catch(_){ } try{officerPhotoRef='memory_officer_face'}catch(_){ }
  const img=document.getElementById('officerPhotoPreview'),wrap=document.getElementById('officerPhotoPreviewWrap'),st=document.getElementById('officerPhotoStatus'),rm=document.getElementById('removeOfficerPhotoBtn');
  if(img)img.src=out;if(wrap)wrap.style.display='block';if(st)st.textContent='✅ Foto wajah siap dimasukkan ke PDF.';if(rm)rm.style.display='inline-flex';return true;
 };
}
function robustFaceControls(){
 const face=document.getElementById('takeOfficerPhotoBtn'),cam=document.getElementById('officerPhotoInput'),gal=document.getElementById('officerGalleryInput');
 if(!face||!cam||!gal||face.dataset.finalAdminFace==='1')return;
 const nf=face.cloneNode(true);nf.dataset.finalAdminFace='1';face.replaceWith(nf);
 const ng=gal.cloneNode(true);ng.dataset.finalAdminGallery='1';gal.replaceWith(ng);
 cam.accept='image/*';cam.setAttribute('capture','user');cam.multiple=false;ng.accept='image/*';ng.removeAttribute('capture');ng.multiple=false;ng.style.display='none';
 let timer=null,waiting=false;const reset=()=>{waiting=false;if(timer){clearTimeout(timer);timer=null}};
 const camera=()=>{reset();cam.value='';cam.click()};
 const gallery=()=>{reset();if(!adminUnlocked){window.alert('🔒 Akses galeri membutuhkan ADMIN. Buka menu ADMIN dan masukkan password terlebih dahulu.');return}ng.value='';ng.click()};
 nf.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();if(waiting){gallery();return}waiting=true;timer=setTimeout(()=>{if(waiting)camera()},380)},true);
 ng.addEventListener('change',async function(){const f=ng.files&&ng.files[0];if(!f)return;try{await window.saveOfficerPhoto(f)}catch(err){window.alert('❌ Foto galeri gagal diproses: '+(err?.message||err))}finally{ng.value=''}},true);
}
function refresh(){removeLegacyPasswordUI();defaults();adminButton();guardCompanyNav();if(!adminUnlocked){window.allsttGalleryUnlocked=false;document.getElementById('companySection')?.classList.remove('menu-section-open')}robustOfficerPhoto();robustFaceControls()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>{refresh();setTimeout(refresh,300)},{once:true});else{refresh();setTimeout(refresh,300)}
window.addEventListener('pageshow',refresh);
})();
</script>
'''
s=s.replace('</body>',patch+'</body>')
p.write_text(s,encoding='utf-8')
