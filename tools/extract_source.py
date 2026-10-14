"""Inventory the uploaded 2014 source; never obtain book content from the web."""
from pathlib import Path
import fitz, json, re, difflib, hashlib, argparse

ROOT = Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--pdf',type=Path,default=ROOT.parent / 'upload' / "D&D 5E - Tasha's Cauldron of Everything.pdf")
PDF=parser.parse_args().pdf
DATA = ROOT / 'source'
DATA.mkdir(parents=True, exist_ok=True)

CLASSES = ['Artificer','Barbarian','Bard','Cleric','Druid','Fighter','Monk','Paladin','Ranger','Rogue','Sorcerer','Warlock','Wizard']
SUBCLASSES = {
 'Artificer':['Alchemist','Armorer','Artillerist','Battle Smith'],
 'Barbarian':['Path of the Beast','Path of Wild Magic'],
 'Bard':['College of Creation','College of Eloquence'],
 'Cleric':['Order Domain','Peace Domain','Twilight Domain'],
 'Druid':['Circle of Spores','Circle of Stars','Circle of Wildfire'],
 'Fighter':['Psi Warrior','Rune Knight'],
 'Monk':['Way of Mercy','Way of the Astral Self'],
 'Paladin':['Oath of Glory','Oath of the Watchers'],
 'Ranger':['Fey Wanderer','Swarmkeeper'],
 'Rogue':['Phantom','Soulknife'],
 'Sorcerer':['Aberrant Mind','Clockwork Soul'],
 'Warlock':['The Fathomless','The Genie'],
 'Wizard':['Bladesinging','Order of Scribes']}
FEATS = ['Artificer Initiate','Chef','Crusher','Eldritch Adept','Fey Touched','Fighting Initiate','Gunner','Metamagic Adept','Piercer','Poisoner','Shadow Touched','Skill Expert','Slasher','Telekinetic','Telepathic']
SPELLS = ['Blade of Disaster','Booming Blade','Dream of the Blue Veil','Green-Flame Blade','Intellect Fortress','Lightning Lure','Mind Sliver','Spirit Shroud','Summon Aberration','Summon Beast','Summon Celestial','Summon Construct','Summon Elemental','Summon Fey','Summon Fiend','Summon Shadowspawn','Summon Undead','Sword Burst',"Tasha's Caustic Brew","Tasha's Mind Whip","Tasha's Otherworldly Guise"]
ITEMS = ['Absorbing Tattoo','Alchemical Compendium','All-Purpose Tool','Amulet of the Devout','Arcane Grimoire','Astral Shard','Astromancy Archive','Atlas of Endless Horizons',"Baba Yaga's Mortar and Pestle",'Barrier Tattoo','Bell Branch','Blood Fury Tattoo','Bloodwell Vial','Cauldron of Rebirth','Coiling Grasp Tattoo','Crook of Rao','Crystalline Chronicle','Demonomicon of Iggwilv',"Devotee's Censer",'Duplicitous Manuscript','Eldritch Claw Tattoo','Elemental Essence Shard','Far Realm Shard','Feywild Shard','Fulminating Treatise','Ghost Step Tattoo','Guardian Emblem',"Heart Weaver's Primer","Illuminator's Tattoo",'Libram of Souls and Flesh','Lifewell Tattoo',"Luba's Tarokka of Souls",'Lyre of Building','Masquerade Tattoo','Mighty Servant of Leuk-o','Moon Sickle',"Nature's Mantle",'Outer Essence Shard',"Planecaller's Codex",'Prosthetic Limb','Protective Verses',"Reveler's Concertina","Rhythm-Maker's Drum",'Shadowfell Brand Tattoo','Shadowfell Shard','Spellwrought Tattoo','Teeth of Dahlver-Nar']
INFUSIONS = ['Arcane Propulsion Armor','Armor of Magical Strength','Boots of the Winding Path','Enhanced Arcane Focus','Enhanced Defense','Enhanced Weapon','Helm of Awareness','Homunculus Servant','Mind Sharpener','Radiant Weapon','Repeating Shot','Replicate Magic Item','Repulsion Shield','Resistant Armor','Returning Weapon','Spell-Refueling Ring']
MANEUVERS = ['Ambush','Bait and Switch','Brace','Commanding Presence','Grappling Strike','Quick Toss','Tactical Assessment']
STYLES = ['Blind Fighting','Interception','Superior Technique','Thrown Weapon Fighting','Unarmed Fighting','Blessed Warrior','Druidic Warrior']
INVOCATIONS = ['Bond of the Talisman','Eldritch Mind','Far Scribe','Gift of the Protectors','Investment of the Chain Master','Protection of the Talisman','Rebuke of the Talisman','Undying Servitude']
FIXES = {
 'THE RIGHT TOOL FOR THE OB':'The Right Tool for the Job',
 'COLLEGE OF ELO UENCE':'College of Eloquence','UICKENED HEALING':'Quickened Healing',
 'BLADE SINGING':'Bladesinging','BLADE SONG':'Bladesong','BARRIER TATTQO':'Barrier Tattoo',
 'PLANECALLER1S CODEX':"Planecaller's Codex",'MIGHTY SERVANT OF LEUK-0':'Mighty Servant of Leuk-o',
 'DEMOMONICON OF lGGWILV':'Demonomicon of Iggwilv','DEMONOMICON OF lGGWILV':'Demonomicon of Iggwilv',
 'Ps10N1c SPELLS':'Psionic Spells','PsIONIC PowER':'Psionic Power',
 'D READFUL STRIKES':'Dreadful Strikes','FEY WAN DERER MAGIC':'Fey Wanderer Magic',
 'FLURRY OF H EALING AND HARM':'Flurry of Healing and Harm',
 'SOUL BLADES ·':'Soul Blades',"DEATH 'S FRIEND":"Death's Friend",'SPELL- STORING ITEM':'Spell-Storing Item',
 'CANNY (lsT LEVEL)':'Canny (1st Level)','HIT POI NTS':'Hit Points',
 'SPELLCASTING Fo cus':'Spellcasting Focus','ENHANCED ARCANE Focus':'Enhanced Arcane Focus','Qu1cK Toss':'Quick Toss',
}
HEADER_FONTS = {'Fd26932','Fd824526','Fd675632','Fd832082','Fd109300','Fd879453'}
SKIP_FONTS = {'Fd879452','Fd363437'}
def norm(s): return re.sub('[^a-z0-9]','',s.lower())
CANON = {norm(n):n for n in CLASSES+sum(SUBCLASSES.values(),[])+FEATS+SPELLS+ITEMS+INFUSIONS+MANEUVERS+STYLES+INVOCATIONS}
def name(s):
 if s in FIXES: return FIXES[s]
 if norm(s) in CANON: return CANON[norm(s)]
 s=s.title().replace(' Of ',' of ').replace(' The ',' the ').replace(' And ',' and ').replace(' In ',' in ').replace(' To ',' to ')
 s=s.replace("'S", "'s")
 return s
def clean(s):
 s=s.replace('\xad','').replace('\u00a0',' ')
 s=re.sub(r'(?<![A-Za-z0-9])[lI](?=d(?:4|6|8|10|12|20)\b)','1',s)
 s=re.sub(r'd[lI]2\b','d12',s)
 s=s.replace('+l','+1').replace('(+O)','(+0)')
 return re.sub(r'\s+',' ',s).strip()
def prose(rows):
 paragraphs=[]; current=''; previous_hyphen=False
 for r in rows:
  t=clean(r['text'])
  if r['font'] in SKIP_FONTS or r['size']>12: continue
  if t.startswith(('•','*')) or r['heading']:
   if current:paragraphs.append(current)
   current=t
  elif previous_hyphen and t and t[0].islower(): current=current.rstrip('-')+t
  else: current=(' '.join([current,t])).strip()
  previous_hyphen=r['text'].rstrip().endswith(('-', '\xad'))
 if current:paragraphs.append(current)
 return '\n\n'.join(paragraphs)

def main():
 doc=fitz.open(PDF); lines=[]
 for n,page in enumerate(doc,1):
  rows=[]
  for b in page.get_text('dict')['blocks']:
   if b['type']!=0:continue
   for l in b['lines']:
    spans=l['spans'];t=''.join(v['text'] for v in spans).strip(); alpha=[c for c in t if c.isalpha()]
    if not t or l['bbox'][1]>page.rect.height-42:continue
    header=bool(alpha and sum(c.isupper() for c in alpha)/len(alpha)>.7 and len(alpha)>4 and spans[0]['font'] in HEADER_FONTS and spans[0]['size']>=9.2)
    # Four-letter class names, and the OCR's two damaged display headings.
    if spans[0]['size']>=17 and norm(t) in {norm(c) for c in CLASSES}:header=True
    if t in ('CHEF',"TASHA'S OTHERWORLDLY GUISE") and spans[0]['size']>=9:header=True
    if norm(t) in ('quicktoss','qu1cktoss') and n==43:header=True
    rows.append({'page':n,'col':int(l['bbox'][0]>=page.rect.width/2),'x':round(l['bbox'][0],1),'y':round(l['bbox'][1],1),'text':t,'font':spans[0]['font'],'size':round(spans[0]['size'],1),'heading':header})
  rows.sort(key=lambda r:(r['col'],r['y']));lines+=rows
 sections=[];current=None
 for i,r in enumerate(lines):
  if r['heading']:
   current={'name':name(r['text']),'page':r['page'],'col':r['col'],'y':r['y'],'font':r['font'],'rows':[],'index':i};sections.append(current)
  elif current:current['rows'].append(r)
 for j,s in enumerate(sections):
  s['text']=prose(s['rows'])
  # A feature's level is the italic line immediately below its heading.
  lead=' '.join(r['text'] for r in s['rows'][:3])
  match=re.search(r'([1-9lIJ][0-9 ]{0,2})(?:st|nd|rd|th)[-\u00ad ]+level',lead,re.I)
  s['level']=int(match.group(1).replace(' ','').replace('l','1').replace('I','1').replace('J','1')) if match else None
  if s['name']=='Controlled Surge':s['level']=14
  if s['name']=='Implement of Peace':s['level']=1
  if s['name']=="Physician's Touch":s['level']=6
  s['end_page']=s['rows'][-1]['page'] if s['rows'] else s['page']
 inventory=[];clazz='Artificer';parent=clazz;sectionmode='features'
 for s in sections:
  n=s['name'];page=s['page']
  if page>148:continue
  if n in CLASSES and page<80:clazz=n;parent=n;sectionmode='features';continue
  if n.startswith('Optional Class Feature'):parent=clazz;sectionmode='features';continue
  if n in sum(SUBCLASSES.values(),[]) and page<80:
   parent=n;inventory.append({**s,'kind':'subclass','class':clazz,'parent':clazz});continue
  if n=='Artificer Infusions':parent='Artificer';sectionmode='infusions';continue
  if n=='Maneuver Options':parent='Fighter';sectionmode='maneuvers';continue
  if n=='Battle Master Builds':sectionmode='reference';continue
  if n in ('Eldritch Invocation','Eldritch Invocation Options'):sectionmode='invocations';parent='Warlock';continue
  if n in ('Expert','Spellcaster','Warrior') and page>=143:
   clazz=parent=n;inventory.append({**s,'kind':'sidekick-class','class':n,'parent':n});continue
  if 80<=page<=82 and n in FEATS:inventory.append({**s,'kind':'feat','class':None,'parent':None});continue
  if 107<=page<=117 and n in SPELLS:inventory.append({**s,'kind':'spell','class':None,'parent':None});continue
  if 120<=page<=138 and n in ITEMS:inventory.append({**s,'kind':'magic-item','class':None,'parent':None});continue
  if 12<=page<=79 or 144<=page<=148:
   kind=None
   if n in INVOCATIONS:kind='invocation'
   elif n=='Primal Companion':kind='feature';parent='Beast Master';clazz='Ranger'
   elif s['font']!='Fd832082' and s['level'] is not None and ('feature' in ' '.join(r['text'] for r in s['rows'][:3]).lower() or n=='Controlled Surge'):kind='feature'
   elif sectionmode=='infusions' and n in INFUSIONS:kind='infusion'
   elif sectionmode=='maneuvers' and n in MANEUVERS:kind='maneuver'
   elif n in STYLES:kind='fighting-style'
   elif n in ('Seeking Spell','Transmuted Spell'):kind='metamagic'
   elif n=='Pact of the Talisman':kind='feature'
   if kind:inventory.append({**s,'kind':kind,'class':clazz,'parent':parent})
 # Attach structural subheadings to the preceding mechanical entry, e.g. the
 # artificer spellcasting rules, and the three steps of Deft Explorer.
 for e in inventory:
  if e['kind'] not in ('feature','infusion'):continue
  end=next((x['index'] for x in inventory if x['index']>e['index']),10**9)
  structural=[s for s in sections if e['index']<s['index']<end and s['page']<=e['page']+3 and s['font']=='Fd824526' and s['name'] not in CANON.values()]
  if structural:
   e['text']+='\n\n'+'\n\n'.join(s['name']+'\n'+s['text'] for s in structural)
   e['end_page']=max([e['end_page']]+[s['end_page'] for s in structural])
 for e in inventory:
  e['page']=max(0,e['page']-1);e['end_page']=max(e['page'],e['end_page']-1)
  e.pop('rows',None)
 (DATA/'inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2))
 (DATA/'sections.json').write_text(json.dumps([{k:v for k,v in s.items() if k!='rows'} for s in sections],ensure_ascii=False,indent=2))
 (DATA/'book-pages.json').write_text(json.dumps([{'pdf_page':n+1,'printed_page':n,'text':prose([r for r in lines if r['page']==n+1])} for n in range(len(doc))],ensure_ascii=False,indent=2))
 expected={'subclass':sum(SUBCLASSES.values(),[]),'feat':FEATS,'spell':SPELLS,'magic-item':ITEMS,'infusion':INFUSIONS,'maneuver':MANEUVERS,'invocation':INVOCATIONS}
 missing={k:[n for n in names if n not in {e['name'] for e in inventory if e['kind']==k}] for k,names in expected.items()}
 audit={'source_sha256':hashlib.sha256(PDF.read_bytes()).hexdigest(),'pdf_pages':len(doc),'rules':'2014','expected':expected,'counts':{k:sum(e['kind']==k for e in inventory) for k in set(e['kind'] for e in inventory)},'missing':missing}
 (DATA/'extraction-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
 print(json.dumps({k:v for k,v in audit.items() if k not in ('expected','source_sha256')},indent=2))

if __name__=='__main__':main()
