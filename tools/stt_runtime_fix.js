(function(){
  'use strict';
  function driveId(url){
    var s=String(url||'').trim();
    var m=s.match(/[?&]id=([A-Za-z0-9_-]{10,})/i) || s.match(/\/d\/([A-Za-z0-9_-]{10,})/i);
    return m ? m[1] : '';
  }
  function directImageUrl(url){
    var s=String(url||'').trim();
    var id=driveId(s);
    if(!id) return s;
    if(/drive\.google\.com|drive\.usercontent\.google\.com/i.test(s)){
      return 'https://drive.google.com/uc?export=view&id='+encodeURIComponent(id);
    }
    return s;
  }
  function fixImage(img){
    if(!img || img.dataset.sttDriveFix==='1') return;
    var src=img.getAttribute('src')||'';
    var fixed=directImageUrl(src);
    if(fixed && fixed!==src){
      img.dataset.sttDriveFix='1';
      img.dataset.sttOriginalSrc=src;
      img.addEventListener('error',function(){
        var id=driveId(img.dataset.sttOriginalSrc||img.src);
        if(!id || img.dataset.sttDriveFallback==='1') return;
        img.dataset.sttDriveFallback='1';
        img.src='https://lh3.googleusercontent.com/d/'+encodeURIComponent(id);
      },{once:false});
      img.src=fixed;
    }
  }
  function scan(root){
    try{
      (root||document).querySelectorAll('.fn-photo-item img,.finding-photo-strip img,#findingNotesSection img').forEach(fixImage);
    }catch(e){}
  }
  function install(){
    scan(document);
    if(window.MutationObserver){
      var mo=new MutationObserver(function(){scan(document);});
      mo.observe(document.body||document.documentElement,{childList:true,subtree:true});
    }
    setInterval(function(){scan(document);},2500);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',install,{once:true}); else install();
})();
