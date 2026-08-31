from pathlib import Path

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

# The announcement is the first UI shown by STT. Keep its continue action
# completely independent from the main application IIFE, localStorage, and
# any later JavaScript. Android WebView can therefore dismiss the modal even
# if another script fails during startup.
old_button = '<button id="aamiinBtn">LANJUTKAN <i class="fas fa-arrow-right"></i></button>'
new_button = '''<button type="button" id="aamiinBtn" onclick="try{var m=document.getElementById('notificationModal');if(m){m.style.display='none';m.style.visibility='hidden';m.removeAttribute('inert');m.setAttribute('aria-hidden','true');}}catch(e){} return false;" style="pointer-events:auto!important;touch-action:manipulation!important;position:relative;z-index:10002!important;">LANJUTKAN <i class="fas fa-arrow-right"></i></button>'''

if old_button in s:
    s = s.replace(old_button, new_button, 1)
elif 'id="aamiinBtn"' not in s:
    raise SystemExit('announcement button not found')

# Replace the old startup handler with a harmless persistence-only handler.
# The actual dismissal is now inline on the button, so it cannot be blocked by
# an exception elsewhere in the startup script.
old_handler = '''  aamiinBtn.addEventListener('click', function() {
    notificationModal.style.display = 'none';
    localStorage.setItem('bangPriNotif', 'dilihat');
  });'''
new_handler = '''  // ALLSTT ANNOUNCEMENT BUTTON FIX V3
  // Dismissal is handled inline on the button so it works independently of
  // startup code and Android WebView event dispatch.
  try {
    aamiinBtn.addEventListener('click', function() {
      try { localStorage.setItem('bangPriNotif', 'dilihat'); } catch (_) {}
    }, false);
  } catch (_) {}'''
if old_handler in s:
    s = s.replace(old_handler, new_handler, 1)

# Ensure the modal/button cannot be covered by a pointer-events rule.
marker = '<!-- Help Button -->'
if marker in s and 'ALLSTT ANNOUNCEMENT BUTTON FIX V3 CSS' not in s:
    inject = '''<style id="ALLSTT-ANNOUNCEMENT-BUTTON-FIX-V3-CSS">
/* ALLSTT ANNOUNCEMENT BUTTON FIX V3 CSS */
#notificationModal { pointer-events:auto!important; }
#aamiinBtn { pointer-events:auto!important; touch-action:manipulation!important; position:relative!important; z-index:10002!important; }
</style>
'''
    s = s.replace(marker, inject + marker, 1)

p.write_text(s, encoding='utf-8')
