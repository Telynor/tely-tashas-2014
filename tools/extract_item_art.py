"""Extract identified official item illustrations from the user-supplied PDF."""
from pathlib import Path
import argparse,fitz,json,re,hashlib
ROOT=Path(__file__).resolve().parents[1];ID='tely-tashas-2014'
# PDF-page positions and printed captions were checked visually. The shard
# illustration is explicitly captioned Far Realm, Feywild, and Shadowfell.
ART=[
 ('atlas-of-endless-horizons',['Atlas of Endless Horizons'],121,2220,None),
 ('baba-yaga-mortar-pestle',["Baba Yaga's Mortar and Pestle"],122,2235,None),
 ('cauldron-of-rebirth',['Cauldron of Rebirth'],124,2270,None),
 ('crook-of-rao',['Crook of Rao'],124,2271,(265,370,580,768)),
 ('crystalline-chronicle',['Crystalline Chronicle'],125,2286,(265,350,580,770)),
 ('demonomicon-of-iggwilv',['Demonomicon of Iggwilv'],126,2298,None),
 ('devotees-censer',["Devotee's Censer"],127,2318,None),
 ('planar-shards',['Far Realm Shard','Feywild Shard','Shadowfell Shard'],128,2337,None),
 ('fulminating-treatise',['Fulminating Treatise'],129,2354,None),
 ('lubas-tarokka',["Luba's Tarokka of Souls"],131,2387,None),
 ('mighty-servant-of-leuk-o',['Mighty Servant of Leuk-o'],133,2424,(0,0,291,350)),
 ('natures-mantle',["Nature's Mantle"],134,2438,(301,361,580,718)),
 ('teeth-of-dahlver-nar',['Teeth of Dahlver-Nar'],136,2471,None),
]
def main():
 p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);args=p.parse_args();pdf=Path(args.pdf)
 doc=fitz.open(pdf);dest=ROOT/'assets/items';dest.mkdir(parents=True,exist_ok=True);rows=[]
 for slug,names,pdf_page,xref,clip in ART:
  path=dest/(slug+'.jpg')
  if clip:
   # The scanned PDF uses graphic clipping to hide black OCR backing patches.
   # Render the original page graphics rather than exposing those backing
   # rectangles from a raw image. Text operators are omitted in this temporary
   # page copy so the extracted figure has no neighboring rules text.
   isolated=fitz.open();isolated.insert_pdf(doc,from_page=pdf_page-1,to_page=pdf_page-1)
   page=isolated[0]
   for stream in page.get_contents():
    content=isolated.xref_stream(stream)
    isolated.update_stream(stream,re.sub(rb'\bBT\b.*?\bET\b',b'',content,flags=re.S))
   image=page.get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(clip),alpha=False)
   path.write_bytes(image.tobytes('jpeg',jpg_quality=94));isolated.close();method='original-page-graphics'
  else:
   image=doc.extract_image(xref)
   if image['ext']!='jpeg':raise ValueError('Unexpected original image format')
   path.write_bytes(image['image']);method='original-embedded-jpeg'
  rows.append({'items':names,'image':f'modules/{ID}/assets/items/{path.name}','pdfPage':pdf_page,'printedPage':pdf_page-1,'imageXref':xref,'method':method,'clip':clip,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 result={'sourceFilename':pdf.name,'sourceSha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'artworks':rows,'baseItemsIllustrated':sum(len(r['items']) for r in rows),'note':'Official printed item art. The three planar shards share their original grouped illustration; implanted tooth entries use the collection illustration.'}
 (ROOT/'source/item-art.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'docs/official-item-art.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('Official art:',len(rows),'illustrations for',result['baseItemsIllustrated'],'base items')
if __name__=='__main__':main()
