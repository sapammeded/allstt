/* ALLSTT STT gallery protection.
   Camera remains unrestricted. Patrol gallery and officer-face gallery
   require the existing session password before a file can be selected. */
(function () {
  'use strict';

  function galleryUnlocked() {
    const access = document.getElementById('cameraGalleryAccess');
    return !!access && getComputedStyle(access).display !== 'none';
  }

  function officerGalleryPasswordOk() {
    const input = document.getElementById('officerGalleryPassword');
    if (!input) return false;
    try {
      return typeof getGalleryPassword === 'function' && input.value === getGalleryPassword();
    } catch (_) {
      return false;
    }
  }

  function processOfficerGalleryFiles(files) {
    const file = files && files[0];
    if (!file) return;

    if (typeof saveOfficerPhoto !== 'function') {
      alert('❌ Fitur foto wajah belum siap.');
      return;
    }

    const run = async function () {
      try {
        if (!file.type || !file.type.startsWith('image/')) {
          throw new Error('File harus berupa gambar.');
        }
        if (file.size > 8 * 1024 * 1024) {
          throw new Error('Foto terlalu besar. Maksimal 8MB.');
        }

        if (typeof showOverlay === 'function') showOverlay('Memproses foto wajah dari galeri...');
        if (typeof setOverlayProgress === 'function') setOverlayProgress(25);

        await saveOfficerPhoto(file);

        if (typeof setOverlayProgress === 'function') setOverlayProgress(100);
        if (typeof hideOverlay === 'function') hideOverlay();

        const status = document.getElementById('officerPhotoStatus');
        if (status) status.textContent = '✅ Foto wajah dari galeri siap dimasukkan ke PDF.';

        alert('✅ Foto wajah berhasil diambil dari galeri.');
      } catch (err) {
        if (typeof hideOverlay === 'function') hideOverlay();
        alert('❌ Foto wajah dari galeri gagal diproses: ' + (err && err.message ? err.message : err));
      }
    };

    run();
  }

  function installOfficerFaceGallery() {
    const password = document.getElementById('officerGalleryPassword');
    const unlock = document.getElementById('unlockOfficerGalleryBtn');
    const access = document.getElementById('officerGalleryAccess');
    const upload = document.getElementById('uploadOfficerGalleryBtn');
    const input = document.getElementById('officerGalleryInput');

    if (!password || !unlock || !access || !upload || !input) return;
    if (upload.dataset.officerGalleryInstalled === '1') return;
    upload.dataset.officerGalleryInstalled = '1';

    // Access is session-only. Never persist the unlocked state.
    access.style.display = 'none';

    function unlockGallery() {
      let ok = false;
      try {
        ok = typeof getGalleryPassword === 'function' && password.value === getGalleryPassword();
      } catch (_) {}

      if (!ok) {
        access.style.display = 'none';
        password.value = '';
        alert('❌ Password galeri salah.');
        return;
      }

      access.style.display = 'block';
      password.value = '';
      alert('✅ Password benar. Akses upload foto wajah dari galeri dibuka.');
    }

    unlock.addEventListener('click', unlockGallery);
    password.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') unlockGallery();
    });

    upload.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopImmediatePropagation();

      if (access.style.display === 'none') {
        alert('🔒 Masukkan password terlebih dahulu.');
        password.focus();
        return;
      }

      input.value = '';
      input.click();
    }, true);

    input.addEventListener('click', function (e) {
      if (access.style.display === 'none') {
        e.preventDefault();
        e.stopImmediatePropagation();
        input.value = '';
        alert('🔒 Upload foto wajah dari galeri terkunci. Masukkan password terlebih dahulu.');
      }
    }, true);

    input.addEventListener('change', function (e) {
      if (access.style.display === 'none') {
        input.value = '';
        return;
      }
      const files = Array.from(e.target.files || []);
      input.value = '';
      processOfficerGalleryFiles(files);
    });
  }

  function installPatrolGalleryGuard() {
    document.querySelectorAll('input[type="file"][multiple]').forEach(function (input) {
      if (input.id === 'officerGalleryInput' || input.dataset.galleryGuardInstalled === '1') return;
      input.dataset.galleryGuardInstalled = '1';
      input.addEventListener('click', function (e) {
        if (!galleryUnlocked()) {
          e.preventDefault();
          e.stopImmediatePropagation();
          alert('🔒 Fitur upload multiple foto dari galeri terkunci. Masukkan password terlebih dahulu.');
          input.value = '';
        }
      }, true);
      input.addEventListener('change', function (e) {
        if (!galleryUnlocked()) {
          e.preventDefault();
          e.stopImmediatePropagation();
          input.value = '';
        }
      }, true);
    });

    const btn = document.getElementById('uploadGalleryBtn');
    if (btn && btn.dataset.galleryGuardInstalled !== '1') {
      btn.dataset.galleryGuardInstalled = '1';
      btn.addEventListener('click', function (e) {
        if (!galleryUnlocked()) {
          e.preventDefault();
          e.stopImmediatePropagation();
          alert('🔒 Fitur upload multiple foto dari galeri terkunci. Masukkan password terlebih dahulu.');
        }
      }, true);
    }
  }

  function install() {
    installOfficerFaceGallery();
    installPatrolGalleryGuard();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', install);
  } else {
    install();
  }

  window.addEventListener('load', install);
})();
