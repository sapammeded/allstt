from pathlib import Path
import re

p = Path('app/src/main/java/com/sapammeded/allstt/MainActivity.java')
s = p.read_text(encoding='utf-8')

# Repair the known malformed saveBlobUrl bridge emitted by older builder
# revisions. Keep this idempotent so every HTML-only upload gets a clean Java
# source before Gradle runs.
lines = s.splitlines()
fixed = []
for line in lines:
    if 'saveBlobUrl(String url, String name)' in line:
        fixed.append('        @JavascriptInterface public void saveBlobUrl(String url, String name) { runOnUiThread(() -> webView.evaluateJavascript("(async()=>{try{const r=await fetch("+org.json.JSONObject.quote(url)+");const b=await r.blob();const fr=new FileReader();fr.onload=()=>Android.saveBase64File("+org.json.JSONObject.quote(name)+", "+org.json.JSONObject.quote(b.type||\\"application/octet-stream\\")+", fr.result.split(\',\')[1]);fr.readAsDataURL(b);}catch(e){Android.downloadError(String(e));}})();", null)); }')
    else:
        fixed.append(line)
s = '\n'.join(fixed) + ('\n' if s.endswith('\n') else '')

# Fail early with a useful message if the malformed single-quote form somehow
# reappears after another build-time patch.
if "b.type||'application/octet-stream'" in s:
    raise SystemExit('Unsafe JavaScript single-quoted MIME literal remains in MainActivity.java')

p.write_text(s, encoding='utf-8')
print('Java syntax safety patch applied')
