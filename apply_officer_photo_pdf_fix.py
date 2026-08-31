from pathlib import Path
import re

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

# Persistent officer/gallery photo storage + PDF recovery.
marker = "let officerPhotoDataUrl = null;"
if "OFFICER_PHOTO_PDF_FIX_V1" not in s:
    s = s.replace(marker, marker + "\n  const OFFICER_PHOTO_PDF_FIX_V1 = 'officer_photo_pdf_v1';", 1)

# Replace the old session-only loader with an IndexedDB-backed loader.
pattern = r"async function loadOfficerPhoto\(\)\{.*?\n  \}\n\n  async function saveOfficerPhoto\(file\)\{"
replacement = r'''async function loadOfficerPhoto(){
    if(officerPhotoDataUrl) return officerPhotoDataUrl;
    try{
      if(!db && typeof openDB === 'function') await openDB();
      if(db && typeof idbGet === 'function'){
        const blob = await idbGet(STORE_BLOBS, OFFICER_PHOTO_PDF_FIX_V1);
        if(blob){
          const raw = await new Promise((resolve,reject)=>{
            const fr = new FileReader();
            fr.onload=()=>resolve(fr.result);
            fr.onerror=()=>reject(fr.error || new Error('Foto tersimpan tidak dapat dibaca.'));
            fr.readAsDataURL(blob);
          });
          officerPhotoDataUrl = raw;
          officerPhotoBlob = blob;
          officerPhotoRef = OFFICER_PHOTO_PDF_FIX_V1;
          const img=document.getElementById('officerPhotoPreview');
          const wrap=document.getElementById('officerPhotoPreviewWrap');
          const status=document.getElementById('officerPhotoStatus');
          const removeBtn=document.getElementById('removeOfficerPhotoBtn');
          if(img) img.src=raw;
          if(wrap) wrap.style.display='block';
          if(status) status.textContent='✅ Foto wajah siap dimasukkan ke PDF.';
          if(removeBtn) removeBtn.style.display='inline-flex';
          return raw;
        }
      }
    }catch(e){ console.warn('[PDF] Gagal memuat foto petugas dari penyimpanan:',e); }
    return null;
  }

  async function saveOfficerPhoto(file){'''
s2, n = re.subn(pattern, replacement, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('save/load officer photo block not found')
s = s2

# Persist the compressed image immediately after the in-memory assignments.
old = "    officerPhotoBlob = file;\n    officerPhotoDataUrl = compressed;\n    officerPhotoRef = 'memory_officer_face';"
new = """    officerPhotoBlob = file;
    officerPhotoDataUrl = compressed;
    officerPhotoRef = OFFICER_PHOTO_PDF_FIX_V1;
    try{
      if(!db && typeof openDB === 'function') await openDB();
      if(db && typeof idbPut === 'function'){
        const storedBlob = await (await fetch(compressed)).blob();
        await idbPut(STORE_BLOBS, OFFICER_PHOTO_PDF_FIX_V1, storedBlob);
        if(typeof idbPut === 'function') await idbPut(STORE_META, OFFICER_PHOTO_PDF_FIX_V1, {name:'officer-photo.jpg',ts:new Date().toISOString(),type:storedBlob.type});
      }
    }catch(e){ console.warn('[PDF] Persist foto petugas gagal, foto tetap tersedia di sesi ini:',e); }"""
if old not in s:
    raise SystemExit('saveOfficerPhoto assignment marker not found')
s = s.replace(old, new, 1)

# Make the PDF cover recover the photo from IndexedDB before rendering.
old = "      if(officerPhotoDataUrl){\n        try{\n          await addContain(\n            officerPhotoDataUrl,"
new = """      const pdfOfficerPhotoData = officerPhotoDataUrl || await loadOfficerPhoto();
      if(pdfOfficerPhotoData){
        try{
          await addContain(
            pdfOfficerPhotoData,"""
if old not in s:
    raise SystemExit('PDF portrait marker not found')
s = s.replace(old, new, 1)

# Delete the persisted copy when the user removes the officer photo.
# IMPORTANT: the remove handler is synchronous, so do not use await here.
old = "    officerPhotoRef=null;\n    officerPhotoBlob=null;\n    officerPhotoDataUrl=null;"
new = """    try{ if(typeof idbDelete==='function' && db) { const r=idbDelete(STORE_BLOBS, OFFICER_PHOTO_PDF_FIX_V1); if(r && typeof r.catch==='function') r.catch(()=>{}); } }catch(_){ }
    try{ if(typeof idbDelete==='function' && db) { const r=idbDelete(STORE_META, OFFICER_PHOTO_PDF_FIX_V1); if(r && typeof r.catch==='function') r.catch(()=>{}); } }catch(_){ }
    officerPhotoRef=null;
    officerPhotoBlob=null;
    officerPhotoDataUrl=null;"""
if old in s:
    s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('OFFICER_PHOTO_PDF_FIX_V1 applied')
