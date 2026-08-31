from pathlib import Path

p = Path('stt.html')
s = p.read_text(encoding='utf-8')
marker = '<!-- ALLSTT CAMERA/GALLERY ADMIN BRIDGE v6 -->'
if marker in s:
    raise SystemExit(0)

patch = r'''<!-- ALLSTT CAMERA/GALLERY ADMIN BRIDGE v6 -->
<style id="allstt-camera-gallery-v6-css">
/* KAMERA & AREA PATROLI is always a baseline feature. */
#cameraTab{display:block!important}
#allsttPatrolEntry{display:flex!important;width:100%;margin:0 0 16px 0}
#allsttPatrolGalleryBtn{display:none!important;width:100%;margin-top:12px}
html[data-allstt-admin="1"] #allsttPatrolGalleryBtn{display:inline-flex!important}
#allsttPatrolGalleryStatus{display:none;margin-top:10px;padding:10px 14px;border-radius:12px;background:#ecfdf5;color:#047857;font-weight:800;font-size:13px}
html[data-allstt-admin="1"] #allsttPatrolGalleryStatus{display:block}
</style>
<script id="allstt-camera-gallery-admin-v6">
(function(){
'use strict';
/* Must match the single unified ADMIN gate in apply_admin_patch.py. */
const ADMIN_SESSION='allstt_admin_unlocked';
function isAdmin(){
  try{return sessionStorage.getItem(ADMIN_SESSION)==='1'}catch(_){return window.allsttAdminUnlocked===true}
}
function syncAdminFlag(){
  const on=isAdmin() || window.allsttAdminUnlocked===true;
  window.allsttGalleryUnlocked=on;
  window.allsttAdminUnlocked=on;
  document.documentElement.dataset.allsttAdmin=on?'1':'0';
  return on;
}
function ensurePatrolEntry(){
  const nav=document.getElementById('sideNav');
  const cameraTab=document.getElementById('cameraTab');
  if(!cameraTab)return;
  /* Keep the actual baseline camera tab visible and reachable. */
  cameraTab.style.display='block';
  const existing=nav && nav.querySelector('.nav-item[data-tab="camera"]');
  if(existing){
    existing.querySelector('span')?.replaceChildren(document.createTextNode('Kamera & Area Patroli'));
  }else if(nav){
    const b=document.createElement('button');
    b.type='button';
    b.className='nav-item';
    b.dataset.tab='camera';
    b.innerHTML='<i class="fas fa-camera"></i><span>Kamera & Area Patroli</span>';
    b.addEventListener('click',function(e){
      e.preventDefault();
      document.querySelectorAll('.menu-only-section').forEach(x=>x.classList.remove('menu-section-open'));
      if(typeof switchToTab==='function')switchToTab('camera');
      document.querySelectorAll('.nav-item').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');
      document.querySelector('.tab-container')?.scrollIntoView({behavior:'smooth',block:'start'});
      document.getElementById('sideNavOverlay')?.click();
    });
    nav.appendChild(b);
  }
  /* Add a clear in-page entry without replacing any baseline controls. */
  if(!document.getElementById('allsttPatrolEntry')){
    const entry=document.createElement('button');
    entry.id='allsttPatrolEntry';
    entry.type='button';
    entry.className='btn btn-primary';
    entry.innerHTML='<i class="fas fa-camera"></i> KAMERA & AREA PATROLI';
    const parent=cameraTab.parentElement;
    parent.insertBefore(entry,cameraTab);
    entry.addEventListener('click',function(){
      cameraTab.scrollIntoView({behavior:'smooth',block:'start'});
    });
  }
}
function install(){
  const camera=document.getElementById('openCameraMenu');
  const native=document.getElementById('nativeCameraInput');
  const gallery=document.getElementById('galleryCameraInput');
  ensurePatrolEntry();
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

  if(gallery.dataset.adminGuardV6!=='1'){
    gallery.dataset.adminGuardV6='1';
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

  /* One tap = camera. Two taps = gallery only after the unified ADMIN gate. */
  if(camera.dataset.adminDoubleTapV6==='1')return;
  camera.dataset.adminDoubleTapV6='1';
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
  ensurePatrolEntry();
  install();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){refresh();setTimeout(refresh,300);setTimeout(refresh,1000);setTimeout(refresh,2000)},{once:true});
else{refresh();setTimeout(refresh,300);setTimeout(refresh,1000);setTimeout(refresh,2000)}
window.addEventListener('pageshow',refresh);
})();
</script>
'''
s=s.replace('</body>',patch+'</body>',1)
p.write_text(s,encoding='utf-8')
