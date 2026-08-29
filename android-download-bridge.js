(function(){
  'use strict';
  function sendToAndroid(url, filename){
    if(!window.Android || !url) return false;
    if(url.indexOf('blob:')===0){
      fetch(url).then(function(r){return r.blob();}).then(function(blob){
        var reader=new FileReader();
        reader.onloadend=function(){ try{ window.Android.saveBase64(reader.result, filename||'ALLSTT'); }catch(e){} };
        reader.readAsDataURL(blob);
      }).catch(function(){});
      return true;
    }
    if(url.indexOf('data:')===0){ try{ window.Android.saveBase64(url, filename||'ALLSTT'); return true; }catch(e){} }
    return false;
  }
  document.addEventListener('click',function(e){
    var a=e.target && e.target.closest ? e.target.closest('a') : null;
    if(!a || !a.download) return;
    var href=a.href||'';
    if(sendToAndroid(href,a.download)){ e.preventDefault(); e.stopImmediatePropagation(); }
  },true);
  window.ALLSTTAndroidDownload=sendToAndroid;
})();
