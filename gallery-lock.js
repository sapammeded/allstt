/* ALLSTT STT hard gallery guard.
   Camera remains unrestricted; only multi-photo gallery upload requires
   the session password unlock already provided by stt.html. */
(function () {
  'use strict';
  function galleryUnlocked() {
    const access = document.getElementById('cameraGalleryAccess');
    return !!access && getComputedStyle(access).display !== 'none';
  }
  function block(e) {
    if (!galleryUnlocked()) {
      e.preventDefault();
      e.stopImmediatePropagation();
      alert('🔒 Fitur upload multiple foto dari galeri terkunci. Masukkan password terlebih dahulu.');
      const input = e.currentTarget;
      if (input && 'value' in input) input.value = '';
      return false;
    }
    return true;
  }
  function install() {
    document.querySelectorAll('input[type="file"][multiple]').forEach(function (input) {
      input.addEventListener('click', block, true);
      input.addEventListener('change', block, true);
    });
    const btn = document.getElementById('uploadGalleryBtn');
    if (btn) btn.addEventListener('click', function (e) {
      if (!galleryUnlocked()) {
        e.preventDefault();
        e.stopImmediatePropagation();
        alert('🔒 Fitur upload multiple foto dari galeri terkunci. Masukkan password terlebih dahulu.');
      }
    }, true);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install);
  else install();
})();
