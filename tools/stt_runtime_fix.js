(function(){
  'use strict';

  // Android WebView compatibility: the native WebChromeClient in older builds
  // may not surface JavaScript alert() reliably. Keep the existing STT code
  // unchanged and provide a small in-page alert fallback for Android builds.
  try{
    if(!window.__ALLSTT_ALERT_FALLBACK_V1){
      window.__ALLSTT_ALERT_FALLBACK_V1=true;
      window.alert=function(message){
        try{
          var old=document.getElementById('__allstt_js_alert');
          if(old) old.remove();
          var wrap=document.createElement('div');
          wrap.id='__allstt_js_alert';
          wrap.style.cssText='position:fixed;inset:0;z-index:2147483647;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;padding:20px;font-family:system-ui,-apple-system,Segoe UI,sans-serif;';
          var box=document.createElement('div');
          box.style.cssText='width:min(420px,100%);background:#fff;color:#111827;border-radius:18px;padding:22px;box-shadow:0 18px 60px rgba(0,0,0,.45);';
          var text=document.createElement('div');
          text.style.cssText='white-space:pre-wrap;word-break:break-word;font-size:16px;line-height:1.5;margin-bottom:18px;';
          text.textContent=String(message==null?'':message);
          var ok=document.createElement('button');
          ok.type='button';
          ok.textContent='OK';
          ok.style.cssText='display:block;margin-left:auto;min-width:90px;border:0;border-radius:10px;padding:11px 18px;background:#2563eb;color:#fff;font-size:15px;font-weight:800;';
          ok.onclick=function(){try{wrap.remove();}catch(e){}};
          box.appendChild(text); box.appendChild(ok); wrap.appendChild(box); document.body.appendChild(wrap);
          ok.focus();
        }catch(e){ try{ console.log(String(message==null?'':message)); }catch(_){} }
      };
    }
  }catch(e){}

  // Unified launcher is the single device-access gate. STT's legacy local
  // gate must not ask for the ADMIN password after Central activation.
  try{ localStorage.setItem('STT_DEVICE_ACCESS_STATUS_V1','allowed'); }catch(e){}

  // HARD STT ENTRY FIX: the old notification/announcement overlay and the
  // legacy local device gate must never trap the user inside STT on Android.
  // The unified launcher already performs Central activation before opening STT.
  function fixSttEntry(){
    try{
      var gate=document.getElementById('sttDeviceAccessGate');
      if(gate) gate.remove();
      document.body.classList.remove('stt-device-locked');

      var modal=document.getElementById('notificationModal');
      var btn=document.getElementById('aamiinBtn');
      if(btn && btn.dataset.allsttEntryFix!=='1'){
        btn.dataset.allsttEntryFix='1';
        var close=function(ev){
          if(ev){try{ev.preventDefault();}catch(_){}try{ev.stopPropagation();}catch(_){}try{ev.stopImmediatePropagation();}catch(_){}
          }
          try{ if(modal) modal.style.display='none'; }catch(_){}
          try{ if(modal) modal.setAttribute('aria-hidden','true'); }catch(_){}
          try{ localStorage.setItem('bangPriNotif','dilihat'); }catch(_){}
          return false;
        };
        btn.addEventListener('pointerdown',close,{capture:true,passive:false});
        btn.addEventListener('touchstart',close,{capture:true,passive:false});
        btn.addEventListener('touchend',close,{capture:true,passive:false});
        btn.addEventListener('click',close,{capture:true,passive:false});
      }
      // If the old modal is still displayed but its button was not rendered
      // correctly, expose the page immediately rather than leaving a dead UI.
      if(modal && modal.style.display!=='none' && !btn){
        modal.style.display='none';
        modal.setAttribute('aria-hidden','true');
      }
    }catch(e){}
  }

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
      fixSttEntry();
      (root||document).querySelectorAll('.fn-photo-item img,.finding-photo-strip img,#findingNotesSection img').forEach(fixImage);
    }catch(e){}
  }
  function install(){
    scan(document);
    if(window.MutationObserver){
      var mo=new MutationObserver(function(){scan(document);});
      mo.observe(document.body||document.documentElement,{childList:true,subtree:true});
    }
    setInterval(function(){scan(document);},500);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',install,{once:true}); else install();
})();
