(function(){
  'use strict';

  function clean(v){
    return String(v == null ? '' : v)
      .trim()
      .replace(/[\\/:*?"<>|]/g,'-')
      .replace(/\s+/g,'_')
      .replace(/_+/g,'_')
      .replace(/^[_-]+|[_-]+$/g,'')
      .slice(0,80);
  }

  function currentReportFilename(fallback){
    var officer = '';
    var date = '';
    var shift = '';

    var officerEl = document.getElementById('petugasName');
    var dateEl = document.getElementById('tanggal');
    var shiftEl = document.getElementById('shift');

    if(officerEl) officer = officerEl.value || '';
    if(dateEl) date = dateEl.value || '';
    if(shiftEl) shift = shiftEl.value || '';

    officer = clean(officer) || 'Petugas';
    shift = clean(shift).toUpperCase() || 'SHIFT';

    // HTML date input normally returns YYYY-MM-DD.
    if(/^\d{4}-\d{2}-\d{2}$/.test(date)){
      date = date.split('-').reverse().join('-');
    }else{
      date = clean(date) || new Date().toLocaleDateString('id-ID').replace(/\//g,'-');
    }

    return officer + '_' + date + '_' + shift + '.pdf';
  }

  function resolveFilename(filename){
    var supplied = clean(filename || '');
    var generic = !supplied || /^(ALLSTT(_Download)?|download)(\.pdf)?$/i.test(supplied);
    if(generic) return currentReportFilename(supplied);
    if(!/\.pdf$/i.test(supplied)) supplied += '.pdf';
    return supplied;
  }

  function sendToAndroid(url, filename){
    if(!window.Android || !url) return false;
    var finalName = resolveFilename(filename);

    if(url.indexOf('blob:')===0){
      fetch(url).then(function(r){return r.blob();}).then(function(blob){
        var reader=new FileReader();
        reader.onloadend=function(){
          try{ window.Android.saveBase64(reader.result, finalName); }catch(e){}
        };
        reader.readAsDataURL(blob);
      }).catch(function(){});
      return true;
    }

    if(url.indexOf('data:')===0){
      try{ window.Android.saveBase64(url, finalName); return true; }catch(e){}
    }
    return false;
  }

  document.addEventListener('click',function(e){
    var a=e.target && e.target.closest ? e.target.closest('a') : null;
    if(!a || !a.download) return;
    var href=a.href||'';
    if(sendToAndroid(href,a.download)){
      e.preventDefault();
      e.stopImmediatePropagation();
    }
  },true);

  // Also expose the bridge for any future export function.
  window.ALLSTTAndroidDownload=sendToAndroid;
  window.ALLSTTResolveFilename=resolveFilename;
})();
