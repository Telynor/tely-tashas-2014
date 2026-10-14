"""Deterministic 2014 content compiler. Source prose comes from the supplied PDF."""
from pathlib import Path
import json,re,hashlib,html,copy,yaml,sys

ROOT=Path(__file__).resolve().parents[1]
ID='tely-tashas-2014'
MOD=f'modules/{ID}'
INV=json.loads((ROOT/'source/inventory.json').read_text())
PACKS={k:[] for k in ['classes','subclasses','features','feats','spells','magic-items','creatures','tables','reference','handouts','macros']}
def uid(s):return hashlib.sha256((ID+':'+s).encode()).hexdigest()[:16]
def slug(s):return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
def uuid(pack,key):return f'Compendium.{ID}.{pack}.{"Actor" if pack=="creatures" else "Item"}.{uid(key)}'
def source(page):return {'book':'TCE','page':str(page),'custom':"Tasha's Cauldron of Everything (2014)",'rules':'2014','license':''}
def description(text,page):
 paragraphs=''.join(f'<p>{html.escape(t)}</p>' for t in text.split('\n\n') if t.strip())
 return paragraphs+f'<p class="tely-source">TCE, p. {page}. @UUID[Compendium.{ID}.reference.JournalEntry.{uid("page:"+str(page+1))}]{{Original source page}}</p>'
def item(name,typ,key,page,text='',pack='features'):
 d={'_id':uid(key),'name':name,'type':typ,'img':'icons/svg/book.svg','system':{'description':{'value':description(text,page),'chat':''},'source':source(page),'identifier':slug(key),'activities':{},'uses':{'spent':0,'max':'','recovery':[]}},'effects':[],'flags':{ID:{'key':key,'sourcePage':page,'automation':'native'}},'folder':None,'sort':0,'ownership':{'default':0},'_stats':{'systemId':'dnd5e','systemVersion':'5.3.3'}}
 if typ=='feat':d['system'].update(type={'value':'class','subtype':''},requirements='',prerequisites={'level':None},properties=[],advancement={})
 PACKS[pack].append(d);return d
def effect(d,name,changes=(),duration=None,statuses=(),transfer=True,mode='base',flags=None):
 e={'_id':uid(d['_id']+':'+name),'name':name,'img':d['img'],'disabled':False,'transfer':transfer,'type':mode,'changes':[{'key':k,'value':str(v),'mode':m,'priority':20} for k,v,m in changes],'statuses':list(statuses),'duration':duration or {},'flags':flags or {}}
 d['effects'].append(e);return e
def damage(formula,typ,scaling=None):
 m=re.fullmatch(r'(\d+)d(\d+)(?:\s*\+\s*(.*))?',formula)
 return {'number':int(m[1]) if m else None,'denomination':int(m[2]) if m else None,'bonus':m[3] or '' if m else '', 'types':[typ] if typ else [],'custom':{'enabled':not bool(m),'formula':formula if not m else ''},'scaling':scaling or {'mode':'','number':None,'formula':''}}
def activity(d,name,typ='utility',activation='action',cost=1,range=0,units='ft',target='creature',count='1',formula=None,damageType=None,save=None,dc='spellcasting',onSave='none',consume=None,slot=False,duration=0,durationUnits='',concentration=False,flags=None):
 a={'_id':uid(d['_id']+':activity:'+name),'name':name,'type':typ,'activation':{'type':activation,'value':cost,'condition':'','override':True},'consumption':{'targets':consume or [],'spellSlot':slot,'scaling':{'allowed':False,'max':''}},'description':{'chatFlavor':''},'duration':{'value':str(duration) if duration else '','units':durationUnits,'concentration':concentration,'special':'','override':True},'effects':[],'range':{'value':range or None,'units':units,'special':'','override':True},'target':{'template':{'count':'','contiguous':False,'type':'','size':'','width':'','height':'','units':'ft'},'affects':{'count':str(count),'type':target,'choice':False,'special':''},'prompt':True,'override':True},'uses':{'spent':0,'max':'','recovery':[]},'visibility':{'level':{'min':None,'max':None},'requireAttunement':d['type'] in ['equipment','weapon'],'requireIdentification':False,'requireMagic':d['type'] in ['spell','equipment','weapon']},'sort':len(d['system']['activities']),'flags':flags or {}}
 if typ=='attack':a.update(attack={'ability':'spellcasting' if d['type']=='spell' else '','bonus':'','flat':False,'critical':{'threshold':None},'type':{'value':'melee','classification':'spell' if d['type']=='spell' else 'weapon'}},damage={'includeBase':d['type']=='weapon','critical':{'bonus':''},'parts':[damage(formula,damageType)] if formula else []})
 if typ=='save':a.update(save={'ability':[save] if save else [],'dc':{'calculation':dc,'formula':''}},damage={'onSave':onSave,'parts':[damage(formula,damageType)] if formula else []})
 if typ=='damage':a['damage']={'critical':{'allow':False,'bonus':''},'parts':[damage(formula,damageType)] if formula else []}
 if typ=='heal':a['healing']=damage(formula or '0',damageType or 'healing')
 if typ=='utility':a['roll']={'prompt':bool(formula),'visible':False,'name':'','formula':formula or ''}
 if typ=='cast':
  for field in ['activation','duration','range','target']:a[field]['override']=False
 d['system']['activities'][a['_id']]=a;return a
def uses(d,maximum,period='lr',recovery=None):d['system']['uses']={'spent':0,'max':str(maximum),'recovery':[{'period':period,'type':'recoverFormula' if recovery else 'recoverAll','formula':recovery or ''}] if period else []}
def consumeUses(n=1,target=''):return [{'type':'itemUses','target':target,'value':str(n),'scaling':{'mode':'','formula':''}}]
def adv(d,typ,title,level=0,configuration=None):
 a={'_id':uid(d['_id']+':adv:'+title+':'+str(level)),'type':typ,'title':title,'level':level,'configuration':configuration or {},'value':{}}
 d['system'].setdefault('advancement',{})[a['_id']]=a;return a
def grant(d,title,level,items,optional=False,spell=None):return adv(d,'ItemGrant',title,level,{'items':[{'uuid':u,'optional':optional} for u in items],'optional':optional,'spell':spell})
def trait(d,title,level=1,grants=(),choices=(),mode='default',restriction=None):
 a=adv(d,'Trait',title,level,{'mode':mode,'allowReplacements':False,'grants':list(grants),'choices':list(choices)})
 if restriction:a['classRestriction']=restriction
 return a
def asi(d,level,abilities=None,points=2):return adv(d,'AbilityScoreImprovement','Ability Score Improvement',level,{'points':points,'cap':2,'max':20,'fixed':{a:0 for a in ['str','dex','con','int','wis','cha']},'locked':[a for a in ['str','dex','con','int','wis','cha'] if abilities and a not in abilities],'recommendation':None})
def entry(parent,name):return next(e for e in INV if e['parent']==parent and e['name']==name)
def lookup(kind,name):return next(e for e in INV if e['kind']==kind and e['name']==name)
def feature_key(e):return f'{e["kind"]}:{e["parent"]}:{e["name"]}'
FEATURES={}
SRD_INDEX=json.loads((ROOT/'source/srd-spell-index.json').read_text())
EXTERNAL_MISSING=set()
def external_spell(name):
 aliases={"Tasha's Hideous Laughter":'Hideous Laughter',"Otto's Irresistible Dance":'Irresistible Dance',"Nystul's Magic Aura":'Arcanist’s Magic Aura',"Tenser's Floating Disk":'Floating Disk',"Leomund's Tiny Hut":'Tiny Hut',"Mordenkainen's Private Sanctum":'Private Sanctum',"Rary's Telepathic Bond":'Telepathic Bond',"Melf's Acid Arrow":'Acid Arrow',"Otiluke's Resilient Sphere":'Resilient Sphere',"Evard's Black Tentacles":'Black Tentacles'}
 if any(e['kind']=='spell' and e['name']==name for e in INV):return uuid('spells','spell:'+name)
 for candidate in [name,aliases.get(name,''),name.replace('’',"'")]:
  for n,v in SRD_INDEX.items():
   if n.lower().replace('’',"'")==candidate.lower().replace('’',"'"):return v['uuid']
 EXTERNAL_MISSING.add(name);return None
def feature(e):
 key=feature_key(e);d=item(e['name'],'feat',key,e['page'],e['text'])
 d['system']['requirements']=f'{e["parent"]} {e["level"] or ""}'.strip()
 d['system']['identifier']=slug(e['name'])
 d['system']['prerequisites']['level']=e['level']
 d['system']['type']={'value':'class','subtype':'eldritchInvocation' if e['kind']=='invocation' else 'fightingStyle' if e['kind']=='fighting-style' else 'maneuver' if e['kind']=='maneuver' else 'artificerInfusion' if e['kind']=='infusion' else 'pact' if e['name']=='Pact of the Talisman' else ''}
 if e['name']=='Pact of the Talisman':d['system']['prerequisites']['level']=3
 d['flags'][ID].update(parent=e['parent'],classIdentifier=slug(e['class'] or ''),kind=e['kind'])
 FEATURES[(e['parent'],e['name'])]=d;return d
def build_features():
 for e in INV:
  if e['kind'] in ['feature','infusion','maneuver','fighting-style','invocation','metamagic']:feature(e)

def normalize_class(c):
 c.pop('_key',None);c.pop('folder',None);c.pop('_stats',None)
 s=c['system'];a=s.get('advancement',{})
 if isinstance(a,list):s['advancement']={v['_id']:v for v in a}
 for advdata in s.get('advancement',{}).values():
  cfg=advdata.get('configuration',{})
  if advdata['type']=='ItemChoice':
   cfg['pool']=[{'uuid':v} if isinstance(v,str) else v for v in cfg.get('pool',[])]
   cfg.setdefault('restriction',{'type':'','subtype':'','level':'','list':[]})
  spell=cfg.get('spell')
  if spell and 'preparation' in spell:
   prep=spell.pop('preparation');spell['method']='spell' if prep in ['always','prepared'] else prep
   spell['prepared']=2 if prep=='always' else 0
  if advdata['type']=='AbilityScoreImprovement':cfg['max']=20
 if 'hitDice' in s:s['hd']={'denomination':s.pop('hitDice'),'spent':s.pop('hitDiceUsed',0),'additional':''}
 s['source']['rules']='2014';s['source']['license']='CC-BY-4.0'
 return c
def build_classes():
 for p in sorted((ROOT/'source/srd/classes').glob('*.yml')):
  c=normalize_class(yaml.safe_load(p.read_text()));baseid=c['_id'];c['_id']=uid('class:'+c['name']);c['name']+=' (2014 + Tasha Options)'
  c['flags']={ID:{'key':'class:'+p.stem.title(),'baseSRDId':baseid,'automation':'native'}}
  c['system']['description']['value']+='<p>Tasha optional features are offered individually. Replacements require an explicit choice.</p>'
  # Keep the 2014 SRD progression and append only optional grants.
  opts=[e for e in INV if e['kind']=='feature' and e['parent'].lower()==p.stem and e['name'] not in ['Fighting Style Options','Pact Boon Option','Pact of the Talisman']]
  for e in opts:
   grant(c,'Optional: '+e['name'],e['level'] or 1,[uuid('features',feature_key(e))],True)
  PACKS['classes'].append(c)
  if p.stem=='warlock':
   for v in c['system']['advancement'].values():
    if v['type']=='ItemChoice' and v['title']=='Pact Boon':v['configuration']['pool'].append({'uuid':uuid('features',feature_key(entry('Warlock','Pact of the Talisman')))})
    if v['type']=='ItemChoice' and v['title']=='Eldritch Invocations':v['configuration']['pool'] += [{'uuid':uuid('features',feature_key(e))} for e in INV if e['kind']=='invocation']
  if p.stem in ['fighter','paladin','ranger']:
   old=yaml.safe_load((ROOT/'source/srd/classfeatures'/p.stem/(p.stem+'-features')/'fighting-style.yml').read_text())
   d=item('Fighting Style ('+p.stem.title()+', 2014)','feat','core-choice:'+p.stem,41,old['system']['description']['value'])
   d['system']['description']['value']=old['system']['description']['value']+'<p>Includes the optional fighting styles from Tasha’s Cauldron of Everything.</p>'
   d['system']['identifier']='fighting-style';d['system']['source']['license']='CC-BY-4.0'
   base=re.findall(r'@UUID\[([^\]]+)\]',old['system']['description']['value'])
   choices=[uuid('features',feature_key(e)) for e in INV if e['kind']=='fighting-style' and e['class'].lower()==p.stem]
   adv(d,'ItemChoice','Choose One Fighting Style',0,{'choices':{'0':{'count':1,'replacement':False}},'allowDrops':False,'type':'feat','pool':[{'uuid':u} for u in base+choices],'restriction':{'type':'class','subtype':'fightingStyle','level':'','list':[]},'spell':None})
   for v in c['system']['advancement'].values():
    for grant_item in v['configuration'].get('items',[]):
     if grant_item['uuid'].endswith(old['_id']):grant_item['uuid']=uuid('features','core-choice:'+p.stem)
 a=item('Artificer','class','class:Artificer',9,'A 2014 artificer. Intelligence-based half spellcasting begins at level 1. See the original source pages for the full class table.','classes')
 a['system'].update(identifier='artificer',hd={'denomination':'d8','spent':0,'additional':''},levels=1,primaryAbility={'value':['int'],'all':True},properties=[],spellcasting={'progression':'artificer','ability':'int','preparation':{'formula':'max(1, @abilities.int.mod + floor(@classes.artificer.levels / 2))'},'ritual':'prepared'},advancement={})
 adv(a,'HitPoints','Hit Points',0,{})
 adv(a,'Subclass','Artificer Specialist',3,{})
 trait(a,'Saving Throws',1,['saves:con','saves:int'],restriction='primary')
 trait(a,'Armor Training',1,['armor:lgt','armor:med','armor:shl'])
 trait(a,'Weapon Training',1,['weapon:sim'])
 trait(a,'Tools',1,['tool:thief','tool:tinker'],[{'count':1,'pool':['tool:art:*']}])
 trait(a,'Skills',1,[],[{'count':2,'pool':['skills:arc','skills:his','skills:inv','skills:med','skills:nat','skills:prc','skills:slt']}],restriction='primary')
 for l in [4,8,12,16,19]:asi(a,l)
 for e in INV:
  if e['kind']=='feature' and e['parent']=='Artificer' and e['name']!='Ability Score Improvement':grant(a,e['name'],e['level'],[uuid('features',feature_key(e))])
 scale={2:2,6:3,10:4,14:5,18:6}
 adv(a,'ScaleValue','Infused Items',0,{'identifier':'infused-items','type':'number','distance':{'units':''},'scale':{str(k):{'value':v} for k,v in scale.items()}})
 adv(a,'ScaleValue','Infusions Known',0,{'identifier':'infusions-known','type':'number','distance':{'units':''},'scale':{str(k):{'value':v*2} for k,v in scale.items()}})
 pool=[{'uuid':uuid('features',feature_key(e))} for e in INV if e['kind']=='infusion']
 adv(a,'ItemChoice','Infusions',0,{'choices':{'2':{'count':4,'replacement':False},'6':{'count':2,'replacement':False},'10':{'count':2,'replacement':False},'14':{'count':2,'replacement':False},'18':{'count':2,'replacement':False}},'allowDrops':False,'type':'feat','pool':pool,'restriction':{'type':'class','subtype':'artificerInfusion','level':'@classes.artificer.levels','list':[]},'spell':None})
 # Sidekick classes keep their own progression; their hit die is copied from
 # the chosen creature by the sidekick builder rather than assumed universally.
 for name,die,ability,progression in [('Expert','d8','','none'),('Warrior','d8','','none'),('Spellcaster','d8','int','artificer')]:
  e=lookup('sidekick-class',name);d=item(name+' (Sidekick)','class','class:'+name,e['page'],e['text'],'classes')
  d['system'].update(identifier=slug(name),levels=1,hd={'denomination':die,'spent':0,'additional':''},primaryAbility={'value':[],'all':False},properties=[],spellcasting={'progression':progression,'ability':ability,'preparation':{'formula':''}},advancement={})
  d['flags'][ID]['sidekick']=True
  adv(d,'HitPoints','Hit Points',0,{})
  for l in ([4,8,10,12,16,19] if name=='Expert' else [4,8,12,14,16,19] if name=='Warrior' else [4,8,12,16,18]):asi(d,l)
  for f in INV:
   if f['kind']=='feature' and f['parent']==name and f['name']!='Ability Score Improvement':grant(d,f['name'],f['level'] or 1,[uuid('features',feature_key(f))])

def build_subclasses():
 for e in INV:
  if e['kind']!='subclass':continue
  d=item(e['name'],'subclass','subclass:'+e['name'],e['page'],e['text'],'subclasses')
  d['system'].update(classIdentifier=slug(e['class']),identifier=slug(e['name']),advancement={},spellcasting={'progression':'none','ability':'','preparation':{'formula':''}})
  for f in INV:
   if f['kind']=='feature' and f['parent']==e['name']:grant(d,f['name'],f['level'] or 1,[uuid('features',feature_key(f))])

def output():
 def keys(doc,collection,ancestors=(),parents=()):
  doc['_key']='!'+'.'.join((*ancestors,collection))+'!'+'.'.join((*parents,doc['_id']))
  children={'actors':['items','effects'],'items':['effects'],'journal':['pages','categories'],'tables':['results']}.get(collection,[])
  for child in children:
   doc.setdefault(child,[])
   for embedded in doc[child]:keys(embedded,child,(*ancestors,collection),(*parents,doc['_id']))
 for pack,docs in PACKS.items():
  path=ROOT/'packs-src'/pack;path.mkdir(parents=True,exist_ok=True)
  for previous in path.glob('*.json'):previous.unlink()
  collection='actors' if pack=='creatures' else 'tables' if pack=='tables' else 'journal' if pack in ['reference','handouts'] else 'macros' if pack=='macros' else 'items'
  for d in docs:
   keys(d,collection)
   (path/(slug(d['name'])+'-'+d['_id']+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2))
  (ROOT/'content').mkdir(exist_ok=True)
  (ROOT/'content'/f'{pack}.json').write_text(json.dumps(docs,ensure_ascii=False,separators=(',',':')))
 (ROOT/'source/build-counts.json').write_text(json.dumps({k:len(v) for k,v in PACKS.items()},indent=2))
 print(json.dumps({k:len(v) for k,v in PACKS.items()},indent=2))

def main():
 build_features();build_classes();build_subclasses()
 sys.path.insert(0,str(ROOT/'tools'))
 import configure_content
 configure_content.build(sys.modules[__name__])
 output()

if __name__=='__main__':main()
