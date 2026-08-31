from pathlib import Path

p = Path('app/src/main/java/com/sapammeded/allstt/MainActivity.java')
s = p.read_text(encoding='utf-8')

# Native Android fallback for the announcement gate. This only watches ACTION_UP
# and only dismisses the modal when the touched DOM element is #aamiinBtn.
# Returning false preserves every existing WebView touch/click behavior.
anchor = "        webView.setDownloadListener((url, userAgent, contentDisposition, mimeType, contentLength) -> handleWebDownload(url, contentDisposition, mimeType));"
call = anchor + "\n        installAnnouncementTouchBridge();"
if 'installAnnouncementTouchBridge();' not in s:
    if anchor not in s:
        raise SystemExit('download listener anchor not found')
    s = s.replace(anchor, call, 1)

method_anchor = '    private void installDownloadBridgePatch(WebView view) {'
method = r'''    private void installAnnouncementTouchBridge() {
        webView.setOnTouchListener((v, event) -> {
            if (event.getAction() == android.view.MotionEvent.ACTION_UP) {
                final float x = event.getX();
                final float y = event.getY();
                String js = "(function(){try{var e=document.elementFromPoint("+x+","+y+");if(e&&e.closest&&e.closest('#aamiinBtn')){var m=document.getElementById('notificationModal');if(m){m.style.display='none';m.style.visibility='hidden';m.setAttribute('aria-hidden','true');try{localStorage.setItem('bangPriNotif','dilihat')}catch(_){} }}}catch(_){} })()";
                webView.evaluateJavascript(js, null);
            }
            return false;
        });
    }

'''
if 'private void installAnnouncementTouchBridge()' not in s:
    if method_anchor not in s:
        raise SystemExit('method anchor not found')
    s = s.replace(method_anchor, method + method_anchor, 1)

p.write_text(s, encoding='utf-8')
