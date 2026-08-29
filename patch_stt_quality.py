from pathlib import Path

p = Path('stt.html')
s = p.read_text(encoding='utf-8')

DEFAULT_DESC = 'Kegiatan patroli area penjagaan telah selesai dilaksanakan dengan hasil situasi terpantau aman dan kondusif, temuan menonjol serta kendala operasional nihil.'

# Upgrade photo processing: keep substantially more source resolution and JPEG quality.
s = s.replace('function compressDataUrl(dataUrl, quality=0.9, maxSize=1920)', 'function compressDataUrl(dataUrl, quality=0.98, maxSize=4096)')
s = s.replace('const compressed = await compressDataUrl(raw, 0.88, 1200);', 'const compressed = await compressDataUrl(raw, 0.98, 2400);')
s = s.replace('const comp = await compressDataUrl(data,0.9,1920);', 'const comp = await compressDataUrl(data,0.98,4096);')
s = s.replace('const comp=await compressDataUrl(data,0.9,1920);', 'const comp=await compressDataUrl(data,0.98,4096);')
s = s.replace('const re = await compressDataUrl(p, 0.85, 1600);', 'const re = await compressDataUrl(p, 0.98, 4096);')
s = s.replace('const re = await compressDataUrl(p, 0.85, 1600);', 'const re = await compressDataUrl(p, 0.98, 4096);')

# Make the automatic empty-description fallback the requested professional sentence.
s = s.replace("area.descriptions.push('TERKENDALI AMAN');", "area.descriptions.push(DEFAULT_PATROL_DESCRIPTION);")
s = s.replace("patrolData[k].descriptions.push('TERKENDALI AMAN');", "patrolData[k].descriptions.push(DEFAULT_PATROL_DESCRIPTION);")
s = s.replace("const currentDesc = a.descriptions[idx] || 'TERKENDALI AMAN';", "const currentDesc = a.descriptions[idx] || DEFAULT_PATROL_DESCRIPTION;")
s = s.replace("a.descriptions[idx] = newDesc === '' ? 'TERKENDALI AMAN' : newDesc;", "a.descriptions[idx] = newDesc === '' ? DEFAULT_PATROL_DESCRIPTION : newDesc;")

# Add the constant once, immediately after the initial configuration block.
marker = 'const DEFAULT_LOGO_URL = "https://i.ibb.co.com/dJV2bjQR/IMG-20251123-001741.png";'
if 'const DEFAULT_PATROL_DESCRIPTION =' not in s:
    s = s.replace(marker, marker + '\n\nconst DEFAULT_PATROL_DESCRIPTION = ' + repr(DEFAULT_DESC) + ';', 1)

p.write_text(s, encoding='utf-8')
print('STT quality/default-description patch applied.')
