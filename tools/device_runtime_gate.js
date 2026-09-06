(function(){
  'use strict';
  const DEVICE_API='__DEVICE_API__';
  const APP_VERSION='__APP_VERSION__';
  const ID_KEY='ALLSTT_INSTALLATION_ID_V1';
  const STATUS_KEY='STT_DEVICE_ACCESS_STATUS_V1';
  const MODULE=(location.pathname.match(/([^/]+)\.html$/i)||[])[1]||'ALLSTT';
  function id(){let v='';try{v=localStorage.getItem(ID_KEY)||''}catch(e){}if(!v){try{const a=new Uint32Array(5);crypto.getRandomValues(a);v='STT-'+Array.from(a).map(x=>x.toString(36).toUpperCase()).join('').slice(0,20)}catch(e){v='STT-'+Date.now().toString(36).toUpperCase()+Math.random().toString(36).slice(2,10).toUpperCase()}try{localStorage.setItem(ID_KEY,v)}catch(e){}}return v}
  function info(){const ua=navigator.userAgent||'';const am=ua.match(/Android\s([0-9.]+)/i);const dm=ua.match(/Android[^;]*;\s*([^;)]+?)(?:\s+Build\/[^;)]+)?[;)]/i);return {android:am?'Android '+am[1]:'Android',device:(dm&&dm[1]||'Android Device').trim()}}
  function gate(title,msg){let g=document.getElementById('__allstt_runtime_gate');if(!g){g=document.createElement('div');g.id='__allstt_runtime_gate';g.style.cssText='position:fixed;inset:0;z-index:2147483647;background:rgba(3,12,30,.97);display:flex;align-items:center;justify-content:center;padding:20px;box-sizing:border-box;font-family:Inter,Segoe UI,system-ui,sans-serif';g.innerHTML='<div style="width:min(480px,100%);background:#fff;border-radius:22px;padding:25px;color:#172033;box-shadow:0 20px 70px rgba(0,0,0,.45);text-align:center"><div id="__rt_title" style="font-size:23px;font-weight:900;color:#b42318;margin-bottom:10px"></div><div id="__rt_msg" style="color:#475569;line-height:1.55"></div><div id="__rt_id" style="margin-top:14px;background:#f1f5f9;border-radius:11px;padding:10px;font-family:monospace;font-size:12px;word-break:break-all"></div></div>';document.documentElement.appendChild(g)}g.querySelector('#__rt_title').textContent=title;g.querySelector('#__rt_msg').textContent=msg;g.querySelector('#__rt_id').textContent='Installation ID: '+id();document.body.style.pointerEvents='none'}
  function unlock(){const g=document.getElementById('__allstt_runtime_gate');if(g)g.remove();document.body.style.pointerEvents=''}
  async function check(){
    if(!DEVICE_API||DEVICE_API.indexOf('__DEVICE_API__')>=0)return true;
    const x=info(),qs=new URLSearchParams({action:'DEVICE_CHECK',installation_id:id(),app:MODULE||'ALLSTT',device:x.device,android:x.android,app_version:APP_VERSION,activation_code:''});
    const r=await fetch(DEVICE_API+'?'+qs.toString()+'&t='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);const j=await r.json();const st=String(j.status||'').toUpperCase();
    try{localStorage.setItem(STATUS_KEY,st.toLowerCase())}catch(e){}
    if(st==='ACTIVE'){unlock();return true}
    gate(st==='BLOCKED'?'🚫 PERANGKAT DIBLOKIR':'🔒 AKSES BELUM AKTIF',j.message||'Akses aplikasi dikendalikan administrator.');return false;
  }
  function start(){setTimeout(async()=>{try{await check()}catch(e){gate('⚠️ CENTRAL TIDAK TERHUBUNG','Koneksi ke Central diperlukan untuk memverifikasi akses perangkat.')}},250);setInterval(async()=>{try{await check()}catch(e){}},900000)}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
