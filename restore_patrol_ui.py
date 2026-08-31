from pathlib import Path

p=Path('stt.html')
s=p.read_text(encoding='utf-8')
marker='<!-- ALLSTT PATROL CAMERA AREA UI RESTORE v1 -->'
if marker in s:
    raise SystemExit(0)

patch=r'''<!-- ALLSTT PATROL CAMERA AREA UI RESTORE v1 -->
<style id="allstt-patrol-camera-area-ui">
/* The main patrol workflow must ALWAYS be visible. */
#cameraTab{display:block !important;visibility:visible !important;}
#cameraTab.active{display:block !important;visibility:visible !important;}
.allstt-main-patrol-title{display:flex;align-items:center;gap:12px;margin:0 0 16px;padding:16px 18px;border-radius:14px;background:linear-gradient(135deg,#0b3d91,#4f46e5);color:#fff;font-weight:900;font-size:18px;box-shadow:0 6px 18px rgba(11,61,145,.18)}
.allstt-main-patrol-title i{font-size:22px}
</style>
<script id="allstt-patrol-camera-area-ui-script">
(function(){
'use strict';
function restore(){
  const nav=document.getElementById('sideNav');
  const tab=document.getElementById('cameraTab');
  if(!tab)return;

  // Restore the original navigation entry if another runtime patch removed it.
  if(nav && !nav.querySelector('.nav-item[data-tab="camera"]')){
    const b=document.createElement('button');
    b.type='button';b.className='nav-item';b.setAttribute('data-tab','camera');
    b.innerHTML='<i class="fas fa-camera"></i><span>Kamera & Area Patroli</span>';
    const patrolTitle=[...nav.querySelectorAll('.side-group-title')].find(x=>/patroli/i.test(x.textContent||''));
    if(patrolTitle)nav.insertBefore(b,patrolTitle.nextSibling);else nav.appendChild(b);
    b.addEventListener('click',function(){
      if(typeof window.switchToTab==='function')window.switchToTab('camera');
      document.querySelector('.tab-container')?.scrollIntoView({behavior:'smooth',block:'start'});
      nav.classList.remove('open');document.getElementById('navOverlay')?.classList.remove('open');
    });
  }

  // Give the main camera/area workflow an unmistakable visible title.
  if(!tab.querySelector('.allstt-main-patrol-title')){
    const title=document.createElement('div');
    title.className='allstt-main-patrol-title';
    title.innerHTML='<i class="fas fa-camera"></i><span>KAMERA &amp; AREA PATROLI</span>';
    tab.insertBefore(title,tab.firstChild);
  }

  tab.classList.add('active');
  tab.style.display='block';
  tab.style.visibility='visible';
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',restore,{once:true});else restore();
window.addEventListener('load',restore);
[250,700,1500].forEach(ms=>setTimeout(restore,ms));
})();
</script>
'''
s=s.replace('</body>',patch+'</body>',1)
p.write_text(s,encoding='utf-8')
