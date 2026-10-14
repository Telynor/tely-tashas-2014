"""2014 spell activities; explicit damage conditions stay explicit."""
import re,copy
SPELLDATA={
 'Blade of Disaster':(9,'con','bonus',60,['vocal','somatic'],1,'minute',True,0),
 'Booming Blade':(0,'evo','action',5,['somatic','material'],1,'round',False,0.1),
 'Dream of the Blue Veil':(7,'con','minute',20,['vocal','somatic','material'],6,'hour',False,0),
 'Green-Flame Blade':(0,'evo','action',5,['somatic','material'],0,'inst',False,0.1),
 'Intellect Fortress':(3,'abj','action',30,['vocal'],1,'hour',True,0),
 'Lightning Lure':(0,'evo','action',15,['vocal'],0,'inst',False,0),
 'Mind Sliver':(0,'enc','action',60,['vocal'],1,'round',False,0),
 'Spirit Shroud':(3,'nec','bonus',0,['vocal','somatic'],1,'minute',True,0),
 'Summon Aberration':(4,'con','action',90,['vocal','somatic','material'],1,'hour',True,400),
 'Summon Beast':(2,'con','action',90,['vocal','somatic','material'],1,'hour',True,200),
 'Summon Celestial':(5,'con','action',90,['vocal','somatic','material'],1,'hour',True,500),
 'Summon Construct':(4,'con','action',90,['vocal','somatic','material'],1,'hour',True,400),
 'Summon Elemental':(4,'con','action',90,['vocal','somatic','material'],1,'hour',True,400),
 'Summon Fey':(3,'con','action',90,['vocal','somatic','material'],1,'hour',True,300),
 'Summon Fiend':(6,'con','action',90,['vocal','somatic','material'],1,'hour',True,600),
 'Summon Shadowspawn':(3,'con','action',90,['vocal','somatic','material'],1,'hour',True,300),
 'Summon Undead':(3,'nec','action',90,['vocal','somatic','material'],1,'hour',True,300),
 'Sword Burst':(0,'con','action',5,['vocal'],0,'inst',False,0),
 "Tasha's Caustic Brew":(1,'evo','action',0,['vocal','somatic','material'],1,'minute',True,0),
 "Tasha's Mind Whip":(2,'enc','action',90,['vocal'],1,'round',False,0),
 "Tasha's Otherworldly Guise":(6,'trs','bonus',0,['vocal','somatic','material'],1,'minute',True,500),
}
SUMMONS={'Summon Aberration':'Aberrant Spirit','Summon Beast':'Bestial Spirit','Summon Celestial':'Celestial Spirit','Summon Construct':'Construct Spirit','Summon Elemental':'Elemental Spirit','Summon Fey':'Fey Spirit','Summon Fiend':'Fiendish Spirit','Summon Shadowspawn':'Shadow Spirit','Summon Undead':'Undead Spirit'}
SPELLS={}

def summon(b,d,names,name='Summon',ability='',activation='action',range=30,consume=None,slot=False,seconds=3600):
 a=b.activity(d,name,'summon',activation=activation,range=range,target='space',count='1',consume=consume,slot=slot,duration=seconds,durationUnits='second')
 a.update(bonuses={k:'' for k in ['ac','hd','hp','attackDamage','saveDamage','healing']},creatureSizes=[],creatureTypes=[],match={'ability':ability,'attacks':True,'disposition':True,'proficiency':True,'saves':True},profiles=[{'_id':b.uid(d['_id']+':profile:'+n),'count':'1','cr':'','level':{'min':None,'max':None},'name':n,'types':[],'uuid':b.uuid('creatures','actor:'+n)} for n in names],summon={'mode':'','prompt':True},tempHP='')
 a['flags'][b.ID]={'handler':'summon','summonNames':names}
 return a

def build(b,creatures):
 for name,data in SPELLDATA.items():
  e=b.lookup('spell',name);level,school,act,range,components,dur,units,conc,cost=data
  d=b.item(name,'spell','spell:'+name,e['page'],e['text'],'spells');SPELLS[name]=d
  m=re.search(r'Components:.*?M \((.*?)\)\s*Duration:',e['text'],re.S)
  d['system'].update(identifier=b.slug(name),level=level,school=school,ability='',method='spell',prepared=1,sourceItem='',properties=components,materials={'value':m.group(1) if m else '', 'consumed':False,'cost':cost,'supply':0},activation={'type':act,'value':10 if name=='Dream of the Blue Veil' else 1,'condition':''},duration={'value':str(dur),'units':units,'concentration':conc,'special':''},range={'value':range or None,'units':'ft' if range else 'self','special':''},target={'template':{'type':'','size':'','count':''},'affects':{'type':'creature','count':'1','choice':False,'special':''}})
  if name in ['Booming Blade','Green-Flame Blade','Lightning Lure','Sword Burst']:
   d['system']['range']={'value':None,'units':'self','special':f'{range}-foot radius'}
  def a(label=None,typ='utility',**kw):
   return b.activity(d,label or name,typ,activation=act,cost=10 if name=='Dream of the Blue Veil' else 1,range=range,units='ft' if range else 'self',slot=level>0,duration=dur,durationUnits=units,concentration=conc,**kw)
  if name in SUMMONS:
   names=[n for n in creatures if n.startswith(SUMMONS[name]+' (')]
   x=summon(b,d,names,name=name,range=range,slot=True);x['duration'].update(value=str(dur),units=units,concentration=True)
   x['consumption']['scaling']={'allowed':True,'max':'9 - @item.level'}
  elif name=='Blade of Disaster':
   a('Create Planar Rift',flags={b.ID:{'handler':'source-prompt','note':'On casting, make two Blade Attacks. Later, one bonus action moves the blade up to 30 feet and makes two attacks.'}})
   x=b.activity(d,'Blade Attack','attack',activation='special',range=5,formula='4d12',damageType='force',slot=False)
   x['attack']['critical']['threshold']=18;x['damage']['critical']['bonus']='4d12'
  elif name in ['Booming Blade','Green-Flame Blade']:
   x=a('Cast with a Melee Weapon',flags={b.ID:{'handler':'blade-cantrip','spell':name}})
   d['flags'][b.ID]['automation']='native+script'
   if name=='Booming Blade':
    x=b.activity(d,'Willing Movement Damage','damage',activation='special',range=5,formula='(1 + floor((@details.level + 1) / 6))d8',damageType='thunder')
    x['flags'][b.ID]={'handler':'source-prompt','note':'Apply only if the affected creature willingly moves at least 5 feet before the caster’s next turn. Forced movement does not trigger this damage.'}
   else:
    x=b.activity(d,'Secondary Target Damage','damage',activation='special',range=5,formula='floor((@details.level + 1) / 6)d8 + @mod',damageType='fire')
    x['flags'][b.ID]={'handler':'source-prompt','note':'Choose another creature within 5 feet of the primary target. At levels 1–4, damage is only the spellcasting modifier.'}
  elif name=='Dream of the Blue Veil':a(target='creature',count='8',flags={b.ID:{'handler':'source-prompt','note':'Up to eight willing creatures. The GM adjudicates a six-hour planar journey and the required origin-world component.'}})
  elif name=='Intellect Fortress':
   x=a(target='creature',count='1 + @scaling')
   ef=b.effect(d,name,[('system.traits.dr.value','psychic',2)]+[(f'flags.midi-qol.advantage.ability.save.{ab}',True,5) for ab in ['int','wis','cha']],duration={'seconds':3600},transfer=False)
   x['effects']=[{'_id':ef['_id']}]
  elif name=='Lightning Lure':
   a('Pull Target','save',save='str',dc='spellcasting',onSave='none',flags={b.ID:{'handler':'source-prompt','note':'On failure pull up to 10 feet toward the caster. Damage is conditional on the target ending within 5 feet.'}})
   x=b.activity(d,'Damage After Pull','damage',activation='special',range=5,formula='1d8',damageType='lightning');x['damage']['parts'][0]['scaling']={'mode':'cantrip','number':1,'formula':''}
  elif name=='Mind Sliver':
   x=a(typ='save',save='int',formula='1d6',damageType='psychic',onSave='none');x['damage']['parts'][0]['scaling']={'mode':'cantrip','number':1,'formula':''}
   ef=b.effect(d,'Mind Sliver: Next Save -1d4',[('system.bonuses.abilities.save','-1d4',2)],duration={'rounds':1,'seconds':6},transfer=False,flags={b.ID:{'expireAfterSave':True,'expires':'end-source-next-turn'}})
   x['effects']=[{'_id':ef['_id'],'onSave':False}]
  elif name=='Spirit Shroud':
   for typ in ['radiant','necrotic','cold']:
    x=a('Spirit Shroud ('+typ+')',target='self')
    ef=b.effect(d,'Spirit Shroud ('+typ+')',duration={'seconds':60},transfer=False,flags={b.ID:{'spiritShroud':{'type':typ,'level':3}}})
    x['effects']=[{'_id':ef['_id']}];x['flags'][b.ID]={'handler':'spirit-shroud','type':typ}
   b.activity(d,'Extra Damage Within 10 Feet','damage',activation='special',range=10,formula='1d8',damageType='radiant')
  elif name=='Sword Burst':
   x=a(typ='save',save='dex',formula='1d6',damageType='force',count='',onSave='none');x['target']['template'].update(type='radius',size='5',units='ft');x['damage']['parts'][0]['scaling']={'mode':'cantrip','number':1,'formula':''}
  elif name=="Tasha's Caustic Brew":
   x=a('Coat Targets','save',save='dex',count='',onSave='none');x['target']['template'].update(type='line',size='30',width='5',units='ft')
   ef=b.effect(d,'Caustic Brew: Acid',[ ],duration={'seconds':60},transfer=False,flags={b.ID:{'dot':{'formula':'2d4','type':'acid'},'expires':'concentration'}})
   x['effects']=[{'_id':ef['_id'],'onSave':False}];x['flags'][b.ID]={'handler':'caustic-brew'}
   x=b.activity(d,'Start-of-Turn Acid Damage','damage',activation='special',formula='2d4',damageType='acid');x['damage']['parts'][0]['scaling']={'mode':'whole','number':2,'formula':''}
   b.activity(d,'Scrape or Wash Off Acid',activation='action',target='creature',flags={b.ID:{'handler':'remove-caustic'}})
  elif name=="Tasha's Mind Whip":
   x=a(typ='save',save='int',formula='3d6',damageType='psychic',onSave='half',count='1 + @scaling')
   ef=b.effect(d,'Mind Whip: No Reactions / Restricted Turn',[('flags.midi-qol.noReactions',True,5)],duration={'seconds':6},transfer=False,flags={b.ID:{'expires':'end-target-next-turn','prompt':'On its next turn, choose one: movement, action, or bonus action.'}})
   x['effects']=[{'_id':ef['_id'],'onSave':False}]
  elif name=="Tasha's Otherworldly Guise":
   for realm,immune,condition in [('Lower Planes',['fire','poison'],'poisoned'),('Upper Planes',['radiant','necrotic'],'charmed')]:
    x=a(realm,target='self');ef=b.effect(d,name+' ('+realm+')',[('system.attributes.movement.fly',40,4),('system.attributes.ac.bonus',2,2),('system.traits.ci.value',condition,2)]+[('system.traits.di.value',t,2) for t in immune],duration={'seconds':60},transfer=False,flags={b.ID:{'guise':True}})
    x['effects']=[{'_id':ef['_id']}]
  else:a()
  if name in ['Intellect Fortress','Spirit Shroud',"Tasha's Caustic Brew","Tasha's Mind Whip"]:
   for x in d['system']['activities'].values():
    if x['consumption']['spellSlot']:x['consumption']['scaling']={'allowed':True,'max':'9 - @item.level'}
 return SPELLS
