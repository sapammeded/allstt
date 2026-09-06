(function(){
  'use strict';
  // Unified launcher is the single device-access gate. STT's legacy local
  // gate must not ask for the ADMIN password after Central activation.
  try{ localStorage.setItem('STT_DEVICE_ACCESS_STATUS_V1','allowed'); }catch(e){}

  function driveId(url){
    var s=String(url||'').trim();
    var m=s.match(/[?&]id=([A-Za-z0-9_-]{10,})/i) || s.match(/\/d\/([A-Za-z0-9_-]{10,})/i);
    return m ? m[1] : '';
  }

  function driveCandidates(url){
    var s=String(url||'').trim(), id=driveId(s), out=[];
    if(!id) return s ? [s] : [];
    // thumbnail is generally more reliable than /uc in Android WebView.
    out.push('https://drive.google.com/thumbnail?id='+encodeURIComponent(id)+'&sz=w1200');
    out.push('https://drive.google.com/uc?export=view&id='+encodeURIComponent(id));
    out.push('https://lh3.googleusercontent.com/d/'+encodeURIComponent(id)+'=w1200');
    out.push('https://drive.google.com/uc?export=download&id='+encodeURIComponent(id));
    return out;
  }

  function fixImage(img){
    if(!img || img.dataset.sttDriveFix==='1') return;
    var src=img.getAttribute('src')||'';
    if(!/drive\.google\.com|drive\.usercontent\.google\.com|googleusercontent\.com/i.test(src)) return;
    var candidates=driveCandidates(src);
    if(!candidates.length) return;
    img.dataset.sttDriveFix='1';
    img.dataset.sttOriginalSrc=src;
    img.dataset.sttDriveCandidate='0';
    function next(){
      var i=Number(img.dataset.sttDriveCandidate||'0');
      if(i>=candidates.length) return;
      img.dataset.sttDriveCandidate=String(i+1);
      img.src=candidates[i];
    }
    img.addEventListener('error',next,false);
    next();
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
