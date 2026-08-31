from pathlib import Path

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

script = r'''<script id="ALLSTT-ADMIN-POLICY-V3">
(function(){
'use strict';
var DEFAULT_NAME='STT DATA CENTRES';
var DEFAULT_ADDRESS='KAWASAN INDUSTRI DELTAMAS GIIC\nCIKARANG PUSAT KABUPATEN BEKASI';
var NAME_KEY='patrol_company_name_v1';
var ADDRESS_KEY='patrol_company_address_v1';
function $(id){return document.getElementById(id)}
function isAdmin(){
  var c=$('adminContent'), a=$('adminSection'), l=$('adminLoginBox');
  return !!(c && a && l && a.style.display!=='none' && c.style.display!=='none' && l.style.display==='none');
}
function setDefaultIdentity(){
  try{
    var n=localStorage.getItem(NAME_KEY), a=localStorage.getItem(ADDRESS_KEY);
    if(!n){localStorage.setItem(NAME_KEY,DEFAULT_NAME);n=DEFAULT_NAME}
    if(!a){localStorage.setItem(ADDRESS_KEY,DEFAULT_ADDRESS);a=DEFAULT_ADDRESS}
    var ni=$('companyName'), ai=$('companyAddress');
    if(ni && !ni.value) ni.value=n;
    if(ai && !ai.value) ai.value=a;
  }catch(e){}
}
function protectIdentity(){
  var admin=isAdmin();
  var ni=$('companyName'), ai=$('companyAddress');
  [ni,ai].forEach(function(x){if(!x)return;x.readOnly=!admin;x.disabled=!admin;x.setAttribute('aria-readonly',String(!admin));});
  var cs=$('companySection'), ls=$('logoUploadSection');
  if(cs && !admin) cs.style.display='none';
  if(ls && !admin) ls.style.display='none';
  document.querySelectorAll('#companySection input[type="file"],#logoUploadSection input[type="file"]').forEach(function(x){x.disabled=!admin;x.setAttribute('aria-disabled',String(!admin));});
}
function protectFiles(){
  var admin=isAdmin();
  document.querySelectorAll('input[type="file"]').forEach(function(x){
    var id=x.id||'';
    if(id==='nativeCameraInput') return;
    var protectedArea=x.closest('#companySection,#logoUploadSection');
    var gallery=x.id==='galleryCameraInput' || x.hasAttribute('multiple');
    if(protectedArea || gallery){
      x.disabled=!admin;
      x.setAttribute('aria-disabled',String(!admin));
    }
  });
}
function guardEvents(){
  document.addEventListener('click',function(e){
    var t=e.target.closest && e.target.closest('input[type="file"]');
    if(!t)return;
    if(t.id==='nativeCameraInput')return;
    if((t.id==='galleryCameraInput'||t.hasAttribute('multiple')||t.closest('#companySection,#logoUploadSection'))&&!isAdmin()){
      e.preventDefault();e.stopImmediatePropagation();
      alert('Akses hanya untuk ADMIN. Buka menu ADMIN dan masukkan kode admin terlebih dahulu.');
    }
  },true);
  document.addEventListener('change',function(e){
    var t=e.target;
    if(!(t instanceof HTMLInputElement)||t.type!=='file')return;
    if(t.id==='nativeCameraInput')return;
    if((t.id==='galleryCameraInput'||t.hasAttribute('multiple')||t.closest('#companySection,#logoUploadSection'))&&!isAdmin()){
      t.value='';
      alert('Akses hanya untuk ADMIN.');
    }
  },true);
}
function watch(){
  var obs=new MutationObserver(function(){setDefaultIdentity();protectIdentity();protectFiles()});
  obs.observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['style','disabled']});
}
function init(){
  setDefaultIdentity();
  protectIdentity();
  protectFiles();
  guardEvents();
  watch();
  setTimeout(function(){setDefaultIdentity();protectIdentity();protectFiles()},300);
  setTimeout(function(){setDefaultIdentity();protectIdentity();protectFiles()},1000);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
</script>'''

if 'ALLSTT-ADMIN-POLICY-V3' not in s:
    s=s.replace('</body>',script+'\n</body>',1)

p.write_text(s,encoding='utf-8')
