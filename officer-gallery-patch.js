// ALLSTT: password-protected officer face gallery upload.
// Injected inside the main STT application scope so it can use
// saveOfficerPhoto() and the same officer photo state used by PDF.
(function setupOfficerFaceGallery(){
  const password = document.getElementById('officerGalleryPassword');
  const unlock = document.getElementById('unlockOfficerGalleryBtn');
  const access = document.getElementById('officerGalleryAccess');
  const upload = document.getElementById('uploadOfficerGalleryBtn');
  const input = document.getElementById('officerGalleryInput');
  if(!password || !unlock || !access || !upload || !input) return;
  if(upload.dataset.officerGalleryReady === '1') return;
  upload.dataset.officerGalleryReady = '1';

  access.style.display = 'none';

  function unlockGallery(){
    const pw = password.value || '';
    if(pw === getGalleryPassword()){
      galleryAccessGranted = true;
      access.style.display = 'block';
      password.value = '';
      alert('✅ Password benar. Akses upload foto wajah dari galeri dibuka.');
    }else{
      galleryAccessGranted = false;
      access.style.display = 'none';
      password.value = '';
      alert('❌ Password galeri salah.');
    }
  }

  unlock.addEventListener('click', unlockGallery);
  password.addEventListener('keydown', e => { if(e.key === 'Enter') unlockGallery(); });

  upload.addEventListener('click', e => {
    e.preventDefault();
    e.stopImmediatePropagation();
    if(access.style.display === 'none'){
      alert('🔒 Masukkan password terlebih dahulu.');
      password.focus();
      return;
    }
    input.value = '';
    input.click();
  }, true);

  input.addEventListener('click', e => {
    if(access.style.display === 'none'){
      e.preventDefault();
      e.stopImmediatePropagation();
      input.value = '';
      alert('🔒 Upload foto wajah dari galeri terkunci.');
    }
  }, true);

  input.addEventListener('change', async e => {
    const file = e.target.files?.[0];
    input.value = '';
    if(!file || access.style.display === 'none') return;
    try{
      showOverlay('Memproses foto wajah dari galeri...');
      setOverlayProgress(25);
      await saveOfficerPhoto(file);
      setOverlayProgress(100);
      hideOverlay();
      alert('✅ Foto wajah dari galeri berhasil dipasang.');
    }catch(err){
      hideOverlay();
      alert('❌ Foto wajah dari galeri gagal diproses: ' + (err?.message || err));
    }
  });
})();
