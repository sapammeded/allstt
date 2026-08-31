from pathlib import Path

p=Path('stt.html')
s=p.read_text(encoding='utf-8')
marker='<!-- ALLSTT FINAL UPLOAD BRIDGE V6 -->'
if marker in s:
    raise SystemExit(0)

patch=r'''<!-- ALLSTT FINAL UPLOAD BRIDGE V6 -->
<style id="allstt-final-upload-v6-css">
#allsttUploadToast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);z-index:65000;display:none;background:#0f172a;color:#fff;padding:13px 18px;border-radius:12px;font-weight:800;box-shadow:0 10px 30px rgba(0,0,0,.25)}
</style>
<div id="allsttUploadToast"></div>
<script id="allstt-final-upload-v6">
(function(){
'use strict';
const CAMERA_IDS=new Set(['nativeCameraInput','officerPhotoInput']);
function admin(){
  if(window.allsttAdminUnlocked===true)return true;
  try{return sessionStorage.getItem('allstt_admin_unlocked')==='1'}catch(_){return false}
}
function toast(msg,ok=true){
  const t=document.getElementById('allsttUploadToast');
  if(!t)return;
  t.textContent=msg;t.style.display='block';t.style.background=ok?'#047857':'#b91c1c';
  clearTimeout(window.__allsttToastTimer);window.__allsttToastTimer=setTimeout(()=>t.style.display='none',2600);
}
function isCameraInput(i){
  if(CAMERA_IDS.has(i.id))return true;
  return i.hasAttribute('capture') && /camera|photo|face|officer/i.test((i.id||'')+' '+(i.name||''));
}
function install(){
  document.querySelectorAll('input[type=file]').forEach(i=>{
    if(i.dataset.allsttV6==='1')return;
    i.dataset.allsttV6='1';
    i.setAttribute('accept',i.getAttribute('accept')||'image/*');
    i.addEventListener('click',function(e){
      if(!admin() && !isCameraInput(i)){
        e.preventDefault();e.stopImmediatePropagation();
        toast('🔒 Upload dari galeri hanya tersedia setelah ADMIN login.',false);
      }
    },true);
    i.addEventListener('change',function(e){
      const files=Array.from(i.files||[]);
      if(!files.length)return;
      if(!admin() && !isCameraInput(i)){
        i.value='';e.stopImmediatePropagation();
        toast('🔒 Upload dari galeri membutuhkan ADMIN.',false);return;
      }
      if(admin() && !isCameraInput(i) && !e.__allsttV6Redispatched){
        setTimeout(()=>{
          try{
            const ev=new Event('change',{bubbles:true});
            ev.__allsttV6Redispatched=true;
            i.dispatchEvent(ev);
          }catch(_){ }
        },60);
      }
    },true);
  });
  if(admin()){
    document.querySelectorAll('input[type=file]').forEach(i=>{
      if(!isCameraInput(i))i.multiple=true;
    });
  }
  const save=document.getElementById('saveCompanyHeaderBtn');
  if(save && save.dataset.allsttSaveNotify!=='1'){
    save.dataset.allsttSaveNotify='1';
    save.addEventListener('click',function(){
      if(!admin())return;
      setTimeout(()=>toast('✅ Identitas perusahaan & logo berhasil disimpan.',true),180);
    },false);
  }
}
function boot(){install();[200,600,1200,2000,3500].forEach(ms=>setTimeout(install,ms))}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
window.addEventListener('load',install);
})();
</script>
'''
if '</body>' not in s:
    raise SystemExit('body end not found')
s=s.replace('</body>',patch+'</body>',1)
p.write_text(s,encoding='utf-8')
