#!/usr/bin/env python3
from pathlib import Path
from html import escape
from urllib.parse import quote
import os

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'app' / 'src' / 'main' / 'assets'
ASSETS.mkdir(parents=True, exist_ok=True)

# Every root-level HTML except launcher.html is an application module.
modules = sorted(p for p in ROOT.glob('*.html') if p.name.lower() != 'launcher.html')
if not modules:
    raise SystemExit('No root HTML application modules found.')

# Never rewrite uploaded source HTML. The STT image hardening patch is applied
# only to the build copy inside Android assets.
stt_patch = ROOT / 'tools' / 'stt_runtime_fix.js'
patch_text = stt_patch.read_text(encoding='utf-8') if stt_patch.exists() else ''
for p in modules:
    target = ASSETS / p.name
    text = p.read_text(encoding='utf-8')
    if p.name.lower() == 'stt.html' and patch_text and 'ALLSTT_BUILD_RUNTIME_FIX_V1' not in text:
        injection = '\n<script id="ALLSTT_BUILD_RUNTIME_FIX_V1">\n' + patch_text + '\n</script>\n'
        pos = text.lower().rfind('</body>')
        text = text[:pos] + injection + text[pos:] if pos >= 0 else text + injection
    target.write_text(text, encoding='utf-8')

labels = {
    'stt.html': ('🛡️ PATROLISTT • SECURITY PATROL', 'Patroli, area, kamera HP, foto, identitas petugas, tanda tangan, penyimpanan dan laporan PDF.', 'BUKA STT'),
    'hvss2.html': ('👥 HVSS2', 'Visitor Registration, Key Loan, dashboard, history, laporan dan seluruh fitur HVSS2.', 'BUKA HVSS2'),
    'vacs.html': ('🚗 VACS', 'Vehicle Access Control System beserta seluruh form, data dan fitur VACS.', 'BUKA VACS'),
}

cards = []
for p in modules:
    title, desc, button = labels.get(p.name.lower(), (f'📦 {p.stem.upper()}', f'Modul {p.name} dari repository ALLSTT.', f'BUKA {p.stem.upper()}'))
    href = 'file:///android_asset/' + quote(p.name)
    cards.append(
        f'<a class="app" data-module="{escape(p.stem.upper())}" href="{escape(href, quote=True)}">'
        f'<h2>{escape(title)}</h2><p>{escape(desc)}</p>'
        f'<span class="badge">{escape(button)}</span></a>'
    )

# Unified Code.gs deployment URL. Deploy the unified Code.gs supplied with this
# upgrade to this Apps Script project so the existing URL can stay unchanged.
device_url = 'https://script.google.com/macros/s/AKfycbxBmXqb3ZR9atxhDn_m7O0MdPNfpeSbw2ibeSN4bVHzDKbhimucSZ44lllvxjWgf2bhVA/exec'
build_sha = os.environ.get('GITHUB_SHA', '')[:7] or 'local'
app_version = '1.0.' + build_sha

launcher = f'''<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>ALLSTT</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;min-height:100vh;font-family:Inter,Segoe UI,system-ui,sans-serif;background:linear-gradient(135deg,#071426,#0b3d91);color:#fff;padding:28px 18px}}main{{max-width:720px;margin:auto}}.brand{{text-align:center;padding:24px 0 30px}}.brand .icon{{font-size:54px}}.brand h1{{margin:8px 0 4px;font-size:34px}}.brand p{{margin:0;opacity:.8}}.apps{{display:grid;gap:16px}}.app{{display:block;text-decoration:none;color:#10203a;background:#fff;border-radius:22px;padding:22px;box-shadow:0 14px 34px rgba(0,0,0,.22);transition:transform .15s}}.app:active{{transform:scale(.98)}}.app h2{{margin:0 0 6px;font-size:22px}}.app p{{margin:0;color:#64748b;line-height:1.45}}.badge{{display:inline-block;margin-top:14px;padding:7px 12px;border-radius:999px;background:#eef4ff;color:#0b3d91;font-weight:800;font-size:12px}}.foot{{text-align:center;opacity:.6;font-size:12px;padding:24px 0}}#gate{{position:fixed;inset:0;background:rgba(4,13,27,.97);display:flex;align-items:center;justify-content:center;padding:18px;z-index:99999}}#gateCard{{width:min(620px,100%);background:#fff;color:#10203a;border-radius:24px;padding:26px;box-shadow:0 20px 60px rgba(0,0,0,.45);border:4px solid #0b3d91}}#gateCard h2{{margin:0 0 8px;color:#0b3d91;font-size:27px}}#gateCard p{{line-height:1.5;color:#64748b}}.idbox{{background:#eef4ff;border-radius:14px;padding:13px;margin:16px 0;font-family:monospace;font-size:14px;word-break:break-all}}#activationCode{{width:100%;padding:14px;border:2px solid #dbe3ef;border-radius:12px;font-size:16px;box-sizing:border-box}}#activateBtn{{width:100%;margin-top:12px;border:0;border-radius:12px;padding:15px;background:linear-gradient(135deg,#0b3d91,#4f46e5);color:#fff;font-size:16px;font-weight:800}}#gateMsg{{min-height:22px;margin-top:12px;font-weight:700}}#copyIdBtn{{border:0;border-radius:10px;padding:9px 12px;background:#e8eef8;color:#0b3d91;font-weight:800;margin-top:8px}}.hidden{{display:none!important}}
</style>
</head>
<body>
<div id="gate">
  <div id="gateCard">
    <h2>🔐 AKTIVASI ALLSTT</h2>
    <p>Perangkat ini belum terdaftar atau belum diaktifkan oleh administrator.</p>
    <div><b>Installation ID</b></div>
    <div class="idbox" id="installationId">Membuat Installation ID...</div>
    <button id="copyIdBtn" type="button">SALIN INSTALLATION ID</button>
    <p style="margin:16px 0 7px"><b>Kode Aktivasi</b></p>
    <input id="activationCode" type="text" autocomplete="off" placeholder="Masukkan kode dari administrator">
    <button id="activateBtn" type="button">CEK & AKTIVASI</button>
    <div id="gateMsg"></div>
  </div>
</div>
<main id="mainApp" class="hidden">
<section class="brand"><div class="icon">🛡️</div><h1>ALLSTT</h1><p>Security Operations & Reporting</p></section>
<section class="apps">{''.join(cards)}</section>
<div class="foot">ALLSTT • Semua modul menggunakan source HTML asli.<br>Build {escape(app_version)}</div>
</main>
<script>
(function(){{
  const DEVICE_API={device_url!r};
  const APP_VERSION={app_version!r};
  const STORAGE_KEY='ALLSTT_INSTALLATION_ID_V1';
  const $=id=>document.getElementById(id);
  function randomId(){{
    if(window.crypto&&crypto.getRandomValues){{const a=new Uint32Array(5);crypto.getRandomValues(a);return 'STT-'+Array.from(a).map(x=>x.toString(36).toUpperCase().padStart(7,'0')).join('').slice(0,20);}}
    return 'STT-'+Date.now().toString(36).toUpperCase()+Math.random().toString(36).slice(2,12).toUpperCase();
  }}
  function installationId(){{let id=localStorage.getItem(STORAGE_KEY);if(!id){{id=randomId();localStorage.setItem(STORAGE_KEY,id);}}return id;}}
  function deviceInfo(){{
    const ua=navigator.userAgent||'';
    const am=ua.match(/Android\\s([0-9.]+)/i);
    const android=am?'Android '+am[1]:'Android';
    let device='Android Device';
    const dm=ua.match(/Android[^;]*;\\s*([^;)]+?)(?:\\s+Build\\/[^;)]+)?[;)]/i);
    if(dm&&dm[1])device=dm[1].trim();
    return {{device,android}};
  }}
  async function check(code){{
    const id=installationId(), info=deviceInfo();
    const qs=new URLSearchParams({{action:'DEVICE_CHECK',installation_id:id,app:'ALLSTT',device:info.device,android:info.android,app_version:APP_VERSION,activation_code:code||''}});
    const r=await fetch(DEVICE_API+'?'+qs.toString()+'&t='+Date.now(),{{cache:'no-store'}});
    if(!r.ok)throw new Error('HTTP '+r.status);
    return await r.json();
  }}
  function showGate(msg,good){{$('gateMsg').textContent=msg||'';$('gateMsg').style.color=good?'#059669':'#b91c1c';}}
  function openApp(){{$('gate').classList.add('hidden');$('mainApp').classList.remove('hidden');}}
  async function boot(){{
    $('installationId').textContent=installationId();
    try{{
      const j=await check('');
      if(String(j.status||'').toUpperCase()==='ACTIVE'){{openApp();return;}}
      showGate(j.message||'Perangkat menunggu aktivasi administrator.',false);
    }}catch(e){{showGate('CENTRAL tidak dapat dihubungi. Internet diperlukan untuk verifikasi.',false);}}
  }}
  $('activateBtn').onclick=async function(){{
    const code=$('activationCode').value.trim();
    if(!code){{showGate('Masukkan kode aktivasi dari administrator.',false);return;}}
    $('activateBtn').disabled=true;$('activateBtn').textContent='MEMERIKSA...';
    try{{const j=await check(code);if(String(j.status||'').toUpperCase()==='ACTIVE'){{showGate('✅ Perangkat aktif.',true);setTimeout(openApp,350);}}else showGate(j.message||'Aktivasi belum disetujui.',false);}}
    catch(e){{showGate('Gagal terhubung ke CENTRAL. Coba lagi.',false);}}
    finally{{$('activateBtn').disabled=false;$('activateBtn').textContent='CEK & AKTIVASI';}}
  }};
  $('activationCode').addEventListener('keydown',e=>{{if(e.key==='Enter')$('activateBtn').click();}});
  $('copyIdBtn').onclick=async function(){{try{{await navigator.clipboard.writeText($('installationId').textContent);showGate('Installation ID disalin.',true);}}catch(e){{showGate('Salin ID secara manual.',false);}}}};
  // Re-check every 15 minutes. If the owner changes ACTIVE to BLOCKED/REVOKED,
  // the launcher reloads and keeps the suite locked.
  setInterval(async()=>{{try{{const j=await check('');if(String(j.status||'').toUpperCase()!=='ACTIVE')location.reload();}}catch(e){{}}}},900000);
  boot();
}})();
</script>
</body>
</html>
'''
(ASSETS / 'launcher.html').write_text(launcher, encoding='utf-8')
print('Built modules:', ', '.join(p.name for p in modules))
print('Device control:', device_url)
