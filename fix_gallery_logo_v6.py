from pathlib import Path
p=Path('stt.html')
s=p.read_text(encoding='utf-8')
marker='<!-- ALLSTT GALLERY LOGO FIX V6 -->'
if marker in s: raise SystemExit(0)
patch=r'''<!-- ALLSTT GALLERY LOGO FIX V6 -->
<script id="allstt-gallery-logo-fix-v6">
(function(){
'use strict';
const ADMIN_KEY='allstt_admin_unlocked_v4';
const COMPANY_KEY='ALLSTT_GLOBAL_COMPANY_IDENTITY_V1';
const admin=()=>{try{return sessionStorage.getItem(ADMIN_KEY)==='1'}catch(e){return false}};
const read=file=>new Promise((res,rej)=>{const r=new FileReader();r.onload=()=>res(String(r.result));r.onerror=()=>rej(new Error('Gagal membaca file dari galeri.'));r.readAsDataURL(file)});
function toast(msg){
 let x=document.getElementById('allsttV6Toast');
 if(!x){x=document.createElement('div');x.id='allsttV6Toast';Object.assign(x.style,{position:'fixed',left:'50%',bottom:'24px',transform:'translateX(-50%)',zIndex:99999,background:'#0f172a',color:'#fff',padding:'14px 18px',borderRadius:'12px',fontWeight:'800',boxShadow:'0 8px 30px rgba(0,0,0,.25)',maxWidth:'90%',textAlign:'center'});document.body.appendChild(x)}
 x.textContent=msg;x.style.display='block';clearTimeout(x._t);x._t=setTimeout(()=>x.style.display='none',2500);
}
async function patrolGallery(input){
 if(!admin()){alert('🔒 Akses galeri membutuhkan ADMIN.');input.value='';return}
 const files=Array.from(input.files||[]);if(!files.length)return;
 const sel=document.getElementById('targetAreaSelect');
 const key=String(sel?.value||'').trim();
 if(!key){alert('Pilih Area Patroli terlebih dahulu.');input.value='';return}
 if(!window.patrolData||!window.patrolData[key]){alert('Area patroli belum tersedia.');input.value='';return}
 const area=window.patrolData[key];if(!Array.isArray(area.photos))area.photos=[];
 for(const f of files){if(!/^image\//i.test(f.type||''))continue;area.photos.push(await read(f))}
 try{if(typeof persistMeta==='function')persistMeta()}catch(e){}
 try{if(typeof renderAreas==='function')renderAreas()}catch(e){}
 toast('✅ '+files.length+' foto galeri berhasil dimasukkan ke Area Patroli.');
 input.value='';
}
function identityFile(input,side){
 if(!admin()){alert('🔒 Fitur logo hanya untuk ADMIN.');input.value='';return}
 const f=input.files?.[0];if(!f)return;
 read(f).then(data=>{
  const preview=document.getElementById(side==='left'?'ciLeftPreview':'ciRightPreview');
  if(preview)preview.src=data;
  input.dataset.v6=data;
  toast('✅ Logo '+(side==='left'?'kiri':'kanan')+' berhasil dimuat. Tekan Simpan Identitas.');
 }).catch(e=>alert('❌ '+e.message));
}
function install(){
 const g=document.getElementById('galleryCameraInput');
 if(g&&g.dataset.v6!=='1'){g.dataset.v6='1';g.multiple=true;g.removeAttribute('capture');g.addEventListener('change',e=>{e.preventDefault();e.stopImmediatePropagation();patrolGallery(g)},true)}
 const l=document.getElementById('ciLeft'),r=document.getElementById('ciRight');
 if(l&&l.dataset.v6!=='1'){l.dataset.v6='1';l.addEventListener('change',e=>{e.preventDefault();e.stopImmediatePropagation();identityFile(l,'left')},true)}
 if(r&&r.dataset.v6!=='1'){r.dataset.v6='1';r.addEventListener('change',e=>{e.preventDefault();e.stopImmediatePropagation();identityFile(r,'right')},true)}
 const save=document.getElementById('ciSave');
 if(save&&save.dataset.v6!=='1'){
  save.dataset.v6='1';save.addEventListener('click',e=>{
   e.preventDefault();e.stopImmediatePropagation();
   if(!admin()){alert('🔒 Fitur Admin.');return}
   let v={name:(document.getElementById('ciName')?.value||'').trim(),address:(document.getElementById('ciAddress')?.value||'').trim(),leftLogo:document.getElementById('ciLeftPreview')?.src||'',rightLogo:document.getElementById('ciRightPreview')?.src||''};
   try{localStorage.setItem(COMPANY_KEY,JSON.stringify(v))}catch(err){alert('❌ Identitas gagal disimpan: '+err.message);return}
   try{if(typeof window.applyCompanyIdentity==='function')window.applyCompanyIdentity(v)}catch(err){}
   try{if(typeof persistMeta==='function')persistMeta()}catch(err){}
   toast('✅ Identitas perusahaan berhasil disimpan.');
   setTimeout(()=>alert('✅ SIMPAN IDENTITAS BERHASIL\n\nNama perusahaan, alamat, dan logo telah disimpan sebagai default.'),120);
  },true)
 }
}
function start(){install();setTimeout(install,300);setTimeout(install,1000)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
new MutationObserver(install).observe(document.documentElement,{subtree:true,childList:true});
})();
</script>
'''
s=s.replace('</body>',patch+'</body>',1)
p.write_text(s,encoding='utf-8')
