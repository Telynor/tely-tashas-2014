"""Verified stat-block transcription and summon profiles from the supplied PDF."""
import re,copy
CREATURES={}

def build(b):
 def actor(name,kind,size,ac,hp,scores,speed,page,di=(),dr=(),ci=(),dark=60,languages=(),scale=None):
  d={'_id':b.uid('actor:'+name),'name':name,'type':'npc','img':'icons/svg/mystery-man.svg','system':{'abilities':{a:{'value':v,'proficient':0,'bonuses':{'check':'','save':''}} for a,v in zip(['str','dex','con','int','wis','cha'],scores)},'attributes':{'ac':{'calc':'flat','flat':ac,'formula':''},'hp':{'max':hp,'value':hp,'temp':0,'formula':''},'movement':{'walk':0,'fly':0,'swim':0,'climb':0,'burrow':0,'units':'ft','hover':False,**speed},'senses':{'darkvision':dark,'blindsight':0,'tremorsense':0,'truesight':0,'units':'ft'},'prof':2,'spellcasting':''},'details':{'type':{'value':kind,'subtype':'','custom':''},'cr':0,'alignment':'Unaligned','biography':{'value':b.description('A creature from the 2014 sourcebook. Summon it through its linked feature or spell to apply the caster’s statistics.',page),'public':''}},'traits':{'size':size,'di':{'value':list(di),'bypasses':[],'custom':''},'dr':{'value':list(dr),'bypasses':[],'custom':''},'dv':{'value':[],'bypasses':[],'custom':''},'ci':{'value':list(ci),'custom':''},'languages':{'value':list(languages),'custom':'Understands the languages of its summoner.'}},'skills':{}},'items':[],'effects':[],'flags':{b.ID:{'key':'actor:'+name,'sourcePage':page,'automation':'native+script','summonScale':scale or {}}},'prototypeToken':{'name':name,'actorLink':False,'disposition':1,'width':2 if size=='lg' else 3 if size=='huge' else 1,'height':2 if size=='lg' else 3 if size=='huge' else 1,'texture':{'src':'icons/svg/mystery-man.svg'},'sight':{'enabled':True,'range':dark},'bar1':{'attribute':'attributes.hp'}},'ownership':{'default':0}}
  b.PACKS['creatures'].append(d);CREATURES[name]=d;return d
 def f(d,name,text):
  x=b.item(name,'feat','actor:'+d['name']+':'+name,d['flags'][b.ID]['sourcePage'],text)
  b.PACKS['features'].remove(x);x['system']['type']['value']='monster';d['items'].append(x);return x
 def attack(d,name,formula,typ,ranged=False,reach=5,classification='weapon',second=None):
  x=f(d,name,'Use the linked summon activity to set the attack modifier, damage, and save DC.');a=b.activity(x,name,'attack',range=reach,formula=formula,damageType=typ)
  a['attack'].update(ability='none',flat=True,bonus='0',type={'value':'ranged' if ranged else 'melee','classification':classification})
  if second:a['damage']['parts'].append(b.damage(second[0],second[1]))
  x['flags'][b.ID]['summonAttack']=True;return x,a
 def save(d,name,formula,typ,ability='wis',onSave='none',radius=0,activation='action',status=None,dur=None,limited=None):
  x=f(d,name,'Use the source stat block to check trigger, exclusions, and repeat saves.');a=b.activity(x,name,'save',activation=activation,range=radius,target='creature',count='',formula=formula,damageType=typ,save=ability,dc='',onSave=onSave)
  a['save']['dc']['formula']='10'
  if radius:a['target']['template'].update(type='radius',size=str(radius),units='ft')
  if limited:b.uses(x,limited,'day');a['consumption']['targets']=b.consumeUses()
  if status:
   e=b.effect(x,name+' Effect',duration={'seconds':dur or 6},statuses=[status],transfer=False)
   a['effects']=[{'_id':e['_id'],'onSave':False}]
  x['flags'][b.ID]['summonSave']=True;return x,a
 def multi(d):
  x=f(d,'Multiattack',"The spirit makes a number of attacks equal to half the spell's level, rounded down.")
  b.activity(x,'Multiattack',flags={b.ID:{'handler':'multiattack'}})
 def trait(d,name,text,changes=()):
  x=f(d,name,text)
  if changes:b.effect(x,name,changes)
  return x
 def heal(d,name,formula,limit=1,typ='healing',range=5):
  x=f(d,name,name);b.uses(x,limit,'day');a=b.activity(x,name,'heal',range=range,formula=formula,damageType=typ,consume=b.consumeUses());x['flags'][b.ID]['summonHealing']=True;return x,a
 # Class companions.
 d=actor('Steel Defender','construct','med',15,2,[14,12,14,4,10,6],{'walk':40},19,di=['poison'],ci=['charmed','exhaustion','poisoned'],scale={'class':'artificer','hpBase':2,'hpPerLevel':5,'hpAbility':'int','improvedAC':True,'damage':'pb','hitDie':8})
 for ab in ['dex','con']:d['system']['abilities'][ab]['proficient']=1
 d['system']['skills']={'ath':{'value':1,'ability':'str'},'prc':{'value':2,'ability':'wis'}}
 attack(d,'Force-Empowered Rend','1d8','force')
 heal(d,'Repair','2d8',3)
 trait(d,'Vigilant',"The defender can't be surprised.")
 x=f(d,'Deflect Attack','Reaction: impose disadvantage on one attack made within 5 feet against someone other than the defender.');b.activity(x,'Deflect Attack',activation='reaction',range=5,flags={b.ID:{'handler':'source-prompt'}})
 d=actor('Homunculus Servant','construct','tiny',13,1,[4,15,12,10,10,7],{'walk':20,'fly':30},22,di=['poison'],ci=['exhaustion','poisoned'],scale={'class':'artificer','hpBase':1,'hpPerLevel':1,'hpAbility':'int','damage':'pb','hitDie':4})
 d['system']['abilities']['dex']['proficient']=1;d['system']['skills']={'prc':{'value':2,'ability':'wis'},'ste':{'value':1,'ability':'dex'}}
 attack(d,'Force Strike','1d4','force',True,30)
 trait(d,'Evasion','Dexterity saves for half damage instead deal no damage on success and half on failure, unless incapacitated.')
 x=f(d,'Channel Magic','Reaction: deliver your summoner’s touch spell while within 120 feet.');b.activity(x,'Channel Magic',activation='reaction',range=120)
 d=actor('Dancing Item','construct','lg',16,10,[18,14,16,4,10,6],{'walk':30,'fly':30,'hover':True},29,di=['poison','psychic'],ci=['charmed','exhaustion','poisoned','frightened'],scale={'class':'bard','hpBase':10,'hpPerLevel':5,'damage':'pb'})
 attack(d,'Force-Empowered Slam','1d10','force');trait(d,'Immutable Form','Immune to effects that alter its form.')
 x=f(d,'Irrepressible Dance','When a creature starts its turn within 10 feet, increase or decrease its walking speed by 10 feet until that turn ends.');b.activity(x,'Irrepressible Dance',activation='special',range=10)
 d=actor('Wildfire Spirit','elemental','sm',13,5,[10,14,14,13,15,11],{'walk':30,'fly':30,'hover':True},40,di=['fire'],ci=['charmed','frightened','grappled','prone','restrained'],scale={'class':'druid','hpBase':5,'hpPerLevel':5,'damage':'pb'})
 attack(d,'Flame Seed','1d6','fire',True,60)
 x,a=save(d,'Fiery Teleportation','1d6','fire','dex',radius=5);x['flags'][b.ID]['scaleSaveDamage']=True
 x['system']['description']['value']=b.description('Teleport the spirit and chosen willing creatures within 5 feet up to 15 feet. Each creature within 5 feet of the space it left then makes the saving throw.',40)
 for form,size,hp,per,die,scores,speed,name,damageType,formula in [
  ('Land','med',5,5,8,[14,14,15,8,14,11],{'walk':40,'climb':40},'Maul','slashing','1d8 + 2'),
  ('Sea','med',5,5,8,[14,14,15,8,14,11],{'walk':5,'swim':60},'Binding Strike','piercing','1d6 + 2'),
  ('Sky','sm',4,4,6,[6,16,13,8,14,11],{'walk':10,'fly':60},'Shred','slashing','1d4 + 3')]:
  d=actor('Beast of the '+form,'beast',size,13,hp,scores,speed,61,scale={'class':'ranger','hpBase':hp,'hpPerLevel':per,'acPB':True,'damage':'pb','primalBond':True,'hitDie':die})
  x,a=attack(d,name,formula,damageType)
  if form=='Sea':a['damage']['parts'][0]['types']=['piercing','bludgeoning'];x['system']['description']['value']=b.description('On a hit, grapple the target (escape DC equals the summoner’s spell save DC). While it grapples this target, the beast cannot use Binding Strike on another target.',61)
  if form=='Land':save(d,'Charge: Knock Prone',None,None,'str',status='prone');x=f(d,'Charge: Extra Damage','After moving at least 20 feet straight toward the target and hitting it with Maul.');b.activity(x,'Charge Damage','damage',formula='1d6',damageType='slashing',activation='special')
  trait(d,'Primal Bond','Add the summoner’s proficiency bonus to every ability check and saving throw.')
  trait(d,'Amphibious' if form=='Sea' else 'Flyby' if form=='Sky' else 'Charge','See source stat block.')
 # The nine 2014 summon spells, with every printed variant represented.
 for form in ['Beholderkin','Slaad','Star Spawn']:
  d=actor('Aberrant Spirit ('+form+')','aberration','med',15,40,[16,10,15,16,10,6],{'walk':30,**({'fly':30,'hover':True} if form=='Beholderkin' else {})},109,di=['psychic'],languages=['deep'],scale={'spell':4,'hpBase':40,'hpPerSlot':10,'acBase':11,'damage':'level'})
  multi(d)
  attack(d,'Eye Ray' if form=='Beholderkin' else 'Claws' if form=='Slaad' else 'Psychic Slam','1d8 + 3' if form!='Slaad' else '1d10 + 3','slashing' if form=='Slaad' else 'psychic',form=='Beholderkin',150 if form=='Beholderkin' else 5,'weapon' if form=='Slaad' else 'spell')
  if form=='Slaad':d['flags'][b.ID]['regeneration']=5;trait(d,'Regeneration','Regain 5 hit points at the start of each turn, while at least 1 hit point remains.');trait(d,'Claws: Prevent Healing','A hit prevents the target from regaining hit points until the start of this spirit’s next turn.')
  if form=='Star Spawn':save(d,'Whispering Aura','2d6','psychic',radius=5,activation='special')
 for form in ['Air','Land','Water']:
  hp=20 if form=='Air' else 30
  d=actor('Bestial Spirit ('+form+')','beast','sm',13,hp,[18,11,16,4,14,5],{'walk':30,**({'fly':60} if form=='Air' else {'climb':30} if form=='Land' else {'swim':30})},109,scale={'spell':2,'hpBase':hp,'hpPerSlot':5,'acBase':11,'damage':'level'})
  multi(d);attack(d,'Maul','1d8 + 4','piercing');trait(d,'Flyby' if form=='Air' else 'Pack Tactics','See source stat block.')
  if form=='Water':trait(d,'Water Breathing','The spirit can breathe only underwater.')
 for form in ['Avenger','Defender']:
  d=actor('Celestial Spirit ('+form+')','celestial','lg',16+(2 if form=='Defender' else 0),40,[16,14,16,10,14,16],{'walk':30,'fly':40},110,dr=['radiant'],ci=['charmed','frightened'],languages=['celestial'],scale={'spell':5,'hpBase':40,'hpPerSlot':10,'acBase':13 if form=='Defender' else 11,'damage':'level'})
  multi(d);attack(d,'Radiant Bow' if form=='Avenger' else 'Radiant Mace','2d6 + 2' if form=='Avenger' else '1d10 + 3','radiant',form=='Avenger',150 if form=='Avenger' else 5)
  if form=='Avenger':
   x=d['items'][-1];x['type']='weapon';x['system'].update(type={'value':'natural'},range={'value':150,'long':600,'reach':None,'units':'ft'},damage={'base':b.damage('2d6 + 2','radiant')},properties=[],equipped=True,quantity=1,magicalBonus=0)
   for a in x['system']['activities'].values():a['range']['override']=False;a['damage']['includeBase']=False
  heal(d,'Healing Touch','2d8')
  if form=='Defender':x=f(d,'Radiant Mace: Temporary Hit Points','After a hit, the celestial or a creature within 10 feet of the target gains 1d10 temporary hit points.');b.activity(x,'Grant Temporary Hit Points','heal',activation='special',range=10,formula='1d10',damageType='temphp')
 for form in ['Clay','Metal','Stone']:
  d=actor('Construct Spirit ('+form+')','construct','med',17,55,[18,10,18,14,11,5],{'walk':30},111,dr=['poison'],ci=['charmed','exhaustion','frightened','incapacitated','paralyzed','petrified','poisoned'],scale={'spell':4,'hpBase':40,'hpPerSlot':15,'hpReferenceSlot':3,'acBase':13,'damage':'level'})
  multi(d);attack(d,'Slam','1d8 + 4','bludgeoning')
  if form=='Clay':x=f(d,'Berserk Lashing','Reaction to damage: make a slam against a random creature within 5 feet, or move toward a visible enemy if none is in reach.');b.activity(x,'Berserk Lashing',activation='reaction',range=5,flags={b.ID:{'handler':'source-prompt'}})
  if form=='Metal':x=f(d,'Heated Body','A creature touching the construct or hitting it with a melee attack while within 5 feet takes 1d10 fire damage.');b.activity(x,'Heated Body','damage',activation='special',range=5,formula='1d10',damageType='fire')
  if form=='Stone':save(d,'Stony Lethargy',None,None,'wis',radius=10,activation='special')
 for form in ['Air','Earth','Fire','Water']:
  d=actor('Elemental Spirit ('+form+')','elemental','med',15,50,[18,15,17,4,10,16],{'walk':40,**({'fly':40,'hover':True} if form=='Air' else {'burrow':40} if form=='Earth' else {'swim':40} if form=='Water' else {})},111,di=['poison']+(['fire'] if form=='Fire' else []),dr=['lightning','thunder'] if form=='Air' else ['piercing','slashing'] if form=='Earth' else ['acid'] if form=='Water' else [],ci=['exhaustion','paralyzed','petrified','poisoned','unconscious'],languages=['primordial'],scale={'spell':4,'hpBase':50,'hpPerSlot':10,'acBase':11,'damage':'level'})
  multi(d);attack(d,'Slam','1d10 + 4','fire' if form=='Fire' else 'bludgeoning')
  if form!='Earth':trait(d,'Amorphous Form','Pass through a space as narrow as 1 inch without squeezing.')
 for mood in ['Fuming','Mirthful','Tricksy']:
  d=actor('Fey Spirit ('+mood+')','fey','sm',15,30,[13,16,14,14,11,16],{'walk':40},112,ci=['charmed'],languages=['sylvan'],scale={'spell':3,'hpBase':30,'hpPerSlot':10,'acBase':12,'damage':'level'})
  multi(d);attack(d,'Shortsword','1d6 + 3','piercing',second=('1d6','force'))
  x=f(d,'Fey Step','Bonus action: teleport up to 30 feet. Fuming gains advantage on its next attack this turn; Mirthful can charm a nearby creature; Tricksy creates a 5-foot cube of darkness.');b.activity(x,'Fey Step',activation='bonus',range=30,flags={b.ID:{'handler':'source-prompt'}})
  if mood=='Mirthful':save(d,'Fey Step: Charm',None,None,'wis',radius=10,activation='special',status='charmed',dur=60)
 for form in ['Demon','Devil','Yugoloth']:
  hp={'Demon':50,'Devil':40,'Yugoloth':60}[form]
  d=actor('Fiendish Spirit ('+form+')','fiend','lg',18,hp,[13,16,15,10,10,16],{'walk':40,**({'climb':40} if form=='Demon' else {'fly':60} if form=='Devil' else {})},112,di=['poison'],dr=['fire'],ci=['poisoned'],languages=['abyssal','infernal'],scale={'spell':6,'hpBase':hp,'hpPerSlot':15,'acBase':12,'damage':'level'})
  multi(d);attack(d,'Bite' if form=='Demon' else 'Hurl Flame' if form=='Devil' else 'Claws','1d12 + 3' if form=='Demon' else '2d6 + 3' if form=='Devil' else '1d8 + 3','necrotic' if form=='Demon' else 'fire' if form=='Devil' else 'slashing',form=='Devil',150 if form=='Devil' else 5,'spell' if form=='Devil' else 'weapon')
  trait(d,'Magic Resistance','Advantage on saving throws against spells and other magical effects.',[('flags.midi-qol.magicResistance.all',True,5)])
  if form=='Demon':x,a=save(d,'Death Throes','2d10','fire','dex','half',radius=10,activation='special');x['flags'][b.ID]['scaleSaveDamage']=True
  if form=='Devil':trait(d,"Devil's Sight",'Magical darkness does not impede darkvision.')
  if form=='Yugoloth':x=f(d,'Claws: Teleport','After a Claws attack hits or misses, teleport up to 30 feet.');b.activity(x,'Teleport',activation='special',range=30)
 for form in ['Fury','Despair','Fear']:
  d=actor('Shadow Spirit ('+form+')','monstrosity','med',14,35,[13,16,15,4,10,16],{'walk':40},114,dr=['necrotic'],ci=['frightened'],dark=120,scale={'spell':3,'hpBase':35,'hpPerSlot':15,'acBase':11,'damage':'level'})
  multi(d);attack(d,'Chilling Rend','1d12 + 3','cold');save(d,'Dreadful Scream',None,None,'wis',radius=30,status='frightened',dur=60,limited=1)
  if form=='Fury':trait(d,'Terror Frenzy','Advantage on attack rolls against frightened creatures.')
  if form=='Despair':x=f(d,'Weight of Sorrow','Creatures other than the caster starting their turn within 5 feet lose 20 feet of speed until the start of their next turn.');b.activity(x,'Weight of Sorrow',activation='special',range=5)
  if form=='Fear':x=f(d,'Shadow Stealth','Bonus action: Hide in dim light or darkness.');b.activity(x,'Shadow Stealth',activation='bonus')
 for form in ['Ghostly','Putrid','Skeletal']:
  hp=20 if form=='Skeletal' else 30
  d=actor('Undead Spirit ('+form+')','undead','med',14,hp,[12,16,15,4,10,9],{'walk':30,**({'fly':40,'hover':True} if form=='Ghostly' else {})},114,di=['necrotic','poison'],ci=['exhaustion','frightened','paralyzed','poisoned'],scale={'spell':3,'hpBase':hp,'hpPerSlot':10,'acBase':11,'damage':'level'})
  multi(d);attack(d,'Deathly Touch' if form=='Ghostly' else 'Rotting Claw' if form=='Putrid' else 'Grave Bolt','1d8 + 3' if form=='Ghostly' else '1d6 + 3' if form=='Putrid' else '2d4 + 3','slashing' if form=='Putrid' else 'necrotic',form=='Skeletal',150 if form=='Skeletal' else 5,'spell' if form=='Skeletal' else 'weapon')
  if form=='Ghostly':save(d,'Deathly Touch: Frighten',None,None,'wis',activation='special',status='frightened');trait(d,'Incorporeal Passage','Move through creatures and objects as difficult terrain; ending inside an object shunts the spirit and deals 1d10 force damage per 5 feet traveled.')
  if form=='Putrid':save(d,'Festering Aura',None,None,'con',radius=5,activation='special',status='poisoned');save(d,'Rotting Claw: Paralyze Poisoned Target',None,None,'con',activation='special',status='paralyzed')
 # Eldritch cannons are magical objects, represented as NPCs for token controls.
 for form in ['Flamethrower','Force Ballista','Protector']:
  d=actor('Eldritch Cannon ('+form+')','construct','sm',18,0,[10]*6,{'walk':15,'climb':15},18,di=['poison','psychic'],ci=['blinded','charmed','deafened','exhaustion','frightened','grappled','incapacitated','invisible','paralyzed','petrified','poisoned','prone','restrained','stunned','unconscious'],dark=0,scale={'class':'artificer','hpBase':0,'hpPerLevel':5,'cannon':form})
  if form=='Flamethrower':x,a=save(d,'Flamethrower','2d8','fire','dex','half');a['target']['template'].update(type='cone',size='15',units='ft')
  elif form=='Force Ballista':attack(d,'Force Ballista','2d8','force',True,120,'spell')
  else:x,a=heal(d,'Protector','1d8',0,'temphp',10);x['system']['uses']['max']='';a['consumption']['targets']=[]
  for x in d['items']:
   for a in x['system']['activities'].values():a['activation']['type']='special'
  d['system']['details']['biography']['value']=b.description('This is a magical object, not a creature. The artificer activates it with a bonus action. It lasts 1 hour, can move up to 15 feet when activated, and cannot benefit from effects restricted to creatures.',18)
 d=actor('Mighty Servant of Leuk-o','construct','huge',22,310,[30,14,20,1,14,10],{'walk':60},132,di=['acid','bludgeoning','cold','fire','lightning','necrotic','poison','psychic','radiant'],dr=['piercing','slashing'],ci=['blinded','charmed','deafened','exhaustion','frightened','grappled','incapacitated','paralyzed','petrified','poisoned','restrained','stunned','unconscious'],dark=0)
 d['system']['attributes']['hp']['formula']='27d12 + 135';d['system']['attributes']['prof']=7;d['system']['attributes']['senses']['blindsight']=120
 b.effect(d,'Printed Proficiency Bonus',[('system.attributes.prof',7,5)],transfer=False)
 d['system']['abilities']['wis']['proficient']=1;d['system']['abilities']['cha']['proficient']=1;d['system']['skills']['prc']={'value':1,'ability':'wis'}
 for ranged in [False,True]:x,a=attack(d,'Destructive Fist'+(' (Ranged)' if ranged else ' (Melee)'),'4d12 + 10','force',ranged,120 if ranged else 10);a['attack']['bonus']='17'
 x,a=save(d,'Crushing Leap','4d12','bludgeoning','dex','half',status='prone');a['save']['dc']['formula']='25'
 d['flags'][b.ID]['regeneration']=10
 trait(d,'Magic Resistant Construction','Advantage on saves against spells and magic; spell attacks against it have disadvantage.',[('flags.midi-qol.magicResistance.all',True,5),('flags.midi-qol.grants.disadvantage.attack.msak',True,5),('flags.midi-qol.grants.disadvantage.attack.rsak',True,5)])
 for name,text in [('Immutable Existence','Immune to changes of form and planar displacement.'),('Standing Leap','Long jump 50 feet; high jump 25 feet, without a running start.'),('Unusual Nature','No need for air, food, drink, or sleep.'),('Regeneration','Regain 10 hit points at the start of each turn. At 0 hit points, requires 24 hours of repair or lightning damage to function again.')]:trait(d,name,text)
 d=actor('Juvenile Mimic','monstrosity','tiny',11,7,[1,12,13,10,13,10],{'walk':10,'climb':10},167,di=['acid'],ci=['prone'],languages=['common','undercommon'])
 d['system']['details']['type']['subtype']='shapechanger';d['system']['attributes']['hp']['formula']='2d4 + 2';d['system']['skills']['ste']={'value':1,'ability':'dex'}
 d['system']['traits']['languages']['custom']='Telepathy 120 ft.'
 x,a=attack(d,'Bite','1','piercing',second=('1d4','acid'));a['attack']['bonus']='3';x['flags'][b.ID]['summonAttack']=False
 trait(d,'False Appearance','While motionless in object form, indistinguishable from an ordinary object.')
 trait(d,'Spider Climb','Climb difficult surfaces, including ceilings, without an ability check.')
 x=f(d,'Shape-Shift','Change into an object or back into its true amorphous form. Statistics and equipment stay the same; death restores its true form.');b.activity(x,'Shape-Shift')
 # Mark all creature actions' triggers explicitly; do not create automatic
 # forced movement or arbitrary aura targets from descriptive text.
 for d in CREATURES.values():
  if d['name']!='Juvenile Mimic':d['system']['details']['cr']=None
 return CREATURES
