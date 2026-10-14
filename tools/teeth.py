"""Twenty implant entries; the pouch's story and sowing restrictions remain source rules."""
def build(b):
 from magic_items import ITEMS
 source=next(e for e in b.INV if e['name']=='Teeth of Dahlver-Nar')
 names=['The Staring Cats of Uldun-dar',"Duggle’s Surprising Day",'The Golden Age of Dhakaan','The Mill Road Murders','Dooms of the Malpheggi',"The Stable Hand’s Secret","The Donkey’s Dream",'Beyond the Rock of Bral','The Disappearances of Half Hollow','Legendry of Phantoms and Ghosts','The Thousand Deaths of Jander Sunstar','Nightmares of Kaggash','Three Bridges to the Sky','The Claws of Dragotha','Ashes of the Ages and Eternal Fire','Daughters of Bel','Why the Sky Screams','The Last Tarrasque',"Incendax’s Tooth","Dahlver-Nar’s Tooth"]
 for number,name in enumerate(names,1):
  d=b.item(f'Implanted Tooth {number:02}: {name}','equipment','tooth:'+str(number),136 if number<=8 else 137,source['text'],'magic-items')
  d['system'].update(type={'value':'trinket'},quantity=1,rarity='artifact',equipped=False,attunement='',attuned=False,identified=True,properties=['mgc'])
  d['flags'][b.ID].update(tooth=number,automation='hybrid',adjudication='Equip only while implanted and attuned to the pouch. Follow implantation limit, drawbacks, sowing, and creature selection on the original pages.')
  def cast(spell,level=None,dc=None,maxuses=None,period='dawn'):
   a=b.activity(d,'Cast '+spell,'cast',slot=False)
   a['visibility']['requireAttunement']=False
   a['activation']['override']=True
   a['spell']={'uuid':b.external_spell(spell),'level':level,'ability':'','properties':['vocal','somatic','material'],'challenge':{'override':dc is not None,'save':dc,'attack':None},'spellbook':True}
   if maxuses is not None:
    b.uses(d,maxuses,period);a['consumption']['targets']=b.consumeUses()
   return a
  if number==1:cast('Revivify',3,maxuses=8,period='')
  elif number==2:a=cast('Sanctuary',1,18);a['activation']['type']='special';a['duration'].update(value='24',units='hour',override=True)
  elif number==3:b.uses(d,1,'sr');b.activity(d,'Redirect Hit to Adjacent Ally',activation='reaction',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'An ally within 5 feet is hit instead of you.'}})
  elif number==4:b.activity(d,'Damage Against Target That Has Not Taken a Turn','damage',activation='special',formula='3d10',damageType='slashing')
  elif number==5:b.effect(d,'Reptilian Scales',[('system.attributes.ac.bonus',2,2)]);b.activity(d,'Long Rest: Exhaustion Save','save',activation='special',target='self',save='con',dc='')['save']['dc']['formula']='15'
  elif number==6:b.activity(d,'Charisma Check Against a Humanoid',activation='special',formula='1d10',flags={b.ID:{'handler':'source-prompt','note':'The creature becomes hostile at the next dawn.'}})
  elif number==7:b.uses(d,3,'dawn');b.activity(d,'Unicorn Healing','heal',range=5,formula='2d8 + 2',consume=b.consumeUses(),flags={b.ID:{'handler':'source-prompt','note':'Also remove all diseases and poisons affecting this target.'}})
  elif number==8:
   cast('Detect Thoughts',2);b.effect(d,'Whispering Minds',[('system.traits.languages.custom','Telepathy 120 feet',2),('system.skills.ins.roll.mode',-1,5),('system.skills.prc.roll.mode',-1,5)])
  elif number==9:b.activity(d,'Long Jump 30 Feet / High Jump 15 Feet',activation='special')
  elif number==10:cast('Black Tentacles',4,18,1)
  elif number==11:
   a=b.activity(d,'Vampire Bite','attack',formula='1d6 + @mod',damageType='piercing');a['attack']['ability']='str';a['damage']['parts'].append(b.damage('3d6','necrotic'));a['flags']={b.ID:{'handler':'source-prompt','note':'Heal only for the necrotic damage actually dealt; no healing in sunlight.'}}
  elif number==12:cast('Eyebite',6,maxuses=1);b.activity(d,'Long Rest: Aberration Risk',activation='special',formula='1d20')
  elif number==13:cast('Detect Magic',1);b.effect(d,'Flying Speed',[('system.attributes.movement.fly',30,4)])
  elif number==14:cast('Create Undead',6,maxuses=1)
  elif number==15:cast('Counterspell',9,maxuses=1);b.activity(d,'Unused Since Last Rest: HP Maximum Loss',activation='special',formula='2d10')
  elif number==16:cast('Dominate Monster',8,18,1)
  elif number==17:b.effect(d,'Lightning Immunity / Thunder Vulnerability',[('system.traits.di.value','lightning',2),('system.traits.dv.value','thunder',2)])
  elif number==18:b.activity(d,'20 Damage in One Turn: Wisdom Save','save',activation='special',target='self',save='wis',dc='')['save']['dc']['formula']='18'
  elif number==19:
   b.effect(d,'Fire Immunity',[('system.traits.di.value','fire',2)])
   a=b.activity(d,'Exhale Fire','save',formula='26d6',damageType='fire',save='dex',dc='',onSave='half',count='');a['save']['dc']['formula']='24';a['target']['template'].update(type='cone',size='90');a['flags']={b.ID:{'handler':'source-prompt','note':'Gain two levels of exhaustion after this breath.'}}
  else:
   a=b.activity(d,'Divine Intervention',flags={b.ID:{'handler':'source-prompt','note':'Describe the requested aid. The DM determines the intervention.','recoveryDays':7}});a['uses']={'spent':0,'max':'1','recovery':[]};a['consumption']['targets']=[{'type':'activityUses','target':'','value':'1'}]
