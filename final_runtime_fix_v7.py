from pathlib import Path
import re

stt = Path('stt.html')
s = stt.read_text(encoding='utf-8')

# Remove the previous V6 redispatch bridge; it can duplicate change events.
s = re.sub(r'<!-- ALLSTT FINAL UPLOAD BRIDGE V6 -->.*?</script>\s*', '', s, count=1, flags=re.S)

# Restore the visible Camera & Area Patroli gallery area.
s = re.sub(r'<style id="hidden-face-gallery-style">.*?</style>\s*', '', s, count=1, flags=re.S)

# IndexedDB must never abort the whole app on a file:// WebView security error.
open_db_pat = re.compile(r'  function openDB\(\)\{.*?\n  \}\n  await openDB\(\);', re.S)
open_db_new = '''  function openDB(){
    return new Promise((res) => {
      try {
        if(!('indexedDB' in window) || !window.indexedDB) return res(null);
        const rq = indexedDB.open(DB_NAME, 2);
        rq.onupgradeneeded = (e)=>{
          const d = e.target.result;
          if(!d.objectStoreNames.contains(STORE_BLOBS)) d.createObjectStore(STORE_BLOBS);
          if(!d.objectStoreNames.contains(STORE_META)) d.createObjectStore(STORE_META);
          if(!d.objectStoreNames.contains(STORE_SYNC)) d.createObjectStore(STORE_SYNC);
        };
        rq.onsuccess = ()=> {
          try { db = rq.result; db.onversionchange = ()=>{ try{db.close()}catch(_){} }; }
          catch(_) { db = null; }
          res(db);
        };
        rq.onerror = ()=> { console.warn('[Patrolistt] IndexedDB open failed:', rq.error); res(null); };
        rq.onblocked = ()=> { console.warn('[Patrolistt] IndexedDB open blocked.'); res(null); };
      } catch(err) {
        console.warn('[Patrolistt] IndexedDB unavailable:', err);
        db = null;
        res(null);
      }
    });
  }
  await openDB();'''
if not open_db_pat.search(s): raise SystemExit('openDB block not found')
s = open_db_pat.sub(open_db_new, s, count=1)

# Robust Android FileReader path with object-URL fallback.
file_pat = re.compile(r'  function fileToDataURL\(file\)\{.*?\n  \}\n\s*\n  function compressDataUrl', re.S)
file_new = '''  function fileToDataURL(file){
    return new Promise((resolve)=>{
      if(!file) return resolve(null);
      try{
        const fr=new FileReader();
        fr.onload=()=>resolve(fr.result || null);
        fr.onerror=async()=>{
          try{
            const u=URL.createObjectURL(file);
            const r=await fetch(u);
            const b=await r.blob();
            URL.revokeObjectURL(u);
            const fr2=new FileReader();
            fr2.onload=()=>resolve(fr2.result || null);
            fr2.onerror=()=>resolve(null);
            fr2.readAsDataURL(b);
          }catch(_){ resolve(null); }
        };
        fr.readAsDataURL(file);
      }catch(_){ resolve(null); }
    });
  }
  
  function compressDataUrl'''
if not file_pat.search(s): raise SystemExit('fileToDataURL block not found')
s = file_pat.sub(file_new, s, count=1)

# Existing area gallery buttons also recognize the unified admin session.
s = s.replace('(galleryAccessGranted || window.allsttGalleryUnlocked)',
              '(galleryAccessGranted || window.allsttGalleryUnlocked || window.allsttAdminUnlocked)')

# Add a visible Gallery button without replacing the existing camera control.
marker = '        <!-- Galeri hanya bisa dibuka setelah password benar -->'
if marker in s:
    gallery_ui = '''        <div id="allsttGalleryPanel" style="margin-top:16px">
          <button type="button" id="allsttGalleryUploadBtn" class="btn btn-primary" style="width:100%;border:0;cursor:pointer">
            <i class="fas fa-images"></i> <span id="allsttGalleryUploadLabel">🔒 UPLOAD MULTIPLE FOTO DARI GALERI — ADMIN</span>
          </button>
          <div id="allsttGalleryStatus" class="quality-notice" style="margin-top:10px">
            🔒 Sebelum ADMIN login: hanya KAMERA HP yang aktif. Setelah ADMIN login: galeri multiple foto terbuka.
          </div>
        </div>

        <!-- Existing baseline gallery input; authorization is controlled by ADMIN session. -->
'''
    s = s.replace(marker, gallery_ui, 1)

# V7: no password duplication and no synthetic change-event redispatch.
v7 = r'''<!-- ALLSTT FINAL UPLOAD BRIDGE V7 -->
<style id="allstt-final-upload-v7-css">
#cameraGalleryPassword,#unlockCameraGalleryBtn,#cameraGalleryAccess,
#currentGalleryPassword,#newGalleryPassword,#confirmGalleryPassword,
#changeGalleryPasswordBtn{display:none!important}
</style>
<script id="allstt-final-upload-v7">
(function(){
'use strict';
function admin(){
  if(window.allsttAdminUnlocked===true)return true;
  try{return sessionStorage.getItem('allstt_admin_unlocked')==='1'}catch(_){return false}
}
function refresh(){
  const b=document.getElementById('allsttGalleryUploadBtn');
  const l=document.getElementById('allsttGalleryUploadLabel');
  const st=document.getElementById('allsttGalleryStatus');
  document.querySelectorAll('input[type=file]').forEach(i=>{
    if(/gallery/i.test(i.id||'')) i.setAttribute('accept',i.getAttribute('accept')||'image/*');
    if(admin() && !i.hasAttribute('capture') && !/nativeCameraInput|officerPhotoInput/.test(i.id||'')) i.multiple=true;
  });
  if(b){
    b.disabled=false;
    if(admin()){
      if(l)l.textContent='📷 UPLOAD MULTIPLE FOTO DARI GALERI';
      if(st)st.textContent='✅ ADMIN aktif — pilih satu atau banyak foto dari Galeri.';
    }else{
      if(l)l.textContent='🔒 UPLOAD MULTIPLE FOTO DARI GALERI — ADMIN';
      if(st)st.textContent='🔒 Sebelum ADMIN login: hanya KAMERA HP yang aktif. Tekan tombol ini untuk membuka login ADMIN.';
    }
  }
}
function install(){
  refresh();
  const b=document.getElementById('allsttGalleryUploadBtn');
  if(b && b.dataset.v7!=='1'){
    b.dataset.v7='1';
    b.addEventListener('click',function(e){
      e.preventDefault();
      const open=()=>{
        refresh();
        const input=document.getElementById('galleryCameraInput');
        if(!input){alert('❌ Input galeri tidak tersedia.');return;}
        input.multiple=true;
        input.value='';
        input.click();
      };
      if(admin()) open();
      else if(typeof window.ALLSTT_ADMIN_GATE==='function') window.ALLSTT_ADMIN_GATE(open);
      else alert('🔒 Masukkan password ADMIN terlebih dahulu.');
    });
  }
  try{
    const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
    const nodes=[];let n;
    while(n=w.nextNode()) if(n.nodeValue && /^\\n+$/.test(n.nodeValue.trim())) nodes.push(n);
    nodes.forEach(x=>x.nodeValue='');
  }catch(_){}
}
function boot(){install();[250,700,1500,3000].forEach(ms=>setTimeout(refresh,ms))}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
window.addEventListener('load',install);
})();
</script>
'''
if 'ALLSTT FINAL UPLOAD BRIDGE V7' not in s:
    if '</body>' not in s: raise SystemExit('body end not found')
    s=s.replace('</body>',v7+'</body>',1)
stt.write_text(s,encoding='utf-8')

# Android WebView chooser hardening: explicitly preserve input[multiple].
java=Path('app/src/main/java/com/sapammeded/allstt/MainActivity.java')
j=java.read_text(encoding='utf-8')
needle='''                if (picker.getType() == null || picker.getType().isEmpty()) picker.setType("image/*");

                Intent camera = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);'''
repl='''                if (picker.getType() == null || picker.getType().isEmpty()) picker.setType("image/*");
                // Preserve the HTML input[multiple] contract on Android WebView.
                boolean allowMultiple = params.getMode() == FileChooserParams.MODE_OPEN_MULTIPLE;
                picker.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, allowMultiple);
                picker.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);

                Intent camera = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);'''
if needle not in j: raise SystemExit('MainActivity picker block not found')
j=j.replace(needle,repl,1)
java.write_text(j,encoding='utf-8')
