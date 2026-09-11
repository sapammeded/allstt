#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
main=ROOT/'app/src/main/java/com/sapammeded/allstt/MainActivity.java'
genius=ROOT/'app/src/main/java/com/sapammeded/allstt/MainActivityGenius.java'

m=main.read_text(encoding='utf-8')
old='''        configureWebView();\n        webView.loadUrl("file:///android_asset/launcher.html");'''
new='''        configureWebView();\n        onWebViewReady(webView);\n        webView.loadUrl("file:///android_asset/launcher.html");'''
if old not in m:
    raise SystemExit('MainActivity startup block not found')
m=m.replace(old,new,1)
anchor='''    private void configureWebView() {'''
if 'protected void onWebViewReady(WebView view)' not in m:
    if anchor not in m: raise SystemExit('configureWebView anchor not found')
    m=m.replace(anchor,'''    /** Hook for specialized activities to install JS bridges before the first page load. */\n    protected void onWebViewReady(WebView view) {}\n\n'''+anchor,1)
main.write_text(m,encoding='utf-8')

g=genius.read_text(encoding='utf-8')
start=g.find('    @Override protected void onCreate(Bundle savedInstanceState) {')
end=g.find('\n    private WebView findWebView',start)
if start<0 or end<0: raise SystemExit('MainActivityGenius onCreate block not found')
replacement='''    @Override protected void onWebViewReady(WebView view) {\n        hvssWebView = view;\n        hvssWebView.addJavascriptInterface(new CentralBridge(), "AndroidCentral");\n        // Bridge is installed before MainActivity loads launcher.html.\n        // This avoids the previous double-load/race during WebView startup.\n    }\n'''
g=g[:start]+replacement+g[end:]
genius.write_text(g,encoding='utf-8')
print('Patched WebView startup: AndroidCentral bridge is installed before the first launcher load.')
