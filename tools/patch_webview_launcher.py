#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
main = ROOT / 'app/src/main/java/com/sapammeded/allstt/MainActivity.java'
genius = ROOT / 'app/src/main/java/com/sapammeded/allstt/MainActivityGenius.java'
m = main.read_text(encoding='utf-8')
if 'protected void onWebViewReady(WebView view)' not in m:
    anchor = '    private void configureWebView() {'
    if anchor not in m: raise SystemExit('configureWebView anchor not found')
    m = m.replace(anchor, '    /** Hook for specialized activities to install JS bridges before the first page load. */\n    protected void onWebViewReady(WebView view) {}\n\n' + anchor, 1)
old = '''        configureWebView();\n\n        // MainActivityGenius must install AndroidCentral before the first\n        // launcher document executes. Do not start a premature document load.\n        if (!(this instanceof MainActivityGenius)) {\n            webView.loadUrl("file:///android_asset/launcher.html");\n        }'''
legacy = '''        configureWebView();\n        webView.loadUrl("file:///android_asset/launcher.html");'''
desired = '''        configureWebView();\n        onWebViewReady(webView);\n        webView.loadUrl("file:///android_asset/launcher.html");'''
if desired not in m:
    if old in m: m = m.replace(old, desired, 1)
    elif legacy in m: m = m.replace(legacy, desired, 1)
    else: raise SystemExit('MainActivity startup block not recognized')
main.write_text(m, encoding='utf-8')
g = genius.read_text(encoding='utf-8')
start = g.find('    @Override protected void onCreate(Bundle savedInstanceState) {')
end = g.find('\n    private WebView findWebView', start)
hook = '''    @Override protected void onWebViewReady(WebView view) {\n        hvssWebView = view;\n        hvssWebView.addJavascriptInterface(new CentralBridge(), "AndroidCentral");\n    }\n'''
if start >= 0 and end >= 0: g = g[:start] + hook + g[end:]
genius.write_text(g, encoding='utf-8')
print('WebView launcher patch applied/verified: AndroidCentral is installed before the first launcher load, with no double-load.')
