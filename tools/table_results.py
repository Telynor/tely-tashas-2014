"""Extract only structurally complete OCR tables; original images remain authoritative."""
import re,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def extract():
 tables=json.loads((ROOT/'source/roll-table-inventory.json').read_text())
 lines=json.loads((ROOT/'source/table-lines.json').read_text())
 out={}
 for t in tables:
  rows=[r for r in lines if r['page']==t['pdf_page'] and r['col']==t['col'] and r['y']>t['y']+10]
  stop=next((r['y'] for r in rows if r['heading'] and r['y']>t['y']+20),750)
  rows=[r for r in rows if r['y']<stop]
  labels=[]
  for r in rows:
   s=re.sub(r'\s+','',r['text']).replace('–','-')
   if re.fullmatch(r'\d+(?:-\d+)?',s) and r['x']<min(x['x'] for x in rows)+18:
    vals=[int(v) for v in s.split('-')];lo,hi=vals[0],vals[-1]
    if 1<=lo<=hi<=t['sides']:labels.append((r['y'],lo,hi,r['x']))
  if not labels:continue
  if labels[0][1]==2:labels.insert(0,(t['y']+26,1,1,labels[0][3]))
  covered=[n for _,lo,hi,_ in labels for n in range(lo,hi+1)]
  if covered!=list(range(1,t['sides']+1)):continue
  results=[]
  for i,(y,lo,hi,x) in enumerate(labels):
   end=labels[i+1][0]-3 if i+1<len(labels) else stop
   texts=[r['text'] for r in rows if y-3<=r['y']<end and r['x']>x+12 and not re.match(r'^d\s*\d',r['text'])]
   text=' '.join(texts).replace('\xad ','').replace('\xad','')
   if not text:break
   results.append({'range':[lo,hi],'text':text})
  else:out[t['title']]=results
 return out
if __name__=='__main__':
 data=extract();(ROOT/'source/table-results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));print(json.dumps({'completeTables':len(data),'individualResults':sum(len(v) for v in data.values())}))
