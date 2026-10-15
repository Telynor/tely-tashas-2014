from pathlib import Path
import json,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'module.json').read_text());out=ROOT/'dist';out.mkdir(exist_ok=True)
target=out/(manifest['id']+'.zip')
files=[ROOT/'module.json',ROOT/'README.md',ROOT/'NOTICE.md']
for folder in ['scripts','packs','assets','docs']:
 files+=sorted(p for p in (ROOT/folder).rglob('*') if p.is_file() and p.name not in ['LOCK','LOG','LOG.old'])
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,p.relative_to(ROOT))
with zipfile.ZipFile(target) as z:
 assert z.testzip() is None
 assert 'module.json' in z.namelist()
 assert len([n for n in z.namelist() if n.startswith('assets/pages/') and n.endswith('.webp')])==194
 for p in manifest['packs']:assert any(n.startswith(p['path']+'/') for n in z.namelist())
(out/'module.json').write_bytes((ROOT/'module.json').read_bytes())
source=out/(manifest['id']+'-source.zip')
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(ROOT.rglob('*')):
  relative=p.relative_to(ROOT)
  if not p.is_file() or any(part in ['.git','node_modules','__pycache__','dist','assets','packs','packs-src','.validation-roundtrip'] for part in relative.parts):continue
  z.write(p,relative)
with zipfile.ZipFile(source) as z:
 assert z.testzip() is None
 assert 'source/inventory.json' in z.namelist()
 assert 'content/creatures.json' in z.namelist()
(out/'SHA256SUMS.txt').write_text('\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name for p in [target,source,out/'module.json'])+'\n')
print(json.dumps({'archive':str(target),'bytes':target.stat().st_size,'files':len(files),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'sourceArchive':str(source),'sourceBytes':source.stat().st_size}))
