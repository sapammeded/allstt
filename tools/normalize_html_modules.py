#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
groups = {}
for p in ROOT.glob('*.html'):
    if p.name.lower() == 'launcher.html':
        continue
    groups.setdefault(p.name.lower(), []).append(p)
for key, files in sorted(groups.items()):
    if len(files) <= 1:
        continue
    canonical = next((p for p in files if p.name == p.name.lower()), sorted(files, key=lambda p: p.name)[0])
    for p in files:
        if p != canonical:
            print(f'WARNING: ignoring duplicate module {p.name}; using {canonical.name}')
            p.unlink()
print('HTML module normalization complete.')
