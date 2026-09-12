#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
main = ROOT / 'app/src/main/java/com/sapammeded/allstt/MainActivity.java'
genius = ROOT / 'app/src/main/java/com/sapammeded/allstt/MainActivityGenius.java'

m = main.read_text(encoding='utf-8')

# The repository may already contain the corrected startup architecture.  In that
# case this step must be a safe no-op rather than failing the entire CI build.
if 'protected void onWebViewReady(WebView view)' not in m:
    anchor = '    private void configureWebView() {'
    if anchor not in m:
        raise SystemExit('configureWebView anchor not found')
    m = m.replace(
        anchor,
        '    /** Hook for specialized activities to install JS bridges before the first page load. */\n'
        '    protected void onWebViewReady(WebView view) {}\n\n' + anchor,
        1,
    )

current_fixed = '''        configureWebView();

        // MainActivityGenius must install AndroidCentral before the first
        // launcher document executes. Do not start a premature document load.
        if (!(this instanceof MainActivityGenius)) {
            webView.loadUrl("file:///android_asset/launcher.html");
        }'''
old_startup = '''        configureWebView();
        webView.loadUrl("file:///android_asset/launcher.html");'''
desired_startup = '''        configureWebView();
        onWebViewReady(webView);
        webView.loadUrl("file:///android_asset/launcher.html");'''

if desired_startup not in m:
    if current_fixed in m:
        m = m.replace(current_fixed, desired_startup, 1)
    elif old_startup in m:
        m = m.replace(old_startup, desired_startup, 1)
    else:
        raise SystemExit('MainActivity startup block not recognized')

main.write_text(m, encoding='utf-8')

g = genius.read_text(encoding='utf-8')

desired_hook = '''    @Override protected void onWebViewReady(WebView view) {
        hvssWebView = view;
        hvssWebView.addJavascriptInterface(new CentralBridge(), "AndroidCentral");
        // Bridge is installed before MainActivity loads launcher.html.
        // This avoids the previous double-load/race during WebView startup.
    }
'''

if 'protected void onWebViewReady(WebView view)' not in g:
    start = g.find('    @Override protected void onCreate(Bundle savedInstanceState) {')
    end = g.find('\n    private WebView findWebView', start)
    if start < 0 or end < 0:
        raise SystemExit('MainActivityGenius onCreate block not found')
    g = g[:start] + desired_hook + g[end:]
else:
    # If a previous run already installed the hook, leave it untouched.
    pass

genius.write_text(g, encoding='utf-8')
print('WebView launcher patch applied/verified: AndroidCentral is installed before the first launcher load, with no double-load.')
