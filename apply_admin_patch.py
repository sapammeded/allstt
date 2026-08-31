from pathlib import Path
p=Path('stt.html'); s=p.read_text(encoding='utf-8')
# Keep the known-good STT baseline intact. Only add access control around existing UI/handlers.
s=s.replace("let companyName = localStorage.getItem('patrol_company_name_v1') || '';", "let companyName = localStorage.getItem('patrol_company_name_v1') || 'STT DATA CENTRES';")
s=s.replace("let companyAddress = localStorage.getItem('patrol_company_address_v1') || '';", "let companyAddress = localStorage.getItem('patrol_company_address_v1') || 'KAWASAN INDUSTRI DELTAMAS GIIC\\nCIKARANG PUSAT KABUPATEN BEKASI';")
patch=r'''<style id="ALLSTT-ADMIN-CLEAN-CSS">
body:not(.allstt-admin-unlocked) #companySection,body:not(.allstt-admin-unlocked) #logoUploadSection,body:not(.allstt-admin-unlocked) .nav-item[data-target="companySection"]{display:none!important}
#allsttAdminGate{position:fixed;inset:0;display:none;align-items:center;justify-content:center;z-index:50000;background:rgba(0,0,0,.72);padding:20px}
#allsttAdminGate .box{width:min(420px,100%);background:#fff;border-radius:18px;padding:24px}
#allsttAdminGate input{width:100%;box-sizing:border-box;padding:14px;margin:12px 0;border:2px solid #dbe2ea;border-radius:12px;font-size:16px}
</style>
<script id="ALLSTT-ADMIN-CLEAN">
(function(){'use strict';var admin=false;
function $(id){return document.getElementById(id)}
function pw(){try{return typeof getLogoUploadPassword==='function'?getLogoUploadPassword():(typeof getGalleryPassword==='function'?getGalleryPassword():'')}catch(e){return ''}}
function hide(){if(admin)return;['companySection','logoUploadSection'].forEach(function(id){var e=$(id);if(e)e.style.display='none'});document.querySelectorAll('.nav-item[data-target="companySection"]').forEach(function(e){e.style.display='none'})}
function gate(){var g=$('allsttAdminGate');if(!g){g=document.createElement('div');g.id='allsttAdminGate';g.innerHTML='<div class="box"><h2 style="color:#0b3d91">ADMIN</h2><div>Masukkan password admin.</div><input id="allsttAdminPassword" type="password" autocomplete="current-password"><div style="display:flex;gap:10px"><button type="button" id="allsttAdminCancel" class="btn btn-ghost" style="flex:1">BATAL</button><button type="button" id="allsttAdminEnter" class="btn btn-primary" style="flex:1">MASUK</button></div></div>';document.body.appendChild(g);$('allsttAdminCancel').onclick=function(){g.style.display='none'};$('allsttAdminEnter').onclick=unlock;$('allsttAdminPassword').onkeydown=function(e){if(e.key==='Enter')unlock()}}g.style.display='flex';$('allsttAdminPassword').value='';$('allsttAdminPassword').focus()}
function unlock(){var f=$('allsttAdminPassword');if(!f||f.value!==pw()){alert('Password admin salah.');return}admin=true;window.allsttAdminUnlocked=true;document.body.classList.add('allstt-admin-unlocked');var g=$('allsttAdminGate');if(g)g.style.display='none';var c=$('companySection');if(c)c.style.display='block';var l=$('logoUploadSection');if(l)l.style.display='block';var gp=$('cameraGalleryPassword'),gu=$('unlockCameraGalleryBtn');if(gp&&gu){gp.value=pw();try{gu.click()}catch(e){}}alert('Mode ADMIN aktif.')}
function menu(){if(document.querySelector('[data-allstt-admin-menu="1"]'))return;var host=document.querySelector('.side-nav');if(!host)return;var b=document.createElement('button');b.type='button';b.className='nav-item';b.setAttribute('data-allstt-admin-menu','1');b.innerHTML='<i class="fas fa-user-shield"></i><span>ADMIN</span>';b.onclick=function(e){e.preventDefault();gate()};host.appendChild(b)}
function guard(){if(admin)return;var b=$('uploadGalleryBtn');if(b)b.addEventListener('click',function(e){e.preventDefault();e.stopImmediatePropagation();alert('Multiple upload galeri hanya tersedia untuk ADMIN.')},true);var i=$('galleryCameraInput');if(i)i.addEventListener('change',function(e){e.target.value='';alert('Multiple upload galeri hanya tersedia untuk ADMIN.')},true);var u=$('unlockCameraGalleryBtn');if(u)u.addEventListener('click',function(e){e.preventDefault();e.stopImmediatePropagation();alert('Fitur ini hanya tersedia untuk ADMIN.')},true)}
function init(){hide();menu();guard();setTimeout(function(){hide();menu();guard()},500)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
</script>
'''
if 'ALLSTT-ADMIN-CLEAN' not in s:s=s.replace('</head>',patch+'</head>',1)
p.write_text(s,encoding='utf-8')
