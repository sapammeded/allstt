from pathlib import Path

p = Path('stt.html')
s = p.read_text(encoding='utf-8')
marker = '<!-- ALLSTT CAMERA/GALLERY ADMIN BRIDGE v5 -->'
if marker in s:
    raise SystemExit(0)

patch = r'''<!-- ALLSTT CAMERA/GALLERY ADMIN BRIDGE v5 -->
<style id="allstt-camera-gallery-v5-css">
#allsttPatrolGalleryBtn{display:none!important;width:100%;margin-top:12px}
html[data-allstt-admin="1"] #allsttPatrolGalleryBtn{display:inline-flex!important}
#allsttPatrolGalleryStatus{display:none;margin-top:10px;padding:10px 14px;border-radius:12px;background:#ecfdf5;color:#047857;font-weight:800;font-size:13px}
html[data-allstt-admin="1"] #allsttPatrolGalleryStatus{display:block}
</style>
<script id="allstt-camera-gallery-admin-v5">
(function(){
'use strict';
const ADMIN_SESSION='allstt_admin_unlocked_v4';
function isAdmin(){
  try{return sessionStorage.getItem(ADMIN_SESSION)==='1'}catch(_){return window.allsttGalleryUnlocked===true}
}
function syncAdminFlag(){
  const on=isAdmin();
  window.allsttGalleryUnlocked=on;
  document.documentElement.dataset.allsttAdmin=on?'1':'0';
  return on;
}
function install(){
  const camera=document.getElementById('openCameraMenu');
  const native=document.getElementById('nativeCameraInput');
  const gallery=document.getElementById('galleryCameraInput');
  if(!camera||!native||!gallery)return;

  gallery.accept='image/*';
  gallery.multiple=true;
  gallery.removeAttribute('capture');
  gallery.style.display='none';

  let btn=document.getElementById('allsttPatrolGalleryBtn');
  if(!btn){
    btn=document.createElement('button');
    btn.id='allsttPatrolGalleryBtn';
    btn.type='button';
    btn.className='btn btn-primary';
    btn.innerHTML='<i class="fas fa-images"></i> UPLOAD MULTIPLE FOTO DARI GALERI';
    camera.parentElement.appendChild(btn);
    btn.addEventListener('click',function(e){
      e.preventDefault();e.stopPropagation();
      if(!syncAdminFlag()){
        alert('🔒 Fitur ini hanya untuk ADMIN. Buka menu ADMIN dan masukkan password terlebih dahulu.');
        return;
      }
      if(typeof ready==='function'&&!ready())return;
      gallery.value='';
      gallery.click();
    });
  }

  let status=document.getElementById('allsttPatrolGalleryStatus');
  if(!status){
    status=document.createElement('div');
    status.id='allsttPatrolGalleryStatus';
    status.innerHTML='<i class="fas fa-unlock"></i> ADMIN AKTIF — Kamera HP + upload multiple foto galeri terbuka';
    camera.parentElement.appendChild(status);
  }

  // Hard guard: ordinary users can never open the gallery input directly.
  if(gallery.dataset.adminGuardV5!=='1'){
    gallery.dataset.adminGuardV5='1';
    gallery.addEventListener('click',function(e){
      if(!syncAdminFlag()){e.preventDefault();e.stopImmediatePropagation();alert('🔒 Upload galeri membutuhkan akses ADMIN.');}
    },true);
    gallery.addEventListener('change',function(e){
      if(!syncAdminFlag()){
        e.target.value='';
        e.stopImmediatePropagation();
        alert('🔒 Upload galeri membutuhkan akses ADMIN.');
      }
    },true);
  }

  // One tap = camera. Two taps = gallery, but only after ADMIN authorization.
  if(camera.dataset.adminDoubleTapV5==='1')return;
  camera.dataset.adminDoubleTapV5='1';
  let timer=null;
  let waiting=false;
  const reset=()=>{waiting=false;if(timer){clearTimeout(timer);timer=null}};
  const openCamera=()=>{reset();native.value='';native.click()};
  const openGallery=()=>{
    reset();
    if(!syncAdminFlag()){openCamera();return}
    if(typeof ready==='function'&&!ready())return;
    gallery.value='';
    gallery.click();
  };
  camera.addEventListener('click',function(e){
    e.preventDefault();
    e.stopImmediatePropagation();
    syncAdminFlag();
    if(waiting){openGallery();return}
    waiting=true;
    timer=setTimeout(function(){if(waiting)openCamera()},360);
  },true);
}
function refresh(){
  syncAdminFlag();
  install();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){refresh();setTimeout(refresh,300);setTimeout(refresh,1000)},{once:true});
else{refresh();setTimeout(refresh,300);setTimeout(refresh,1000)}
window.addEventListener('pageshow',refresh);
})();
</script>
'''
s=s.replace('</body>',patch+'</body>',1)
p.write_text(s,encoding='utf-8')
