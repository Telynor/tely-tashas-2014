"""Deterministic themed icons, selected only from upstream-verified image paths."""
from pathlib import Path
import json,re,csv,collections

ROOT=Path(__file__).resolve().parents[1]
CATALOG=json.loads((ROOT/'source/icon-catalog.json').read_text())
PATHS=set(CATALOG['paths'])
ART_SOURCE=json.loads((ROOT/'source/item-art.json').read_text())
OFFICIAL_ART={name:entry['image'] for entry in ART_SOURCE['artworks'] for name in entry['items']}
CREATURE_ART_SOURCE=json.loads((ROOT/'source/creature-art.json').read_text())
CREATURE_ART={name:entry['image'] for entry in CREATURE_ART_SOURCE['artworks'] for name in entry['actors']}
PLACEHOLDER_PREFIXES=('icons/svg/','icons/blank','icons/default')

def pick(*terms):
 matches=[p for p in PATHS if all(t.lower() in p.lower() for t in terms)]
 if not matches:raise ValueError('No verified icon matches '+repr(terms))
 return min(matches,key=lambda p:(len(p),p))

# Each palette image has a recorded reference in the official D&D5e 5.3.3 source.
P={
 'tool':pick('skills/trades/smithing','anvil'), 'cog':pick('commodities/tech/cog','bronze'),
 'armor':pick('equipment/chest/breastplate','steel'), 'shield':pick('magic/defensive/shield-barrier','blue'),
 'sword':pick('weapons/swords/sword-runed'), 'strike':pick('skills/melee/strike-sword','red'),
 'bow':pick('weapons/bows/shortbow'), 'dagger':pick('weapons/daggers/','blue'),
 'fist':pick('magic/lightning/fist-unarmed'), 'hammer':pick('weapons/hammers/hammer-double','glowing'),
 'fire':pick('magic/fire/projectile-fireball','orange'), 'cold':pick('magic/water','ice','blue'),
 'acid':pick('magic/acid/'), 'lightning':pick('magic/lightning/bolt-strike-blue.webp'),
 'thunder':pick('magic/sonic/explosion-shock-sound'), 'force':pick('magic/lightning/orb-ball-purple'),
 'radiant':pick('magic/holy/angel-winged'), 'necrotic':pick('magic/death/skull-energy','purple'),
 'poison':pick('skills/toxins/symbol-poison'), 'psychic':pick('skills/wounds/anatomy-organ-brain'),
 'heal':pick('magic/life/heart-cross-strong-green'), 'heart':pick('magic/life/heart-pink'),
 'potion':pick('consumables/potions/bottle-conical-bubbling'), 'holy':pick('magic/life/ankh-gold'),
 'peace':pick('skills/social/diplomacy-handshake.webp'), 'law':pick('skills/social/trading-injustice'),
 'star':pick('magic/symbols/star-yellow'), 'moon':pick('magic/nature/symbol-moon-stars'),
 'rune':pick('magic/symbols/runes-carved-stone','green'), 'spell':pick('sundries/books/book-open-purple'),
 'quill':pick('tools/scribal/ink-quill'), 'scroll':pick('sundries/scrolls/scroll-yellow'),
 'eye':pick('magic/perception/eye-ringed'), 'focus':pick('magic/perception/orb-crystal'),
 'ghost':pick('creatures/magical/spirit-undead-ghost-purple'),
 'shadow':pick('magic/perception/shadow-stealth-eyes'), 'tentacle':pick('creatures/tentacles/tentacle-eyes'),
 'wolf':pick('creatures/mammals/wolf-shadow'), 'fish':pick('creatures/fish/fish-bluefin'),
 'bird':pick('creatures/birds/raptor-owl-flying'), 'frog':pick('creatures/amphibians/bullfrog'),
 'golem':pick('creatures/magical/construct-golem'), 'iron':pick('creatures/magical/construct-iron'),
 'clay':pick('creatures/magical/construct-stone-earth'), 'spiritfire':pick('creatures/magical/spirit-fire-orange'),
 'fey':pick('creatures/magical/fae-fairy'), 'demon':pick('creatures/unholy/demon-fire-imp'),
 'devil':pick('creatures/unholy/demon-horned-winged'), 'alien':pick('creatures/magical/humanoid-silhouette-aliens'),
 'skeleton':pick('magic/death','skeleton','skull'), 'zombie':pick('magic/death/hand-dirt-undead'),
 'fungus':pick('consumables/mushrooms/mushroom-spotted'), 'leaf':pick('magic/nature/leaf-rune'),
 'insect':pick('commodities/gems/gem-amber-insect'), 'claw':pick('creatures/claws/claw-scaled'),
 'tooth':pick('commodities/bones/tooth'), 'blood':pick('creatures/abilities/fang-tooth-blood'),
 'chest':pick('containers/chest/chest-reinforced-box'), 'cauldron':pick('tools/laboratory/cauldron-filled'),
 'music':pick('skills/trades/music-notes'), 'voice':pick('skills/trades/music-singing'),
 'harp':pick('tools/instruments/harp'), 'drum':pick('tools/instruments/drum'), 'bell':pick('tools/instruments/bell-gold'),
 'gem':pick('commodities/gems/gem-faceted','teal'), 'darkgem':pick('commodities/gems/gem-faceted','black'),
 'amulet':pick('equipment/neck/pendant','blue'), 'ring':pick('equipment/finger/ring-faceted','purple'),
 'mask':pick('equipment/head/mask-plague'), 'cloak':pick('equipment/back/cloak','green'),
 'boots':pick('skills/movement/feet-winged-boots','blue'), 'hand':pick('equipment/hand/gauntlet-armored'),
 'sickle':pick('weapons/sickles/sickle-blue-purple'), 'flail':pick('weapons/maces/flail-ball'),
 'cards':pick('sundries/gaming/playing-cards.webp'), 'map':pick('tools/navigation/map-chart'),
 'compass':pick('tools/navigation/compass-brass'), 'clock':pick('magic/time/clock-spinning'),
 'wind':pick('magic/air/wind-vortex-swirl-blue.webp'), 'water':pick('magic/water','wave'),
 'earth':pick('magic/earth/'), 'levitate':pick('magic/control/debuff-energy-hold-levitate','pink'),
 'portal':pick('magic/movement/portal'), 'luck':pick('magic/control/buff-luck-fortune-green-gold'),
 'crown':pick('magic/control/control-influence-crown-gold'), 'dice':pick('sundries/gaming/dice-runed'),
 'knowledge':pick('skills/trades/academics-investigation'), 'food':pick('consumables/food/soup-broth'),
 'gun':pick('weapons/crossbows/'), 'mirror':pick('sundries/survival/mirror'),
}
CLASS={'artificer':'tool','barbarian':'claw','bard':'music','cleric':'holy','druid':'leaf','fighter':'sword','monk':'fist','paladin':'shield','ranger':'bow','rogue':'dagger','sorcerer':'lightning','warlock':'tentacle','wizard':'spell','expert':'knowledge','warrior':'sword','spellcaster':'spell'}
SUBCLASSES={
 'Alchemist':'potion','Armorer':'armor','Artillerist':'gun','Battle Smith':'tool',
 'Path of the Beast':'wolf','Path of Wild Magic':'luck','College of Creation':'star','College of Eloquence':'voice',
 'Order Domain':'law','Peace Domain':'peace','Twilight Domain':'moon','Circle of Spores':'fungus','Circle of Stars':'star','Circle of Wildfire':'spiritfire',
 'Psi Warrior':'psychic','Rune Knight':'rune','Way of Mercy':'heal','Way of the Astral Self':'fist','Oath of Glory':'radiant','Oath of the Watchers':'eye',
 'Fey Wanderer':'fey','Swarmkeeper':'insect','Phantom':'ghost','Soulknife':'dagger','Aberrant Mind':'alien','Clockwork Soul':'clock',
 'The Fathomless':'tentacle','The Genie':'wind','Bladesinging':'sword','Order of Scribes':'quill',
}
EXACT={
 'Artificer Initiate':'tool','Chef':'food','Crusher':'hammer','Eldritch Adept':'tentacle','Fey Touched':'fey','Fighting Initiate':'sword','Gunner':'gun',
 'Metamagic Adept':'spell','Piercer':'dagger','Poisoner':'poison','Shadow Touched':'shadow','Skill Expert':'knowledge','Slasher':'strike','Telekinetic':'levitate','Telepathic':'psychic',
 'Blade of Disaster':'sword','Booming Blade':'thunder','Dream of the Blue Veil':'portal','Green-Flame Blade':'fire','Intellect Fortress':'psychic',
 'Lightning Lure':'lightning','Mind Sliver':'psychic','Spirit Shroud':'ghost','Summon Aberration':'alien','Summon Beast':'wolf','Summon Celestial':'radiant',
 'Summon Construct':'golem','Summon Elemental':'earth','Summon Fey':'fey','Summon Fiend':'devil','Summon Shadowspawn':'shadow','Summon Undead':'skeleton',
 'Sword Burst':'strike',"Tasha's Caustic Brew":'acid',"Tasha's Mind Whip":'psychic',"Tasha's Otherworldly Guise":'radiant',
 'All-Purpose Tool':'tool','Amulet of the Devout':'amulet','Arcane Grimoire':'spell','Bloodwell Vial':'blood','Moon Sickle':'sickle',"Rhythm-Maker's Drum":'drum',
 'Alchemical Compendium':'potion','Astral Shard':'gem','Astromancy Archive':'focus','Atlas of Endless Horizons':'map',"Baba Yaga's Mortar and Pestle":'cauldron',
 'Barrier Tattoo':'shield','Bell Branch':'bell','Blood Fury Tattoo':'blood','Cauldron of Rebirth':'cauldron','Coiling Grasp Tattoo':'tentacle','Crook of Rao':'holy',
 'Crystalline Chronicle':'gem','Demonomicon of Iggwilv':'devil',"Devotee's Censer":'flail','Duplicitous Manuscript':'spell','Eldritch Claw Tattoo':'claw',
 'Far Realm Shard':'tentacle','Feywild Shard':'fey','Fulminating Treatise':'fire','Ghost Step Tattoo':'ghost','Guardian Emblem':'shield',"Heart Weaver's Primer":'heart',
 "Illuminator's Tattoo":'quill','Libram of Souls and Flesh':'necrotic','Lifewell Tattoo':'heal',"Luba's Tarokka of Souls":'cards','Lyre of Building':'harp',
 'Masquerade Tattoo':'mask','Mighty Servant of Leuk-o':'iron',"Nature's Mantle":'cloak',"Planecaller's Codex":'portal','Prosthetic Limb':'hand',
 'Protective Verses':'shield',"Reveler's Concertina":'music','Shadowfell Brand Tattoo':'shadow','Shadowfell Shard':'darkgem','Spellwrought Tattoo':'rune',
 'Teeth of Dahlver-Nar':'tooth','Potent Poison (Poisoner)':'poison',
 'Steel Defender':'iron','Homunculus Servant':'demon','Dancing Item':'levitate','Wildfire Spirit':'spiritfire','Juvenile Mimic':'chest',
 'Beast of the Land':'wolf','Beast of the Sea':'fish','Beast of the Sky':'bird',
 'Magical Tinkering':'cog','Infuse Item':'gem','The Right Tool for the Job':'tool','Tool Expertise':'tool','Flash of Genius':'knowledge',
 'Experimental Elixir':'potion','Star Map':'star','Steady Aim':'bow','Psychic Blades':'dagger','Spell-Storing Item':'ring',
 'Eldritch Cannon':'gun','Arcane Firearm':'gun','Armor Model':'armor','Armor Modifications':'armor','Perfected Armor':'armor',
 'Psionic Power':'psychic','Rune Carver':'rune',"Giant's Might":'hammer','Great Stature':'hammer','Runic Juggernaut':'hammer',
 'Wild Companion':'wolf','Primal Companion':'wolf','Magic Item Adept':'gem','Magic Item Savant':'gem','Magic Item Master':'gem',
 'Second Wind':'heal','Indomitable':'shield','Evasion':'boots','Cunning Action':'shadow','Expertise':'knowledge','Ability Score Improvement':'knowledge',
 'Helpful':'peace','Inspiring Help':'peace','Reliable Talent':'knowledge','Bonus Proficiencies':'knowledge','Tool Proficiency':'tool',
 'Custom Lineage: Darkvision':'eye','Custom Lineage: Skill':'knowledge',
}
# Ordered rules favor the subject of the feature over its source class.
RULES=[
 (r'spore|fungal|mushroom','fungus'),(r'teleport|plunge|horizon|planar|fey reinforcements','portal'),
 (r'telekin|levitat|animating performance','levitate'),(r'psychic|psionic|telepath|mind|sharp mind|guarded mind','psychic'),
 (r'tooth|teeth','tooth'),(r'claw|rend|beast|bestial|primal knowledge|instinctive|hunt|pounce','claw'),
 (r'ghost|grave|departed|phantom|undying|dead|death|necrotic|souls','ghost'),
 (r'poison|toxic','poison'),(r'caustic|acid|corros','acid'),(r'lightning|thunderbolt','lightning'),(r'thunder|booming|shock wave','thunder'),
 (r'fire|flame|blaz|explosi|burn|inferno','fire'),(r'frost|cold|ice\b','cold'),
 (r'star|cosmic|constellation|astral|twilight|night|moon','star'),(r'cloud|wind|air\b|storm','wind'),(r'ocean|sea\b|water|wave','water'),
 (r'tentacle|grasping|fathom|aberrant','tentacle'),(r'swarm|insect|infest','insect'),(r'fey|glamour|fairy|misty','fey'),
 (r'heal|mercy|reagents|reviv|rebirth|second wind|regener|repair|restore resource','heal'),
 (r'armor|defen|shield|protect|sanctuary|bulwark|bastion|guardian','shield'),
 (r'rune|runic|sigil','rune'),(r'hand of harm|wound|harm\b|blood','blood'),
 (r'boots|leap|flight|fly\b|pounc|stride|step|alacrity|tide|dispersal|movement','boots'),
 (r'bow|arrow|shot|aim\b|ranged','bow'),(r'blade|sword|slas|pierc|weapon|attack|martial|brace|strike|quick toss','strike'),
 (r'unarmed|ki-|astral self|flurry|grappl','fist'),
 (r'divine|holy|bless|glory|harness|rebuke|oath|channel divinity|prayer','holy'),
 (r'bond|peace|balance|bai[t]|coordinated|gift of the protector','peace'),(r'speech|tongue|word|authority|presence|demand','voice'),
 (r'inspir|music|performance|crescendo|song|bardic','music'),
 (r'explor|awareness|perception|sight|blind fighting|watcher|sentinel|vigilant','eye'),
 (r'nature|primal|druidic|leaf|fruit|plant|spring','leaf'),(r'quill|scrib|spellbook|scrivener','quill'),
 (r'metamagic|spells|spellcasting|cantrip|magic|sorcer','spell'),(r'tool|artifice|tinker|infus|trade','tool'),
 (r'knowledge|guidance|genius|expert|proficien|talent|tactical assessment|versatility','knowledge'),
 (r'crown|sovereign|aristocrat','crown'),(r'clock|order|law','cog'),
]

def themed(name,fallback):
 if name in EXACT:return P[EXACT[name]]
 for pattern,key in RULES:
  if re.search(pattern,name,re.I):return P[key]
 return fallback

def choose_document(doc,pack,scope):
 name=doc['name'];m=doc.get('flags',{}).get(scope,{})
 if pack=='creatures':return CREATURE_ART[name]
 art_name='Teeth of Dahlver-Nar' if m.get('tooth') else m.get('baseName',name)
 if art_name in OFFICIAL_ART:return OFFICIAL_ART[art_name]
 if pack=='classes':
  return doc.get('img') if doc.get('img') in PATHS else P[CLASS[doc['system']['identifier']]]
 if pack=='subclasses':return P[SUBCLASSES[name]]
 if pack=='origins':return P[{'str':'hammer','dex':'boots','con':'heart','int':'spell','wis':'eye','cha':'peace'}[doc['system']['identifier'].split('-')[-1]]]
 if name.startswith('Implanted Tooth'):return P['tooth']
 if m.get('baseName')=='Absorbing Tattoo':return P[name.rsplit('(',1)[-1].rstrip(')').lower()]
 if m.get('baseName') in ['Elemental Essence Shard','Outer Essence Shard']:
  return P[{'Air':'wind','Earth':'earth','Fire':'fire','Water':'water','Lawful':'cog','Chaotic':'luck','Good':'holy','Evil':'devil'}[name.rsplit('(',1)[-1].rstrip(')')]]
 if m.get('baseName') in EXACT:return P[EXACT[m['baseName']]]
 if pack=='macros':return P['knowledge' if 'Validate' in name else 'rune' if 'Stored' in name else 'peace' if 'Sidekick' in name else 'scroll']
 parent=m.get('parent','');fallback=P[SUBCLASSES[parent]] if parent in SUBCLASSES else P[CLASS.get(m.get('classIdentifier',''),'spell')]
 if pack=='tables':
  for word,key in [('Academy','spell'),('Ancient Being','alien'),('Aristocrat','crown'),('Syndicate','shadow'),('Guild','tool'),('Military','sword'),('Commanding','sword'),('Religious','holy'),('Sovereign','crown'),('Mirror','mirror'),('Enchanted Spring','water'),('Primal Fruit','leaf'),('Party Origin','compass'),('Offerings','gem')]:
   if word in name:return P[key]
  fallback=P['dice']
 return themed(name,fallback)

def build(packs,scope):
 rows=[];counts=collections.Counter()
 def record(pack,kind,name,path):
  if not path or path.startswith(PLACEHOLDER_PREFIXES):raise ValueError(f'{pack}/{name}: generic or missing icon')
  if path.startswith('modules/'+scope+'/'):
   if not (ROOT/path.removeprefix('modules/'+scope+'/')).is_file():raise ValueError('Missing source image '+path)
  elif path not in PATHS:raise ValueError('Unverified icon '+path)
  rows.append({'pack':pack,'kind':kind,'name':name,'image':path});counts[kind]+=1
 def embedded(item,pack,parent):
  item['img']=themed(item['name'],parent)
  record(pack,'actorItem',item['name'],item['img']);details(item,pack)
 def details(doc,pack):
  for effect in doc.get('effects',[]):
   effect['img']=themed(effect['name'],doc['img']);record(pack,'effect',effect['name'],effect['img'])
  for activity in doc.get('system',{}).get('activities',{}).values():
   activity['img']=themed(activity['name'],doc['img']);record(pack,'activity',activity['name'],activity['img'])
 for pack,docs in packs.items():
  for doc in docs:
   if pack in ['reference','handouts']:
    image=next((p['src'] for p in doc['pages'] if p['type']=='image'),None)
    if not image:
     n={'Character Options':8,'Group Patrons':84,'Magical Miscellany':106,'Dungeon Master’s Tools':140}[doc['name']]
     image=f'modules/{scope}/assets/pages/page-{n:03}.webp'
    doc.setdefault('flags',{}).setdefault(scope,{})['icon']=image
    record(pack,'entry',doc['name'],image)
    continue
   doc['img']=choose_document(doc,pack,scope);record(pack,'entry',doc['name'],doc['img']);details(doc,pack)
   if doc.get('type')=='npc':
    doc['prototypeToken'].setdefault('texture',{})['src']=doc['img'];record(pack,'token',doc['name'],doc['img'])
    for child in doc.get('items',[]):embedded(child,pack,doc['img'])
   for result in doc.get('results',[]):
    result['img']=doc['img'];record(pack,'tableResult',str(result['range']),result['img'])
 (ROOT/'docs').mkdir(exist_ok=True)
 with (ROOT/'docs/icon-audit.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=['pack','kind','name','image'],lineterminator='\n');writer.writeheader();writer.writerows(rows)
 report={'moduleVersion':json.loads((ROOT/'module.json').read_text())['version'],'entries':counts['entry'],'packEntries':{p:len(v) for p,v in packs.items()},'imageFields':dict(counts),'uniqueImages':len({r['image'] for r in rows}),'missingOrGeneric':0,'officialMagicItemBaseArt':len(OFFICIAL_ART),'magicItemEntriesUsingOfficialArt':sum(d['img'] in OFFICIAL_ART.values() for d in packs['magic-items']),'creatureEntriesUsingOfficialArt':sum(d['img']==CREATURE_ART[d['name']] for d in packs['creatures']),'transparentCreatureArtAssets':len(CREATURE_ART_SOURCE['artworks']),'catalogSource':CATALOG['source'],'externalImageDownloadsRequired':False}
 (ROOT/'docs/icon-coverage.json').write_text(json.dumps(report,indent=2)+'\n')
