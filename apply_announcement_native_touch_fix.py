from pathlib import Path

p = Path('app/src/main/java/com/sapammeded/allstt/MainActivity.java')
s = p.read_text(encoding='utf-8')

# Native Android fallback for the announcement gate. It only unlocks when the
# touched DOM element is #aamiinBtn, so all other WebView touch behavior stays
# unchanged. The JS routine removes the modal instead of merely hiding it.
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
                String js = "(function(){try{var e=document.elementFromPoint("+x+","+y+");if(e&&e.closest&&e.closest('#aamiinBtn')){if(window.__ALLSTT_UNLOCK_APP){window.__ALLSTT_UNLOCK_APP();}else{var m=document.getElementById('notificationModal');if(m)m.remove();document.documentElement.style.overflow='';document.body.style.overflow='';}}}catch(_){} })()";
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
