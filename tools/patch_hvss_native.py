from pathlib import Path

p = Path("hvss2.html")
s = p.read_text(encoding="utf-8")

old = '''function pullCentral(){
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
  }'''

new = '''function nativeCentralCall(type, payload, timeoutMs=30000){
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
  function pullCentral(){
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
  }'''

assert old in s
s = s.replace(old, new, 1)

old2 = '''      let sent=false;
      try{
        const r=await fetch(C.gasUrl,{method:"POST",headers:{"Content-Type":"text/plain;charset=utf-8"},body});
        const text=await r.text(); let data; try{data=JSON.parse(text)}catch(e){throw new Error("Apps Script response bukan JSON")}
        if(!data.ok)throw new Error(data.error||"Apps Script menolak sync");
        sent=true;
      }catch(e){
        if(navigator.sendBeacon) sent=navigator.sendBeacon(C.gasUrl,new Blob([body],{type:"text/plain;charset=utf-8"}));
        if(!sent) throw e;
      }
      // Central is authoritative: read it back after the write.
      const central=await pullCentral();
      return {ok:true,visitorCount:central.visitors.length,keyCount:central.keys.length,message:"CENTRAL VERIFIED"};'''

new2 = '''      let sent=false;
      if(window.AndroidCentral){
        const data=await nativeCentralCall("post",body,30000);
        if(!data||!data.ok)throw new Error((data&&data.error)||"Apps Script menolak sync");
        sent=true;
      }else{
        try{
          const r=await fetch(C.gasUrl,{method:"POST",headers:{"Content-Type":"text/plain;charset=utf-8"},body});
          const text=await r.text(); let data; try{data=JSON.parse(text)}catch(e){throw new Error("Apps Script response bukan JSON")}
          if(!data.ok)throw new Error(data.error||"Apps Script menolak sync");
          sent=true;
        }catch(e){
          if(navigator.sendBeacon) sent=navigator.sendBeacon(C.gasUrl,new Blob([body],{type:"text/plain;charset=utf-8"}));
          if(!sent) throw e;
        }
      }
      const central=await pullCentral();
      return {ok:true,visitorCount:central.visitors.length,keyCount:central.keys.length,message:"CENTRAL VERIFIED"};'''

assert old2 in s
s = s.replace(old2, new2, 1)

old3 = '''  window.HVSS_RESET_CENTRAL=async function(){
    const body=JSON.stringify({action:"resetCentral",spreadsheetId:C.spreadsheetId,visitorSheet:C.visitorSheet,keySheet:C.keySheet});
    let done=false;
    try{const r=await fetch(C.gasUrl,{method:"POST",headers:{"Content-Type":"text/plain;charset=utf-8"},body});const d=await r.json();if(!d.ok)throw new Error(d.error||"Reset ditolak");done=true}catch(e){if(navigator.sendBeacon)done=navigator.sendBeacon(C.gasUrl,new Blob([body],{type:"text/plain;charset=utf-8"}));if(!done)throw e}
    return window.HVSS_RESET_DEVICE_TO_CENTRAL();
  };'''

new3 = '''  window.HVSS_RESET_CENTRAL=async function(){
    const body=JSON.stringify({action:"resetCentral",spreadsheetId:C.spreadsheetId,visitorSheet:C.visitorSheet,keySheet:C.keySheet});
    let done=false;
    if(window.AndroidCentral){
      const d=await nativeCentralCall("post",body,30000);
      if(!d||!d.ok)throw new Error((d&&d.error)||"Reset ditolak");
      done=true;
    }else{
      try{const r=await fetch(C.gasUrl,{method:"POST",headers:{"Content-Type":"text/plain;charset=utf-8"},body});const d=await r.json();if(!d.ok)throw new Error(d.error||"Reset ditolak");done=true}catch(e){if(navigator.sendBeacon)done=navigator.sendBeacon(C.gasUrl,new Blob([body],{type:"text/plain;charset=utf-8"}));if(!done)throw e}
    }
    return window.HVSS_RESET_DEVICE_TO_CENTRAL();
  };'''

assert old3 in s
s = s.replace(old3, new3, 1)
p.write_text(s, encoding="utf-8")
print("HVSS2 native CENTRAL patch applied")
