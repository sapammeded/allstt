from pathlib import Path

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

# Make the announcement gate independent from every later startup script.
# The unlock routine removes the modal itself (not just visually hiding it),
# resets body scrolling, and survives later scripts that try to show the modal.
old_button = '<button id="aamiinBtn">LANJUTKAN <i class="fas fa-arrow-right"></i></button>'
new_button = '''<button type="button" id="aamiinBtn" onclick="try{if(window.__ALLSTT_UNLOCK_APP){window.__ALLSTT_UNLOCK_APP();}else{var m=document.getElementById('notificationModal');if(m)m.remove();document.documentElement.style.overflow='';document.body.style.overflow='';}}catch(e){} return false;" style="pointer-events:auto!important;touch-action:manipulation!important;position:relative;z-index:10002!important;">LANJUTKAN <i class="fas fa-arrow-right"></i></button>'''

if old_button in s:
    s = s.replace(old_button, new_button, 1)
elif 'id="aamiinBtn"' not in s:
    raise SystemExit('announcement button not found')

# Replace the old startup handler with persistence-only behavior. The actual
# dismissal is handled by the emergency unlock routine below.
old_handler = '''  aamiinBtn.addEventListener('click', function() {
    notificationModal.style.display = 'none';
    localStorage.setItem('bangPriNotif', 'dilihat');
  });'''
new_handler = '''  // ALLSTT ANNOUNCEMENT BUTTON FIX V4
  try {
    aamiinBtn.addEventListener('click', function() {
      try { localStorage.setItem('bangPriNotif', 'dilihat'); } catch (_) {}
      try { if (window.__ALLSTT_UNLOCK_APP) window.__ALLSTT_UNLOCK_APP(); } catch (_) {}
    }, false);
  } catch (_) {}'''
if old_handler in s:
    s = s.replace(old_handler, new_handler, 1)

# Keep the modal/button clickable above every other layer.
marker = '<!-- Help Button -->'
css = '''<style id="ALLSTT-ANNOUNCEMENT-BUTTON-FIX-V4-CSS">
/* ALLSTT ANNOUNCEMENT BUTTON FIX V4 CSS */
#notificationModal { pointer-events:auto!important; }
#aamiinBtn { pointer-events:auto!important; touch-action:manipulation!important; position:relative!important; z-index:10002!important; }
</style>
'''
if 'ALLSTT-ANNOUNCEMENT-BUTTON-FIX-V4-CSS' not in s:
    if marker in s:
        s = s.replace(marker, css + marker, 1)
    else:
        s = s.replace('</head>', css + '</head>', 1)

# Emergency unlock is deliberately tiny and self-contained. It is installed
# before the rest of the page scripts and therefore still works if another
# startup script throws an exception. It also watches for a modal being
# re-created after the user has already pressed Continue.
emergency = r'''<script id="ALLSTT-ANNOUNCEMENT-EMERGENCY-UNLOCK-V4">
(function(){
  function unlock(){
    try{localStorage.setItem('bangPriNotif','dilihat');}catch(_){ }
    try{
      var m=document.getElementById('notificationModal');
      if(m){m.style.display='none';m.style.visibility='hidden';m.setAttribute('aria-hidden','true');m.remove();}
    }catch(_){ }
    try{document.documentElement.style.overflow='';document.body.style.overflow='';document.body.style.position='';}catch(_){ }
  }
  window.__ALLSTT_UNLOCK_APP=unlock;
  function hit(e){
    try{
      var t=e&&e.target;
      if(t&&t.closest&&t.closest('#aamiinBtn')){e.preventDefault();e.stopPropagation();unlock();return false;}
    }catch(_){ }
  }
  document.addEventListener('touchend',hit,true);
  document.addEventListener('pointerup',hit,true);
  document.addEventListener('click',hit,true);
  try{
    new MutationObserver(function(){
      try{
        if(localStorage.getItem('bangPriNotif')==='dilihat' && document.getElementById('notificationModal')) unlock();
      }catch(_){ }
    }).observe(document.documentElement,{childList:true,subtree:true});
  }catch(_){ }
})();
</script>
'''
if 'ALLSTT-ANNOUNCEMENT-EMERGENCY-UNLOCK-V4' not in s:
    s = s.replace('</head>', emergency + '</head>', 1)

p.write_text(s, encoding='utf-8')
