from pathlib import Path
import re

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

if 'NOTIFICATION_CONTINUE_CLICK_FIX_V1' not in s:
    marker = "  // Notifikasi BANG Pri\n  const notificationModal = document.getElementById('notificationModal');\n  const aamiinBtn = document.getElementById('aamiinBtn');"
    replacement = """  // Notifikasi BANG Pri
  // NOTIFICATION_CONTINUE_CLICK_FIX_V1: Android WebView-safe click handling.
  const NOTIFICATION_CONTINUE_CLICK_FIX_V1 = true;
  const notificationModal = document.getElementById('notificationModal');
  const aamiinBtn = document.getElementById('aamiinBtn');

  function closeNotificationModal(){
    if(notificationModal) notificationModal.style.display = 'none';
    try { localStorage.setItem('bangPriNotif', 'dilihat'); } catch(e) { console.warn('[NOTIF] localStorage unavailable:', e); }
  }

  if(aamiinBtn){
    aamiinBtn.type = 'button';
    aamiinBtn.style.pointerEvents = 'auto';
    aamiinBtn.style.touchAction = 'manipulation';
    aamiinBtn.style.position = 'relative';
    aamiinBtn.style.zIndex = '10002';
    aamiinBtn.addEventListener('click', closeNotificationModal, false);
    aamiinBtn.addEventListener('touchend', function(e){
      e.preventDefault();
      closeNotificationModal();
    }, {passive:false});
  }"""
    if marker not in s:
        raise SystemExit('notification initialization block not found')
    s = s.replace(marker, replacement, 1)

    old = """  if (localStorage.getItem('bangPriNotif') !== 'dilihat') {
    notificationModal.style.display = 'flex';
  }
  
  aamiinBtn.addEventListener('click', function() {
    notificationModal.style.display = 'none';
    localStorage.setItem('bangPriNotif', 'dilihat');
  });"""
    new = """  let notifSeen = false;
  try { notifSeen = localStorage.getItem('bangPriNotif') === 'dilihat'; } catch(e) { console.warn('[NOTIF] localStorage unavailable:', e); }
  if (!notifSeen && notificationModal) {
    notificationModal.style.display = 'flex';
  }"""
    if old not in s:
        raise SystemExit('legacy notification click block not found')
    s = s.replace(old, new, 1)

    # Ensure the modal and button always sit above the app content in Android WebView.
    css_marker = "#notificationModal {\n  position: fixed;"
    css_replacement = "#notificationModal {\n  position: fixed;\n  pointer-events: auto;"
    if css_marker in s:
        s = s.replace(css_marker, css_replacement, 1)

p.write_text(s, encoding='utf-8')
print('NOTIFICATION_CONTINUE_CLICK_FIX_V1 applied')
