"""Advancement choices, spell grants, runes, infusion enchantments, and sidekicks."""
import re
GRANTS={
 'Alchemist':{3:['Healing Word','Ray of Sickness'],5:['Flaming Sphere',"Melf's Acid Arrow"],9:['Gaseous Form','Mass Healing Word'],13:['Blight','Death Ward'],17:['Cloudkill','Raise Dead']},
 'Armorer':{3:['Magic Missile','Thunderwave'],5:['Mirror Image','Shatter'],9:['Hypnotic Pattern','Lightning Bolt'],13:['Fire Shield','Greater Invisibility'],17:['Passwall','Wall of Force']},
 'Artillerist':{3:['Shield','Thunderwave'],5:['Scorching Ray','Shatter'],9:['Fireball','Wind Wall'],13:['Ice Storm','Wall of Fire'],17:['Cone of Cold','Wall of Force']},
 'Battle Smith':{3:['Heroism','Shield'],5:['Branding Smite','Warding Bond'],9:['Aura of Vitality','Conjure Barrage'],13:['Aura of Purity','Fire Shield'],17:['Banishing Smite','Mass Cure Wounds']},
 'Order Domain':{1:['Command','Heroism'],3:['Hold Person','Zone of Truth'],5:['Mass Healing Word','Slow'],7:['Compulsion','Locate Creature'],9:['Commune','Dominate Person']},
 'Peace Domain':{1:['Heroism','Sanctuary'],3:['Aid','Warding Bond'],5:['Beacon of Hope','Sending'],7:['Aura of Purity',"Otiluke's Resilient Sphere"],9:['Greater Restoration',"Rary's Telepathic Bond"]},
 'Twilight Domain':{1:['Faerie Fire','Sleep'],3:['Moonbeam','See Invisibility'],5:['Aura of Vitality',"Leomund's Tiny Hut"],7:['Aura of Life','Greater Invisibility'],9:['Circle of Power','Mislead']},
 'Circle of Spores':{2:['Chill Touch'],3:['Blindness/Deafness','Gentle Repose'],5:['Animate Dead','Gaseous Form'],7:['Blight','Confusion'],9:['Cloudkill','Contagion']},
 'Circle of Wildfire':{2:['Burning Hands','Cure Wounds'],3:['Flaming Sphere','Scorching Ray'],5:['Plant Growth','Revivify'],7:['Aura of Life','Fire Shield'],9:['Flame Strike','Mass Cure Wounds']},
 'Aberrant Mind':{1:['Arms of Hadar','Dissonant Whispers','Mind Sliver'],3:['Calm Emotions','Detect Thoughts'],5:['Hunger of Hadar','Sending'],7:["Evard's Black Tentacles",'Summon Aberration'],9:["Rary's Telepathic Bond",'Telekinesis']},
 'Clockwork Soul':{1:['Alarm','Protection from Evil and Good'],3:['Aid','Lesser Restoration'],5:['Dispel Magic','Protection from Energy'],7:['Freedom of Movement','Summon Construct'],9:['Greater Restoration','Wall of Force']},
 'Fey Wanderer':{3:['Charm Person'],5:['Misty Step'],9:['Dispel Magic'],13:['Dimension Door'],17:['Mislead']},
 'Swarmkeeper':{3:['Faerie Fire','Mage Hand'],5:['Web'],9:['Gaseous Form'],13:['Arcane Eye'],17:['Insect Plague']},
 'Oath of Glory':{3:['Guiding Bolt','Heroism'],5:['Enhance Ability','Magic Weapon'],9:['Haste','Protection from Energy'],13:['Compulsion','Freedom of Movement'],17:['Commune','Flame Strike']},
 'Oath of the Watchers':{3:['Alarm','Detect Magic'],5:['Moonbeam','See Invisibility'],9:['Counterspell','Nondetection'],13:['Aura of Purity','Banishment'],17:['Hold Monster','Scrying']},
}

def build(b):
 subclasses={d['name']:d for d in b.PACKS['subclasses']}
 for parent,levels in GRANTS.items():
  d=subclasses[parent];cl=d['system']['classIdentifier'];ab='int' if cl=='artificer' else 'wis' if cl in ['cleric','druid','ranger'] else 'cha'
  for level,names in levels.items():
   refs=[]
   for name in names:
    u=b.external_spell(name)
    if u:refs.append(u)
    else:d['flags'][b.ID].setdefault('externalGrants',[]).append({'name':name,'level':level,'ability':ab})
   if refs:b.grant(d,'Subclass Spells '+str(level),level,refs,spell={'ability':[ab],'method':'spell','prepared':2,'uses':{'max':'','per':'','requireSlot':False}})
  if parent in ['Aberrant Mind','Clockwork Soul']:d['flags'][b.ID]['spellReplacementRules']='See the original feature for permitted spell schools, lists, and level-up replacement choices.'
 # Expanded warlock lists are available choices, not automatically known spells.
 for parent in ['The Fathomless','The Genie']:
  d=subclasses[parent];d['flags'][b.ID]['expandedSpellListOnly']=True
 # Fighting styles, invocations, and metamagic choices on their owning features.
 for d in b.PACKS['features']:
  name=d['name'];parent=d['flags'][b.ID].get('parent')
  kind=d['flags'][b.ID].get('kind')
  if kind=='metamagic':d['system']['type']['subtype']='metamagic'
  if name=='Fighting Style Options':d['flags'][b.ID]['automation']='reference'
  if kind=='fighting-style':
   if name=='Blind Fighting':b.effect(d,'Blindsight 10 Feet',[('system.attributes.senses.blindsight',10,4)])
   elif name=='Interception':b.activity(d,'Interception',activation='reaction',range=5,formula='1d10 + @prof')
   elif name=='Thrown Weapon Fighting':d['flags'][b.ID]['thrownDamageBonus']=2
   elif name=='Unarmed Fighting':
    a=b.activity(d,'Unarmed Strike','attack',formula='1d6 + @mod',damageType='bludgeoning');a['attack']['ability']='str'
    a=b.activity(d,'Unarmed Strike (No Weapon or Shield)','attack',formula='1d8 + @mod',damageType='bludgeoning');a['attack']['ability']='str'
    b.activity(d,'Grappled Creature Damage','damage',activation='special',formula='1d4',damageType='bludgeoning')
   elif name=='Superior Technique':b.uses(d,1,'sr');b.activity(d,'Superiority Die',activation='special',formula='1d6',consume=b.consumeUses())
   elif name in ['Blessed Warrior','Druidic Warrior']:
    b.adv(d,'ItemChoice','Two Cantrips',0,{'choices':{'0':{'count':2,'replacement':False}},'type':'spell','allowDrops':True,'pool':[],'restriction':{'level':'0','list':['cleric' if name=='Blessed Warrior' else 'druid'],'type':'','subtype':''},'spell':{'ability':['cha' if name=='Blessed Warrior' else 'wis'],'method':'spell','prepared':2,'uses':{'max':'','per':'','requireSlot':False}}})
  if kind=='maneuver':
   b.activity(d,name,activation='reaction' if name=='Brace' else 'bonus' if name in ['Quick Toss','Grappling Strike'] else 'special',consume=b.consumeUses(1,'combat-superiority'),flags={b.ID:{'handler':'source-prompt','note':'Use the actor’s superiority die and check the maneuver’s triggering attack or check.'}})
  if kind=='invocation':
   if name=='Eldritch Mind':b.effect(d,'Advantage on Concentration Saves',[('system.attributes.concentration.roll.mode',1,5)])
   elif name=='Undying Servitude':
    b.uses(d,1,'lr');ref=b.external_spell('Animate Dead');a=b.activity(d,'Animate Dead','cast',consume=b.consumeUses());a['spell']={'uuid':ref,'ability':'cha','level':3,'properties':[],'challenge':{'attack':None,'save':None,'override':False},'spellbook':True}
   else:b.activity(d,name,activation='reaction' if name=='Rebuke of the Talisman' else 'special',flags={b.ID:{'handler':'source-prompt'}})
 # Artificer cantrip learning follows the printed 2 / 3 / 4 progression.
 talisman=b.FEATURES[('Warlock','Pact of the Talisman')];b.uses(talisman,'@prof','lr');b.activity(talisman,'Aid a Failed Ability Check',activation='special',formula='1d4',consume=b.consumeUses())
 art=next(d for d in b.PACKS['classes'] if d['system']['identifier']=='artificer')
 b.adv(art,'ItemChoice','Artificer Cantrips',0,{'choices':{'1':{'count':2,'replacement':False},'10':{'count':1,'replacement':False},'14':{'count':1,'replacement':False}},'allowDrops':True,'type':'spell','pool':[],'restriction':{'level':'0','list':['artificer'],'type':'','subtype':''},'spell':{'ability':['int'],'method':'spell','prepared':2,'uses':{'max':'','per':'','requireSlot':False}}})
 # Six runes, each independently tracked. Master of Runes allows two uses of
 # each rune between short/long rests from fighter level 15.
 carver=b.FEATURES[('Rune Knight','Rune Carver')]
 text=next(e['text'] for e in b.INV if e['parent']=='Rune Knight' and e['name']=='Rune Carver')
 rune_pool=[]
 for name,level in [('Cloud Rune',3),('Fire Rune',3),('Frost Rune',3),('Stone Rune',3),('Hill Rune',7),('Storm Rune',7)]:
  m=re.search(re.escape(name)+r'\.(.*?)(?=(?:Cloud|Fire|Frost|Stone|Hill|Storm) Rune\.|$)',text,re.S)
  d=b.item(name,'feat','rune:'+name,44,m.group(0) if m else 'See the complete Rune Carver source entry.')
  d['system']['type']={'value':'class','subtype':'rune'};d['system']['requirements']='Rune Knight '+str(level);d['system']['prerequisites']['level']=level;b.uses(d,'1 + floor(@classes.fighter.levels / 15)','sr');rune_pool.append({'uuid':b.uuid('features','rune:'+name)})
  if name=='Cloud Rune':b.effect(d,'Cloud Rune Skill Advantage',[(f'flags.midi-qol.advantage.skill.{s}',True,5) for s in ['slt','dec']]);b.activity(d,'Redirect an Attack',activation='reaction',range=30,consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt'}})
  elif name=='Fire Rune':
   b.effect(d,'Fire Rune Tool Expertise',[('flags.dnd5e.toolExpertise',True,5)])
   b.activity(d,'Fire Rune Extra Damage','damage',activation='special',formula='2d6',damageType='fire',consume=b.consumeUses())
   a=b.activity(d,'Fiery Shackles','save',activation='special',save='str',dc='con');ef=b.effect(d,'Fiery Shackles',duration={'seconds':60},statuses=['restrained'],transfer=False,flags={b.ID:{'dot':{'formula':'2d6','type':'fire'},'repeatSave':{'ability':'str','timing':'end'}}});a['effects']=[{'_id':ef['_id'],'onSave':False}]
  elif name=='Frost Rune':b.effect(d,'Frost Rune Skill Advantage',[(f'flags.midi-qol.advantage.skill.{s}',True,5) for s in ['ani','itm']]);a=b.activity(d,'Invoke Frost Rune',activation='bonus',consume=b.consumeUses());ef=b.effect(d,'Frost Rune Invoked',[(f'system.abilities.{ab}.bonuses.{kind}',2,2) for ab in ['str','con'] for kind in ['check','save']],duration={'seconds':600},transfer=False);a['effects']=[{'_id':ef['_id']}]
  elif name=='Stone Rune':b.effect(d,'Stone Rune Gifts',[('flags.midi-qol.advantage.skill.ins',True,5),('system.attributes.senses.darkvision',120,4)]);a=b.activity(d,'Stone Rune Charm','save',activation='reaction',range=30,save='wis',dc='con',consume=b.consumeUses());ef=b.effect(d,'Stone Rune Dream',duration={'seconds':60},statuses=['charmed','incapacitated'],transfer=False);a['effects']=[{'_id':ef['_id'],'onSave':False}]
  elif name=='Hill Rune':b.effect(d,'Hill Rune Poison Resistance',[('system.traits.dr.value','poison',2)]);a=b.activity(d,'Invoke Hill Rune',activation='bonus',consume=b.consumeUses());ef=b.effect(d,'Hill Rune Invoked',[(f'system.traits.dr.value',t,2) for t in ['bludgeoning','piercing','slashing']],duration={'seconds':60},transfer=False);a['effects']=[{'_id':ef['_id']}]
  else:b.effect(d,'Storm Rune Arcana Advantage',[('flags.midi-qol.advantage.skill.arc',True,5)]);b.activity(d,'Invoke Storm Rune',activation='bonus',consume=b.consumeUses(),duration=1,durationUnits='minute');b.activity(d,'Storm Rune: Alter Roll',activation='reaction',range=60,flags={b.ID:{'handler':'source-prompt','note':'While invoked, choose advantage or disadvantage for the triggering attack, check, or save.'}})
 b.adv(carver,'ItemChoice','Runes Known',0,{'choices':{'3':{'count':2,'replacement':False},'7':{'count':1,'replacement':False},'10':{'count':1,'replacement':False},'15':{'count':1,'replacement':False}},'type':'feat','allowDrops':False,'pool':rune_pool,'restriction':{'type':'class','subtype':'rune','level':'@classes.fighter.levels','list':[]},'spell':None})
 # Infusions use Enchant activities for ordinary numerical item modifications.
 for d in b.PACKS['features'][:]:
  if d['flags'][b.ID].get('kind')!='infusion':continue
  n=d['name'];d['flags'][b.ID]['infusion']=True
  if n in ['Enhanced Weapon','Enhanced Defense','Enhanced Arcane Focus','Repeating Shot','Returning Weapon','Radiant Weapon','Repulsion Shield']:
   for bonus in ([1,2] if n.startswith('Enhanced') else [1]):
    a=b.activity(d,f'Infuse (+{bonus})','enchant',activation='special',target='object')
    a.update(enchant={'self':False},restrictions={'type':'weapon' if n in ['Enhanced Weapon','Repeating Shot','Returning Weapon','Radiant Weapon'] else 'equipment','allowMagical':False,'categories':[],'properties':[]})
    if n.startswith('Enhanced'):
     a['visibility']['identifier']='artificer';a['visibility']['level']={'min':10 if bonus==2 else 2,'max':9 if bonus==1 else None}
    key='system.armor.magicalBonus' if n in ['Enhanced Defense','Repulsion Shield'] else 'flags.'+b.ID+'.focusAttackBonus' if n=='Enhanced Arcane Focus' else 'system.magicalBonus'
    ef=b.effect(d,n+f' (+{bonus})',[(key,bonus,2)],transfer=False,mode='enchantment')
    if n in ['Radiant Weapon','Repeating Shot','Enhanced Arcane Focus','Repulsion Shield']:ef['changes'].append({'key':'system.attunement','mode':5,'value':'required','priority':20})
    d['flags'][b.ID]['automation']='hybrid'
    d['flags'][b.ID]['adjudication']='Enchant applies the numerical bonus. Check the printed item restrictions, attunement, half cover, ammunition, return, and charge riders on the original page.'
    a['effects']=[{'_id':ef['_id'],'level':{'min':None,'max':None},'riders':{'activity':[],'effect':[],'item':[]}}]
  elif n=='Spell-Refueling Ring':b.uses(d,1,'dawn');b.activity(d,'Refuel Spell Slot',consume=b.consumeUses(),flags={b.ID:{'handler':'restore-slot','maximum':'3'}})
  elif n=='Mind Sharpener':b.uses(d,4,'dawn','1d4');b.activity(d,'Succeed on Failed Concentration Save',activation='reaction',consume=b.consumeUses())
  elif n=='Armor of Magical Strength':b.uses(d,6,'dawn','1d6');b.activity(d,'Spend Charge',activation='special',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'Add Intelligence to a Strength check/save, or use a reaction to avoid being knocked prone.'}})
  elif n=='Boots of the Winding Path':b.activity(d,'Teleport to Previously Occupied Space',activation='bonus',range=15,flags={b.ID:{'handler':'source-prompt','note':'Destination must be visible and must have been occupied by you during this turn.'}})
  elif n=='Helm of Awareness':b.effect(d,'Advantage on Initiative',[('system.attributes.init.roll.mode',1,5)])
  elif n=='Resistant Armor':b.activity(d,'Choose Infused Resistance',activation='special',flags={b.ID:{'handler':'choose-resistance'}})
  elif n=='Arcane Propulsion Armor':b.activity(d,'Force Gauntlet','attack',formula='1d8 + @mod',damageType='force',range=20)['attack']['ability']='str'
 # Sidekick features and scale values retain the printed progression.
 for parent,skillcount,saves,armor in [('Expert',5,['dex','int','cha'],['armor:lgt']),('Warrior',2,['str','dex','con'],['armor:lgt','armor:med','armor:hvy']),('Spellcaster',2,['int','wis','cha'],['armor:lgt'])]:
  d=b.FEATURES[(parent,'Bonus Proficiencies')]
  b.trait(d,'Saving Throw',0,choices=[{'count':1,'pool':['saves:'+s for s in saves]}]);b.trait(d,'Armor',0,armor)
  skillpool=['skills:*'] if parent=='Expert' else ['skills:'+s for s in (['acr','ani','ath','itm','nat','prc','sur'] if parent=='Warrior' else ['arc','his','ins','inv','med','prf','per','rel'])]
  b.trait(d,'Skills',0,choices=[{'count':skillcount,'pool':skillpool}])
  if parent=='Expert':b.trait(d,'Two Tools',0,choices=[{'count':2,'pool':['tool:*']}])
  d['flags'][b.ID]['conditionalWeapons']='Simple weapons for humanoids or creatures already carrying simple/martial weapons; Warrior also gains martial weapons.'
 for parent,name,labels in [('Expert','Helpful',['Help']),('Expert','Cunning Action',['Dash','Disengage','Hide'])]:
  d=b.FEATURES[(parent,name)]
  for label in labels:b.activity(d,label,activation='bonus')
 d=b.FEATURES[('Expert','Expertise')]
 for level in [0,15]:b.trait(d,'Expertise '+str(level),level,choices=[{'count':2,'pool':['skills:*']}],mode='expertise')
 d=b.FEATURES[('Expert','Sharp Mind')];b.trait(d,'Saving Throw',0,choices=[{'count':1,'pool':['saves:int','saves:wis','saves:cha']}])
 b.effect(b.FEATURES[('Expert','Reliable Talent')],'Reliable Talent',[('flags.dnd5e.reliableTalent',True,5)])
 d=b.FEATURES[('Warrior','Second Wind')];b.uses(d,'1 + floor(@classes.warrior.levels / 20)','sr');b.activity(d,'Second Wind','heal',activation='bonus',target='self',formula='1d10 + @classes.warrior.levels',consume=b.consumeUses())
 b.effect(b.FEATURES[('Warrior','Improved Critical')],'Improved Critical',[('flags.dnd5e.weaponCriticalThreshold',19,3)])
 b.effect(b.FEATURES[('Warrior','Battle Readiness')],'Battle Readiness',[('system.attributes.init.roll.mode',1,5)])
 b.effect(b.FEATURES[('Warrior','Improved Defense')],'Improved Defense',[('system.attributes.ac.bonus',1,2)])
 d=b.FEATURES[('Warrior','Indomitable')];b.uses(d,'1 + floor(@classes.warrior.levels / 18)','lr');b.activity(d,'Reroll Failed Save',activation='special',consume=b.consumeUses())
 d=b.FEATURES[('Warrior','Martial Role')]
 for role in ['Attacker','Defender']:b.activity(d,'Choose '+role,activation='special',flags={b.ID:{'handler':'sidekick-role','role':role}})
 b.FEATURES[('Spellcaster','Potent Cantrips')]['flags'][b.ID]['cantripDamageBonus']='spellcasting'
 b.FEATURES[('Spellcaster','Empowered Spells')]['flags'][b.ID]['schoolDamageBonus']=True
 b.FEATURES[('Spellcaster','Focused Casting')]['flags'][b.ID]['concentrationDamageImmune']=True
 side=next(d for d in b.PACKS['classes'] if d['system']['identifier']=='spellcaster')
 common={'allowDrops':True,'type':'spell','pool':[],'spell':{'ability':['int'],'method':'spell','prepared':2,'uses':{'max':'','per':'','requireSlot':False}}}
 b.adv(side,'ItemChoice','Sidekick Cantrips',0,{**common,'choices':{'1':{'count':2,'replacement':False},'4':{'count':1,'replacement':False},'10':{'count':1,'replacement':False}},'restriction':{'level':'0','list':['wizard'],'type':'','subtype':''}})
 known={str(l):{'count':1,'replacement':False} for l in [1,2,3,5,7,9,11,13,15,17,19]}
 b.adv(side,'ItemChoice','Sidekick Spells Known',0,{**common,'choices':known,'restriction':{'level':'min(5, ceil(@classes.spellcaster.levels / 4))','list':['wizard'],'type':'','subtype':''}})
