"""Coverage, internal link integrity, object shape, source assets and mechanical regressions."""
from pathlib import Path
import json,re,csv,collections
ROOT=Path(__file__).resolve().parents[1];ID='tely-tashas-2014'
packs={p.stem:json.loads(p.read_text()) for p in sorted((ROOT/'content').glob('*.json'))}
errors=[];checks=0
def check(ok,message):
 global checks
 checks+=1
 if not ok:errors.append(message)
def visit(value):
 if isinstance(value,dict):
  for v in value.values():yield from visit(v)
 elif isinstance(value,list):
  for v in value:yield from visit(v)
 elif isinstance(value,str):yield value
lookup={f'Compendium.{ID}.{pack}.{typ}.{d["_id"]}':d for pack,docs in packs.items() for d in docs for typ in [('Actor' if pack=='creatures' else 'JournalEntry' if pack in ['reference','handouts'] else 'RollTable' if pack=='tables' else 'Macro' if pack=='macros' else 'Item')]}
inventory=json.loads((ROOT/'source/inventory.json').read_text());audit=json.loads((ROOT/'source/extraction-audit.json').read_text())
for kind,pack in [('subclass','subclasses'),('feat','feats'),('spell','spells')]:
 actual={d['name'] for d in packs[pack]};expected=set(audit['expected'][kind]);check(actual==expected,f'{kind}: source coverage differs')
check(set(audit['expected']['magic-item'])<={d['flags'][ID].get('baseName') for d in packs['magic-items']},'Magic-item coverage missing')
for e in inventory:
 if e['kind'] in ['feature','infusion','maneuver','fighting-style','invocation','metamagic']:
  key=f'{e["kind"]}:{e["parent"]}:{e["name"]}';check(any(d['flags'][ID].get('key')==key for d in packs['features']),f'Missing {key}')
activity_types={'attack','save','damage','heal','utility','summon','cast','enchant','check','forward'}
allitems=[]
for pack,docs in packs.items():
 ids=[d['_id'] for d in docs];check(len(ids)==len(set(ids)),f'{pack}: duplicate IDs')
 for d in docs:
  check(bool(re.fullmatch('[A-Za-z0-9]{16}',d['_id'])),f'{d["name"]}: invalid ID')
  for string in visit(d):
   for ref in re.findall(r'Compendium\.tely-tashas-2014\.[\w-]+\.(?:Item|Actor|JournalEntry|Macro|RollTable)\.[A-Za-z0-9]{16}',string):check(ref in lookup,f'{d["name"]}: unresolved {ref}')
   if string.startswith(f'modules/{ID}/assets/'):
    check((ROOT/string.removeprefix(f'modules/{ID}/')).is_file(),f'Missing asset {string}')
  for item in ([d]+d.get('items',[])):
   if item.get('type')=='npc':continue
   if 'system' not in item:continue
   allitems.append((pack,item))
   system=item['system'];name=item['name'];check(system.get('source',{}).get('rules')=='2014',f'{name}: rules edition missing')
   check(isinstance(system.get('activities',{}),dict),f'{name}: activities must be object')
   check(isinstance(system.get('advancement',{}),dict),f'{name}: advancement must be object')
   for key,a in system.get('activities',{}).items():
    check(key==a['_id'] and len(key)==16,f'{name}: invalid activity key');check(a['type'] in activity_types,f'{name}: unknown activity type')
    check(a.get('type')!='cast' or bool(a.get('spell',{}).get('uuid')),f'{name}: cast missing spell')
    for ef in a.get('effects',[]):check(ef['_id'] in {e['_id'] for e in item.get('effects',[])},f'{name}: dangling applied effect')
    for c in a.get('consumption',{}).get('targets',[]):
     check(c['type'] in {'itemUses','activityUses','attribute','spellSlots','hitDice','material'},f'{name}: unknown consumption type')
     if c['type']=='itemUses' and not c.get('target'):check(bool(system.get('uses',{}).get('max')),f'{name}: consuming nonexistent item pool')
     if c['type']=='activityUses':check(bool(a.get('uses',{}).get('max')),f'{name}: consuming nonexistent activity pool')
   for key,a in system.get('advancement',{}).items():check(key==a['_id'] and len(key)==16,f'{name}: invalid advancement key')
check(len(list((ROOT/'assets/pages').glob('page-*.webp')))==194,'Source page count differs')
for d in packs['tables']:
 cover=[i for r in d['results'] for i in range(r['range'][0],r['range'][1]+1)];check(cover==list(range(1,int(d['formula'][2:])+1)),f'{d["name"]}: table gaps or overlap')
def named(pack,name):return next(d for d in packs[pack] if d['name']==name)
def activity(item,name):return next(a for a in item['system']['activities'].values() if a['name']==name)
check(named('creatures','Juvenile Mimic')['system']['attributes']['hp']['max']==7,'Juvenile mimic HP')
servant=named('creatures','Mighty Servant of Leuk-o');check(servant['system']['attributes']['hp']['max']==310,'Servant HP');check(servant['system']['attributes']['ac']['flat']==22,'Servant AC')
blade=activity(named('spells','Blade of Disaster'),'Blade Attack');check(blade['attack']['critical']['threshold']==18,'Blade critical threshold');check(blade['damage']['critical']['bonus']=='4d12','Blade critical damage')
ghost=named('magic-items','Ghost Step Tattoo');check(not any(c['key']=='system.traits.dr.value' for e in ghost['effects'] for c in e['changes']),'Ghost Step must not resist magical attacks')
check(not named('magic-items','Libram of Souls and Flesh')['effects'][0]['changes'],'Semblance must not grant undead immunities')
classes={d['system']['identifier']:d for d in packs['classes']}
for cl in ['fighter','paladin','ranger']:
 granted=[i['uuid'] for a in classes[cl]['system']['advancement'].values() for i in a['configuration'].get('items',[])];wrappers=[lookup[u] for u in granted if u in lookup and lookup[u]['system'].get('identifier')=='fighting-style'];check(len(wrappers)==1,f'{cl}: style choice must be single replacement')
warlock=classes['warlock'];tal=named('features','Pact of the Talisman');url=next(u for u,d in lookup.items() if d is tal)
check(any(url==p['uuid'] for a in warlock['system']['advancement'].values() if a['type']=='ItemChoice' for p in a['configuration'].get('pool',[])),'Talisman missing from pact choice')
for cl,expected in [('expert',[4,8,10,12,16,19]),('warrior',[4,8,12,14,16,19]),('spellcaster',[4,8,12,16,18])]:check(sorted(a['level'] for a in classes[cl]['system']['advancement'].values() if a['type']=='AbilityScoreImprovement')==expected,f'{cl}: ASI progression differs')
(ROOT/'docs').mkdir(exist_ok=True)
rows=[]
for pack,d in allitems:
 handlers=sorted({a.get('flags',{}).get(ID,{}).get('handler') for a in d['system'].get('activities',{}).values()}-{None})
 flags=d.get('flags',{}).get(ID,{})
 rows.append({'pack':pack,'name':d['name'],'source_page':flags.get('sourcePage',d['system'].get('source',{}).get('page','')),'activities':len(d['system'].get('activities',{})),'effects':len(d.get('effects',[])),'advancements':len(d['system'].get('advancement',{})),'handlers':'; '.join(handlers),'gm_adjudication':'yes' if 'source-prompt' in handlers or flags.get('adjudication') else 'see source restrictions','live_tested':'no'})
with (ROOT/'docs/content-audit.csv').open('w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
result={'checks':checks,'failures':errors,'counts':{k:len(v) for k,v in packs.items()},'originalPages':194,'encodedRollTables':sum(d['flags'][ID].get('automation')=='native-roll-table' for d in packs['tables']),'sourceLookupTables':sum(d['flags'][ID].get('automation')=='source-lookup' for d in packs['tables']),'externalSpellDefinitionsRequired':json.loads((ROOT/'source/external-spells-required.json').read_text()),'liveFoundryTested':False,'automationCoverage':'See content-audit.csv; source-prompt activities require GM adjudication.'}
(ROOT/'docs/validation-report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
raise SystemExit(bool(errors))
