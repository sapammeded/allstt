#!/usr/bin/env python3
from pathlib import Path
from html import escape
from urllib.parse import quote
import shutil

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "app" / "src" / "main" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

# Every root-level HTML except launcher.html is an application module.
modules = sorted(p for p in ROOT.glob("*.html") if p.name.lower() != "launcher.html")
if not modules:
    raise SystemExit("No root HTML application modules found.")

# Keep the source HTML files untouched. Build-time injection adds only the
# small STT image/runtime hardening layer to the STT asset.
stt_patch = ROOT / "tools" / "stt_runtime_fix.js"
patch_text = stt_patch.read_text(encoding="utf-8") if stt_patch.exists() else ""

for p in modules:
    target = ASSETS / p.name
    text = p.read_text(encoding="utf-8")
    if p.name.lower() == "stt.html" and patch_text:
        marker = "<!-- ALLSTT_BUILD_RUNTIME_FIX_V1 -->"
        if marker not in text:
            injection = f"\n<script id=\"ALLSTT_BUILD_RUNTIME_FIX_V1\">\n{patch_text}\n</script>\n"
            pos = text.lower().rfind("</body>")
            text = text[:pos] + injection + text[pos:] if pos >= 0 else text + injection
    target.write_text(text, encoding="utf-8")

labels = {
    "stt.html": ("🛡️ PATROLISTT • SECURITY PATROL", "Patroli, area, kamera HP, foto, identitas petugas, tanda tangan, penyimpanan dan laporan PDF."),
    "hvss2.html": ("👥 HVSS2", "Visitor Registration, Key Loan, dashboard, history, laporan dan seluruh fitur HVSS2."),
    "vacs.html": ("🚗 VACS", "Vehicle Access Control System beserta seluruh form, data dan fitur VACS."),
}

cards = []
for p in modules:
    title, desc = labels.get(p.name.lower(), (f"📦 {p.stem.upper()}", f"Modul {p.name} dari repository ALLSTT."))
    href = "file:///android_asset/" + quote(p.name)
    cards.append(
        f'<a class="app" href="{escape(href, quote=True)}">'
        f'<h2>{escape(title)}</h2><p>{escape(desc)}</p>'
        f'<span class="badge">BUKA MODUL</span></a>'
    )

launcher = f'''<!DOCTYPE html>
<html lang="id"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>ALLSTT</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;min-height:100vh;font-family:Inter,Segoe UI,system-ui,sans-serif;background:linear-gradient(135deg,#071426,#0b3d91);color:#fff;padding:28px 18px}}main{{max-width:720px;margin:auto}}.brand{{text-align:center;padding:24px 0 30px}}.brand .icon{{font-size:54px}}.brand h1{{margin:8px 0 4px;font-size:34px}}.brand p{{margin:0;opacity:.8}}.apps{{display:grid;gap:16px}}.app{{display:block;text-decoration:none;color:#10203a;background:#fff;border-radius:22px;padding:22px;box-shadow:0 14px 34px rgba(0,0,0,.22);transition:transform .15s}}.app:active{{transform:scale(.98)}}.app h2{{margin:0 0 6px;font-size:22px}}.app p{{margin:0;color:#64748b;line-height:1.45}}.badge{{display:inline-block;margin-top:14px;padding:7px 12px;border-radius:999px;background:#eef4ff;color:#0b3d91;font-weight:800;font-size:12px}}.foot{{text-align:center;opacity:.6;font-size:12px;padding:24px 0}}
</style></head><body><main>
<section class="brand"><div class="icon">🛡️</div><h1>ALLSTT</h1><p>Security Operations & Reporting</p></section>
<section class="apps">{''.join(cards)}</section>
<div class="foot">ALLSTT • Semua modul menggunakan source HTML dari root repository.</div>
</main></body></html>
'''
(ASSETS / "launcher.html").write_text(launcher, encoding="utf-8")
print("Built modules:", ", ".join(p.name for p in modules))
