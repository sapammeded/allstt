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
    out.push('https://drive.google.com/thumbnail?id='+encodeURIComponent(id)+'&sz=w1600');
    out.push('https://drive.google.com/uc?export=view&id='+encodeURIComponent(id));
    out.push('https://lh3.googleusercontent.com/d/'+encodeURIComponent(id)+'=w1600');
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

  // Word DOCX export calls photoDataWord(). The original exporter referenced
  // that helper but did not define it, causing "photoDataWord is not defined".
  // Keep the existing exporter intact and provide only the missing resolver.
  async function photoDataWordImpl(url){
    var src=String(url||'').trim();
    if(!src) return null;
    if(/^data:image\//i.test(src)) return src;
    var candidates=driveCandidates(src);
    var lastErr=null;
    for(var i=0;i<candidates.length;i++){
      try{
        var r=await fetch(candidates[i],{mode:'cors',cache:'force-cache'});
        if(!r.ok) throw new Error('HTTP '+r.status);
        var blob=await r.blob();
        if(!blob || !blob.size) throw new Error('Gambar kosong');
        return await new Promise(function(resolve,reject){
          var fr=new FileReader();
          fr.onload=function(){resolve(String(fr.result||''));};
          fr.onerror=reject;
          fr.readAsDataURL(blob);
        });
      }catch(e){ lastErr=e; }
    }
    // Same-origin/local data fallback for images already available to the page.
    try{
      var img=new Image();
      img.crossOrigin='anonymous';
      await new Promise(function(resolve,reject){img.onload=resolve;img.onerror=reject;img.src=src;});
      var c=document.createElement('canvas');
      c.width=img.naturalWidth||img.width; c.height=img.naturalHeight||img.height;
      if(!c.width||!c.height) throw new Error('Dimensi gambar kosong');
      c.getContext('2d').drawImage(img,0,0);
      return c.toDataURL('image/jpeg',0.9);
    }catch(e){ lastErr=e; }
    throw lastErr||new Error('Foto Finding tidak dapat dimuat');
  }
  window.photoDataWord=photoDataWordImpl;

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
