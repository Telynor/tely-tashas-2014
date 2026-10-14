"""Feature mechanics are explicit specifications, not prose-to-damage guesses."""
import copy,re

def build(b,creatures,spells):
 from spells import summon
 def get(parent,name):return b.FEATURES.get((parent,name))
 def act(parent,name,label=None,typ='utility',**kw):
  d=get(parent,name)
  if not d:return None
  return b.activity(d,label or name,typ,**kw)
 def pool(parent,name,maximum,period='lr'):
  d=get(parent,name)
  if d:b.uses(d,maximum,period)
  return d
 def applied(parent,name,changes=(),seconds=None,statuses=(),activation='action',consume=None,target='self',flags=None):
  d=get(parent,name)
  if not d:return None
  a=b.activity(d,name,activation=activation,consume=consume,target=target)
  e=b.effect(d,name,changes,duration={'seconds':seconds} if seconds else {},statuses=statuses,transfer=False,flags=flags)
  a['effects']=[{'_id':e['_id']}];return a,e
 def passive(parent,name,changes):
  d=get(parent,name)
  if d:b.effect(d,name,changes)
 def traits(parent,name,grants=(),pool=(),count=1,mode='default'):
  d=get(parent,name)
  if d:b.trait(d,name,0,grants,[{'count':count,'pool':list(pool)}] if pool else [],mode)
 # Proficiencies and passive statistics.
 for p,tool in [('Alchemist','alchemist'),('Armorer','smith'),('Artillerist','woodcarver'),('Battle Smith','smith')]:traits(p,'Tools of the Trade' if p=='Armorer' else 'Tool Proficiency',['tool:'+tool])
 traits('Armorer','Tools of the Trade',['armor:hvy']);traits('Battle Smith','Battle Ready',['weapon:mar'])
 traits('Order Domain','Bonus Proficiencies',['armor:hvy'],['skills:itm','skills:per'])
 traits('Twilight Domain','Bonus Proficiencies',['armor:hvy','weapon:mar'])
 traits('Peace Domain','Implement of Peace',pool=['skills:ins','skills:prf','skills:per'])
 traits('Rune Knight','Bonus Proficiencies',['tool:smith','languages:giant'])
 traits('Way of Mercy','Implements of Mercy',['skills:ins','skills:med','tool:herb'])
 traits('Bladesinging','Training in War and Song',['armor:lgt','skills:prf'],['weapon:sim:melee:*','weapon:mar:melee:*'])
 traits('Fey Wanderer','Otherworldly Glamour',pool=['skills:dec','skills:prf','skills:per'])
 passive('Fey Wanderer','Otherworldly Glamour',[('system.abilities.cha.bonuses.check','max(1, @abilities.wis.mod)',2)])
 passive('College of Eloquence','Silver Tongue',[('system.skills.dec.roll.min',10,4),('system.skills.per.roll.min',10,4)])
 passive('The Fathomless','Gift of the Sea',[('system.attributes.movement.swim',40,4)])
 passive('The Fathomless','Oceanic Soul',[('system.traits.dr.value','cold',2)])
 passive('Aberrant Mind','Psychic Defenses',[('system.traits.dr.value','psychic',2)])
 passive('Psi Warrior','Guarded Mind',[('system.traits.dr.value','psychic',2)])
 passive('Circle of Stars','Full of Stars',[(f'system.traits.dr.value',t,2) for t in ['bludgeoning','piercing','slashing']])
 d=get('Circle of Stars','Full of Stars')
 if d:
  for e in d['effects']:e['flags'][b.ID]={'condition':'starry-form'}
 passive('Circle of Spores','Fungal Body',[(f'system.traits.ci.value',t,2) for t in ['blinded','deafened','frightened','poisoned']])
 passive('Artificer','Tool Expertise',[('flags.dnd5e.toolExpertise',True,5)])
 for n in ['Magic Item Adept','Magic Item Savant','Magic Item Master']:passive('Artificer',n,[('system.attributes.attunement.max',1,2)])
 passive('Artificer','Soul of Artifice',[('system.bonuses.abilities.save','@attributes.attunement.value',2)])
 traits('Barbarian','Primal Knowledge',pool=['skills:ani','skills:ath','skills:itm','skills:nat','skills:prc','skills:sur'])
 d=get('Barbarian','Primal Knowledge')
 if d:b.trait(d,'Additional Skill at Level 10',10,choices=[{'count':1,'pool':['skills:ani','skills:ath','skills:itm','skills:nat','skills:prc','skills:sur']}])
 # Artificer and subclass resource use.
 pool('Artificer','Flash of Genius','max(1, @abilities.int.mod)');act('Artificer','Flash of Genius',activation='reaction',range=30,formula='@abilities.int.mod',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'Add this bonus to the triggering ability check or saving throw.'}})
 act('Artificer','Magical Tinkering',flags={b.ID:{'handler':'source-prompt'}})
 act('Artificer','The Right Tool for the Job',activation='hour',cost=1)
 act('Artificer','Spell-Storing Item',flags={b.ID:{'handler':'source-prompt','note':'Store an eligible 1st- or 2nd-level artificer spell; uses equal twice the artificer’s Intelligence modifier, minimum two.'}})
 act('Artificer','Soul of Artifice','Remain at 1 HP',activation='reaction',flags={b.ID:{'handler':'source-prompt','note':'End one infusion to drop to 1 HP instead of 0.'}})
 pool('Alchemist','Experimental Elixir','1 + min(1, floor(@classes.artificer.levels / 6)) + floor(@classes.artificer.levels / 15)')
 act('Alchemist','Experimental Elixir','Roll Daily Elixir',activation='special',consume=b.consumeUses(),flags={b.ID:{'handler':'elixir'}})
 a=act('Alchemist','Experimental Elixir','Create Chosen Elixir with a Spell Slot',consume=[{'type':'spellSlots','target':'1','value':'1','scaling':{'mode':'level','formula':''}}],flags={b.ID:{'handler':'elixir','chooseElixir':True}})
 a['consumption']['scaling']={'allowed':True,'max':'8'}
 for name in ['Restorative Reagents','Chemical Mastery']:d=get('Alchemist',name)
 pool('Alchemist','Restorative Reagents','max(1, @abilities.int.mod)')
 d=get('Alchemist','Restorative Reagents')
 if d:
  c=b.activity(d,'Cast Lesser Restoration','cast',consume=b.consumeUses());c['spell']={'uuid':b.external_spell('Lesser Restoration'),'ability':'int','level':2,'properties':[],'challenge':{'attack':None,'save':None,'override':False},'spellbook':True}
  b.activity(d,'Elixir: Additional Temporary Hit Points','heal',activation='special',formula='max(1, 2d6 + @abilities.int.mod)',damageType='temphp')
 passive('Alchemist','Chemical Mastery',[('system.traits.dr.value','acid',2),('system.traits.dr.value','poison',2),('system.traits.ci.value','poisoned',2)])
 for spell in ['Greater Restoration','Heal']:
  d=get('Alchemist','Chemical Mastery')
  if d:
   a=b.activity(d,'Cast '+spell,'cast');a['spell']={'uuid':b.external_spell(spell),'ability':'int','level':5 if spell=='Greater Restoration' else 6,'properties':['material'],'challenge':{'override':False,'attack':None,'save':None},'spellbook':True};a['uses']={'max':'1','spent':0,'recovery':[{'period':'lr','type':'recoverAll'}]};a['consumption']['targets']=[{'type':'activityUses','target':'','value':'1'}]
 act('Armorer','Arcane Armor','Create Arcane Armor');act('Armorer','Armor Model','Choose Guardian or Infiltrator',activation='special',flags={b.ID:{'handler':'source-prompt','note':'Change models only at the end of a short or long rest while using smith’s tools.'}})
 d=get('Armorer','Armor Model')
 if d:
  a=b.activity(d,'Thunder Gauntlets','attack',formula='1d8 + @mod',damageType='thunder',range=5);a['attack']['ability']='int';a['flags'][b.ID]={'handler':'source-prompt','note':'A hit imposes disadvantage on attacks against anyone other than the artificer until the start of the artificer’s next turn.'}
  a=b.activity(d,'Lightning Launcher','attack',formula='1d6 + @mod',damageType='lightning',range=90);a['range']['long']=300;a['attack'].update(ability='int',type={'value':'ranged','classification':'weapon'})
  a=b.activity(d,'Lightning Launcher: Once-per-Turn Extra Damage','damage',activation='special',formula='1d6',damageType='lightning')
  a=b.activity(d,'Defensive Field','heal',activation='bonus',formula='@classes.artificer.levels',damageType='temphp');a['uses']={'max':'@prof','spent':0,'recovery':[{'period':'lr','type':'recoverAll'}]};a['consumption']['targets']=[{'type':'activityUses','target':'','value':'1'}]
  d['flags'][b.ID]['armorModels']=True
 for parent,name,names,ab in [('Artillerist','Eldritch Cannon',[n for n in creatures if n.startswith('Eldritch Cannon (')],'int'),('Battle Smith','Steel Defender',['Steel Defender'],'int'),('College of Creation','Animating Performance',['Dancing Item'],'cha'),('Circle of Wildfire','Summon Wildfire Spirit',['Wildfire Spirit'],'wis'),('Beast Master','Primal Companion',[n for n in creatures if n.startswith('Beast of the ')],'wis'),('Artificer','Homunculus Servant',['Homunculus Servant'],'int')]:
  d=get(parent,name)
  if not d and name=='Homunculus Servant':d=get('Artificer',name)
  if d:
   if name in ['Eldritch Cannon','Animating Performance']:b.uses(d,1,'lr')
   consume=b.consumeUses(target='wild-shape') if name=='Summon Wildfire Spirit' else b.consumeUses() if name in ['Eldritch Cannon','Animating Performance'] else []
   summon(b,d,names,ability=ab,consume=consume,range=30 if name in ['Animating Performance','Summon Wildfire Spirit'] else 5)
   if name=='Summon Wildfire Spirit':b.activity(d,'Appearance: Fire Burst','save',range=10,count='',formula='2d6',damageType='fire',save='dex',dc='wis')
   if name in ['Eldritch Cannon','Animating Performance']:
    a=b.activity(d,'Create Again with a Spell Slot',flags={b.ID:{'handler':'source-prompt','note':'Expend a qualifying spell slot instead of the free daily use, then summon through the existing activity with consumption disabled.'}})
 pool('Battle Smith','Arcane Jolt','max(1, @abilities.int.mod)')
 for typ,dt in [('damage','force'),('heal','healing')]:act('Battle Smith','Arcane Jolt','Arcane Jolt: '+typ.title(),typ,activation='special',range=30,formula='(2 + 2 * floor(@classes.artificer.levels / 15))d6',damageType=dt,consume=b.consumeUses())
 act('Battle Smith','Improved Defender','Deflect Attack: Retaliation','damage',activation='special',formula='1d4 + @abilities.int.mod',damageType='force')
 act('Artillerist','Arcane Firearm','Additional Spell Damage','damage',activation='special',formula='1d8',damageType='',flags={b.ID:{'handler':'source-prompt','note':'Add to one damage roll of an artificer spell cast through the firearm; use the spell’s damage type.'}})
 act('Artillerist','Explosive Cannon','Detonate Cannon','save',range=20,count='',formula='3d8',damageType='force',save='dex',dc='int',onSave='half')
 act('Alchemist','Alchemical Savant','Add Intelligence to One Eligible Spell Roll',activation='special',formula='max(1, @abilities.int.mod)',flags={b.ID:{'handler':'source-prompt','note':'Only healing or acid, fire, necrotic, or poison damage from a spell using alchemist’s supplies.'}})
 # Barbarian paths.
 act('Barbarian','Instinctive Pounce',activation='special',flags={b.ID:{'handler':'source-prompt','note':'As part of entering rage, move up to half your speed.'}})
 for n in ['Infectious Fury','Call the Hunt']:pool('Path of the Beast',n,'@prof')
 act('Path of the Beast','Infectious Fury',typ='save',activation='special',save='wis',dc='con',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'After a natural-weapon hit, choose an induced melee attack or 2d12 psychic damage on a failed save.'}})
 act('Path of the Beast','Infectious Fury','Psychic Damage','damage',activation='special',formula='2d12',damageType='psychic')
 act('Path of the Beast','Call the Hunt',activation='special',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'On entering rage choose up to Constitution modifier willing creatures within 30 feet. Gain 5 temporary HP per accepting creature; each ally can add 1d6 to a weapon hit once on each of its turns.'}})
 act('Path of the Beast','Form of the Beast',flags={b.ID:{'handler':'source-prompt','note':'Choose bite, claws, or tail when entering rage. Use the natural weapons below.'}})
 d=get('Path of the Beast','Form of the Beast')
 if d:
  for n,die,typ,reach in [('Bite',8,'piercing',5),('Claws',6,'slashing',5),('Tail',8,'piercing',10)]:
   a=b.activity(d,n,'attack',formula=f'1d{die} + @mod',damageType=typ,range=reach);a['attack']['ability']='str'
  b.activity(d,'Tail: Defensive Roll',activation='reaction',formula='1d8')
 pool('Path of Wild Magic','Magic Awareness','@prof');act('Path of Wild Magic','Magic Awareness',activation='action',range=60,consume=b.consumeUses())
 act('Path of Wild Magic','Wild Surge',activation='special',formula='1d8',flags={b.ID:{'handler':'wild-magic-barbarian'}})
 pool('Path of Wild Magic','Bolstering Magic','@prof');act('Path of Wild Magic','Bolstering Magic',activation='action',range=5,formula='1d3',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'Choose a d3 bonus to attacks/checks for 10 minutes, or restore one expended spell slot up to the d3 result. Each creature can receive slot restoration only once per long rest.'}})
 act('Path of Wild Magic','Unstable Backlash',activation='reaction',formula='1d8',flags={b.ID:{'handler':'wild-magic-barbarian'}})
 # Bard colleges.
 act('Bard','Magical Inspiration',activation='special',flags={b.ID:{'handler':'source-prompt','note':'Spend an existing Bardic Inspiration die to increase one target’s spell damage or healing.'}})
 act('College of Creation','Performance of Creation',activation='action',flags={b.ID:{'handler':'source-prompt','note':'One free use per long rest; further uses cost a 2nd-level or higher slot. Size and value limits scale with bard level.'}});pool('College of Creation','Performance of Creation',1)
 act('College of Creation','Mote of Potential',activation='special',flags={b.ID:{'handler':'source-prompt','note':'Apply the correct rider only when the recipient spends its Bardic Inspiration die.'}})
 act('College of Eloquence','Unsettling Words',activation='bonus',range=60,formula='@scale.bard.inspiration',consume=b.consumeUses(target='bardic-inspiration'),flags={b.ID:{'handler':'source-prompt','note':'Subtract the rolled die from the creature’s next save before your next turn.'}})
 pool('College of Eloquence','Universal Speech',1);act('College of Eloquence','Universal Speech',range=60,consume=b.consumeUses())
 pool('College of Eloquence','Infectious Inspiration','@abilities.cha.mod');act('College of Eloquence','Infectious Inspiration',activation='reaction',range=60,consume=b.consumeUses())
 # Cleric features, including distinct Channel Divinity consumption.
 for parent,level in [('Cleric',2),('Paladin',3)]:
  maximum='1 + min(1, floor(@classes.cleric.levels / 6)) + floor(@classes.cleric.levels / 18)' if parent=='Cleric' else '1 + min(1, floor(@classes.paladin.levels / 7)) + floor(@classes.paladin.levels / 15)'
  pool(parent,'Harness Divine Power',maximum);act(parent,'Harness Divine Power',activation='bonus',consume=b.consumeUses()+b.consumeUses(target='channel-divinity'),flags={b.ID:{'handler':'restore-slot','maximum':'ceil(@prof / 2)'}})
 act('Cleric','Blessed Strikes',typ='damage',activation='special',formula='1d8',damageType='radiant')
 for parent,ab in [('Order Domain','wis'),('Twilight Domain','wis')]:act(parent,'Divine Strike',typ='damage',activation='special',formula='(1 + floor(@classes.cleric.levels / 14))d8',damageType='psychic' if parent=='Order Domain' else 'radiant')
 act('Order Domain',"Channel Divinity: Order's Demand",typ='save',save='wis',dc='wis',range=30,count='',consume=b.consumeUses(target='channel-divinity'))
 pool('Order Domain','Embodiment of the Law','max(1, @abilities.wis.mod)');act('Order Domain','Embodiment of the Law',activation='special',consume=b.consumeUses())
 act('Order Domain',"Order's Wrath",typ='damage',activation='special',formula='2d8',damageType='psychic')
 pool('Peace Domain','Emboldening Bond','@prof');act('Peace Domain','Emboldening Bond',range=30,count='@prof',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'Bonded creatures within range of another bonded creature can add 1d4 once per turn. At level 17, range increases to 60 feet.'}})
 act('Peace Domain','Channel Divinity: Balm of Peace',typ='heal',formula='2d6 + @abilities.wis.mod',range=5,count='',consume=b.consumeUses(target='channel-divinity'))
 act('Peace Domain','Protective Bond',activation='reaction',flags={b.ID:{'handler':'source-prompt','note':'A qualifying bonded creature teleports and takes all the triggering damage instead. Expansive Bond gives it resistance to that instance.'}})
 passive('Peace Domain','Potent Spellcasting',[('system.bonuses.spell.damage','@abilities.wis.mod',2)])
 # Avoid an unconditional spell-damage effect: this is only cleric cantrip damage.
 d=get('Peace Domain','Potent Spellcasting')
 if d:d['effects']=[];d['flags'][b.ID]['cantripDamageBonus']='wis'
 passive('Twilight Domain','Eyes of Night',[('system.attributes.senses.darkvision',300,4)])
 pool('Twilight Domain','Eyes of Night',1);act('Twilight Domain','Eyes of Night','Share Eyes of Night',range=10,count='max(1, @abilities.wis.mod)',consume=b.consumeUses())
 applied('Twilight Domain','Vigilant Blessing',[('flags.midi-qol.advantage.ability.check.init',True,5)],target='creature')
 act('Twilight Domain','Channel Divinity: Twilight Sanctuary',consume=b.consumeUses(target='channel-divinity'),flags={b.ID:{'handler':'source-prompt','note':'Creates a 30-foot sphere for 1 minute. At each creature’s turn end choose temporary HP or removal of one charm/fear effect.'}})
 act('Twilight Domain','Channel Divinity: Twilight Sanctuary','Sanctuary Temporary HP','heal',activation='special',formula='1d6 + @classes.cleric.levels',damageType='temphp',range=30)
 pool('Twilight Domain','Steps of Night','@prof');applied('Twilight Domain','Steps of Night',[('system.attributes.movement.fly','@attributes.movement.walk',4)],60,activation='bonus',consume=b.consumeUses())
 # Druid options and circles.
 act('Druid','Wild Companion',consume=b.consumeUses(target='wild-shape'),flags={b.ID:{'handler':'external-spell','name':'Find Familiar','note':'No material components; the familiar is a fey and disappears after half your druid level in hours.'}})
 act('Circle of Spores','Halo of Spores',typ='save',activation='reaction',range=10,save='con',dc='wis',formula='1d(4 + 2 * (min(1, floor(@classes.druid.levels / 6)) + min(1, floor(@classes.druid.levels / 10)) + floor(@classes.druid.levels / 14)))',damageType='necrotic',onSave='none')
 act('Circle of Spores','Symbiotic Entity',typ='heal',formula='4 * @classes.druid.levels',damageType='temphp',target='self',consume=b.consumeUses(target='wild-shape'))
 act('Circle of Spores','Symbiotic Entity','Extra Melee Weapon Damage','damage',activation='special',formula='1d6',damageType='necrotic')
 pool('Circle of Spores','Fungal Infestation','@abilities.wis.mod');act('Circle of Spores','Fungal Infestation',activation='reaction',range=10,consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'Animate the qualifying corpse using the 2014 Zombie stat block at 1 HP. It lasts 1 hour and can only make one melee attack when commanded.'}})
 act('Circle of Spores','Spreading Spores',activation='bonus',range=30,flags={b.ID:{'handler':'source-prompt','note':'A 10-foot cube uses Halo of Spores damage, once per turn per creature; your reaction Halo is unavailable while the cube persists.'}})
 pool('Circle of Stars','Star Map','@prof');act('Circle of Stars','Star Map','Free Guiding Bolt',consume=b.consumeUses(),flags={b.ID:{'handler':'external-spell','name':'Guiding Bolt'}})
 d=get('Circle of Stars','Star Map')
 if d:
  b.grant(d,'Star Map Spells',0,[b.external_spell('Guidance'),b.external_spell('Guiding Bolt')],spell={'ability':['wis'],'method':'spell','prepared':2,'uses':{'max':'','per':'','requireSlot':False}})
 for form in ['Archer','Chalice','Dragon']:
  d=get('Circle of Stars','Starry Form');a=b.activity(d,'Starry Form: '+form,activation='bonus',consume=b.consumeUses(target='wild-shape'),target='self')
  ef=b.effect(d,'Starry Form: '+form,duration={'seconds':600},transfer=False,flags={b.ID:{'starryForm':form}});a['effects']=[{'_id':ef['_id']}]
 act('Circle of Stars','Starry Form','Archer Attack','attack',activation='bonus',range=60,formula='(1 + floor(@classes.druid.levels / 10))d8 + @mod',damageType='radiant')['attack'].update(ability='wis',type={'value':'ranged','classification':'spell'})
 act('Circle of Stars','Starry Form','Chalice Healing','heal',activation='special',range=30,formula='(1 + floor(@classes.druid.levels / 10))d8 + @abilities.wis.mod')
 pool('Circle of Stars','Cosmic Omen','@prof');act('Circle of Stars','Cosmic Omen',activation='reaction',range=30,formula='1d6',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'Daily omen parity determines addition or subtraction; confirm it before applying the d6.'}})
 act('Circle of Wildfire','Enhanced Bond',activation='special',formula='1d8',flags={b.ID:{'handler':'source-prompt','note':'While your spirit is summoned, add to one damage/healing roll of an eligible spell.'}})
 pool('Circle of Wildfire','Cauterizing Flames','@prof')
 for typ in ['heal','damage']:act('Circle of Wildfire','Cauterizing Flames','Cauterize: '+typ.title(),typ,activation='reaction',formula='2d10 + @abilities.wis.mod',damageType='healing' if typ=='heal' else 'fire',consume=b.consumeUses())
 pool('Circle of Wildfire','Blazing Revival',1);act('Circle of Wildfire','Blazing Revival',activation='special',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'Sacrifice the spirit within 120 feet; regain half your maximum HP and stand.'}})
 # Psionic Energy dice are separate from bardic inspiration and superiority.
 for p,c in [('Psi Warrior','fighter'),('Soulknife','rogue')]:
  d=pool(p,'Psionic Power','2 * @prof')
  if d:
   d['flags'][b.ID]['psionicDieClass']=c
   for label in ['Psionic Energy Die','Protective Field' if p=='Psi Warrior' else 'Psi-Bolstered Knack','Psionic Strike' if p=='Psi Warrior' else 'Psychic Whispers']:
    a=b.activity(d,label,activation='reaction' if label=='Protective Field' else 'special',formula=f'1d(6 + 2 * floor((@classes.{c}.levels + 1) / 6))',consume=b.consumeUses() if label not in ['Psi-Bolstered Knack','Psychic Whispers'] else [],flags={b.ID:{'handler':'source-prompt','note':'Check the printed trigger and whether the die is expended before adjusting the pool.'}})
   a=b.activity(d,'Recover One Psionic Energy Die',activation='bonus',flags={b.ID:{'handler':'restore-self','amount':1}});a['uses']={'max':'1','spent':0,'recovery':[{'period':'sr','type':'recoverAll'}]};a['consumption']['targets']=[{'type':'activityUses','target':'','value':'1'}]
 act('Psi Warrior','Telekinetic Adept','Psi-Powered Leap',activation='bonus');act('Psi Warrior','Telekinetic Adept','Telekinetic Thrust','save',activation='special',save='str',dc='int',flags={b.ID:{'handler':'source-prompt','note':'After Psionic Strike damage, knock prone or move the target up to 10 feet on failure.'}})
 pool('Psi Warrior','Bulwark of Force','1');act('Psi Warrior','Bulwark of Force',activation='bonus',range=30,count='max(1, @abilities.int.mod)',consume=b.consumeUses())
 pool('Psi Warrior','Telekinetic Master',1);act('Psi Warrior','Telekinetic Master',consume=b.consumeUses(),flags={b.ID:{'handler':'external-spell','name':'Telekinesis','note':'Further uses cost a Psionic Energy die. While concentrating, a bonus action can make one weapon attack.'}})
 # Rune Knight's full rune choices are added below.
 pool('Rune Knight',"Giant's Might",'@prof');applied('Rune Knight',"Giant's Might",[('flags.midi-qol.advantage.ability.check.str',True,5),('flags.midi-qol.advantage.ability.save.str',True,5)],60,activation='bonus',consume=b.consumeUses())
 act('Rune Knight',"Giant's Might",'Once-per-Turn Extra Damage','damage',activation='special',formula='1d(6 + 2 * min(1, floor(@classes.fighter.levels / 10)) + 2 * floor(@classes.fighter.levels / 18))',damageType='')
 pool('Rune Knight','Runic Shield','@prof');act('Rune Knight','Runic Shield',activation='reaction',range=60,consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'After another creature is hit, make the attacker reroll the d20 and use the new result.'}})
 # Monk resources use the actor's Ki item rather than invented slot resources.
 act('Monk','Ki-Fueled Attack',activation='bonus');act('Monk','Quickened Healing',typ='heal',formula='@scale.monk.die + @prof',target='self',consume=b.consumeUses(2,'ki'))
 for cost in [1,2,3]:act('Monk','Focused Aim',f'Spend {cost} Ki: +{cost*2} to Missed Attack',activation='special',consume=b.consumeUses(cost,'ki'))
 act('Way of Mercy','Hand of Healing',typ='heal',formula='@scale.monk.die + @abilities.wis.mod',range=5,consume=b.consumeUses(1,'ki'))
 act('Way of Mercy','Hand of Harm',typ='damage',activation='special',formula='@scale.monk.die + @abilities.wis.mod',damageType='necrotic',consume=b.consumeUses(1,'ki'))
 pool('Way of Mercy','Hand of Ultimate Mercy',1);act('Way of Mercy','Hand of Ultimate Mercy',consume=b.consumeUses()+b.consumeUses(5,'ki'),flags={b.ID:{'handler':'source-prompt','note':'Revive a creature dead no longer than 24 hours; restore 4d10 + Wisdom modifier HP and eligible conditions.'}})
 act('Way of Mercy','Hand of Ultimate Mercy','Revival Hit Points','heal',activation='special',formula='4d10 + @abilities.wis.mod')
 act('Way of the Astral Self','Arms of the Astral Self',typ='save',save='dex',dc='wis',range=10,count='',formula='2 * @scale.monk.die',damageType='force',consume=b.consumeUses(1,'ki'))
 act('Way of the Astral Self','Visage of the Astral Self',activation='bonus',consume=b.consumeUses(1,'ki'))
 act('Way of the Astral Self','Body of the Astral Self','Deflect Energy',activation='reaction',formula='1d10 + @abilities.wis.mod')
 act('Way of the Astral Self','Awakened Astral Self',activation='bonus',consume=b.consumeUses(5,'ki'))
 # Paladin oath actions.
 for parent,names in [('Oath of Glory',['Peerless Athlete','Inspiring Smite']),('Oath of the Watchers',["Watcher's Will",'Abjure the Extraplanar'])]:
  for n in names:act(parent,'Channel Divinity',n,consume=b.consumeUses(target='channel-divinity'),activation='bonus' if n=='Inspiring Smite' else 'action')
 act('Oath of Glory','Channel Divinity','Inspiring Smite Temporary HP','heal',activation='special',formula='2d8 + @classes.paladin.levels',damageType='temphp')
 pool('Oath of Glory','Glorious Defense','max(1, @abilities.cha.mod)');act('Oath of Glory','Glorious Defense',activation='reaction',range=10,consume=b.consumeUses())
 for parent,n in [('Oath of Glory','Living Legend'),('Oath of the Watchers','Mortal Bulwark')]:pool(parent,n,1);act(parent,n,activation='bonus',consume=b.consumeUses())
 act('Oath of the Watchers','Vigilant Rebuke',typ='damage',activation='reaction',range=30,formula='2d8 + @abilities.cha.mod',damageType='force')
 # Ranger replacement features remain opt-in.
 d=get('Ranger','Deft Explorer')
 if d:
  b.trait(d,'Canny: Expertise',0,choices=[{'count':1,'pool':['skills:*']}],mode='expertise');b.trait(d,'Canny: Languages',0,choices=[{'count':2,'pool':['languages:*']}]);b.effect(d,'Roving',[('system.attributes.movement.walk',5,2)],flags={b.ID:{'minClassLevel':{'class':'ranger','level':6}}});b.uses(d,'@prof');a=b.activity(d,'Tireless: Temporary HP','heal',formula='1d8 + @abilities.wis.mod',damageType='temphp',consume=b.consumeUses());a['visibility']['identifier']='ranger';a['visibility']['level']['min']=10
 pool('Ranger','Favored Foe','@prof');act('Ranger','Favored Foe','Mark Favored Foe',activation='special',consume=b.consumeUses(),duration=1,durationUnits='minute',concentration=True)
 act('Ranger','Favored Foe','Once-per-Turn Extra Damage','damage',activation='special',formula='1d(4 + 2 * min(1, floor(@classes.ranger.levels / 6)) + 2 * floor(@classes.ranger.levels / 14))',damageType='')
 pool('Ranger',"Nature's Veil",'@prof');applied('Ranger',"Nature's Veil",seconds=6,statuses=['invisible'],activation='bonus',consume=b.consumeUses(),flags={b.ID:{'expires':'start-source-next-turn'}})
 act('Fey Wanderer','Dreadful Strikes',typ='damage',activation='special',formula='1d(4 + 2 * floor(@classes.ranger.levels / 11))',damageType='psychic')
 act('Fey Wanderer','Beguiling Twist',typ='save',activation='reaction',range=120,save='wis',dc='wis',flags={b.ID:{'handler':'source-prompt','note':'After a creature succeeds against charm/fear, a different creature may be charmed or frightened for 1 minute on failure, with repeat saves.'}})
 pool('Fey Wanderer','Fey Reinforcements',1);act('Fey Wanderer','Fey Reinforcements',consume=b.consumeUses(),flags={b.ID:{'handler':'external-spell','name':'Summon Fey','note':'Optionally remove concentration to reduce duration to 1 minute.'}})
 pool('Fey Wanderer','Misty Wanderer','max(1, @abilities.wis.mod)');act('Fey Wanderer','Misty Wanderer',activation='bonus',consume=b.consumeUses(),flags={b.ID:{'handler':'external-spell','name':'Misty Step','note':'Can bring one willing creature within 5 feet to a space within 5 feet of your destination.'}})
 act('Swarmkeeper','Gathered Swarm','Extra Swarm Damage','damage',activation='special',formula='1d(6 + 2 * floor(@classes.ranger.levels / 11))',damageType='piercing')
 act('Swarmkeeper','Gathered Swarm','Move Target Horizontally','save',activation='special',save='str',dc='wis',flags={b.ID:{'handler':'source-prompt','note':'Move up to 15 feet on failure; Mighty Swarm can also knock prone.'}})
 act('Swarmkeeper','Gathered Swarm','Move Self 5 Feet',activation='special')
 pool('Swarmkeeper','Writhing Tide','@prof');applied('Swarmkeeper','Writhing Tide',[('system.attributes.movement.fly',10,4),('system.attributes.movement.hover',True,5)],60,activation='bonus',consume=b.consumeUses())
 pool('Swarmkeeper','Swarming Dispersal','@prof');act('Swarmkeeper','Swarming Dispersal',activation='reaction',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'Gain resistance to the triggering damage, then teleport up to 30 feet.'}})
 # Rogue features.
 applied('Rogue','Steady Aim',[('system.attributes.movement.walk',0,5)],6,activation='bonus',flags={b.ID:{'expires':'end-source-turn','nextAttackAdvantage':True}})
 traits('Phantom','Whispers of the Dead',pool=['skills:*','tool:*'])
 pool('Phantom','Wails From the Grave','@prof');act('Phantom','Wails From the Grave',typ='damage',activation='special',range=30,formula='ceil(ceil(@classes.rogue.levels / 2) / 2)d6',damageType='necrotic',consume=b.consumeUses())
 pool('Phantom','Ghost Walk',1);applied('Phantom','Ghost Walk',[('system.attributes.movement.fly',10,4),('system.attributes.movement.hover',True,5),('flags.midi-qol.grants.disadvantage.attack.all',True,5)],600,consume=b.consumeUses())
 d=get('Soulknife','Psychic Blades')
 if d:
  for n,die,acttype in [('Psychic Blade',6,'action'),('Second Psychic Blade',4,'bonus')]:
   a=b.activity(d,n,'attack',activation=acttype,formula=f'1d{die} + @mod',damageType='psychic',range=60);a['attack'].update(ability='dex',type={'value':'ranged','classification':'weapon'});a['flags'][b.ID]={'finesse':True}
 act('Soulknife','Soul Blades','Homing Strikes',activation='special',formula='1d(6 + 2 * floor((@classes.rogue.levels + 1) / 6))')
 act('Soulknife','Soul Blades','Psychic Teleportation',activation='bonus',formula='1d(6 + 2 * floor((@classes.rogue.levels + 1) / 6))',flags={b.ID:{'handler':'source-prompt','note':'Teleport up to ten times the die roll; expend the die.'}})
 pool('Soulknife','Psychic Veil',1);applied('Soulknife','Psychic Veil',seconds=3600,statuses=['invisible'],consume=b.consumeUses())
 pool('Soulknife','Rend Mind',1);act('Soulknife','Rend Mind',typ='save',activation='special',save='wis',dc='dex',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'After Psychic Blades deals Sneak Attack damage: on failure stun for 1 minute, with repeat saves. Subsequent uses cost three Psionic Energy dice.'}})
 # Sorcerer pools and subclass activities.
 act('Sorcerer','Magical Guidance',activation='special',consume=b.consumeUses(1,'sorcery-points'))
 act('Aberrant Mind','Telepathic Speech',activation='bonus',range=30)
 act('Aberrant Mind','Psionic Sorcery',activation='special',flags={b.ID:{'handler':'source-prompt','note':'Pay sorcery points equal to the spell’s level for an eligible Psionic Spells spell; remove components except consumed materials.'}})
 for cost in range(1,5):act('Aberrant Mind','Revelation in Flesh',f'Choose {cost} Transformation'+('s' if cost>1 else ''),activation='bonus',consume=b.consumeUses(cost,'sorcery-points'))
 pool('Aberrant Mind','Warping Implosion',1);act('Aberrant Mind','Warping Implosion',typ='save',save='str',dc='cha',range=30,count='',formula='3d10',damageType='force',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'Teleport up to 120 feet, then eligible creatures are drawn up to 30 feet toward the vacated space on failure.'}})
 pool('Clockwork Soul','Restore Balance','@prof');act('Clockwork Soul','Restore Balance',activation='reaction',range=60,consume=b.consumeUses())
 for cost in range(1,6):act('Clockwork Soul','Bastion of Law',f'Create {cost} Bastion Die'+('s' if cost>1 else ''),consume=b.consumeUses(cost,'sorcery-points'),range=30)
 pool('Clockwork Soul','Trance of Order',1);act('Clockwork Soul','Trance of Order',activation='bonus',consume=b.consumeUses())
 pool('Clockwork Soul','Clockwork Cavalcade',1);act('Clockwork Soul','Clockwork Cavalcade',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'Distribute up to 100 healing, repair qualifying objects, and end eligible spells in a 30-foot cube; subsequent uses cost 7 sorcery points.'}})
 # Warlock features and wizard traditions.
 pool('The Fathomless','Tentacle of the Deeps','@prof');act('The Fathomless','Tentacle of the Deeps','Create Tentacle',activation='bonus',range=60,consume=b.consumeUses())
 a=act('The Fathomless','Tentacle of the Deeps','Tentacle Attack','attack',activation='bonus',range=10,formula='(1 + floor(@classes.warlock.levels / 10))d8 + 0',damageType='cold');a['attack'].update(ability='cha',type={'value':'melee','classification':'spell'})
 act('The Fathomless','Guardian Coil',activation='reaction',formula='(1 + floor(@classes.warlock.levels / 10))d8')
 pool('The Fathomless','Fathomless Plunge',1);act('The Fathomless','Fathomless Plunge',consume=b.consumeUses())
 pool('The Genie',"Genie's Vessel",1);act('The Genie',"Genie's Vessel",'Bottled Respite',consume=b.consumeUses())
 act('The Genie',"Genie's Vessel",'Genie’s Wrath','damage',activation='special',formula='@prof',damageType='',flags={b.ID:{'handler':'source-prompt','note':'Once on each turn after an attack hits. Damage type is determined by your genie kind.'}})
 pool('The Genie','Elemental Gift','@prof');applied('The Genie','Elemental Gift',[('system.attributes.movement.fly',30,4),('system.attributes.movement.hover',True,5)],600,activation='bonus',consume=b.consumeUses())
 pool('The Genie','Limited Wish',1);act('The Genie','Limited Wish',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'Request an eligible spell of 6th level or lower with a 1-action casting time; recovery is 1d4 long rests, not a single rest.'}})
 d=get('The Genie','Limited Wish')
 if d:d['system']['uses']['recovery']=[]
 pool('Bladesinging','Bladesong','@prof');applied('Bladesinging','Bladesong',[('system.attributes.ac.bonus','max(1, @abilities.int.mod)',2),('system.attributes.movement.walk',10,2),('flags.midi-qol.advantage.skill.acr',True,5),('system.attributes.concentration.bonuses.save','max(1, @abilities.int.mod)',2)],60,activation='bonus',consume=b.consumeUses(),flags={b.ID:{'bladesong':True}})
 for level in range(1,10):act('Bladesinging','Song of Defense',f'Spend Level {level} Slot: Reduce {5*level} Damage',activation='reaction',flags={b.ID:{'handler':'source-prompt','note':'Expend the chosen spell slot before reducing damage.'}})
 act('Order of Scribes','Wizardly Quill',activation='bonus')
 pool('Order of Scribes','Manifest Mind','@prof');act('Order of Scribes','Manifest Mind',activation='bonus',range=60)
 act('Order of Scribes','Master Scrivener',activation='special',flags={b.ID:{'handler':'source-prompt','note':'After a long rest, make one empowered 1st- or 2nd-level spell scroll; it casts one level higher and vanishes after the next long rest.'}})
 pool('Order of Scribes','One With the Word',1);act('Order of Scribes','One With the Word',activation='reaction',consume=b.consumeUses(),formula='3d6',flags={b.ID:{'handler':'source-prompt','note':'Use manifested mind to prevent all triggering damage; lose spells totaling at least the rolled levels for 1d6 long rests.'}})
 # Remaining narrative, choice, and triggered features receive a usable rules
 # action, explicitly labelled as adjudicated rather than falsely automatic.
 for d in b.PACKS['features']:
  if d['type']!='feat':continue
  if not d['system'].get('activities') and not d['effects'] and not d['system'].get('advancement'):
   b.activity(d,'Use / Review '+d['name'],activation='special',flags={b.ID:{'handler':'source-prompt'}});d['flags'][b.ID]['automation']='adjudicated'
  else:d['flags'][b.ID]['automation']='native' if not any(a.get('flags',{}).get(b.ID,{}).get('handler') for a in d['system']['activities'].values()) else 'native+script'
