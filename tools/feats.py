"""Feat advancements and independently usable supporting items."""
def build(b):
 asi={'Chef':['con','wis'],'Crusher':['str','con'],'Fey Touched':['int','wis','cha'],'Gunner':['dex'],'Piercer':['str','dex'],'Shadow Touched':['int','wis','cha'],'Skill Expert':['str','dex','con','int','wis','cha'],'Slasher':['str','dex'],'Telekinetic':['int','wis','cha'],'Telepathic':['int','wis','cha']}
 for e in b.INV:
  if e['kind']!='feat':continue
  n=e['name'];d=b.item(n,'feat','feat:'+n,e['page'],e['text'],'feats');d['system']['identifier']=b.slug(n);d['system']['type']['value']='feat';d['system']['requirements']='Spellcasting or Pact Magic' if n in ['Eldritch Adept','Metamagic Adept'] else 'Proficiency with a martial weapon' if n=='Fighting Initiate' else ''
  if n in asi:b.asi(d,0,asi[n],1)
  def a(label,typ='utility',**kw):return b.activity(d,label,typ,**kw)
  def choice(title,level=0,spellLevel=None,schools=(),count=1,list=None):
   return b.adv(d,'ItemChoice',title,level,{'choices':{'0':{'count':count,'replacement':False}},'allowDrops':True,'type':'spell','pool':[],'restriction':{'level':str(spellLevel) if spellLevel is not None else '','list':list or [],'type':'','subtype':''},'spell':{'ability':asi.get(n,['int']),'method':'spell','prepared':2,'uses':{'max':'1' if spellLevel else '', 'per':'lr' if spellLevel else '', 'requireSlot':False}}})
  if n=='Artificer Initiate':
   choice('Artificer Cantrip',spellLevel=0,list=['artificer']);choice('Artificer 1st-level Spell',spellLevel=1,list=['artificer']);b.trait(d,'Artisan Tool',0,choices=[{'count':1,'pool':['tool:art:*']}])
  elif n=='Chef':
   b.trait(d,'Cook’s Utensils',0,['tool:cook']);a('Prepare Special Food',activation='hour',cost=1,flags={b.ID:{'handler':'source-prompt','note':'After a short rest, up to 4 + proficiency bonus creatures that eat and spend Hit Dice each regain an additional 1d8 hit points.'}});a('Cook Treats',activation='hour',cost=1,flags={b.ID:{'handler':'chef-treats'}})
  elif n in ['Crusher','Slasher','Piercer']:
   labels={'Crusher':['Move Hit Creature 5 Feet','Critical Hit: Grant Advantage'],'Slasher':['Reduce Speed by 10 Feet','Critical Hit: Impose Disadvantage'],'Piercer':['Reroll One Damage Die','Critical Hit: Extra Damage Die']}[n]
   for label in labels:a(label,activation='special',flags={b.ID:{'handler':'source-prompt','note':'Check the feat’s damage type, once-per-turn limit, and trigger before applying.'}})
  elif n=='Eldritch Adept':
   pool=[{'uuid':b.uuid('features',b.feature_key(f))} for f in b.INV if f['kind']=='invocation']
   b.adv(d,'ItemChoice','Eldritch Invocation',0,{'choices':{'0':{'count':1,'replacement':False}},'type':'feat','allowDrops':True,'pool':pool,'restriction':{'type':'class','subtype':'eldritchInvocation','level':'','list':[]},'spell':None})
  elif n in ['Fey Touched','Shadow Touched']:
   spell='Misty Step' if n=='Fey Touched' else 'Invisibility'
   b.grant(d,spell,0,[b.external_spell(spell)],spell={'ability':asi[n],'method':'spell','prepared':2,'uses':{'max':'1','per':'lr','requireSlot':False}})
   choice('Choose a 1st-level '+('Divination or Enchantment' if n=='Fey Touched' else 'Illusion or Necromancy')+' Spell',spellLevel=1)
   d['flags'][b.ID]['spellSchoolRestriction']=['div','enc'] if n=='Fey Touched' else ['ill','nec']
  elif n=='Fighting Initiate':
   b.adv(d,'ItemChoice','Fighting Style',0,{'choices':{'0':{'count':1,'replacement':False}},'type':'feat','allowDrops':True,'pool':[{'uuid':b.uuid('features',b.feature_key(f))} for f in b.INV if f['kind']=='fighting-style'],'restriction':{'type':'class','subtype':'fightingStyle','level':'','list':[]},'spell':None})
  elif n=='Gunner':b.trait(d,'Firearms Proficiency',0,['weapon:firearms']);d['flags'][b.ID]['gunner']=True
  elif n=='Metamagic Adept':
   b.uses(d,2,'lr');b.adv(d,'ItemChoice','Metamagic Options',0,{'choices':{'0':{'count':2,'replacement':False}},'type':'feat','allowDrops':True,'pool':[{'uuid':b.uuid('features',b.feature_key(f))} for f in b.INV if f['kind']=='metamagic'],'restriction':{'type':'class','subtype':'metamagic','level':'','list':[]},'spell':None})
   a('Spend Feat Sorcery Point',consume=b.consumeUses(),activation='special');d['flags'][b.ID]['restrictedSorceryPoints']=True
  elif n=='Poisoner':
   b.trait(d,'Poisoner’s Kit',0,['tool:pois']);a('Craft Potent Poison',activation='hour',cost=1,flags={b.ID:{'handler':'poisoner-craft'}});a('Apply Poison to Weapon',activation='bonus');d['flags'][b.ID]['poisoner']=True
  elif n=='Skill Expert':
   b.trait(d,'Skill Proficiency',0,choices=[{'count':1,'pool':['skills:*']}]);b.trait(d,'Skill Expertise',0,choices=[{'count':1,'pool':['skills:*']}],mode='expertise')
  elif n=='Telekinetic':
   b.grant(d,'Mage Hand',0,[b.external_spell('Mage Hand')],spell={'ability':asi[n],'method':'spell','prepared':2,'uses':{'max':'','per':'','requireSlot':False}})
   a('Telekinetic Shove','save',activation='bonus',range=30,save='str',dc='spellcasting',flags={b.ID:{'handler':'source-prompt','note':'Use the ability increased by this feat for the DC. Push or pull 5 feet on failure; a willing target may fail voluntarily.'}})
   d['flags'][b.ID]['featSpellAbility']=True
  elif n=='Telepathic':
   b.grant(d,'Detect Thoughts',0,[b.external_spell('Detect Thoughts')],spell={'ability':asi[n],'method':'spell','prepared':2,'uses':{'max':'1','per':'lr','requireSlot':False}})
   a('Telepathic Speech',activation='special',range=60,flags={b.ID:{'handler':'source-prompt','note':'The recipient must understand a language you speak. This does not grant it the ability to reply telepathically.'}})
 # A consumable dose uses the feat's printed fixed DC and damage, with no slot.
 p=b.item('Potent Poison (Poisoner)','consumable','support:potent-poison',80,'An injury poison crafted with the Poisoner feat. One dose poisons a weapon or ammunition for 1 minute or until it hits. On a hit: DC 14 Constitution save; 2d8 poison damage and poisoned until the end of the target’s next turn on failure.','magic-items')
 p['system'].update(type={'value':'poison','subtype':''},quantity=1,price={'value':0,'denomination':'gp'},weight={'value':0,'units':'lb'},properties=[],identified=True,uses={'spent':0,'max':'1','recovery':[]})
 a=b.activity(p,'Potent Poison Hit','save',activation='special',formula='2d8',damageType='poison',save='con',dc='',onSave='none',consume=b.consumeUses());a['save']['dc']['formula']='14'
 ef=b.effect(p,'Potent Poison: Poisoned',duration={'seconds':6},statuses=['poisoned'],transfer=False,flags={b.ID:{'expires':'end-target-next-turn'}});a['effects']=[{'_id':ef['_id'],'onSave':False}]
