from pathlib import Path
import re

p = Path('hvss2.html')
s = p.read_text(encoding='utf-8')

# BUILD-TIME ONLY: hvss2.html in git stays the user's uploaded baseline.
# The native CENTRAL transport must be reproducible from a normal HVSS2
# upload; never require the uploaded file to already contain our patch.
for marker in (
    'window.HVSS_CENTRAL = {',
    'function applyCentral(data){',
    'function pullCentral(){',
    'async function syncNow(reason){',
    'window.HVSS_RESET_CENTRAL=async function(){'
):
    if marker not in s:
        raise SystemExit(f'Expected HVSS2 anchor not found: {marker}')

render_anchor = 'function renderAll(){renderDashboard();renderVisitors();renderKeys();renderReport();renderHistory()}'
render_export = render_anchor + '\nwindow.HVSS_RENDER_ALL=renderAll;\nwindow.HVSS_RENDER_KEY_LOG=renderKeyLog;\nwindow.HVSS_ADD_BULK_KEY_ROW=addBulkKeyRow;'
if 'window.HVSS_RENDER_ALL=renderAll;' not in s:
    if render_anchor not in s:
        raise SystemExit('renderAll anchor not found')
    s = s.replace(render_anchor, render_export, 1)

old_ui = '''    if(typeof renderAll==='function') if(document.getElementById("bkRows")&&!document.querySelector("#bkRows .key-bulk-row"))addBulkKeyRow();
renderAll();
    if(typeof renderKeyLog==='function')renderKeyLog();'''
new_ui = '''    if(typeof window.HVSS_ADD_BULK_KEY_ROW==='function'){
      if(document.getElementById("bkRows")&&!document.querySelector("#bkRows .key-bulk-row"))window.HVSS_ADD_BULK_KEY_ROW();
    }
    if(typeof window.HVSS_RENDER_ALL==='function')window.HVSS_RENDER_ALL();
    if(typeof window.HVSS_RENDER_KEY_LOG==='function')window.HVSS_RENDER_KEY_LOG();'''
if old_ui in s:
    s = s.replace(old_ui, new_ui, 1)
else:
    # Some uploaded baselines differ only in whitespace/indentation. Apply the
    # same fix by replacing the complete applyCentral refresh tail, so a
    # build can never leave an out-of-scope renderAll() call behind.
    apply_start = s.find('  function applyCentral(data){')
    pull_start = s.find('  function pullCentral(){', apply_start)
    if apply_start < 0 or pull_start < 0:
        raise SystemExit('Could not locate applyCentral/pullCentral boundaries')
    block = s[apply_start:pull_start]
    if 'renderAll();' not in block:
        raise SystemExit('CENTRAL UI refresh renderAll anchor not found')
    block = re.sub(r'(?m)^\s*if\(typeof renderAll===\'function\'\).*?addBulkKeyRow\(\);\s*\n', '', block, count=1)
    block = re.sub(r'(?m)^\s*renderAll\(\);\s*\n', '    if(typeof window.HVSS_RENDER_ALL===\'function\')window.HVSS_RENDER_ALL();\n', block, count=1)
    block = re.sub(r'(?m)^\s*if\(typeof renderKeyLog===\'function\)renderKeyLog\(\);\s*\n', '    if(typeof window.HVSS_RENDER_KEY_LOG===\'function\')window.HVSS_RENDER_KEY_LOG();\n', block, count=1)
    s = s[:apply_start] + block + s[pull_start:]

native_bridge = '''  function nativeCentralCall(type, payload, timeoutMs=30000){
    if(!window.AndroidCentral) return null;
    return new Promise((resolve,reject)=>{
      const id="hvssNative_"+Date.now()+"_"+Math.random().toString(36).slice(2);
      let done=false;
      const timer=setTimeout(()=>{done=true;delete window.__HVSS_NATIVE_CENTRAL_WAIT[id];reject(new Error("Timeout komunikasi CENTRAL"))},timeoutMs);
      if(!window.__HVSS_NATIVE_CENTRAL_WAIT)window.__HVSS_NATIVE_CENTRAL_WAIT={};
      window.__HVSS_NATIVE_CENTRAL_WAIT[id]=(ok,data)=>{
        if(done)return;done=true;clearTimeout(timer);delete window.__HVSS_NATIVE_CENTRAL_WAIT[id];
        if(ok){try{resolve(typeof data==="string"?JSON.parse(data):data)}catch(e){reject(new Error("Response CENTRAL bukan JSON: "+e.message))}}
        else reject(new Error(String(data||"Koneksi CENTRAL gagal")));
      };
      try{
        if(type==="get") AndroidCentral.getCentral(C.gasUrl,C.spreadsheetId,id);
        else AndroidCentral.postCentral(C.gasUrl,String(payload||""),id);
      }catch(e){clearTimeout(timer);delete window.__HVSS_NATIVE_CENTRAL_WAIT[id];reject(e)}
    });
  }
  window.__HVSS_NATIVE_CENTRAL_RESOLVE=function(id,ok,data){
    const fn=window.__HVSS_NATIVE_CENTRAL_WAIT&&window.__HVSS_NATIVE_CENTRAL_WAIT[id];
    if(fn)fn(!!ok,String(data==null?"":data));
  };
'''
if 'function nativeCentralCall(' not in s:
    s = s.replace('  function pullCentral(){', native_bridge + '  function pullCentral(){', 1)

native_pull = '''  function pullCentral(){
    const native=window.AndroidCentral?nativeCentralCall("get",null,30000):null;
    if(native)return native.then(applyCentral);
    return new Promise((resolve,reject)=>{
      const cb="hvssCentralCb_"+Date.now()+Math.random().toString(36).slice(2);
      const script=document.createElement("script");
      const timer=setTimeout(()=>{cleanup();reject(new Error("Timeout mengambil data CENTRAL"))},15000);
      function cleanup(){clearTimeout(timer);try{delete window[cb]}catch(e){}script.remove()}
      window[cb]=data=>{cleanup();try{resolve(applyCentral(data))}catch(e){reject(e)}};
      script.onerror=()=>{cleanup();reject(new Error("Gagal terhubung ke Apps Script CENTRAL"))};
      script.src=C.gasUrl+"?action=getCentral&spreadsheetId="+encodeURIComponent(C.spreadsheetId)+"&callback="+encodeURIComponent(cb)+"&_="+Date.now();
      document.head.appendChild(script);
    });
  }
'''
a = s.find('  function pullCentral(){')
b = s.find('  async function syncNow(reason){', a)
if a < 0 or b < 0:
    raise SystemExit('Could not locate pullCentral/syncNow boundaries')
s = s[:a] + native_pull + s[b:]

native_sync = '''  async function syncNow(reason){
    if(syncing)return {ok:false,busy:true};
    syncing=true;
    try{
      const payload={action:"syncAll",spreadsheetId:C.spreadsheetId,visitorSheet:C.visitorSheet,keySheet:C.keySheet,
        visitors:Array.isArray(window.HVSS_DB?.visitors)?window.HVSS_DB.visitors:[],
        keys:Array.isArray(window.HVSS_DB?.keys)?window.HVSS_DB.keys:[],
        visitorHeaders:window.HVSS_VISITOR_HEADERS,keyHeaders:window.HVSS_KEY_HEADERS,
        clientTime:new Date().toISOString(),reason:reason||"manual"};
      const body=JSON.stringify(payload);
      let sent=false;
      if(window.AndroidCentral){
        const data=await nativeCentralCall("post",body,30000);
        if(!data||!data.ok)throw new Error((data&&data.error)||"Apps Script menolak sync");
        sent=true;
      }else{
        try{
          const r=await fetch(C.gasUrl,{method:"POST",headers:{"Content-Type":"text/plain;charset=utf-8"},body});
          const text=await r.text();let data;
          try{data=JSON.parse(text)}catch(e){throw new Error("Apps Script response bukan JSON")}
          if(!data.ok)throw new Error(data.error||"Apps Script menolak sync");
          sent=true;
        }catch(e){
          if(navigator.sendBeacon)sent=navigator.sendBeacon(C.gasUrl,new Blob([body],{type:"text/plain;charset=utf-8"}));
          if(!sent)throw e;
        }
      }
      const central=await pullCentral();
      return {ok:true,visitorCount:central.visitors.length,keyCount:central.keys.length,message:"CENTRAL VERIFIED"};
    }finally{syncing=false}
  }
'''
a = s.find('  async function syncNow(reason){')
b = s.find('  window.HVSS_CENTRAL_PULL=pullCentral;', a)
if a < 0 or b < 0:
    raise SystemExit('Could not locate syncNow/export boundary')
s = s[:a] + native_sync + s[b:]

native_reset = '''  window.HVSS_RESET_CENTRAL=async function(){
    const body=JSON.stringify({action:"resetCentral",spreadsheetId:C.spreadsheetId,visitorSheet:C.visitorSheet,keySheet:C.keySheet});
    let done=false;
    if(window.AndroidCentral){
      const d=await nativeCentralCall("post",body,30000);
      if(!d||!d.ok)throw new Error((d&&d.error)||"Reset ditolak");
      done=true;
    }else{
      try{
        const r=await fetch(C.gasUrl,{method:"POST",headers:{"Content-Type":"text/plain;charset=utf-8"},body});
        const d=await r.json();
        if(!d.ok)throw new Error(d.error||"Reset ditolak");
        done=true;
      }catch(e){
        if(navigator.sendBeacon)done=navigator.sendBeacon(C.gasUrl,new Blob([body],{type:"text/plain;charset=utf-8"}));
        if(!done)throw e;
      }
    }
    return window.HVSS_RESET_DEVICE_TO_CENTRAL();
  };
'''
a = s.find('  window.HVSS_RESET_CENTRAL=async function(){')
b = s.find('  window.addEventListener("load",()=>setTimeout(async()=>', a)
if a < 0 or b < 0:
    raise SystemExit('Could not locate resetCentral/load boundary')
s = s[:a] + native_reset + s[b:]

# Final invariant: CENTRAL code is outside the main UI IIFE, therefore it must
# never call the local renderAll/renderKeyLog identifiers directly.
apply_start = s.find('  function applyCentral(data){')
pull_start = s.find('  function pullCentral(){', apply_start)
if apply_start < 0 or pull_start < 0:
    raise SystemExit('Final CENTRAL scope verification failed')
central_block = s[apply_start:pull_start]
if re.search(r'(?<![.\w])renderAll\s*\(', central_block):
    raise SystemExit('Unscoped renderAll() remains in CENTRAL apply block')
if re.search(r'(?<![.\w])renderKeyLog\s*\(', central_block):
    raise SystemExit('Unscoped renderKeyLog() remains in CENTRAL apply block')

for marker in (
    'function nativeCentralCall(',
    'window.__HVSS_NATIVE_CENTRAL_RESOLVE=',
    'AndroidCentral.getCentral',
    'AndroidCentral.postCentral',
    'window.HVSS_RENDER_ALL=renderAll;',
    'window.HVSS_RENDER_KEY_LOG=renderKeyLog;',
    'window.HVSS_ADD_BULK_KEY_ROW=addBulkKeyRow;',
    'window.HVSS_RENDER_ALL()'
):
    if marker not in s:
        raise SystemExit(f'Native CENTRAL patch verification failed: {marker}')

p.write_text(s, encoding='utf-8')
print('HVSS2 native CENTRAL transport + UI scope repair applied')
