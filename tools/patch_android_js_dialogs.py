from pathlib import Path

p = Path('app/src/main/java/com/sapammeded/allstt/MainActivity.java')
s = p.read_text(encoding='utf-8')

if 'import android.webkit.JsPromptResult;' not in s:
    anchor = 'import android.webkit.JavascriptInterface;'
    if anchor not in s:
        raise SystemExit('JavascriptInterface import not found')
    s = s.replace(anchor, anchor + '\nimport android.webkit.JsPromptResult;\nimport android.webkit.JsResult;', 1)

marker = '        webView.setWebChromeClient(new WebChromeClient() {\n'
if marker not in s:
    raise SystemExit('WebChromeClient marker not found')

block = '''        webView.setWebChromeClient(new WebChromeClient() {\n            @Override public boolean onJsAlert(WebView view, String url, String message, JsResult result) {\n                new android.app.AlertDialog.Builder(MainActivity.this)\n                    .setMessage(message == null ? "" : message)\n                    .setPositiveButton(android.R.string.ok, (dialog, which) -> result.confirm())\n                    .setOnCancelListener(dialog -> result.cancel())\n                    .show();\n                return true;\n            }\n\n            @Override public boolean onJsConfirm(WebView view, String url, String message, JsResult result) {\n                new android.app.AlertDialog.Builder(MainActivity.this)\n                    .setMessage(message == null ? "" : message)\n                    .setNegativeButton(android.R.string.cancel, (dialog, which) -> result.cancel())\n                    .setPositiveButton(android.R.string.ok, (dialog, which) -> result.confirm())\n                    .setOnCancelListener(dialog -> result.cancel())\n                    .show();\n                return true;\n            }\n\n            @Override public boolean onJsPrompt(WebView view, String url, String message, String defaultValue, JsPromptResult result) {\n                final android.widget.EditText input = new android.widget.EditText(MainActivity.this);\n                input.setSingleLine(false);\n                input.setText(defaultValue == null ? "" : defaultValue);\n                new android.app.AlertDialog.Builder(MainActivity.this)\n                    .setMessage(message == null ? "" : message)\n                    .setView(input)\n                    .setNegativeButton(android.R.string.cancel, (dialog, which) -> result.cancel())\n                    .setPositiveButton(android.R.string.ok, (dialog, which) -> result.confirm(input.getText().toString()))\n                    .setOnCancelListener(dialog -> result.cancel())\n                    .show();\n                return true;\n            }\n\n'''

if 'public boolean onJsAlert(WebView view' not in s:
    s = s.replace(marker, block, 1)

# Prevent Java lambda capture errors when the resolved PDF filename is built
# inside evaluateJavascript's callback.
needle = '                    handleWebDownloadResolved(downloadUrl, cd, downloadMime, resolved);'
replacement = '                    final String resolvedFilename = resolved;\n                    handleWebDownloadResolved(downloadUrl, cd, downloadMime, resolvedFilename);'
if needle in s and 'final String resolvedFilename = resolved;' not in s:
    s = s.replace(needle, replacement, 1)

p.write_text(s, encoding='utf-8')
print('Android WebView dialog + Java lambda safety patch applied')
