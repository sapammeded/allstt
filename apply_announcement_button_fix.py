from pathlib import Path
import re

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

# Android WebView-safe announcement button: do not depend on localStorage or a
# single DOM event path for the only button that gates access to the app.
s = s.replace(
    '<button id="aamiinBtn">LANJUTKAN <i class="fas fa-arrow-right"></i></button>',
    '<button type="button" id="aamiinBtn" onclick="window.__allsttContinueAnnouncement && window.__allsttContinueAnnouncement(event)" ontouchend="window.__allsttContinueAnnouncement && window.__allsttContinueAnnouncement(event)" style="pointer-events:auto!important;touch-action:manipulation;">LANJUTKAN <i class="fas fa-arrow-right"></i></button>',
    1
)

old = '''  aamiinBtn.addEventListener('click', function() {
    notificationModal.style.display = 'none';
    localStorage.setItem('bangPriNotif', 'dilihat');
  });'''
new = '''  // ALLSTT ANNOUNCEMENT BUTTON FIX V2 — Android WebView safe.
  window.__allsttContinueAnnouncement = function(ev) {
    try { if (ev) { ev.preventDefault(); ev.stopPropagation(); } } catch(_) {}
    try { notificationModal.style.display = 'none'; } catch(_) {}
    try { notificationModal.style.visibility = 'hidden'; } catch(_) {}
    try { notificationModal.setAttribute('aria-hidden', 'true'); } catch(_) {}
    try { localStorage.setItem('bangPriNotif', 'dilihat'); } catch(_) {}
    return false;
  };

  aamiinBtn.addEventListener('click', window.__allsttContinueAnnouncement, true);
  aamiinBtn.addEventListener('touchend', window.__allsttContinueAnnouncement, {capture:true, passive:false});
  document.addEventListener('click', function(ev) {
    const b = ev.target && ev.target.closest ? ev.target.closest('#aamiinBtn') : null;
    if (b) window.__allsttContinueAnnouncement(ev);
  }, true);
  document.addEventListener('touchend', function(ev) {
    const b = ev.target && ev.target.closest ? ev.target.closest('#aamiinBtn') : null;
    if (b) window.__allsttContinueAnnouncement(ev);
  }, {capture:true, passive:false});'''
if old not in s:
    raise SystemExit('announcement handler block not found')
s = s.replace(old, new, 1)

# Keep the fix self-contained and fail-safe even if a later script throws.
marker = '<!-- Help Button -->'
if marker in s and 'ALLSTT ANNOUNCEMENT BUTTON FIX V2 CSS' not in s:
    inject = '''<style id="ALLSTT-ANNOUNCEMENT-BUTTON-FIX-V2-CSS">
/* ALLSTT ANNOUNCEMENT BUTTON FIX V2 CSS */
#aamiinBtn { pointer-events:auto!important; touch-action:manipulation!important; position:relative; z-index:10002!important; }
#notificationModal { pointer-events:auto!important; }
</style>
'''
    s = s.replace(marker, inject + marker, 1)

p.write_text(s, encoding='utf-8')
