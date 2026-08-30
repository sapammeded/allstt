from pathlib import Path

p = Path('app/src/main/java/com/sapammeded/allstt/MainActivity.java')
s = p.read_text(encoding='utf-8')
needle = '''        webView.setWebViewClient(new WebViewClient() {\n            @Override public void onPageFinished(WebView view, String url) {'''
replacement = '''        webView.setWebViewClient(new WebViewClient() {\n            @Override public boolean shouldOverrideUrlLoading(WebView view, String url) {\n                if (url != null && url.startsWith("file:///android_asset/")) {\n                    view.loadUrl(url);\n                    return true;\n                }\n                return false;\n            }\n\n            @Override public void onPageFinished(WebView view, String url) {'''
if needle not in s:
    raise SystemExit('Navigation hook not found')
if 'shouldOverrideUrlLoading(WebView view, String url)' not in s:
    s = s.replace(needle, replacement, 1)
p.write_text(s, encoding='utf-8')
