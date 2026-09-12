from pathlib import Path

p = Path('app/src/main/java/com/sapammeded/allstt/MainActivity.java')
s = p.read_text(encoding='utf-8')

# Repair only malformed saveBlobUrl bridges. Never rewrite an already-correct
# bridge, because escaping a JavaScript literal inside Java is easy to corrupt.
correct = '''        @JavascriptInterface public void saveBlobUrl(String url, String name) { runOnUiThread(() -> webView.evaluateJavascript("(async()=>{try{const r=await fetch("+safeUrl+");const b=await r.blob();const fr=new FileReader();fr.onload=()=>Android.saveBase64File("+safeName+","+safeMime+",fr.result.split(',')[1]);fr.readAsDataURL(b);}catch(e){Android.downloadError(String(e));}})();", null)); }'''

lines = s.splitlines()
fixed = []
for line in lines:
    if 'saveBlobUrl(String url, String name)' in line:
        if 'safeUrl' in line and 'safeName' in line and 'safeMime' in line:
            fixed.append(line)
        else:
            fixed.append(correct)
    else:
        fixed.append(line)

s = '\n'.join(fixed) + ('\n' if s.endswith('\n') else '')
p.write_text(s, encoding='utf-8')
print('Java bridge repair applied safely')
