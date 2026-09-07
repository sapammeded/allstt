from pathlib import Path

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

FINDING_URL = 'https://script.google.com/macros/s/AKfycbyAJ9CFiTESUWLiCF_x0APclk4U-Zd85jI6LfWjE22hN8nyS_9yDEf0-rYrObuwyf59lA/exec'

# Idempotent build-time hardening. Never fail merely because an older DOCX
# anchor disappeared: the current stt.html already contains the modern Word
# Export implementation and its JSZip/runtime checks.

def replace_once(old, new):
    global s
    if old in s:
        s = s.replace(old, new, 1)
        return True
    return False

# Finding Notes must use Central Findings, never the PDF upload service.
replace_once(
    "const API=(typeof PDF_UPLOAD_URL==='string'&&PDF_UPLOAD_URL.trim())?PDF_UPLOAD_URL.trim():'';",
    f"const API=(typeof STT_FINDING_CENTRAL_URL==='string'&&STT_FINDING_CENTRAL_URL.trim())?STT_FINDING_CENTRAL_URL.trim():{FINDING_URL!r};",
)

# Ensure the Central URL exists exactly once when the source is an older file.
if 'const STT_FINDING_CENTRAL_URL' not in s:
    marker = 'const PDF_UPLOAD_URL = '
    idx = s.find(marker)
    if idx >= 0:
        line_end = s.find('\n', idx)
        if line_end < 0:
            line_end = len(s)
        s = s[:line_end + 1] + f"const STT_FINDING_CENTRAL_URL = {FINDING_URL!r};\n" + s[line_end + 1:]
        print('STT_FINDING_CENTRAL_URL added')
    else:
        print('STT_FINDING_CENTRAL_URL marker absent; skipped')

# CENTRAL returns uppercase FIXED.
replace_once(
    "return list.filter(f=>f&&f.status!=='fixed'&&((f.areaKey!=null&&String(f.areaKey)===key)||String(f.area||'').trim().toLowerCase()===target));",
    "return list.filter(f=>{const st=String(f?.status||'').toUpperCase();return f&&st!=='FIXED'&&((f.areaKey!=null&&String(f.areaKey)===key)||String(f.area_code||f.area||'').trim().toLowerCase()===target);});",
)

# Legacy DOCX helper injection is conditional. Modern source already contains
# photoDataWord and uses window.JSZip, so a missing legacy anchor is harmless.
legacy_anchor = "    const zip=new JSZip(),media=[];let rid=1;"
if 'async function photoDataWord(p)' not in s and legacy_anchor in s:
    helper = '''    async function photoDataWord(p){
      if(p&&typeof p==='object'&&p.ref){const b=await idbGet(STORE_BLOBS,p.ref);return b?await blobToBase64(b):null;}
      return typeof p==='string'?p:null;
    }\n'''
    s = s.replace(legacy_anchor, legacy_anchor + helper, 1)
    print('legacy photoDataWord helper injected')
else:
    print('DOCX anchor not required: modern Word Export detected or legacy anchor absent')

# Safe long-text wrapping for legacy pLines implementation.
old_plines = "function pLines(lines,opt={}){return lines.map((x,i)=>pText(x,{...opt,after:i===lines.length-1?(opt.after??80):0})).join('');}"
new_plines = "function pLines(lines,opt={}){const raw=Array.isArray(lines)?lines:String(lines==null?'':lines).replace(/\\r/g,'').split('\\n'),a=[];raw.forEach(line=>{let r=String(line||'');if(!r){a.push('');return;}while(r.length>92){let cut=r.lastIndexOf(' ',92);if(cut<45)cut=92;a.push(r.slice(0,cut).trim());r=r.slice(cut).trim();}a.push(r);});return a.map((x,i)=>pText(x,{...opt,after:i===a.length-1?(opt.after??80):0})).join('');}"
replace_once(old_plines, new_plines)

# Legacy Finding Notes UI hardening. No-op when the modern selectors are already present.
replace_once(
    '#findingNotesSection .fn-finding-card{margin-top:14px;border:3px solid #dc2626;border-radius:16px;background:#fff;padding:16px;box-shadow:0 4px 16px rgba(15,23,42,.08)}',
    '#findingNotesSection .fn-finding-card{margin-top:14px;border:3px solid #dc2626;border-radius:16px;background:#fef2f2;padding:16px;box-shadow:0 4px 16px rgba(15,23,42,.08);min-width:0;overflow:hidden;overflow-wrap:anywhere}',
)
replace_once(
    '#findingNotesSection .fn-notes-box{width:100%;min-height:220px;box-sizing:border-box;border:3px solid #94a3b8;border-radius:13px;background:#fff;padding:15px;font-size:20px;line-height:1.55;font-weight:800;white-space:pre-wrap;overflow-wrap:anywhere;resize:vertical}',
    '#findingNotesSection .fn-notes-box{display:block;width:100%;max-width:100%;min-width:0;min-height:220px;box-sizing:border-box;border:3px solid #dc2626;border-radius:13px;background:#fee2e2;color:#991b1b;padding:15px;font-size:22px;line-height:1.58;font-weight:900;white-space:pre-wrap;overflow:auto;overflow-wrap:anywhere;word-break:break-word;resize:vertical}',
)
replace_once(
    '#findingNotesSection .fn-new-box textarea{width:100%;min-height:240px;box-sizing:border-box;font-size:20px;font-weight:800;line-height:1.55;padding:15px;border:3px solid #2563eb;border-radius:12px;resize:vertical}',
    '#findingNotesSection .fn-new-box textarea{display:block;width:100%;max-width:100%;min-width:0;min-height:240px;box-sizing:border-box;font-size:22px;font-weight:900;line-height:1.58;padding:15px;border:3px solid #dc2626;border-radius:12px;background:#fee2e2;color:#991b1b;resize:vertical;overflow:auto;overflow-wrap:anywhere;word-break:break-word}',
)

p.write_text(s, encoding='utf-8')
print('STT hardening patch completed successfully')
