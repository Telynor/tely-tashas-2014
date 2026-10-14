"""All source pages, handouts, and random tables stay available in Foundry."""
import json,html,re
from pathlib import Path

def build(b):
 pages=json.loads((b.ROOT/'source/book-pages.json').read_text())
 b.PACKS['origins']=[]
 # Six ability variants enforce the source's single +2 increase, rather than
 # silently allowing a split +1/+1 through a generic ASI choice.
 for ab,label in [('str','Strength'),('dex','Dexterity'),('con','Constitution'),('int','Intelligence'),('wis','Wisdom'),('cha','Charisma')]:
  d=b.item('Custom Lineage ('+label+')','race','origin:'+ab,8,'Humanoid; Small or Medium; speed 30 feet; +2 to the selected ability; one eligible feat; either darkvision 60 feet or one skill proficiency; Common and one other appropriate language.','origins')
  d['system'].update(identifier='custom-lineage-'+ab,type={'value':'humanoid','subtype':'','custom':''},movement={'walk':30,'units':'ft'},advancement={})
  b.adv(d,'AbilityScoreImprovement','Single Ability +2',0,{'points':0,'cap':2,'max':20,'fixed':{ab:2},'locked':[],'recommendation':None})
  b.adv(d,'Size','Size',0,{'sizes':['sm','med']})
  b.trait(d,'Languages',0,['languages:common'],[{'count':1,'pool':['languages:*']}])
  b.adv(d,'ItemChoice','Feat',0,{'choices':{'0':{'count':1,'replacement':False}},'type':'feat','allowDrops':True,'pool':[],'restriction':{'type':'feat','subtype':'','level':'','list':[]},'spell':None})
  b.adv(d,'ItemChoice','Variable Trait',0,{'choices':{'0':{'count':1,'replacement':False}},'type':'feat','allowDrops':False,'pool':[{'uuid':b.uuid('features','origin:darkvision')},{'uuid':b.uuid('features','origin:skill')}],'restriction':{'type':'','subtype':'','level':'','list':[]},'spell':None})
 dv=b.item('Custom Lineage: Darkvision','feat','origin:darkvision',8,'Darkvision out to 60 feet.');dv['system']['type']['value']='race';b.effect(dv,'Darkvision',[('system.attributes.senses.darkvision',60,4)])
 sk=b.item('Custom Lineage: Skill','feat','origin:skill',8,'Gain proficiency in one skill of your choice.');sk['system']['type']['value']='race';b.trait(sk,'Skill',0,choices=[{'count':1,'pool':['skills:*']}])
 for page in pages:
  n=page['pdf_page'];printed=page['printed_page'];label='Cover' if n==1 else 'Source Page '+str(printed)
  d={'_id':b.uid('page:'+str(n)),'name':label,'pages':[{'_id':b.uid('image:'+str(n)),'name':'Original Printed Page','type':'image','src':f'{b.MOD}/assets/pages/page-{n:03}.webp','image':{'caption':label},'title':{'show':True,'level':1}},{'_id':b.uid('text:'+str(n)),'name':'Searchable Transcription','type':'text','text':{'content':'<p>'+html.escape(page['text']).replace('\n\n','</p><p>')+'</p>','format':1},'title':{'show':True,'level':1}}],'folder':None,'sort':n*100000,'ownership':{'default':0},'flags':{b.ID:{'sourcePdfPage':n,'sourcePage':printed,'automation':'reference'}}}
  b.PACKS['reference'].append(d)
 for name,start,end in [('Character Options',8,83),('Group Patrons',84,105),('Magical Miscellany',106,139),('Dungeon Master’s Tools',140,189)]:
  content='<p>'+''.join(f'@UUID[Compendium.{b.ID}.reference.JournalEntry.{b.uid("page:"+str(n))}]{{Page {n-1}}}<br>' for n in range(start,end+1))+'</p>'
  b.PACKS['reference'].append({'_id':b.uid('chapter:'+name),'name':name,'pages':[{'_id':b.uid('chapter-page:'+name),'name':name,'type':'text','text':{'content':content,'format':1},'title':{'show':True,'level':1}}],'ownership':{'default':0},'flags':{b.ID:{'automation':'reference'}}})
 for n in range(190,194):
  b.PACKS['handouts'].append({'_id':b.uid('handout:'+str(n)),'name':'Puzzle Handouts '+str(n-189),'pages':[{'_id':b.uid('handout-image:'+str(n)),'name':'Player Handouts','type':'image','src':f'{b.MOD}/assets/pages/page-{n:03}.webp','image':{'caption':'TCE player handouts'},'title':{'show':True,'level':1}}],'ownership':{'default':2},'flags':{b.ID:{'sourcePdfPage':n}}})
 # Every discovered random table has an exact die and a link to the original
 # page. Multi-column/OCR-sensitive tables deliberately remain source lookup
 # tables instead of publishing guessed result prose.
 tables=json.loads((b.ROOT/'source/roll-table-inventory.json').read_text())
 results=json.loads((b.ROOT/'source/table-results.json').read_text()) if (b.ROOT/'source/table-results.json').exists() else {}
 tables += [{'pdf_page':149,'name':'FEY: DESIRED OFFERINGS','sides':4},{'pdf_page':150,'name':'OOZES: DESIRED OFFERINGS','sides':4}]
 for t in tables:
  key='table:'+str(t['pdf_page'])+':'+t['name'];name=t.get('title',t['name'].title());n=t['pdf_page']
  result=f'@UUID[Compendium.{b.ID}.reference.JournalEntry.{b.uid("page:"+str(n))}]{{{name}: use the rolled number on the original table}}'
  d={'_id':b.uid(key),'name':name,'description':f'TCE, p. {n-1}. Original table reproduced in the linked source page.','formula':'1d'+str(t['sides']),'replacement':True,'displayRoll':True,'results':[{'_id':b.uid(key+':source'),'type':0,'text':result,'range':[1,t['sides']],'weight':t['sides'],'drawn':False}],'ownership':{'default':0},'flags':{b.ID:{'sourcePage':n-1,'automation':'source-lookup'}}}
  if name in results:
   d['results']=[{'_id':b.uid(key+':'+str(r['range'][0])),'type':0,'text':html.escape(r['text'])+f' @UUID[Compendium.{b.ID}.reference.JournalEntry.{b.uid("page:"+str(n))}]{{Original table}}','range':r['range'],'weight':r['range'][1]-r['range'][0]+1,'drawn':False} for r in results[name]]
   d['flags'][b.ID]['automation']='native-roll-table'
  b.PACKS['tables'].append(d)
 for name,method in [('Tasha: Validate Installed Content','validate'),('Tasha: Configure a Stored Spell','configureStoredSpell'),('Tasha: Sidekick Builder','sidekickBuilder'),('Tasha: Resolve External Spells','resolveExternalSpells')]:
  b.PACKS['macros'].append({'_id':b.uid('macro:'+name),'name':name,'type':'script','scope':'global','img':'icons/svg/book.svg','command':f'await game.modules.get("{b.ID}").api.{method}();','ownership':{'default':2},'flags':{b.ID:{'automation':'script'}}})
