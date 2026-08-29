from pathlib import Path

p = Path('stt.html')
s = p.read_text(encoding='utf-8')
if 'STT_IDENTITY_LETTERHEAD_V1' in s:
    print('identity patch already present')
    raise SystemExit(0)
marker = """const pdf = new jsPDFCtor({
        orientation:'p',
        unit:'mm',
        format:'a4',
        compress:true
      });"""
replacement = marker + "\n\n      // STT_IDENTITY_LETTERHEAD_V1: apply saved company letterhead before report content.\n      if(window.__sttApplyLetterhead) await window.__sttApplyLetterhead(pdf);"
if marker not in s:
    raise SystemExit('PDF construction marker not found; aborting without modifying stt.html')
s = s.replace(marker, replacement, 1)
module = r'''\n<!-- STT_IDENTITY_LETTERHEAD_V1 -->
<style>
#sttIdentityPanel{margin-top:18px;padding:18px;border-radius:16px;border:2px solid #dbe4f0;background:linear-gradient(180deg,#fff,#f8fafc);box-shadow:var(--shadow-md)}
#sttIdentityPanel .id-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
#sttIdentityPanel .id-field{margin-top:10px}
#sttIdentityPanel .id-field input,#sttIdentityPanel .id-field textarea{width:100%;padding:13px 15px;border:2px solid #e2e8f0;border-radius:12px;background:#f8fafc}
#sttIdentityPanel .id-logo-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}
#sttIdentityPanel .id-logo{padding:12px;border:2px dashed #dbe4f0;border-radius:14px;text-align:center;background:#fff}
#sttIdentityPanel .id-logo img{width:88px;height:88px;object-fit:contain;border:1px solid #e2e8f0;border-radius:10px;background:#fff;display:block;margin:8px auto}
#sttIdentityPanel .id-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
#sttIdentityPanel .id-status{margin-top:10px;padding:10px 12px;border-radius:10px;font-weight:700;background:#eef6ff;color:#0b3d91}
#sttIdentityPanel .id-locked{opacity:.72}
@media(max-width:680px){#sttIdentityPanel .id-grid,#sttIdentityPanel .id-logo-grid{grid-template-columns:1fr}}
</style>
<script>
(function(){
  'use strict';
  const DB_NAME='STTIdentityDB_V1', STORE='identity', KEY='default';
  let idbPromise=null;
  function openDB(){if(idbPromise)return idbPromise;idbPromise=new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,1);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)});return idbPromise}
  async function idbPut(data){const db=await openDB();return new Promise((res,rej)=>{const tx=db.transaction(STORE,'readwrite');tx.objectStore(STORE).put(data,KEY);tx.oncomplete=res;tx.onerror=()=>rej(tx.error)})}
  async function idbGet(){const db=await openDB();return new Promise((res,rej)=>{const tx=db.transaction(STORE,'readonly');const q=tx.objectStore(STORE).get(KEY);q.onsuccess=()=>res(q.result||null);q.onerror=()=>rej(q.error)})}
  async function toBlob(dataUrl){if(!dataUrl||!dataUrl.startsWith('data:'))return null;return await(await fetch(dataUrl)).blob()}
  function blobToDataUrl(blob){return new Promise((res,rej)=>{if(!blob)return res('');const fr=new FileReader();fr.onload=()=>res(fr.result);fr.onerror=()=>rej(fr.error);fr.readAsDataURL(blob)})}
  function ensurePanel(){
    if(document.getElementById('sttIdentityPanel'))return document.getElementById('sttIdentityPanel');
    const host=document.getElementById('companySection');if(!host)return null;
    const panel=document.createElement('div');panel.id='sttIdentityPanel';
    panel.innerHTML=`<div style="display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap"><div><div style="font-size:18px;font-weight:900;color:var(--primary)"><i class="fas fa-building"></i> SIMPAN IDENTITAS & KOP SURAT</div><div class="small" style="color:var(--muted)">Identitas menjadi DEFAULT untuk setiap PDF. Logo disimpan di IndexedDB.</div></div><span id="sttIdentityLockBadge" class="btn btn-ghost" style="padding:9px 13px;cursor:default"><i class="fas fa-lock"></i> DEFAULT TERKUNCI</span></div><div class="id-grid"><div class="id-field"><label>NAMA PERUSAHAAN</label><input id="sttIdCompanyName" type="text" placeholder="Contoh: PT. NAMA PERUSAHAAN"></div><div class="id-field"><label>JUDUL KOP SURAT</label><input id="sttIdLetterTitle" type="text" placeholder="Contoh: SECURITY PATROL REPORT"></div></div><div class="id-field"><label>ALAMAT</label><textarea id="sttIdAddress" rows="2" placeholder="Alamat perusahaan"></textarea></div><div class="id-field"><label>SUBJUDUL / KETERANGAN</label><input id="sttIdSubtitle" type="text" placeholder="Keterangan resmi perusahaan"></div><div class="id-field"><label>FOOTER</label><input id="sttIdFooter" type="text" placeholder="Footer laporan (opsional)"></div><div class="id-logo-grid"><div class="id-logo"><b>LOGO DEFAULT KIRI 🔒</b><img id="sttIdLogoLeftPreview" alt="Logo default kiri"><input id="sttIdLogoLeft" type="file" accept="image/png,image/jpeg,image/webp"></div><div class="id-logo"><b>LOGO DEFAULT KANAN 🔒</b><img id="sttIdLogoRightPreview" alt="Logo default kanan"><input id="sttIdLogoRight" type="file" accept="image/png,image/jpeg,image/webp"></div></div><div class="id-actions"><button id="sttIdSave" type="button" class="btn btn-primary"><i class="fas fa-save"></i> SIMPAN SEBAGAI DEFAULT</button><button id="sttIdEdit" type="button" class="btn btn-warning" style="display:none"><i class="fas fa-pen"></i> EDIT IDENTITAS</button></div><div id="sttIdStatus" class="id-status">Belum ada identitas default. Silakan isi lalu simpan.</div>`;
    host.parentElement.insertBefore(panel,host.nextSibling);return panel;
  }
  const panel=ensurePanel();if(!panel)return;
  ['companyEmail','companyPhone'].forEach(id=>document.getElementById(id)?.closest('.col')?.remove());
  const pw=document.getElementById('logoPassword');if(pw){const box=pw.closest('div[style*="margin-top:14px"]')||pw.parentElement?.parentElement;if(box)box.style.display='none'}
  ['changeLogoPasswordBtn','newLogoPassword','confirmLogoPassword','unlockLogoBtn'].forEach(id=>{const e=document.getElementById(id);if(e){const b=e.closest('div');if(b)b.style.display='none';e.style.display='none'}});
  const fields={name:document.getElementById('sttIdCompanyName'),title:document.getElementById('sttIdLetterTitle'),address:document.getElementById('sttIdAddress'),subtitle:document.getElementById('sttIdSubtitle'),footer:document.getElementById('sttIdFooter'),left:document.getElementById('sttIdLogoLeft'),right:document.getElementById('sttIdLogoRight')};
  const previews={left:document.getElementById('sttIdLogoLeftPreview'),right:document.getElementById('sttIdLogoRightPreview')};
  const saveBtn=document.getElementById('sttIdSave'),editBtn=document.getElementById('sttIdEdit'),status=document.getElementById('sttIdStatus'),badge=document.getElementById('sttIdentityLockBadge');
  let leftData='',rightData='',unlocked=false;
  function setLocked(v){unlocked=!v;Object.values(fields).forEach(e=>{if(e)e.disabled=v});saveBtn.style.display=v?'none':'inline-flex';editBtn.style.display=v?'inline-flex':'none';panel.classList.toggle('id-locked',v);badge.innerHTML=v?'<i class="fas fa-lock"></i> DEFAULT TERKUNCI':'<i class="fas fa-lock-open"></i> MODE EDIT'}
  async function load(){try{const d=await idbGet();if(d){leftData=await blobToDataUrl(d.left);rightData=await blobToDataUrl(d.right)}}catch(e){console.warn('STT identity IndexedDB:',e)}fields.name.value=localStorage.getItem('patrol_company_name_v1')||'';fields.title.value=localStorage.getItem('patrol_letter_title_v1')||'';fields.address.value=localStorage.getItem('patrol_company_address_v1')||'';fields.subtitle.value=localStorage.getItem('patrol_letter_subtitle_v1')||'';fields.footer.value=localStorage.getItem('patrol_letter_footer_v1')||'';if(leftData)previews.left.src=leftData;if(rightData)previews.right.src=rightData;const has=!!(fields.name.value||fields.address.value||leftData||rightData);status.textContent=has?'✅ Identitas & kop surat aktif sebagai DEFAULT.':'Belum ada identitas default. Silakan isi lalu simpan.';setLocked(has)}
  function syncGlobals(){try{window.__sttIdentityLeft=leftData;window.__sttIdentityRight=rightData;if(typeof logoData!=='undefined'&&leftData)logoData=leftData;if(typeof logoDataRight!=='undefined'&&rightData)logoDataRight=rightData;if(typeof companyName!=='undefined')companyName=fields.name.value.trim();if(typeof companyAddress!=='undefined')companyAddress=fields.address.value.trim()}catch(_){} }
  function readFile(f){return new Promise((res,rej)=>{const fr=new FileReader();fr.onload=()=>res(fr.result);fr.onerror=()=>rej(fr.error);fr.readAsDataURL(f)})}
  fields.left.addEventListener('change',async e=>{if(!unlocked)return;const f=e.target.files?.[0];if(!f)return;if(f.size>2*1024*1024){alert('Logo maksimal 2 MB.');return}leftData=await readFile(f);previews.left.src=leftData;syncGlobals()});
  fields.right.addEventListener('change',async e=>{if(!unlocked)return;const f=e.target.files?.[0];if(!f)return;if(f.size>2*1024*1024){alert('Logo maksimal 2 MB.');return}rightData=await readFile(f);previews.right.src=rightData;syncGlobals()});
  saveBtn.addEventListener('click',async()=>{try{const name=fields.name.value.trim(),address=fields.address.value.trim();if(!name){alert('Nama perusahaan wajib diisi.');return}localStorage.setItem('patrol_company_name_v1',name);localStorage.setItem('patrol_company_address_v1',address);localStorage.setItem('patrol_letter_title_v1',fields.title.value.trim());localStorage.setItem('patrol_letter_subtitle_v1',fields.subtitle.value.trim());localStorage.setItem('patrol_letter_footer_v1',fields.footer.value.trim());await idbPut({left:await toBlob(leftData),right:await toBlob(rightData),savedAt:Date.now()});syncGlobals();status.textContent='✅ Tersimpan sebagai DEFAULT. Logo kiri & kanan sekarang dikunci dan dipakai otomatis pada PDF.';setLocked(true);alert('✅ Identitas & kop surat berhasil disimpan sebagai DEFAULT.')}catch(e){alert('❌ Gagal menyimpan identitas: '+e.message)}});
  editBtn.addEventListener('click',()=>{setLocked(false);status.textContent='✏️ Mode edit aktif. Setelah selesai tekan SIMPAN SEBAGAI DEFAULT.'});
  window.__sttApplyLetterhead=async function(pdf){syncGlobals();const W=pdf.internal.pageSize.getWidth(),L=12,R=12;if(leftData){try{pdf.addImage(leftData,'AUTO',L,10,28,28)}catch(_){}}if(rightData){try{pdf.addImage(rightData,'AUTO',W-R-28,10,28,28)}catch(_){}}pdf.setTextColor(11,61,145);pdf.setFont('helvetica','bold');pdf.setFontSize(15);pdf.text(fields.name.value.trim()||'NAMA PERUSAHAAN',W/2,15,{align:'center'});if(fields.title.value.trim()){pdf.setFontSize(10);pdf.text(fields.title.value.trim(),W/2,22,{align:'center'})}pdf.setTextColor(30,41,59);pdf.setFont('helvetica','normal');pdf.setFontSize(8);let y=28;if(fields.address.value.trim()){const lines=pdf.splitTextToSize(fields.address.value.trim(),105);pdf.text(lines,W/2,y,{align:'center'});y+=lines.length*4}if(fields.subtitle.value.trim())pdf.text(fields.subtitle.value.trim(),W/2,y,{align:'center'});pdf.setDrawColor(11,61,145);pdf.setLineWidth(.6);pdf.line(L,40,W-R,40)};
  load();
})();
</script>
'''
s = s.replace('</body>', module + '</body>', 1)
p.write_text(s, encoding='utf-8')
print('identity patch applied')
