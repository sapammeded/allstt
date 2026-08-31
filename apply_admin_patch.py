from pathlib import Path
import re

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

# Keep the baseline STT intact. Only move protected controls behind ADMIN.
s = s.replace('<button class="nav-item" data-target="companySection"><i class="fas fa-building"></i><span>Kop Surat & Logo</span></button>', '<button class="nav-item" data-admin="true"><i class="fas fa-user-shield"></i><span>ADMIN</span></button>', 1)
s = s.replace('<div id="companySection" style="margin-top:20px" class="menu-only-section">', '<div id="companySection" style="margin-top:20px;display:none" class="menu-only-section">', 1)

# Remove visible admin credential UI; retain invisible bridge for the baseline handlers.
s, n = re.subn(r'\s*<div style="margin-top:14px">\s*<label class="small"><i class="fas fa-key"></i> PASSWORD ADMIN KOP & LOGO</label>.*?</div>\s*\n\s*<div id="logoUploadSection"', '\n      <div id="adminCredentialBridge" style="display:none" aria-hidden="true"><input id="logoPassword" type="password"><button id="unlockLogoBtn" type="button">ADMIN</button></div>\n      <div id="logoUploadSection"', s, count=1, flags=re.S|re.I)
if n != 1: raise RuntimeError('Admin credential block not found')
s = re.sub(r'\s*<div style="margin-top:10px">\s*<button id="changeLogoPasswordBtn".*?</div>\s*\n\s*</div>\s*\n\s*<!-- ==================== TANDA TANGAN', '\n    </div>\n\n    <!-- ==================== TANDA TANGAN', s, count=1, flags=re.S|re.I)

# Replace old gallery credential UI. Hidden IDs remain so the proven baseline gallery handler is reused.
st = s.find('<!-- SATU FITUR KAMERA: kamera HP + galeri terkunci password -->')
en = s.find('<!-- Tombol Tambah Area', st)
if st < 0 or en < 0: raise RuntimeError('Camera/gallery section markers not found')
cam = '''<!-- SATU FITUR KAMERA: kamera HP + galeri dikendalikan ADMIN -->
        <div style="text-align:center; margin:28px 0">
          <button type="button" class="camera-native-btn" id="openCameraMenu" style="border:0;width:100%;cursor:pointer"><i class="fas fa-camera"></i> KAMERA HP</button>
          <input type="file" id="nativeCameraInput" accept="image/*" capture="environment" style="display:none" />
          <input type="file" id="galleryCameraInput" accept="image/*" multiple style="display:none" />
          <div class="quality-notice" style="margin-top:14px"><i class="fas fa-camera"></i> <strong>Ambil foto langsung dari kamera bawaan HP.</strong></div>
        </div>
        <div id="galleryAdminBridge" style="display:none" aria-hidden="true"><input id="cameraGalleryPassword" type="password"><button id="unlockCameraGalleryBtn" type="button">ADMIN</button></div>
        <div class="card" id="galleryAccessCard" style="margin-top:18px">
          <div style="font-weight:800;margin-bottom:8px"><i class="fas fa-images"></i> UPLOAD DARI GALERI</div>
          <div class="small" style="margin-bottom:12px">Fitur ini hanya tersedia setelah administrator membuka akses melalui menu ADMIN.</div>
          <div id="cameraGalleryAccess" style="display:none;margin-top:12px">
            <div class="quality-notice"><i class="fas fa-check-circle"></i> Akses galeri aktif untuk sesi administrator.</div>
            <button id="uploadGalleryBtn" type="button" class="btn btn-info" style="width:100%;margin-top:10px"><i class="fas fa-images"></i> UPLOAD DARI GALERI</button>
          </div>
        </div>
        <div id="galleryPasswordSettingsLegacy" style="display:none" aria-hidden="true"><input id="currentGalleryPassword" type="password"><input id="newGalleryPassword" type="password"><input id="confirmGalleryPassword" type="password"><button id="changeGalleryPasswordBtn" type="button">ADMIN</button></div>

        '''
s = s[:st] + cam + s[en:]

# Remove the old credential wording from visible text and alerts.
for a,b in {
'PASSWORD ADMIN LOGO':'AKSES ADMIN','PASSWORD ADMIN KOP & LOGO':'AKSES ADMIN','GANTI PASSWORD ADMIN':'GANTI KODE ADMIN','GANTI PASSWORD GALERI':'PENGATURAN AKSES GALERI','SIMPAN PASSWORD BARU':'SIMPAN PENGATURAN AKSES','PASSWORD UPLOAD LOGO CUSTOM':'AKSES ADMIN UNTUK LOGO','Masukkan password untuk membuka akses upload foto dari galeri.':'Buka akses upload foto dari galeri melalui menu ADMIN.','Untuk akses galeri, buka menu ☰ → pilih <strong>Kamera & Area Patroli</strong> → masukkan password untuk membuka akses galeri.':'Untuk upload dari galeri, buka menu ☰ → pilih <strong>ADMIN</strong> → autentikasi administrator → aktifkan akses galeri.','Masukkan password admin terlebih dahulu.':'Masuk ke menu ADMIN terlebih dahulu.','Buka pengaturan dengan password admin terlebih dahulu.':'Buka pengaturan melalui menu ADMIN terlebih dahulu.','Password benar. Pengaturan kop surat dan dua logo terbuka.':'Akses ADMIN berhasil. Pengaturan kop surat dan dua logo terbuka.','Password admin salah.':'Kode admin salah.','Password logo benar. Sekarang pilih logo perusahaan.':'Akses ADMIN berhasil. Sekarang pilih logo perusahaan.','Password logo salah.':'Kode admin salah.','Password admin saat ini salah.':'Kode admin saat ini salah.','Password logo saat ini salah.':'Kode admin saat ini salah.','Password galeri berhasil diganti.':'Pengaturan akses galeri berhasil diperbarui.','Password salah!':'Kode admin salah!','Masukkan password terlebih dahulu.':'Buka akses melalui menu ADMIN terlebih dahulu.'}.items():
    s = s.replace(a,b)

panel = '''<!-- ==================== CENTRAL ADMIN PANEL ==================== -->
<div id="adminSection" class="menu-only-section card" style="margin-top:20px;border-left:6px solid var(--primary);display:none">
  <h3 style="margin:0 0 12px;color:var(--primary)"><i class="fas fa-user-shield"></i> ADMIN</h3>
  <div id="adminLoginBox"><div class="small">Masukkan kode admin untuk membuka pengaturan khusus.</div><div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px"><input id="adminAccessCode" type="password" placeholder="Kode admin" autocomplete="current-password" style="flex:1;min-width:190px;padding:12px 15px;border:2px solid #e2e8f0;border-radius:10px"><button id="adminLoginBtn" type="button" class="btn btn-primary"><i class="fas fa-unlock"></i> MASUK ADMIN</button></div></div>
  <div id="adminContent" style="display:none"><div id="adminIdentityStatus" class="quality-notice" style="margin-bottom:12px"></div><button id="adminEditIdentityBtn" type="button" class="btn btn-primary" style="width:100%;margin-bottom:8px"><i class="fas fa-building"></i> IDENTITAS PERUSAHAAN & LOGO</button><button id="adminGalleryBtn" type="button" class="btn btn-info" style="width:100%;margin-bottom:8px"><i class="fas fa-images"></i> AKTIFKAN UPLOAD FOTO DARI GALERI</button><button id="adminChangeCodeBtn" type="button" class="btn btn-ghost" style="width:100%;margin-bottom:8px"><i class="fas fa-key"></i> GANTI KODE ADMIN</button><button id="adminLogoutBtn" type="button" class="btn btn-ghost" style="width:100%"><i class="fas fa-lock"></i> KUNCI KEMBALI ADMIN</button></div>
</div>

'''
marker = '<!-- ==================== IDENTITAS PERUSAHAAN + KOP SURAT ==================== -->'
if marker not in s: raise RuntimeError('Company marker not found')
s = s.replace(marker, panel + marker, 1)

controller = r'''<script id="ALLSTT-CENTRAL-ADMIN">(function(){
'use strict';
const ADMIN_KEY='patrol_logo_password_v1', DEFAULT_ADMIN='mbahpritampan', ID_KEY='allstt_identity_initialized_v1';
let adminUnlocked=false; const $=id=>document.getElementById(id);
function code(){try{return localStorage.getItem(ADMIN_KEY)||DEFAULT_ADMIN}catch(e){return DEFAULT_ADMIN}}
function hasIdentity(){try{return localStorage.getItem(ID_KEY)==='1'||!!(localStorage.getItem('patrol_company_name_v1')||localStorage.getItem('patrol_company_address_v1')||localStorage.getItem('patrol_logo_left_v1')||localStorage.getItem('patrol_logo_right_v1'))}catch(e){return false}}
function company(v){const x=$('companySection'),l=$('logoUploadSection');if(x)x.style.display=v?'block':'none';if(l)l.style.display=v?'block':'none'}
function gallery(v){const x=$('cameraGalleryAccess');if(x)x.style.display=v?'block':'none'}
function unlockLogo(){const i=$('logoPassword'),b=$('unlockLogoBtn');if(!i||!b)return false;i.value=code();b.click();return true}
function unlockGallery(){const i=$('cameraGalleryPassword'),b=$('unlockCameraGalleryBtn');if(!i||!b)return false;localStorage.setItem('patrol_gallery_password_v1',code());i.value=code();b.click();return true}
function render(){const sec=$('adminSection');if(sec)sec.style.display='block';if($('adminLoginBox'))$('adminLoginBox').style.display=adminUnlocked?'none':'block';if($('adminContent'))$('adminContent').style.display=adminUnlocked?'block':'none';if(adminUnlocked){company(true);const st=$('adminIdentityStatus');if(st)st.textContent=hasIdentity()?'✅ Identitas perusahaan dan logo sudah menjadi default aplikasi.':'⚠️ Konfigurasi awal: isi nama perusahaan, alamat, dan logo lalu simpan.'}else{company(false);gallery(false)}}
function openAdmin(){render();$('adminSection')?.scrollIntoView({behavior:'smooth',block:'start'})}
function login(){const v=String($('adminAccessCode')?.value||'');if(v===code()){adminUnlocked=true;$('adminAccessCode').value='';render();alert('✅ Akses ADMIN dibuka.')}else alert('❌ Kode admin salah.')}
function wire(){document.querySelectorAll('.nav-item[data-admin="true"]').forEach(b=>b.addEventListener('click',e=>{e.preventDefault();openAdmin()}));$('adminLoginBtn')?.addEventListener('click',login);$('adminAccessCode')?.addEventListener('keydown',e=>{if(e.key==='Enter')login()});$('adminEditIdentityBtn')?.addEventListener('click',()=>{if(!adminUnlocked)return;company(true);unlockLogo();$('companySection')?.scrollIntoView({behavior:'smooth',block:'start')});$('adminGalleryBtn')?.addEventListener('click',()=>{if(!adminUnlocked)return;unlockGallery();gallery(true);alert('✅ Akses upload foto dari galeri aktif untuk sesi administrator.')});$('adminChangeCodeBtn')?.addEventListener('click',()=>{if(!adminUnlocked)return;const n=prompt('Masukkan kode admin baru (minimal 4 karakter):');if(n===null)return;const c=prompt('Ulangi kode admin baru:');if(n!==c||String(n).trim().length<4){alert('❌ Kode admin tidak valid atau tidak sama.');return}try{localStorage.setItem(ADMIN_KEY,String(n).trim());localStorage.setItem('patrol_gallery_password_v1',String(n).trim());alert('✅ Kode admin berhasil diperbarui.')}catch(e){alert('❌ Gagal menyimpan kode admin.')}});$('adminLogoutBtn')?.addEventListener('click',()=>{adminUnlocked=false;company(false);gallery(false);render()});$('saveCompanyHeaderBtn')?.addEventListener('click',()=>setTimeout(()=>{const n=($('companyName')?.value||'').trim(),a=($('companyAddress')?.value||'').trim();if(n||a)localStorage.setItem(ID_KEY,'1')},100));render()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire,{once:true});else wire();
})();</script>'''
s = s.replace('</body>', controller + '\n</body>', 1)
p.write_text(s, encoding='utf-8')
print('ADMIN patch applied to baseline stt.html')
