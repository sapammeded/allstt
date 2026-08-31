from pathlib import Path
import re

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

# Multiple gallery uploads are intentionally silent. The existing processing
# overlay/thumbnail is the only feedback during normal operation.
s = re.sub(r"\s*alert\(\s*['\"]✅ Foto berhasil ditambahkan ke ['\"]\s*\+\s*area\.name\s*\)\s*;?", "", s, count=1)

# Replace the previous generated policy so every build is deterministic.
s = re.sub(r'<style id="ALLSTT-FINAL-ADMIN-GATE-CSS">.*?<script id="ALLSTT-FINAL-ADMIN-GATE-V1">.*?</script>\s*', '', s, count=1, flags=re.S)

script = r'''<style id="ALLSTT-FINAL-ADMIN-GATE-CSS">
/* ONE ADMIN SESSION protects every gallery/company administration action. */
body:not(.allstt-admin-unlocked) #companySection{display:none!important;}
body:not(.allstt-admin-unlocked) .nav-item[data-target="companySection"]{display:none!important;}
body.allstt-admin-unlocked #companySection{display:block!important;}
body:not(.allstt-admin-unlocked) #companyName,
body:not(.allstt-admin-unlocked) #companyAddress{cursor:pointer!important;background:#f8fafc!important;color:#64748b!important;}
body:not(.allstt-admin-unlocked) #logoUploadSection{display:none!important;}
</style>
<script id="ALLSTT-FINAL-ADMIN-GATE-V1">
(function(){
'use strict';
const ADMIN_STATE_KEY='allstt_admin_unlocked';
const COMPANY_KEY='ALLSTT_GLOBAL_COMPANY_IDENTITY_V1';
const DEFAULT_NAME='STT DATA CENTRES';
const DEFAULT_ADDRESS='KAWASAN INDUSTRI DELTAMAS GIIC\nCIKARANG PUSAT KABUPATEN BEKASI';

function byId(id){return document.getElementById(id)}
function admin(){
  if(window.allsttAdminUnlocked===true)return true;
  try{return sessionStorage.getItem(ADMIN_STATE_KEY)==='1'}catch(_){return false}
}
function sync(){
  const ok=admin();
  window.allsttAdminUnlocked=ok;
  document.body.classList.toggle('allstt-admin-unlocked',ok);
  const company=byId('companySection');
  if(company) company.style.display=ok?'block':'none';
  const nav=document.querySelector('.nav-item[data-target="companySection"]');
  if(nav) nav.style.display=ok?'':'none';
  ['companyName','companyAddress'].forEach(id=>{
    const x=byId(id); if(!x)return;
    x.readOnly=!ok; x.disabled=false; x.setAttribute('aria-readonly',String(!ok));
  });
  const logo=byId('logoUploadSection');
  if(logo && !ok) logo.style.display='none';
}
function gate(after){
  if(admin()){sync();if(after)after();return}
  if(typeof window.ALLSTT_ADMIN_GATE==='function'){
    window.ALLSTT_ADMIN_GATE(function(){sync();if(after)after()});
  }else{
    alert('🔒 Masukkan password ADMIN terlebih dahulu.');
  }
}
function readDataURL(file){
  return new Promise((resolve,reject)=>{
    if(!file)return reject(new Error('File tidak dipilih.'));
    const r=new FileReader();
    r.onload=()=>resolve(String(r.result||''));
    r.onerror=()=>reject(new Error('Gagal membaca file dari galeri.'));
    r.readAsDataURL(file);
  });
}
function loadIdentity(){
  try{return Object.assign({name:DEFAULT_NAME,address:DEFAULT_ADDRESS,leftLogo:'',rightLogo:''},JSON.parse(localStorage.getItem(COMPANY_KEY)||'{}'))}
  catch(_){return {name:DEFAULT_NAME,address:DEFAULT_ADDRESS,leftLogo:'',rightLogo:''}}
}
function saveIdentity(v){
  localStorage.setItem(COMPANY_KEY,JSON.stringify(v));
  try{localStorage.setItem('patrol_company_name_v1',v.name||'');localStorage.setItem('patrol_company_address_v1',v.address||'')}catch(_){}
  try{localStorage.setItem('patrol_logo_left_v1',v.leftLogo||'');localStorage.setItem('patrol_logo_right_v1',v.rightLogo||'')}catch(_){}
  try{if(typeof window.applyCompanyIdentity==='function')window.applyCompanyIdentity(v)}catch(_){}
  try{if(typeof persistMeta==='function')persistMeta()}catch(_){}
}
function currentIdentity(){
  const v=loadIdentity();
  v.name=(byId('companyName')?.value||byId('ciName')?.value||v.name||DEFAULT_NAME).trim();
  v.address=(byId('companyAddress')?.value||byId('ciAddress')?.value||v.address||DEFAULT_ADDRESS).trim();
  const l=byId('ciLeftPreview')?.src||'';
  const r=byId('ciRightPreview')?.src||'';
  if(l && l.indexOf('data:image/')===0)v.leftLogo=l;
  if(r && r.indexOf('data:image/')===0)v.rightLogo=r;
  return v;
}
function setLogoPreview(side,data){
  const id=side==='left'?'ciLeftPreview':'ciRightPreview';
  const preview=byId(id);if(preview)preview.src=data;
  const selectors=side==='left'
    ? ['#logoLeft','#leftLogo','img[data-logo="left"]','.logo-left']
    : ['#logoRight','#rightLogo','img[data-logo="right"]','.logo-right'];
  selectors.forEach(sel=>document.querySelectorAll(sel).forEach(img=>{if(img.tagName==='IMG')img.src=data}));
}
function handleLogo(input,side){
  if(!admin()){input.value='';gate(()=>{});return}
  const file=input.files&&input.files[0];if(!file){input.value='';return}
  readDataURL(file).then(data=>{
    setLogoPreview(side,data);
    const v=loadIdentity();
    if(side==='left')v.leftLogo=data;else v.rightLogo=data;
    saveIdentity(v);
  }).catch(err=>alert('❌ Logo gagal diproses: '+err.message)).finally(()=>{input.value=''})
}
function handleCompanySave(e){
  if(!admin()){
    e.preventDefault();e.stopImmediatePropagation();gate(()=>{});return;
  }
  e.preventDefault();e.stopImmediatePropagation();
  const v=currentIdentity();
  saveIdentity(v);
  const n=byId('companyName');const a=byId('companyAddress');
  if(n)n.value=v.name;if(a)a.value=v.address;
  if(typeof window.updateLogoPreviews==='function')try{window.updateLogoPreviews()}catch(_){}
}
function install(){
  sync();

  // Text identity: never allow edits while locked.
  ['companyName','companyAddress','ciName','ciAddress'].forEach(id=>{
    const x=byId(id);if(!x||x.dataset.allsttAdminGuard==='1')return;
    x.dataset.allsttAdminGuard='1';
    x.addEventListener('click',function(e){
      if(!admin()){e.preventDefault();e.stopImmediatePropagation();gate(()=>{x.readOnly=false;x.focus()})}
    },true);
    x.addEventListener('beforeinput',function(e){
      if(!admin()){e.preventDefault();e.stopImmediatePropagation();gate(()=>{x.readOnly=false;x.focus()})}
    },true);
    x.addEventListener('input',function(e){
      if(!admin()){e.target.value=loadIdentity()[id.includes('Address')||id==='ciAddress'?'address':'name']||'';e.stopImmediatePropagation()}
    },true);
  });

  // Save buttons are protected separately because legacy handlers previously
  // wrote companyName/companyAddress without consulting the ADMIN session.
  ['ciSave','saveCompanyHeaderBtn'].forEach(id=>{
    const b=byId(id);if(!b||b.dataset.allsttAdminGuard==='1')return;
    b.dataset.allsttAdminGuard='1';
    b.addEventListener('click',handleCompanySave,true);
  });

  // Both generations of logo controls are protected and use a persistent
  // DataURL, never a transient blob/object URL.
  [['ciLeft','left'],['ciRight','right'],['uploadLogoLeft','left'],['uploadLogoRight','right']].forEach(pair=>{
    const input=byId(pair[0]);if(!input||input.dataset.allsttAdminGuard==='1')return;
    input.dataset.allsttAdminGuard='1';
    input.addEventListener('click',function(e){
      if(!admin()){
        e.preventDefault();e.stopImmediatePropagation();gate(()=>{try{input.click()}catch(_){} });
      }
    },true);
    input.addEventListener('change',function(e){
      e.preventDefault();e.stopImmediatePropagation();
      if(!admin()){input.value='';gate(()=>{});return}
      handleLogo(input,pair[1]);
    },true);
  });

  // Multiple patrol gallery: no success alert; processing/thumbnail is enough.
  const gallery=byId('galleryCameraInput');
  if(gallery && gallery.dataset.allsttAdminGuard!=='1'){
    gallery.dataset.allsttAdminGuard='1';
    gallery.addEventListener('change',function(e){
      if(!admin()){e.preventDefault();e.stopImmediatePropagation();gallery.value='';gate(()=>{});return}
    },true);
  }

  // Remove the old success alert even if another generated patch reintroduced it.
  try{
    const old=window.alert;
    if(!window.__allsttAlertGuard){
      window.__allsttAlertGuard=true;
      window.alert=function(msg){
        if(typeof msg==='string' && /Foto berhasil ditambahkan ke Area/i.test(msg))return;
        return old.apply(this,arguments);
      };
    }
  }catch(_){}
}
function boot(){install();[300,900,1800].forEach(ms=>setTimeout(sync,ms))}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
window.addEventListener('load',install);
})();
</script>'''

s=s.replace('</body>',script+'\n</body>',1)
p.write_text(s,encoding='utf-8')
