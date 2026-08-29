from pathlib import Path
import re

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

DEFAULT_DESC = 'Kegiatan patroli area tersebut telah selesai dilaksanakan dengan hasil situasi terpantau terkendali aman dan kondusif, temuan menonjol serta kendala operasional nihil.'

# Upgrade photo processing: keep substantially more source resolution and JPEG quality.
s = s.replace('function compressDataUrl(dataUrl, quality=0.9, maxSize=1920)', 'function compressDataUrl(dataUrl, quality=0.98, maxSize=4096)')
s = s.replace('const compressed = await compressDataUrl(raw, 0.88, 1200);', 'const compressed = await compressDataUrl(raw, 0.98, 2400);')
s = s.replace('const comp = await compressDataUrl(data,0.9,1920);', 'const comp = await compressDataUrl(data,0.98,4096);')
s = s.replace('const comp=await compressDataUrl(data,0.9,1920);', 'const comp=await compressDataUrl(data,0.98,4096);')
s = s.replace('const re = await compressDataUrl(p, 0.85, 1600);', 'const re = await compressDataUrl(p, 0.98, 4096);')

# Add the requested default patrol description once.
marker = 'const DEFAULT_LOGO_URL = "https://i.ibb.co.com/dJV2bjQR/IMG-20251123-001741.png";'
if 'const DEFAULT_PATROL_DESCRIPTION =' not in s:
    s = s.replace(marker, marker + '\n\nconst DEFAULT_PATROL_DESCRIPTION = ' + repr(DEFAULT_DESC) + ';', 1)

# Empty description fallback: use the requested professional sentence everywhere the
# patrol evidence description is generated or edited.
s = s.replace("area.descriptions.push('TERKENDALI AMAN');", "area.descriptions.push(DEFAULT_PATROL_DESCRIPTION);")
s = s.replace("patrolData[k].descriptions.push('TERKENDALI AMAN');", "patrolData[k].descriptions.push(DEFAULT_PATROL_DESCRIPTION);")
s = s.replace("const currentDesc = a.descriptions[idx] || 'TERKENDALI AMAN';", "const currentDesc = a.descriptions[idx] || DEFAULT_PATROL_DESCRIPTION;")
s = s.replace("a.descriptions[idx] = newDesc === '' ? 'TERKENDALI AMAN' : newDesc;", "a.descriptions[idx] = newDesc === '' ? DEFAULT_PATROL_DESCRIPTION : newDesc;")
s = s.replace("const desc = String(area.descriptions?.[i] || 'TERKENDALI AMAN').trim() || 'TERKENDALI AMAN';", "const desc = String(area.descriptions?.[i] || DEFAULT_PATROL_DESCRIPTION).trim() || DEFAULT_PATROL_DESCRIPTION;")

# Remove telephone and email inputs from the Company / Letterhead tab.
s = re.sub(r'\s*<div class="col">\s*<label class="small">EMAIL PERUSAHAAN</label>\s*<input id="companyEmail".*?</div>\s*', '\n', s, count=1, flags=re.S)
s = re.sub(r'\s*<div class="col">\s*<label class="small">TELEPON / HOTLINE</label>\s*<input id="companyPhone".*?</div>\s*', '\n', s, count=1, flags=re.S)

# Make the letterhead editor cleaner and more premium without changing its features.
if 'ALLSTT premium letterhead editor' not in s:
    premium_css = '''\n<style id="ALLSTT premium letterhead editor">\n#companySection {\n  background: linear-gradient(145deg,#ffffff,#f8fbff);\n  border: 1px solid #dbe5f0;\n  border-left: 6px solid #0b3d91;\n  border-radius: 20px;\n  padding: 24px;\n  box-shadow: 0 10px 28px rgba(15,23,42,.10);\n}\n#companySection > label:first-child {\n  display:block;\n  font-size: 20px;\n  font-weight: 900;\n  letter-spacing: .3px;\n  color:#0b3d91;\n  text-transform: none;\n}\n#companySection .small { line-height:1.55; }\n#companySection input, #companySection textarea { font-size:16px; }\n</style>\n'''
    s = s.replace('</head>', premium_css + '</head>', 1)

# Remove old contact rendering from the PDF cover and replace it with a stronger
# typographic hierarchy: company name, address, and report title use different sizes.
s = s.replace("const contactY = 26 + (addressLines.length * 3.2) + 1.5;\n      pdf.text(`Telp: ${companyPhone || '—'}  |  Email: ${companyEmail || '—'}`,W/2,contactY,{align:'center'});", "const contactY = 26 + (addressLines.length * 3.2) + 2;\n      pdf.setFont('helvetica','bold');\n      pdf.setFontSize(8);\n      pdf.setTextColor(...BLUE);\n      pdf.text('SECURITY PATROL & INCIDENT DOCUMENTATION',W/2,contactY,{align:'center'});")

# Improve the PDF letterhead typography and spacing.
s = s.replace("pdf.setFontSize(13.5);\n      pdf.setTextColor(...BLUE);\n      pdf.text(companyName || 'NAMA PERUSAHAAN',W/2,20,{align:'center'});", "pdf.setFontSize(16);\n      pdf.setTextColor(...BLUE);\n      pdf.text(companyName || 'NAMA PERUSAHAAN',W/2,20,{align:'center'});")
s = s.replace("pdf.setFont('helvetica','normal');\n      pdf.setFontSize(7.5);\n      pdf.setTextColor(...TEXT);", "pdf.setFont('helvetica','normal');\n      pdf.setFontSize(8.5);\n      pdf.setTextColor(...TEXT);", 1)
s = s.replace("pdf.setFont('helvetica','bold');\n      pdf.setFontSize(15.5);\n      pdf.setTextColor(...TEXT);\n      pdf.text('LAPORAN PATROLI SECURITY',W/2,48,{align:'center'});", "pdf.setFont('helvetica','bold');\n      pdf.setFontSize(18);\n      pdf.setTextColor(...TEXT);\n      pdf.text('LAPORAN PATROLI SECURITY',W/2,50,{align:'center'});")

# Filename: Petugas_DD-MM-YYYY_SHIFT.pdf, e.g. Apri_29-08-2026_P8.pdf
old_filename = "const filename = `Laporan_Patroli_${safe(petugas)}_${safe(tanggal)}.pdf`;"
new_filename = """const filenameDate = /^\\d{4}-\\d{2}-\\d{2}$/.test(tanggal)\n        ? tanggal.split('-').reverse().join('-')\n        : safe(tanggal || new Date().toISOString().slice(0,10));\n      const filenameShift = safe((document.getElementById('shift')?.value || shift || '').trim()).replace(/_+/g,'_') || 'SHIFT';\n      const filename = `${safe(petugas || 'Petugas')}_${filenameDate}_${filenameShift}.pdf`;"""
s = s.replace(old_filename, new_filename)

# Keep old saved company contact data harmlessly ignored; no phone/email are displayed
# or required by the new letterhead UI/PDF.
p.write_text(s, encoding='utf-8')
print('STT letterhead, filename and default-description patch applied.')