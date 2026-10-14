"""Magic-item variants, independent use counters, and explicit trigger activities."""
import copy,re
BOOST={'All-Purpose Tool':['artificer'],'Amulet of the Devout':[], 'Arcane Grimoire':['wizard'],'Bloodwell Vial':['sorcerer'],'Moon Sickle':['druid','ranger'],"Rhythm-Maker's Drum":['bard']}
BOOKS={'Alchemical Compendium':'trs','Astromancy Archive':'div','Atlas of Endless Horizons':'con','Duplicitous Manuscript':'ill','Fulminating Treatise':'evo',"Heart Weaver's Primer":'enc','Libram of Souls and Flesh':'nec',"Planecaller's Codex":'con','Protective Verses':'abj'}
BOOKSPELLS={
 'Alchemical Compendium':['Enlarge/Reduce','Feather Fall','Flesh to Stone','Gaseous Form','Magic Weapon','Polymorph'],
 'Astromancy Archive':['Augury','Divination','Find the Path','Foresight','Locate Creature','Locate Object'],
 'Atlas of Endless Horizons':['Arcane Gate','Dimension Door','Gate','Misty Step','Plane Shift','Teleportation Circle','Word of Recall'],
 'Duplicitous Manuscript':['Hallucinatory Terrain','Major Image','Mirror Image','Mislead',"Nystul's Magic Aura",'Phantasmal Force','Silent Image'],
 'Fulminating Treatise':['Contingency','Fireball','Gust of Wind',"Leomund's Tiny Hut",'Magic Missile','Thunderwave','Wall of Force'],
 "Heart Weaver's Primer":['Antipathy/Sympathy','Charm Person','Dominate Person','Enthrall','Hypnotic Pattern','Modify Memory','Suggestion'],
 'Libram of Souls and Flesh':['Animate Dead','Circle of Death','False Life','Finger of Death','Speak with Dead','Summon Undead','Vampiric Touch'],
 "Planecaller's Codex":['Banishment','Find Familiar','Gate','Magic Circle','Planar Binding','Summon Elemental'],
 'Protective Verses':['Arcane Lock','Dispel Magic','Globe of Invulnerability','Glyph of Warding',"Mordenkainen's Private Sanctum",'Protection from Evil and Good','Symbol'],
 'Crystalline Chronicle':['Detect Thoughts','Intellect Fortress',"Rary's Telepathic Bond",'Sending','Telekinesis',"Tasha's Mind Whip","Tenser's Floating Disk"],
}
ITEMS={}
def build(b):
 def casting(d,name,cost=0,dc=None,daily=False,activation='action',override=False,ability='',spelllevel=None,properties=None):
  ref=b.external_spell(name)
  if ref:
   a=b.activity(d,'Cast '+name,'cast',activation=activation,consume=b.consumeUses(cost) if cost else [],slot=False)
   a['spell']={'uuid':ref,'ability':ability,'level':spelllevel,'properties':properties or ['vocal','somatic','material'],'spellbook':True,'challenge':{'attack':None,'save':dc,'override':dc is not None}}
  else:
   a=b.activity(d,'Cast '+name,activation=activation,consume=b.consumeUses(cost) if cost else [],flags={b.ID:{'handler':'external-spell','name':name,'dc':dc}})
   d['flags'][b.ID].setdefault('externalSpells',[]).append(name)
  if daily:
   a['uses']={'spent':0,'max':'1','recovery':[{'period':'dawn','type':'recoverAll','formula':''}]};a['consumption']['targets']=[{'type':'activityUses','target':'','value':'1','scaling':{'mode':'','formula':''}}]
  a['activation']['override']=True
  return a
 for e in b.INV:
  if e['kind']!='magic-item':continue
  n=e['name'];variants=[('',None)]
  if n in BOOST:variants=[(f' (+{i})',i) for i in [1,2,3]]
  elif n=='Absorbing Tattoo':variants=[(' ('+t.title()+')',t) for t in ['acid','cold','fire','force','lightning','necrotic','poison','psychic','radiant','thunder']]
  elif n=='Barrier Tattoo':variants=[(' (Uncommon)',13),(' (Rare)',15),(' (Very Rare)',18)]
  elif n=='Elemental Essence Shard':variants=[(' ('+s+')',s) for s in ['Air','Earth','Fire','Water']]
  elif n=='Outer Essence Shard':variants=[(' ('+s+')',s) for s in ['Lawful','Chaotic','Good','Evil']]
  elif n=='Spellwrought Tattoo':variants=[(' (Cantrip)',0)]+[(f' (Level {l})',l) for l in range(1,6)]
  for suffix,v in variants:
   typ='weapon' if n in ['Moon Sickle',"Devotee's Censer"] else 'equipment'
   d=b.item(n+suffix,typ,'item:'+n+suffix,e['page'],e['text'],'magic-items');ITEMS[n+suffix]=d
   rarity='artifact' if 'artifact' in e['text'][:100] else 'legendary' if 'legendary' in e['text'][:100] else 'veryRare' if 'very rare' in e['text'][:100] else 'uncommon' if 'uncommon' in e['text'][:100] else 'common' if 'common' in e['text'][:100] else 'rare'
   if n in BOOST:rarity=['uncommon','rare','veryRare'][v-1]
   if n=='Barrier Tattoo':rarity={13:'uncommon',15:'rare',18:'veryRare'}[v]
   if n=='Spellwrought Tattoo':rarity='common' if v<=1 else 'uncommon' if v<=3 else 'rare'
   attune=n not in ['Prosthetic Limb','Spellwrought Tattoo']
   d['system'].update(type={'value':'simpleM' if n=='Moon Sickle' else 'martialM' if typ=='weapon' else 'trinket','subtype':''},quantity=1,weight={'value':0,'units':'lb'},price={'value':0,'denomination':'gp'},rarity=rarity,identified=True,equipped=False,attunement='required' if attune else '',attuned=False,properties=['mgc'])
   d['flags'][b.ID]['baseName']=n
   if n in BOOKSPELLS:
    d['flags'][b.ID]['bookSpells']=BOOKSPELLS[n]
    for spell in BOOKSPELLS[n]:
     if not b.external_spell(spell):d['flags'][b.ID].setdefault('externalBookSpells',[]).append(spell)
   if typ=='weapon':
    d['system'].update(proficient=None,range={'value':5,'long':None,'reach':5,'units':'ft'},damage={'base':b.damage('1d4' if n=='Moon Sickle' else '1d8','slashing' if n=='Moon Sickle' else 'bludgeoning'),'versatile':b.damage('',None)},magicalBonus=v or 0)
    x=b.activity(d,'Attack','attack',range=5);x['damage']['includeBase']=True
    if n=="Devotee's Censer":x['damage']['parts']=[b.damage('1d8','radiant')]
   def a(label,typ='utility',**kw):return b.activity(d,label,typ,**kw)
   def limited(label,typ='utility',maximum=1,period='dawn',cost=1,**kw):
    b.uses(d,maximum,period);return a(label,typ,consume=b.consumeUses(cost),**kw)
   def applied(label,changes=(),seconds=60,statuses=(),activation='action',consume=None):
    x=a(label,activation=activation,consume=consume or [])
    ef=b.effect(d,label,changes,duration={'seconds':seconds},statuses=statuses,transfer=False)
    x['effects']=[{'_id':ef['_id']}];return x,ef
   if n in BOOST:
    d['flags'][b.ID]['spellBonus']={'classes':BOOST[n],'attack':v,'dc':v}
    if n=='Amulet of the Devout':limited('Extra Channel Divinity Use',activation='special',flags={b.ID:{'handler':'restore-resource','identifier':'channel-divinity','amount':1,'note':'Use this to pay for one Channel Divinity use without consuming the ordinary pool.'}})
    elif n=='All-Purpose Tool':a('Transform Artisan Tool');limited('Learn a Cantrip for 8 Hours',flags={b.ID:{'handler':'all-purpose-cantrip'}})
    elif n=='Bloodwell Vial':limited('Recover 5 Sorcery Points After Spending Hit Dice',activation='special',flags={b.ID:{'handler':'restore-resource','identifier':'sorcery-points','amount':5}})
    elif n=="Rhythm-Maker's Drum":limited('Recover Bardic Inspiration',flags={b.ID:{'handler':'restore-resource','identifier':'bardic-inspiration','amount':1}})
    elif n=='Arcane Grimoire':a('Arcane Recovery: One Additional Slot Level',activation='special',flags={b.ID:{'handler':'source-prompt'}})
    elif n=='Moon Sickle':a('Additional Healing','heal',activation='special',formula='1d4',flags={b.ID:{'handler':'source-prompt','note':'Add to one healing roll of a spell when the sickle is used as its spellcasting focus.'}})
   if n in BOOKS:
    b.uses(d,3,'dawn','1d3');a('Replace a Prepared Wizard Spell',activation='minute',consume=b.consumeUses(),flags={b.ID:{'handler':'spellbook-swap','school':BOOKS[n]}})
   if n=='Absorbing Tattoo':
    b.effect(d,'Damage Resistance',[('system.traits.dr.value',v,2)])
    limited('Absorb '+v.title()+' Damage',activation='reaction',flags={b.ID:{'handler':'absorb-damage','type':v}})
   elif n=='Alchemical Compendium':
    x=a('Transmute a Nonmagical Object',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'1 charge permits an object 1 foot on a side; each additional charge increases the maximum dimension by 2 feet. Check value, material, shape, and worn/carried restrictions.'}});x['consumption']['scaling']={'allowed':True,'max':'2'};x['consumption']['targets'][0]['scaling']={'mode':'amount','formula':''}
   elif n=='Astral Shard':a('Metamagic: Teleport 30 Feet',activation='special',range=30,flags={b.ID:{'handler':'source-prompt','note':'Use immediately after using a Metamagic option, while holding or wearing the shard.'}})
   elif n=='Astromancy Archive':a('Reaction: Fortune Adjustment',activation='reaction',range=30,formula='1d4',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'Add or subtract the d4 from a visible creature’s attack, check, or save.'}})
   elif n=='Atlas of Endless Horizons':a('Reaction: Teleport 10 Feet',activation='reaction',range=10,consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'If the teleport places you outside the attack’s reach or range, the attack misses.'}})
   elif n=="Baba Yaga's Mortar and Pestle":
    b.uses(d,12,'dawn');a('Primal Parts: Start Grinding',duration=1,durationUnits='minute');a('Primal Parts: Grinding Damage','damage',activation='special',formula='4d10',damageType='force')
    for i in [1,2,3]:a(f'Pestle: Spend {i} Charge'+('s' if i>1 else ''),'damage',activation='special',formula=f'{i}d8',damageType='force',consume=b.consumeUses(i))
    x=a('Perfect Tools',activation='action',flags={b.ID:{'handler':'source-prompt'}});x['uses']={'spent':0,'max':'1','recovery':[{'period':'sr','type':'recoverAll'}]};x['consumption']['targets']=[{'type':'activityUses','target':'','value':'1'}]
    a('Traverse the Night / Bones Know Their Home',flags={b.ID:{'handler':'source-prompt'}})
   elif n=='Barrier Tattoo':
    formula='13 + @abilities.dex.mod' if v==13 else '15 + min(2, @abilities.dex.mod)' if v==15 else '18'
    b.effect(d,'Unarmored Tattoo AC',[('system.attributes.ac.calc','custom',5),('system.attributes.ac.formula',formula,5)],flags={b.ID:{'condition':'unarmored'}})
   elif n=='Bell Branch':b.uses(d,3,'dawn','1d3');a('Detect Otherworldly Creatures',activation='bonus',range=60,consume=b.consumeUses());casting(d,'Protection from Evil and Good',1)
   elif n=='Blood Fury Tattoo':
    b.uses(d,10,'dawn');a('Bloodthirsty Strike','damage',activation='special',formula='4d6',damageType='necrotic',consume=b.consumeUses(),flags={b.ID:{'handler':'blood-fury'}});a('Bloodthirsty Retaliation',activation='reaction',consume=b.consumeUses(),flags={b.ID:{'handler':'weapon-attack','advantage':True}})
   elif n=='Cauldron of Rebirth':
    a('Create Potion of Greater Healing',activation='special',flags={b.ID:{'handler':'source-prompt','note':'After a long rest, use the cauldron to create one potion; it lasts 24 hours.'}})
    x=a('Raise Dead at Dawn',activation='special',flags={b.ID:{'handler':'source-prompt','note':'A humanoid corpse and 200 pounds of salt must remain in the cauldron for at least 8 hours. Salt is consumed; resurrection occurs at dawn. Recovery takes 7 days.','recoveryDays':7}});x['uses']={'spent':0,'max':'1','recovery':[]};x['consumption']['targets']=[{'type':'activityUses','target':'','value':'1'}]
   elif n=='Coiling Grasp Tattoo':
    x=a('Grasping Tendrils','save',range=15,formula='3d6',damageType='force',save='str',dc='',onSave='none');x['save']['dc']['formula']='14'
    ef=b.effect(d,'Grappled by Coiling Grasp',statuses=['grappled'],transfer=False,flags={b.ID:{'tether':15}});x['effects']=[{'_id':ef['_id'],'onSave':False}]
   elif n=='Crook of Rao':
    b.uses(d,6,'dawn','1d6')
    for spell,cost in [('Aura of Life',2),('Aura of Purity',2),('Banishment',1),('Beacon of Hope',1),('Mass Cure Wounds',3)]:casting(d,spell,cost,18)
    x=a('Absolute Banishment',flags={b.ID:{'handler':'source-prompt','note':'Check fiend CR limits, a 1-mile radius, and the century-long return restriction; then roll Extraplanar Reversal.'}});x['uses']={'max':'1','spent':0,'recovery':[]};x['flags'][b.ID]['recoveryDays']=10;x['consumption']['targets']=[{'type':'activityUses','target':'','value':'1'}]
   elif n=='Crystalline Chronicle':
    b.uses(d,3,'dawn','1d3');a('Replace a Prepared Wizard Spell',activation='minute',consume=b.consumeUses(),flags={b.ID:{'handler':'spellbook-swap'}})
    a('Psionic Casting',activation='special',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'Cast a wizard spell without verbal, somatic, or material components worth up to 100 gp.'}})
   elif n=='Demonomicon of Iggwilv':
    b.uses(d,8,'dawn','1d8');casting(d,"Tasha's Hideous Laughter",dc=20)
    for spell,cost in [('Magic Circle',1),('Magic Jar',3),('Planar Ally',3),('Planar Binding',2),('Plane Shift',3),('Summon Fiend',3)]:casting(d,spell,cost,20)
    a('Contain a Fiend','save',range=0,save='cha',dc='',flags={b.ID:{'handler':'source-prompt','note':'A fiend trapped in a magic circle makes a DC 20 Charisma save. Track up to 10 occupied pages and the long-rest possession risk.'}})['save']['dc']['formula']='20'
   elif n=="Devotee's Censer":
    x=limited('Activate Healing Incense',activation='bonus',duration=1,durationUnits='minute');ef=b.effect(d,'Healing Incense',duration={'seconds':60},transfer=False,flags={b.ID:{'healingAura':{'formula':'1d4','range':10,'timing':'source-start'}}});x['effects']=[{'_id':ef['_id']}]
    a('Incense Healing','heal',activation='special',range=10,count='',formula='1d4')
   elif n=='Duplicitous Manuscript':a('Impose Disadvantage on Illusion Investigation or Save',activation='reaction',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt'}})
   elif n=='Eldritch Claw Tattoo':
    d['flags'][b.ID]['unarmedBonus']=1
    x=limited('Eldritch Maul',activation='bonus',duration=1,durationUnits='minute');ef=b.effect(d,'Eldritch Maul',duration={'seconds':60},transfer=False,flags={b.ID:{'meleeExtraDamage':'1d6','type':'force','reach':15}});x['effects']=[{'_id':ef['_id']}]
   elif n=='Elemental Essence Shard':
    if v=='Air':a('Metamagic: Fly 60 Feet',activation='special',range=60,flags={b.ID:{'handler':'source-prompt','note':'This movement does not provoke opportunity attacks.'}})
    elif v=='Earth':a('Metamagic: Choose Damage Resistance',activation='special',flags={b.ID:{'handler':'choose-resistance','expires':'start-source-next-turn'}})
    elif v=='Fire':a('Metamagic: Ignite Spell Target','damage',activation='special',formula='2d10',damageType='fire',flags={b.ID:{'handler':'source-prompt','note':'Apply this damage only at the start of the selected spell target’s next turn.'}})
    else:
     a('Metamagic: Wave Damage','damage',activation='special',range=10,formula='2d6',damageType='cold',count='')
     x=a('Metamagic: Wave Push and Prone','save',activation='special',range=10,save='str',dc='spellcasting',count='');ef=b.effect(d,'Wave: Prone',statuses=['prone'],transfer=False);x['effects']=[{'_id':ef['_id'],'onSave':False}]
   elif n=='Far Realm Shard':
    x=a('Metamagic: Far Realm Tentacle','save',activation='special',range=30,save='cha',formula='3d6',damageType='psychic',onSave='none');ef=b.effect(d,'Far Realm: Frightened',duration={'seconds':6},statuses=['frightened'],transfer=False,flags={b.ID:{'expires':'start-source-next-turn'}});x['effects']=[{'_id':ef['_id'],'onSave':False}]
   elif n=='Feywild Shard':a('Metamagic: Wild Magic Surge',activation='special',flags={b.ID:{'handler':'source-prompt','note':'Roll on the 2014 sorcerer Wild Magic Surge table. A non-Wild-Magic sorcerer can trigger this property only once per dawn.'}})
   elif n=='Fulminating Treatise':a('Evocation Reaction Damage','damage',activation='reaction',formula='2d6',damageType='force',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'After a visible target takes damage from your evocation spell, add damage and knock it prone if Large or smaller.'}})
   elif n=='Ghost Step Tattoo':
    b.uses(d,3,'dawn');x,ef=applied('Ghost Step',[('system.traits.dr.value','bludgeoning',2),('system.traits.dr.value','piercing',2),('system.traits.dr.value','slashing',2)],6,activation='bonus',consume=b.consumeUses())
    ef['flags'][b.ID]={'expires':'end-source-next-turn','ghostStep':True};ef['changes']=[{'key':'system.traits.ci.value','mode':2,'value':s,'priority':20} for s in ['grappled','restrained']];d['flags'][b.ID]['ghostStepResistance']='nonmagical B/P/S only'
   elif n=='Guardian Emblem':limited('Turn a Critical Hit into a Normal Hit',maximum=3,activation='reaction',range=30,flags={b.ID:{'handler':'source-prompt','note':'Use before damage is finalized; cancel this attack’s critical damage.'}})
   elif n=="Heart Weaver's Primer":a('Enchantment: Disadvantage on First Save',activation='special',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt'}})
   elif n=="Illuminator's Tattoo":a('Write with Fingertip',activation='special');limited('Make a Written Page Invisible',flags={b.ID:{'handler':'source-prompt','note':'Touch a page and name a creature. Only you and that creature can see the writing for 24 hours.'}})
   elif n=='Libram of Souls and Flesh':applied('Semblance of Undeath',[],600,consume=b.consumeUses())
   elif n=='Lifewell Tattoo':b.effect(d,'Necrotic Resistance',[('system.traits.dr.value','necrotic',2)]);limited('Life Ward: Remain at 1 HP',activation='special',flags={b.ID:{'handler':'life-ward'}})
   elif n=="Luba's Tarokka of Souls":
    b.uses(d,2,'dawn')
    for spell in ['Comprehend Languages','Detect Evil and Good','Detect Magic','Detect Poison and Disease','Locate Object','Scrying']:casting(d,spell,dc=18,daily=True)
    for fortune,flag in [('Weal','advantage'),('Woe','disadvantage')]:
     x,ef=applied('Twist of Fate: '+fortune,[(f'flags.midi-qol.{flag}.attack.all',True,5),(f'flags.midi-qol.{flag}.ability.check.all',True,5),(f'flags.midi-qol.{flag}.ability.save.all',True,5)],3600,consume=b.consumeUses());x['range']['value']=15;x['flags'][b.ID]={'handler':'source-prompt','note':'After applying, roll on Souls of the Tarokka and track released souls.'}
   elif n=='Lyre of Building':
    casting(d,'Mending')
    for spell in ['Fabricate','Move Earth','Passwall','Summon Construct']:casting(d,spell,daily=True)
    a('Protect a Structure from Damage',activation='reaction',range=300,flags={b.ID:{'handler':'source-prompt','note':'Chosen object or structure is immune to the triggering damage and further damage of that type until your next turn.'}})
   elif n=='Masquerade Tattoo':casting(d,'Disguise Self',dc=13,daily=True);a('Fluid Ink',activation='bonus')
   elif n=='Mighty Servant of Leuk-o':a('Operating and Crew Rules',flags={b.ID:{'handler':'source-prompt','note':'Use its linked creature entry. Requires two attuned operators, crew actions, and a 10-day attunement process.'}})
   elif n=="Nature's Mantle":b.effect(d,'Advantage on Stealth',[('flags.midi-qol.advantage.skill.ste',True,5)]);a('Hide in Light Obscurement',activation='bonus',flags={b.ID:{'handler':'source-prompt'}})
   elif n=='Outer Essence Shard':
    if v=='Lawful':a('Metamagic: End a Condition',activation='special',range=30,flags={b.ID:{'handler':'end-condition','choices':['charmed','blinded','deafened','frightened','poisoned','stunned']}})
    elif v=='Chaotic':applied('Metamagic: Chaotic Disadvantage',[(f'flags.midi-qol.disadvantage.{k}.all',True,5) for k in ['attack','ability.check']],6,activation='special')
    elif v=='Good':a('Metamagic: Temporary Hit Points','heal',activation='special',range=30,formula='3d6',damageType='temphp')
    else:a('Metamagic: Extra Necrotic Damage','damage',activation='special',formula='3d6',damageType='necrotic')
   elif n=="Planecaller's Codex":applied('Empower a Conjured Creature',[('flags.midi-qol.advantage.attack.all',True,5)],60,activation='special',consume=b.consumeUses())
   elif n=='Prosthetic Limb':a('Attach or Detach Prosthetic',activation='action')
   elif n=='Protective Verses':a('Abjuration: Grant Temporary Hit Points','heal',activation='special',range=30,formula='2d10',damageType='temphp',consume=b.consumeUses())
   elif n=="Reveler's Concertina":d['flags'][b.ID]['spellBonus']={'classes':['bard'],'attack':0,'dc':2};casting(d,"Otto's Irresistible Dance",daily=True)
   elif n=='Shadowfell Brand Tattoo':b.effect(d,'Shadow Essence',[('system.attributes.senses.darkvision',60,4),('flags.midi-qol.advantage.skill.ste',True,5)]);limited('Shadowy Defense: Halve Triggering Damage',activation='reaction',period='dusk',flags={b.ID:{'handler':'source-prompt'}})
   elif n=='Shadowfell Shard':a('Metamagic: Choose Ability for Disadvantage',activation='special',flags={b.ID:{'handler':'choose-disadvantage','note':'Choose an ability. One target of the spell has disadvantage on ability checks and saves using it until the end of your next turn.'}})
   elif n=='Spellwrought Tattoo':
    d['system']['uses']={'max':'1','spent':0,'recovery':[]};a('Configure Stored Spell',flags={b.ID:{'handler':'spellwrought','level':v,'dc':13 if v<=2 else 15 if v<=4 else 17,'attack':5 if v<=2 else 7 if v<=4 else 9,'mod':3 if v<=2 else 4 if v<=4 else 5}})
   elif n=='Teeth of Dahlver-Nar':a('Draw a Tooth',flags={b.ID:{'handler':'source-prompt','note':'Roll the Teeth of Dahlver-Nar table, then choose sowing or implantation. Track teeth removed from the pouch.'}})
   # Activities without attunement must remain usable; native visibility handles
   # the actual required/optional state for attunable items.
   for x in d['system']['activities'].values():x['visibility']['requireAttunement']=attune
   if n=='Moon Sickle':d['system']['properties'].append('lgt')
 return ITEMS
