from pathlib import Path

p = Path('app/src/main/java/com/sapammeded/allstt/MainActivity.java')
s = p.read_text(encoding='utf-8')

# Keep the existing WebView/native behavior intact. Only make the standard
# JavaScript dialog callbacks explicit so alert()/confirm()/prompt() from the
# already-working HTML are handled by Android instead of depending on the
# WebChromeClient default implementation.
if 'import android.webkit.JsPromptResult;' not in s:
    s = s.replace('import android.webkit.JavaScriptInterface;' if 'import android.webkit.JavaScriptInterface;' in s else 'import android.webkit.JavascriptInterface;', 'import android.webkit.JavascriptInterface;\nimport android.webkit.JsPromptResult;\nimport android.webkit.JsResult;', 1)

marker = '        webView.setWebChromeClient(new WebChromeClient() {\n'
if marker not in s:
    raise SystemExit('WebChromeClient marker not found')

block = '''        webView.setWebChromeClient(new WebChromeClient() {\n            @Override public boolean onJsAlert(WebView view, String url, String message, JsResult result) {\n                new android.app.AlertDialog.Builder(MainActivity.this)\n                    .setMessage(message == null ? "" : message)\n                    .setPositiveButton(android.R.string.ok, (dialog, which) -> result.confirm())\n                    .setOnCancelListener(dialog -> result.cancel())\n                    .show();\n                return true;\n            }\n\n            @Override public boolean onJsConfirm(WebView view, String url, String message, JsResult result) {\n                new android.app.AlertDialog.Builder(MainActivity.this)\n                    .setMessage(message == null ? "" : message)\n                    .setNegativeButton(android.R.string.cancel, (dialog, which) -> result.cancel())\n                    .setPositiveButton(android.R.string.ok, (dialog, which) -> result.confirm())\n                    .setOnCancelListener(dialog -> result.cancel())\n                    .show();\n                return true;\n            }\n\n            @Override public boolean onJsPrompt(WebView view, String url, String message, String defaultValue, JsPromptResult result) {\n                final android.widget.EditText input = new android.widget.EditText(MainActivity.this);\n                input.setSingleLine(false);\n                input.setText(defaultValue == null ? "" : defaultValue);\n                new android.app.AlertDialog.Builder(MainActivity.this)\n                    .setMessage(message == null ? "" : message)\n                    .setView(input)\n                    .setNegativeButton(android.R.string.cancel, (dialog, which) -> result.cancel())\n                    .setPositiveButton(android.R.string.ok, (dialog, which) -> result.confirm(input.getText().toString()))\n                    .setOnCancelListener(dialog -> result.cancel())\n                    .show();\n                return true;\n            }\n\n'''

if 'public boolean onJsAlert(WebView view' not in s:
    s = s.replace(marker, block, 1)

p.write_text(s, encoding='utf-8')
print('Android WebView JavaScript dialog callbacks patched')
