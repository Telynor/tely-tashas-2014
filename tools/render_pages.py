"""Preserve every supplied printed page, illustration, table, and handout."""
from pathlib import Path
import fitz,io,json,argparse
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--pdf',type=Path,default=ROOT.parent/'upload'/"D&D 5E - Tasha's Cauldron of Everything.pdf")
pdf=parser.parse_args().pdf
out=ROOT/'assets/pages';out.mkdir(parents=True,exist_ok=True)
doc=fitz.open(pdf)
for n,page in enumerate(doc,1):
 target=out/f'page-{n:03}.webp'
 if target.exists():continue
 pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
 im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
 im.save(target,'WEBP',quality=90,method=4)
print(json.dumps({'pages':len(list(out.glob('*.webp'))),'bytes':sum(p.stat().st_size for p in out.glob('*.webp'))}))
