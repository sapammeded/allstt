from pathlib import Path
import re

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

# Remove only our previous build patches. Do not alter baseline STT logic.
s = re.sub(r'<script[^>]+id=["\']ALLSTT-[^"\']+["\'][^>]*>.*?</script>', '', s, flags=re.S|re.I)
s = re.sub(r'<style[^>]+id=["\']ALLSTT-ADMIN-CSS["\'][^>]*>.*?</style>', '', s, flags=re.S|re.I)

# The normal hamburger must never expose the old identity/configuration entry.
s = re.sub(r'<button[^>]+data-target=["\']companySection["\'][^>]*>.*?</button>', '', s, count=1, flags=re.S|re.I)

controller = r'''<style id="ALLSTT-ADMIN-CSS">
#companySection,#logoUploadSection{display:none!important}
#allsttAdminGate{position:fixed;inset:0;background:rgba(0,0,0,.72);z-index:30000;display:none;align-items:center;justify-content:center;padding:20px}
#allsttAdminGate .box{background:#fff;border-radius:18px;padding:24px;max-width:420px;width:100%;box-shadow:0 20px 50px rgba(0,0,0,.35)}
#allsttAdminGate input{width:100%;padding:14px;border:2px solid #dbe2ea;border-radius:12px;font-size:16px;margin:10px 0}
body.allstt-admin-unlocked #companySection,body.allstt-admin-unlocked #logoUploadSection{display:block!important}
</style>
<script id="ALLSTT-ADMIN-CONTROLLER">(function(){
'use strict';
var unlocked=false;
function q(s){return document.querySelector(s)}
function qa(s){return Array.prototype.slice.call(document.querySelectorAll(s))}
function protect(){
  var ids=['#companySection','#logoUploadSection'];
  ids.forEach(function(id){var e=q(id);if(e)e.style.display='none'});
  qa('button,a').forEach(function(e){var t=(e.textContent||'').toUpperCase();if(t.indexOf('UPLOAD DARI GALERI')>=0)e.style.display='none'});
  qa('input[type=file]').forEach(function(e){var id=(e.id||'').toLowerCase();if(id.indexOf('logo')>=0||id.indexOf('gallery')>=0)e.style.display='none'});
}
function unlock(){
  unlocked=true;document.body.classList.add('allstt-admin-unlocked');
  var lp=q('#logoPassword'),lu=q('#unlockLogoBtn');
  var cp=q('#cameraGalleryPassword'),cu=q('#unlockCameraGalleryBtn');
  var pass=q('#allsttAdminPassword').value;
  if(lp)lp.value=pass;if(lu)try{lu.click()}catch(e){}
  if(cp)cp.value=pass;if(cu)try{cu.click()}catch(e){}
  qa('input[type=file]').forEach(function(e){var id=(e.id||'').toLowerCase();if(id.indexOf('logo')>=0||id.indexOf('gallery')>=0)e.style.display='';});
  qa('button,a').forEach(function(e){var t=(e.textContent||'').toUpperCase();if(t.indexOf('UPLOAD DARI GALERI')>=0)e.style.display='';});
  var sec=q('#companySection');if(sec)sec.style.display='block';
  var logo=q('#logoUploadSection');if(logo)logo.style.display='block';
  var g=q('#galleryAccessCard');if(g)g.style.display='block';
  var m=q('#allsttAdminGate');if(m)m.style.display='none';
}
function gate(){
  if(q('#allsttAdminGate')){q('#allsttAdminGate').style.display='flex';q('#allsttAdminPassword').focus();return}
  var m=document.createElement('div');m.id='allsttAdminGate';m.innerHTML='<div class="box"><h2 style="margin:0 0 8px;color:#0b3d91">ADMIN</h2><div style="color:#64748b">Masukkan password administrator.</div><input id="allsttAdminPassword" type="password" autocomplete="current-password" placeholder="Password admin"><div style="display:flex;gap:8px"><button id="allsttAdminCancel" type="button" class="btn btn-ghost" style="flex:1">BATAL</button><button id="allsttAdminLogin" type="button" class="btn btn-primary" style="flex:1">MASUK</button></div></div>';document.body.appendChild(m);
  q('#allsttAdminCancel').onclick=function(){m.style.display='none'};
  q('#allsttAdminLogin').onclick=unlock;
  q('#allsttAdminPassword').onkeydown=function(e){if(e.key==='Enter')unlock()};
  m.style.display='flex';q('#allsttAdminPassword').focus();
}
function addAdmin(){
  if(q('[data-allstt-admin-menu="1"]'))return;
  var b=document.createElement('button');b.type='button';b.className='nav-item';b.setAttribute('data-allstt-admin-menu','1');b.innerHTML='<i class="fas fa-user-shield"></i><span>ADMIN</span>';b.onclick=function(e){e.preventDefault();gate()};
  var host=qa('.nav-menu,.sidebar,.menu-items,.menu-list,.side-menu').find(function(x){return x.querySelector('.nav-item')});
  if(host)host.appendChild(b);else{var ref=qa('.nav-item').find(function(x){return /Tanda Tangan|Pengaturan/i.test(x.textContent||'')});if(ref&&ref.parentNode)ref.parentNode.appendChild(b)}
}
function init(){protect();addAdmin();setTimeout(function(){if(!unlocked)protect();addAdmin()},800)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();</script>'''

s = s.replace('</head>', controller + '</head>', 1)
p.write_text(s, encoding='utf-8')
