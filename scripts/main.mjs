import { ID, summonStats, cantripDice, psionicDie, boundedRestore, itemSpellBonus, eligibleSlotLevels, expiredAtTurn, physical, isEquipped, resourceItem, storedSpellData, compendiumReferences } from "./mechanics.mjs";
import "./icons.mjs";
const meta=d=>d?.flags?.[ID] ?? {};
const h=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const activeGM=()=>game.user?.id===game.users?.activeGM?.id;
const eligibleActor=a=>a && (a.isOwner || game.user.isGM);
const classLevel=(a,c)=>a.classes?.[c]?.system.levels ?? 0;
const formula=(s,a)=>Roll.safeEval(Roll.replaceFormulaData(String(s),a.getRollData(),{missing:"0"}));
const pending = new Map();
let previousTurn=null;
const syncing=new Set();

async function choose(title,options,{label="Choose",extra=""}={}) {
 if(!options.length)return null;
 return foundry.applications.api.DialogV2.wait({window:{title},content:`<form><label>${h(label)}<select name="choice">${options.map(o=>`<option value="${h(o.value)}">${h(o.label)}</option>`).join("")}</select></label>${extra}</form>`,buttons:[{action:"choose",label:"Continue",default:true,callback:(_event,_button,dialog)=>dialog.element.querySelector('[name="choice"]').value},{action:"cancel",label:"Cancel",callback:()=>null}],rejectClose:false});
}
async function amount(title,defaultValue=0) {
 return foundry.applications.api.DialogV2.wait({window:{title},content:`<form><label>Amount<input name="amount" type="number" min="0" value="${defaultValue}"></label></form>`,buttons:[{action:"apply",label:"Apply",default:true,callback:(_e,_b,d)=>Math.max(0,Number(d.element.querySelector('[name="amount"]').value))},{action:"cancel",label:"Cancel",callback:()=>null}],rejectClose:false});
}
async function note(activity,message="") {
 return ChatMessage.create({speaker:ChatMessage.getSpeaker({actor:activity.actor}),content:`<section><h3>${h(activity.item.name)} — ${h(activity.name)}</h3><p>${h(message || meta(activity).note || "Check the original rule’s trigger, target restrictions, and choices before applying it.")}</p>${activity.item.system.description.value}</section>`});
}
async function actorDamage(actor,value,type) {
 if(!eligibleActor(actor))throw new Error("You do not have permission to update this actor.");
 return actor.applyDamage([{value,type,properties:new Set()}]);
}
async function applyEffects(actor,effects) {
 if(actor.isOwner)return actor.createEmbeddedDocuments("ActiveEffect",effects);
 if(globalThis.MidiQOL?.socket)return MidiQOL.socket().executeAsGM("createEffects",{actorUuid:actor.uuid,effects});
 ui.notifications.warn("Ask the GM to apply this effect to the selected actor.");return [];
}
function targets(activity) {const selected=Array.from(game.user.targets).map(t=>t.actor).filter(Boolean);return selected.length?selected:[activity.actor];}
function actualItem(activity) {return activity.actor?.items.get(activity.item.id) ?? activity.item;}
async function restoreResource(activity,identifier,number) {
 const item=identifier?resourceItem(activity.actor,identifier):actualItem(activity);
 if(!item)throw new Error(`No ${identifier} resource item is on this actor.`);
 const spent=item.system.uses.spent,max=item.system.uses.max;
 await item.update({"system.uses.spent":boundedRestore(spent,max,number)});
}
async function restoreSlot(activity,maximum) {
 const a=activity.actor,keys=eligibleSlotLevels(a.system.spells,maximum);
 const key=await choose("Restore an Expended Spell Slot",keys.map(k=>({value:k,label:`Level ${k.slice(5)}`})));
 if(key)await a.update({[`system.spells.${key}.value`]:Math.min(a.system.spells[key].max,a.system.spells[key].value+1)});
 return !!key;
}
async function spellIndex() {
 const out=[];
 for(const pack of game.packs.filter(p=>p.documentName==="Item" && p.visible)) {
  const index=await pack.getIndex({fields:["type","system.level","system.source.rules","system.school"]});
  for(const e of index)if(e.type==="spell" && e.system?.source?.rules!=="2024")out.push({name:e.name,level:e.system?.level??0,school:e.system?.school,uuid:pack.getUuid(e._id)});
 }
 return out;
}
async function findSpell(name) {
 const normalized=s=>s.toLowerCase().replace(/[’']/g,"'");
 const local=game.items.find(i=>i.type==="spell" && i.name.toLowerCase()===name.toLowerCase() && i.system.source.rules!=="2024");
 if(local)return local;
 const aliases={"nystul's magic aura":"arcanist's magic aura"};
 const candidate=aliases[normalized(name)]??normalized(name).replace(/^[a-z]+\'s /,"");
 const entry=(await spellIndex()).find(s=>normalized(s.name)===normalized(name)||normalized(s.name)===candidate);
 return entry?fromUuid(entry.uuid):null;
}
async function castExternal(activity,name) {
 const spell=await findSpell(name);
 if(!spell){await note(activity,`The referenced spell ${name} is outside this sourcebook. Install its 2014 spell entry, then use Resolve External Spells.`);return;}
 const data=spell.toObject();delete data._id;delete data.folder;
 data.system.method="innate";data.system.prepared=2;data.flags??={};data.flags[ID]={temporaryCast:true};
 for(const a of Object.values(data.system.activities??{})){a.consumption.spellSlot=false;a.consumption.targets=[];}
 const [embedded]=await activity.actor.createEmbeddedDocuments("Item",[data]);
 try {const a=embedded.system.activities.find(a=>["save","attack","summon","utility","heal"].includes(a.type));await a?.use();}
 finally {await embedded.setFlag(ID,"expiresAt",game.time.worldTime+3600);}
}
async function configureStoredSpell(item=null,settings={}) {
 if(!item) {
  const actor=canvas.tokens.controlled[0]?.actor ?? game.user.character;
  if(!actor)return ui.notifications.warn("Select your token first.");
  const id=await choose("Choose a Stored-Spell Item",actor.items.filter(i=>meta(i).baseName==="Spellwrought Tattoo" || meta(i).storedSpell).map(i=>({value:i.id,label:i.name})));
  if(!id)return;item=actor.items.get(id);
 }
 const data=settings.level!==undefined?settings:Array.from(item.system.activities??[]).map(meta).find(m=>m.handler==="spellwrought")??{};
 const index=(await spellIndex()).filter(s=>s.level===(data.level??0));
 const id=await choose("Store a 2014 Spell",index.map(s=>({value:s.uuid,label:s.name})));
 if(!id)return;
 const spell=await fromUuid(id);const activityId=foundry.utils.randomID();
 const a={_id:activityId,name:`Cast ${spell.name}`,type:"cast",activation:{type:spell.system.activation.type,value:spell.system.activation.value,override:true},consumption:{spellSlot:false,targets:[{type:"itemUses",target:"",value:"1"}]},spell:{uuid:id,level:data.level??spell.system.level,ability:"",properties:["material"],spellbook:true,challenge:{override:true,save:data.dc,attack:data.attack}},flags:{[ID]:{castModifier:data.mod,spentTattoo:true}}};
 await item.update({[`system.activities.${activityId}`]:a,[`flags.${ID}.storedSpell`]:id});
 ui.notifications.info(`Stored ${spell.name}. Use its new Cast activity on the item.`);
}

/** Called at the official preSummonToken hook, before any token is created. */
export function applySummonScaling(activity,profile,config) {
 const scale=meta(config.actor).summonScale;
 if(!scale || !Object.keys(scale).length)return;
 const actor=activity.actor;const rd=activity.getRollData();
 const lvl=scale.spell?activity.relevantLevel:classLevel(actor,scale.class);
 const mod=actor.system.abilities[scale.hpAbility??activity.match.ability??actor.system.attributes.spellcasting]?.mod??rd.mod??0;
 const stats=summonStats(scale,{level:lvl,classLevel:lvl,abilityMod:mod,proficiency:actor.system.attributes.prof});
 const u=config.actorUpdates;u["system.attributes.hp.max"]=stats.hp;u["system.attributes.hp.value"]=stats.hp;
 if(stats.ac!==null)u["system.attributes.ac.flat"]=stats.ac;
 u[`flags.${ID}.summon`]={sourceActor:actor.uuid,level:lvl,multiattack:stats.multiattack};
 if(stats.hitDieCount)u["system.attributes.hp.formula"]=`${stats.hitDieCount}d${scale.hitDie}`;
 u.items??=[];
 for(const item of config.actor.items) {
  const im=meta(item);let update=u.items.find(i=>i._id===item.id);
  if(!update){update={_id:item.id};u.items.push(update);}
  for(const a of item.system.activities??[]) {
   if(im.summonAttack && a.damage?.parts?.length) {
    const base=Number(item._source.system.activities[a.id].damage.parts[0].bonus||0);
    update[`system.activities.${a.id}.damage.parts.0.bonus`]=String(base+stats.damageBonus);
   }
   if(im.scaleSaveDamage && a.damage?.parts?.length)update[`system.activities.${a.id}.damage.parts.0.bonus`]=String(stats.damageBonus);
   if(im.summonHealing && a.healing)update[`system.activities.${a.id}.healing.bonus`]=String(scale.spell?lvl:actor.system.attributes.prof);
   if(scale.cannon && a.damage?.parts?.length)update[`system.activities.${a.id}.damage.parts.0.number`]=stats.cannonDice;
   if(scale.cannon==="Protector" && a.healing)update[`system.activities.${a.id}.healing.bonus`]=String(stats.cannonHealingBonus);
  }
 }
 if(scale.primalBond) {
  const abilities={};for(const [ab,v] of Object.entries(config.actor.system.abilities))abilities[ab]={proficient:1};
  u["system.abilities"]=abilities;
  const skills={};for(const [skill,v] of Object.entries(config.actor.system.skills))skills[skill]={value:1};u["system.skills"]=skills;
 }
}

async function multiattack(activity) {
 const actor=activity.actor,number=actor.getFlag(ID,"summon.multiattack")??1;
 const attacks=actor.items.flatMap(i=>Array.from(i.system.activities??[]).filter(a=>a.type==="attack"));
 if(!attacks.length)return;
 const id=await choose("Choose an Attack",attacks.map(a=>({value:a.uuid,label:a.name})));
 if(!id)return;const selected=attacks.find(a=>a.uuid===id);
 for(let n=0;n<number;n++) {
  if(globalThis.MidiQOL?.completeActivityUse)await MidiQOL.completeActivityUse(selected,{consume:false},{});
  else await selected.use({consume:false});
 }
}
async function bladeCantrip(activity,name) {
 const actor=activity.actor;
 const weapons=actor.items.filter(i=>i.type==="weapon" && Array.from(i.system.activities??[]).some(a=>a.type==="attack"&&a.attack.type.value==="melee"));
 const id=await choose(name,weapons.map(w=>({value:w.id,label:w.name})));
 if(!id)return;const weapon=actor.items.get(id),a=weapon.system.activities.find(a=>a.type==="attack"&&a.attack.type.value==="melee");
 const count=cantripDice(actor.system.details.level)-1;
 const data=weapon.toObject();delete data._id;data.name=name+": "+weapon.name;data.system.quantity=1;
 for(const child of Object.values(data.system.activities))child.consumption={spellSlot:false,targets:[],scaling:{allowed:false}};
 const attack=data.system.activities[a.id];attack.range={value:5,units:"ft",override:true};attack.activation={type:"special",value:1,override:true};
 if(count)attack.damage.parts.push({number:count,denomination:8,bonus:"",types:[name==="Booming Blade"?"thunder":"fire"],custom:{enabled:false,formula:""},scaling:{mode:"",number:null,formula:""}});
 data.flags??={};data.flags[ID]={temporaryCast:true,bladeCantrip:name};
 const [embedded]=await actor.createEmbeddedDocuments("Item",[data]);
 try {const act=embedded.system.activities.get(a.id);if(globalThis.MidiQOL?.completeActivityUse)await MidiQOL.completeActivityUse(act,{consume:false},{});else await act.use({consume:false});}
 finally{await embedded.setFlag(ID,"expiresAt",game.time.worldTime+3600);}
}
async function resourceCraft(activity,kind) {
 const actor=activity.actor,prof=actor.system.attributes.prof;
 if(kind==="poisoner") {
  if(actor.system.currency.gp<50)return ui.notifications.warn("Crafting requires 50 gp and one hour with a poisoner’s kit.");
  const p=game.packs.get(`${ID}.magic-items`);const entry=(await p.getIndex()).find(i=>i.name==="Potent Poison (Poisoner)");const data=(await p.getDocument(entry._id)).toObject();delete data._id;delete data.folder;data.system.quantity=prof;
  await actor.update({"system.currency.gp":actor.system.currency.gp-50});await actor.createEmbeddedDocuments("Item",[data]);
 } else {
  const data={name:"Chef Treats",type:"consumable",img:"icons/consumables/food/bread-loaf-boule-tan.webp",system:{type:{value:"food"},quantity:prof,uses:{max:"1",spent:0,autoDestroy:true},description:{value:"A Chef treat. Lasts 8 hours; consume as a bonus action for temporary HP equal to its creator’s proficiency bonus."},activities:{}}};
  const id=foundry.utils.randomID();data.system.activities[id]={_id:id,type:"heal",name:"Eat Treat",activation:{type:"bonus",value:1},consumption:{spellSlot:false,targets:[{type:"itemUses",target:"",value:"1"}]},healing:{custom:{enabled:true,formula:String(prof)},types:["temphp"]}};data.flags={[ID]:{expiresAt:game.time.worldTime+28800}};
  await actor.createEmbeddedDocuments("Item",[data]);
 }
}
async function learnToolCantrip(activity) {
 const actor=activity.actor,index=(await spellIndex()).filter(s=>s.level===0&&!actor.items.some(i=>i.type==="spell"&&i.name===s.name));
 const uuid=await choose("All-Purpose Tool: Choose a Cantrip",index.map(s=>({value:s.uuid,label:s.name})));if(!uuid)return false;
 const spell=await fromUuid(uuid),data=spell.toObject();delete data._id;delete data.folder;
 data.system.ability="int";data.system.sourceItem="class:artificer";data.system.method="spell";data.system.prepared=2;data.flags??={};data.flags[ID]={expiresAt:game.time.worldTime+28800,toolCantrip:true};
 await actor.createEmbeddedDocuments("Item",[data]);return true;
}
async function swapBookSpell(activity) {
 const actor=activity.actor,school=meta(activity).school,book=meta(activity.item).bookSpells??[];
 const prepared=actor.items.filter(i=>i.type==="spell"&&i.system.sourceItem==="class:wizard"&&i.system.prepared===1);
 const oldId=await choose("Choose a Prepared Wizard Spell to Replace",prepared.map(i=>({value:i.id,label:i.name})));if(!oldId)return false;
 const choices=[];
 for(const name of book){const spell=await findSpell(name);if(spell&&(!school||spell.system.school===school))choices.push(spell);}
 const newId=await choose("Choose a Spell from the Book",choices.map(i=>({value:i.uuid,label:i.name})));if(!newId)return false;
 const spell=choices.find(i=>i.uuid===newId),existing=actor.items.find(i=>i.type==="spell"&&i.name===spell.name);
 await actor.items.get(oldId).update({"system.prepared":0});
 if(existing)await existing.update({"system.prepared":1,"system.sourceItem":"class:wizard"});
 else{const data=spell.toObject();delete data._id;delete data.folder;data.system.method="spell";data.system.prepared=1;data.system.ability="int";data.system.sourceItem="class:wizard";await actor.createEmbeddedDocuments("Item",[data]);}
 return true;
}
async function makeElixir(activity) {
 const actor=activity.actor,names=["Healing","Swiftness","Resilience","Boldness","Flight","Transformation"];
 let choice;
 if(meta(activity).chooseElixir){const selected=await choose("Choose Experimental Elixir",names.map((n,i)=>({value:String(i+1),label:n})));if(!selected)return;choice=Number(selected);}
 else{const roll=await new Roll("1d6").evaluate();await roll.toMessage({speaker:ChatMessage.getSpeaker({actor}),flavor:"Experimental Elixir"});choice=roll.total;}
 const id=foundry.utils.randomID(),mod=actor.system.abilities.int.mod;
 const data={name:"Experimental Elixir: "+names[choice-1],type:"consumable",img:"icons/consumables/potions/potion-bottle-corked-red.webp",system:{type:{value:"potion"},quantity:1,uses:{max:"1",spent:0,autoDestroy:true},description:{value:`<p>Experimental Elixir created by ${h(actor.name)}. See the source table, TCE p. 14.</p>`},activities:{}}};
 const a={_id:id,name:"Drink Elixir",type:choice===1?"heal":"utility",activation:{type:"action",value:1},consumption:{spellSlot:false,targets:[{type:"itemUses",target:"",value:"1"}]},target:{affects:{type:"self"}},effects:[]};data.system.activities[id]=a;
 if(choice===1)a.healing={custom:{enabled:true,formula:`2d4 + ${mod}`},types:["healing"]};
 else if(choice===6){a.type="cast";const spell=await findSpell("Alter Self");a.spell={uuid:spell.uuid,ability:"int",level:2,properties:["vocal","somatic","material"],challenge:{override:false},spellbook:true};a.duration={value:"10",units:"minute",concentration:false,override:true};}
 else {
  const changes=choice===2?[{key:"system.attributes.movement.walk",value:10,mode:2}]:choice===3?[{key:"system.attributes.ac.bonus",value:1,mode:2}]:choice===4?[...['mwak','rwak','msak','rsak'].map(t=>({key:`system.bonuses.${t}.attack`,value:"1d4",mode:2})),{key:"system.bonuses.abilities.save",value:"1d4",mode:2}]:[{key:"system.attributes.movement.fly",value:10,mode:4}];
  const effectId=foundry.utils.randomID();data.effects=[{_id:effectId,name:data.name,changes,duration:{seconds:choice===2?3600:choice===4?60:600},transfer:false}];a.effects=[{_id:effectId}];
 }
 // The source expires these at the creator's next long rest, not after 24 hours.
 data.flags={[ID]:{elixir:true,creator:actor.uuid,creatorInt:mod,restorative:classLevel(actor,"artificer")>=9}};
 if(classLevel(actor,"artificer")>=9){const extra=foundry.utils.randomID();data.system.activities[extra]={_id:extra,name:"Restorative Reagents: Temporary HP",type:"heal",activation:{type:"special",value:1},healing:{custom:{enabled:true,formula:`max(1, 2d6 + ${mod})`},types:["temphp"]},consumption:{spellSlot:false,targets:[]}};data.system.description.value+="<p>After drinking, apply Restorative Reagents once using the separate Temporary HP activity.</p>";data.system.uses.autoDestroy=false;}
 await actor.createEmbeddedDocuments("Item",[data]);
}
async function runHandler(activity,usage,results) {
 const data=meta(activity),actor=activity.actor;
 switch(data.handler) {
  case "source-prompt":return note(activity);
  case "restore-resource":return restoreResource(activity,data.identifier,data.amount);
  case "restore-self":return restoreResource(activity,"",data.amount);
  case "restore-slot":return restoreSlot(activity,formula(data.maximum,actor));
  case "external-spell":return castExternal(activity,data.name);
  case "multiattack":return multiattack(activity);
  case "blade-cantrip":return bladeCantrip(activity,data.spell);
  case "poisoner-craft":return resourceCraft(activity,"poisoner");
  case "chef-treats":return resourceCraft(activity,"chef");
  case "spellwrought":return configureStoredSpell(actualItem(activity),data);
  case "life-ward":if(actor.system.attributes.hp.value===0)return actor.update({"system.attributes.hp.value":1});return note(activity,"Use when damage would reduce you to 0 HP; the resulting HP is 1.");
  case "absorb-damage":{const n=await amount("Damage Prevented by Absorbing Tattoo");if(n!==null)await actorDamage(actor,Math.floor(n/2),"healing");return note(activity,"The triggering instance is immune. Remove that instance of damage from its application; resistance does not halve the amount used for this healing.");}
  case "end-condition":{const condition=await choose("End a Condition",data.choices.map(c=>({value:c,label:c})));if(!condition)return;for(const a of targets(activity))for(const e of a.effects.filter(e=>e.statuses.has(condition)))if(a.isOwner)await e.delete();return;}
  case "choose-resistance":case "choose-disadvantage":{
   const resistance=data.handler==="choose-resistance";const values=resistance?Object.keys(CONFIG.DND5E.damageTypes):Object.keys(CONFIG.DND5E.abilities);
   const choice=await choose(resistance?"Choose Damage Resistance":"Choose an Ability",values.map(v=>({value:v,label:v})));if(!choice)return;
   for(const target of targets(activity))await applyEffects(target,[{name:activity.item.name,origin:activity.item.uuid,transfer:false,duration:{seconds:6},changes:resistance?[{key:"system.traits.dr.value",value:choice,mode:2}]:["check","save"].map(k=>({key:`system.abilities.${choice}.${k}.roll.mode`,value:-1,mode:5})),flags:{[ID]:{expires:resistance?data.expires:"end-source-next-turn",sourceActor:actor.uuid,createdTurn:turnState()}}}]);return;
  }
  case "remove-caustic":for(const a of targets(activity))for(const e of a.effects.filter(e=>meta(e).dot?.type==="acid"&&e.name.includes("Caustic")))if(a.isOwner)await e.delete();return;
  case "sidekick-role":{
   const previous=actor.effects.filter(e=>meta(e).sidekickRole);if(previous.length)await actor.deleteEmbeddedDocuments("ActiveEffect",previous.map(e=>e.id));
   await actor.update({[`flags.${ID}.sidekickRole`]:data.role});
   if(data.role==="Attacker")await applyEffects(actor,[{name:"Warrior: Attacker",changes:['mwak','rwak','msak','rsak'].map(t=>({key:`system.bonuses.${t}.attack`,value:2,mode:2})),flags:{[ID]:{sidekickRole:true}}}]);return;
  }
  case "weapon-attack":{const weapons=actor.items.flatMap(i=>Array.from(i.system.activities??[]).filter(a=>a.type==="attack"&&a.attack.type.value==="melee"));const id=await choose("Choose a Melee Attack",weapons.map(a=>({value:a.uuid,label:a.name})));if(id)await weapons.find(a=>a.uuid===id).use({consume:false},{options:{advantage:true}});return;}
  case "all-purpose-cantrip":return learnToolCantrip(activity);
  case "spellbook-swap":return swapBookSpell(activity);
  case "elixir":return makeElixir(activity);
  case "wild-magic-barbarian":return note(activity,"Read the result on the Path of Wild Magic table, TCE p. 26. Controlled Surge changes how the result is chosen from barbarian level 14.");
  // Damage-dependent handlers finish through Midi-QOL's RollComplete event.
  case "blood-fury":return;
  case "spirit-shroud":case "caustic-brew":{
   const state={...data,level:activity.item.system.level+(usage.scaling??0)};pending.set(activity.item.uuid,state);
   await actor.setFlag(ID,"castScaling."+activity.item.id,state);
   for(const effect of actor.effects)if(meta(effect).spiritShroud)await effect.update({[`flags.${ID}.spiritShroud.level`]:state.level});return;
  }
  case "summon":return;
  default:if(data.handler)console.warn(`${ID}: unrecognized handler`,data.handler);
 }
}
function turnState() {const c=game.combat;return c?{round:c.round,turn:c.turn,actorId:c.combatant?.actor?.uuid}:null;}
async function syncConditionalEffects(actor) {
 if(!eligibleActor(actor)||syncing.has(actor.uuid))return;syncing.add(actor.uuid);
 try {
  const armored=actor.items.some(i=>i.type==="equipment"&&i.system.equipped&&['light','medium','heavy'].includes(i.system.type.value));
  const starry=actor.effects.some(e=>!e.disabled&&meta(e).starryForm);
  for(const item of actor.items)for(const effect of item.effects) {
   const m=meta(effect);let enabled=null;
   if(m.condition==="unarmored")enabled=!armored;
   if(m.condition==="starry-form")enabled=starry;
   if(m.minClassLevel)enabled=classLevel(actor,m.minClassLevel.class)>=m.minClassLevel.level;
   if(enabled!==null&&effect.disabled===enabled)await effect.update({disabled:!enabled});
  }
  const incompatible=actor.items.some(i=>i.type==="equipment"&&i.system.equipped&&['medium','heavy','shield'].includes(i.system.type.value));
  if(incompatible)for(const effect of actor.effects.filter(e=>meta(e).bladesong))await effect.delete();
 } finally {syncing.delete(actor.uuid);}
}
const replacements={"deft-explorer":["natural-explorer"],"favored-foe":["favored-enemy"],"primal-awareness":["primeval-awareness"],"nature-s-veil":["hide-in-plain-sight"],"blessed-strikes":["divine-strike","potent-spellcasting"],"primal-companion":["rangers-companion","ranger-s-companion"]};
async function checkReplacement(item) {
 const actor=item.actor;if(!eligibleActor(actor)||!meta(item).key)return;
 const names=replacements[item.system.identifier];
 if(names) {
  const old=actor.items.filter(i=>i.id!==item.id&&names.includes(i.system.identifier));
  if(!old.length)return;
  const confirmed=await foundry.applications.api.DialogV2.confirm({window:{title:"Optional Feature Replacement"},content:`<p>${h(item.name)} replaces ${old.map(i=>h(i.name)).join(", ")}. Apply the replacement?</p>`});
  if(confirmed){await actor.setFlag(ID,"replacements."+item.system.identifier,names);await actor.deleteEmbeddedDocuments("Item",old.map(i=>i.id));}
 } else {
  const adopted=Object.values(actor.getFlag(ID,"replacements")??{}).flat();
  if(adopted.includes(item.system.identifier))await item.delete();
 }
}
async function onTurn(combat,change) {
 if(!activeGM() || !game.settings.get(ID,"automaticTurns") || !("turn" in change || "round" in change))return;
 const current=turnState();if(!current || !combat.combatant?.actor)return;
 for(const actor of new Set(combat.combatants.map(c=>c.actor).filter(Boolean))) {
  for(const effect of actor.effects) {
   const m=meta(effect);
   if(expiredAtTurn(m.expires,m.createdTurn,previousTurn,current,m.sourceActor,actor.uuid))await effect.delete();
  }
 }
 const actor=combat.combatant.actor;
 const regen=meta(actor).regeneration;
 if(regen && actor.system.attributes.hp.value>0)await actorDamage(actor,regen,"healing");
 for(const effect of actor.effects.filter(e=>!e.disabled && meta(e).dot)) {
  const dot=meta(effect).dot,roll=await new Roll(dot.formula).evaluate();await roll.toMessage({speaker:ChatMessage.getSpeaker({actor}),flavor:effect.name});await actorDamage(actor,roll.total,dot.type);
 }
 previousTurn=current;
}

async function resolveExternalSpells({quiet=false}={}) {
 if(!game.user.isGM)return ui.notifications.warn("Only the GM can configure shared compendium content.");
 const index=await spellIndex(),resolved=[],missing=[];
 for(const pack of game.packs.filter(p=>p.metadata.packageName===ID && p.documentName==="Item")) {
  const docs=await pack.getDocuments();const updates=[];
  for(const item of docs) {
   const m=meta(item),adv=foundry.utils.deepClone(item._source.system.advancement??{});
   for(const name of [...(m.externalBookSpells??[]),...(m.externalSpells??[])])if(!index.some(s=>s.name.toLowerCase()===name.toLowerCase()))missing.push(name);
   let changed=false;
   for(const g of m.externalGrants??[]) {
    const spell=index.find(s=>s.name.toLowerCase()===g.name.toLowerCase());
    if(!spell){missing.push(g.name);continue;}
    if(Object.values(adv).some(a=>a.configuration?.items?.some(i=>i.uuid===spell.uuid)))continue;
    const id=foundry.utils.randomID();adv[id]={_id:id,type:"ItemGrant",title:g.name,level:g.level,configuration:{items:[{uuid:spell.uuid,optional:false}],optional:false,spell:{ability:[g.ability],method:"spell",prepared:2,uses:{max:"",per:"",requireSlot:false}}},value:{}};changed=true;resolved.push(g.name);
   }
   if(changed)updates.push({_id:item.id,"system.advancement":adv});
  }
  if(updates.length){const locked=pack.locked;try{await pack.configure({locked:false});await Item.updateDocuments(updates,{pack:pack.collection});}finally{await pack.configure({locked});}}
 }
 const result={resolved:[...new Set(resolved)],missing:[...new Set(missing)]};
 if(!quiet)await foundry.applications.api.DialogV2.wait({window:{title:"External Spell References"},content:`<p>Resolved: ${h(result.resolved.join(", ")||"none needed")}</p><p>Additional 2014 spell entries required: ${h(result.missing.join(", ")||"none")}</p>`,buttons:[{action:"close",label:"Close"}],rejectClose:false});
 return result;
}
export async function validate() {
 if(!game.user.isGM)return ui.notifications.warn("Run installed-content validation as the GM.");
 const failures=[],counts={},references=new Map();
 const packNames=["classes","subclasses","features","feats","spells","magic-items","creatures","tables","reference","handouts","macros","origins"];
 const checkDocument=(doc,label)=>{
  if(doc.invalid)failures.push(`${label}: ${JSON.stringify(doc.validationFailures)}`);
  for(const field of ["items","effects","pages","results"])for(const child of doc[field]??[])checkDocument(child,`${label} / ${child.name??child.id??field}`);
 };
 for(const name of packNames) {
  const pack=game.packs.get(`${ID}.${name}`);
  if(!pack){failures.push(`Missing compendium: ${ID}.${name}`);continue;}
  let docs;
  try{docs=await pack.getDocuments();}catch(error){failures.push(`${name}: cannot load compendium (${error.message})`);continue;}
  counts[name]=docs.length;
  for(const doc of docs) {
   checkDocument(doc,doc.name);
   for(const uuid of compendiumReferences(doc._source??{})){
    const names=references.get(uuid)??new Set();names.add(doc.name);references.set(uuid,names);
   }
  }
 }
 for(const [uuid,names] of references){
  try{if(await fromUuid(uuid))continue;}catch{}
  failures.push(`${[...names].join(", ")}: missing ${uuid}`);
 }
 const result={counts,failures,runtime:game.version,system:game.system.version,midi:game.modules.get("midi-qol")?.version??null};
 console.info(`${ID}: installed-content validation`,result);
 await foundry.applications.api.DialogV2.wait({window:{title:"Tasha Installed Content Check"},content:`<p>${failures.length?"Issues found":"Document and reference checks passed"}.</p><pre>${h(JSON.stringify(result,null,2))}</pre><p>This check validates installed data and references. Combat workflows still need to be exercised in your world.</p>`,buttons:[{action:"close",label:"Close"}],rejectClose:false});
 return result;
}
async function sidekickBuilder() {
 if(!game.user.isGM)return ui.notifications.warn("The sidekick builder is a GM tool.");
 const actor=canvas.tokens.controlled[0]?.actor;
 if(!actor)return ui.notifications.warn("Select the base creature’s token first.");
 if((actor.system.details.cr??1)>0.5)return ui.notifications.warn("The printed sidekick rules require a creature with CR 1/2 or lower.");
 const role=await choose("Choose a Sidekick Class",["Expert","Warrior","Spellcaster"].map(n=>({value:n,label:n})));if(!role)return;
 const pack=game.packs.get(`${ID}.classes`);const index=await pack.getIndex();const entry=index.find(i=>i.name===role+" (Sidekick)");const item=(await pack.getDocument(entry._id)).toObject();delete item._id;delete item.folder;
 const die=actor.system.attributes.hp.formula?.match(/d(\d+)/)?.[1]??"8";item.system.hd.denomination="d"+die;
 if(role==="Spellcaster") {
  const spellRole=await choose("Spellcaster Role",["Mage","Healer","Prodigy"].map(n=>({value:n,label:n})));if(!spellRole)return;
  item.system.spellcasting.ability={Mage:"int",Healer:"wis",Prodigy:"cha"}[spellRole];item.flags[ID].spellRole=spellRole;
  for(const advancement of Object.values(item.system.advancement))if(advancement.type==="ItemChoice"&&advancement.configuration.type==="spell"){
   advancement.configuration.restriction.list={Mage:["wizard"],Healer:["cleric","druid"],Prodigy:["bard","warlock"]}[spellRole];
   advancement.configuration.spell.ability=[item.system.spellcasting.ability];
  }
 }
 await actor.createEmbeddedDocuments("Item",[item]);await actor.setFlag(ID,"sidekick",true);
 ui.notifications.info("Sidekick class added with its original creature’s hit die. Open the class Advancement tab to apply its features and choices.");
}

Hooks.once("init",()=> {
 game.settings.register(ID,"automaticTurns",{name:"Automatic start-of-turn effects",hint:"Apply this module’s damage over time and regeneration on the active GM client.",scope:"world",config:true,type:Boolean,default:true});
 game.settings.register(ID,"insertSummons",{name:"Add summons to combat",hint:"Insert summoned companions immediately after their summoner when combat is active.",scope:"world",config:true,type:Boolean,default:true});
});
Hooks.once("ready",()=> {
 const module=game.modules.get(ID);module.api={validate,configureStoredSpell,sidekickBuilder,resolveExternalSpells,applySummonScaling};
 previousTurn=turnState();
 for(const actor of game.actors)if(eligibleActor(actor))syncConditionalEffects(actor).catch(console.error);
 if(game.system.id!=="dnd5e" || Number(game.system.version.split(".")[0])!==5)ui.notifications.warn("This sourcebook module targets D&D5e 5.3.3 through 5.x with 2014 rules.");
});
Hooks.on("dnd5e.preSummonToken",applySummonScaling);
Hooks.on("preCreateItem",(item,data)=>{
 const match=data.flags?.dnd5e?.cachedFor?.match(/Item\.([A-Za-z0-9]{16})\.Activity\.([A-Za-z0-9]{16})/);
 if(!match||!item.parent?.items)return;
 const linked=item.parent.items.get(match[1])?.system.activities.get(match[2]);
 if(meta(linked).castModifier!==undefined)item.updateSource(storedSpellData(data,meta(linked).castModifier));
});
Hooks.on("dnd5e.preUseActivity",(activity,usage)=> {
 const consumption=activity.consumption.targets.map(c=>c.toObject?c.toObject():foundry.utils.deepClone(c));
 let changed=false;
 for(const c of consumption)if(c.type==="itemUses"&&c.target&&!activity.actor.items.get(c.target)){
  const resource=resourceItem(activity.actor,c.target);
  if(!resource){ui.notifications.warn(`Add the ${c.target} resource feature to this actor before using ${activity.name}.`);return false;}
  c.target=resource.id;changed=true;
 }
 if(changed)activity.updateSource({consumption:{targets:consumption}});
 const handler=meta(activity).handler;
 if(handler==="restore-slot"&&!eligibleSlotLevels(activity.actor.system.spells,formula(meta(activity).maximum,activity.actor)).length){ui.notifications.warn("No eligible expended spell slot is available.");return false;}
 if(activity.type==="save"&&activity.item.type==="spell"&&activity.save.dc.calculation!=="") {
  const bonus=itemSpellBonus(activity.actor,activity.item).dc;
  if(bonus){const dc=activity.save.dc.value;activity.updateSource({save:{dc:{calculation:"",formula:String(dc+bonus)}}});}
 }
 if(activity.type==="attack"&&meta(activity).finesse&&activity.actor.system.abilities.str.mod>activity.actor.system.abilities.dex.mod)activity.updateSource({attack:{ability:"str"}});
 if(activity.type==="attack"&&activity.item.type==="weapon") {
  const actor=activity.actor;
  if(actor.items.some(i=>i.system.identifier==="battle-ready")&&(activity.item.system.properties.has("mgc")||activity.item.system.magicalBonus>0)&&actor.system.abilities.int.mod>(actor.system.abilities[activity.ability]?.mod??-99))activity.updateSource({attack:{ability:"int"}});
  const guise=actor.effects.some(e=>!e.disabled&&meta(e).guise);if(guise)activity.updateSource({attack:{ability:actor.system.attributes.spellcasting}});
 }
 if(activity.type==="damage"&&activity.name==="Extra Damage Within 10 Feet") {
  const buff=activity.actor.effects.find(e=>!e.disabled&&meta(e).spiritShroud);if(buff){const s=meta(buff).spiritShroud;activity.updateSource({damage:{parts:[{number:1+Math.floor((s.level-3)/2),denomination:8,bonus:"",types:[s.type],custom:{enabled:false,formula:""},scaling:{mode:""}}]}});}
 }
});
Hooks.on("dnd5e.preRollAttackV2",config=> {
 const a=config.subject;if(!a?.actor)return;
 const bonus=a.item.type==="spell"&&!a.attack?.flat?itemSpellBonus(a.actor,a.item).attack:0;
 for(const roll of config.rolls??[]) {
  if(bonus)roll.parts.push(String(bonus));
  roll.options??={};if(a.actor.effects.some(e=>!e.disabled&&meta(e).nextAttackAdvantage))roll.options.advantage=true;
 }
});
Hooks.on("dnd5e.rollAttackV2",async(rolls,{subject})=> {
 if(!rolls?.length||!eligibleActor(subject?.actor))return;
 // Steady Aim grants advantage on the next attack only. Its movement
 // restriction still lasts until this turn ends, so retain the effect.
 for(const effect of subject.actor.effects.filter(e=>!e.disabled&&meta(e).nextAttackAdvantage))await effect.setFlag(ID,"nextAttackAdvantage",false);
});
Hooks.on("dnd5e.postUseActivity",(activity,usage,results)=> {
 if(meta(activity).recoveryDays)actualItem(activity).setFlag(ID,"recoverAt."+activity.id,game.time.worldTime+meta(activity).recoveryDays*86400).catch(console.error);
 if(!meta(activity).handler || !eligibleActor(activity.actor))return;
 runHandler(activity,usage,results).catch(e=>{console.error(`${ID}: activity helper failed`,e);ui.notifications.error(e.message);});
});
Hooks.on("createActiveEffect",async(effect,options,userId)=> {
 if(!activeGM() && userId!==game.user.id)return;
 if(effect.parent?.documentName==="Actor")await syncConditionalEffects(effect.parent);
 const m=meta(effect);if(!m.expires&&!m.dot&&!m.spiritShroud)return;
 let source=null;try{source=effect.origin?await fromUuid(effect.origin):null;}catch{}
 const sourceActor=source?.actor?.uuid??source?.parent?.uuid;
 const updates={};if(!m.createdTurn)updates[`flags.${ID}.createdTurn`]=turnState();if(sourceActor&&!m.sourceActor)updates[`flags.${ID}.sourceActor`]=sourceActor;
 const item=source?.item??source;const scaled=pending.get(source?.uuid??source?.item?.uuid)??item?.actor?.getFlag(ID,"castScaling."+item.id);
 if(scaled?.handler==="caustic-brew")updates[`flags.${ID}.dot.formula`]=`${2*scaled.level}d4`;
 if(scaled?.handler==="spirit-shroud")updates[`flags.${ID}.spiritShroud.level`]=scaled.level;
 if(Object.keys(updates).length&&effect.isOwner)await effect.update(updates);
 if(effect.parent?.documentName==="Actor")await syncConditionalEffects(effect.parent);
});
Hooks.on("createItem",(item,_options,userId)=>{if(userId===game.user.id&&item.actor){syncConditionalEffects(item.actor).catch(console.error);checkReplacement(item).catch(console.error);}});
Hooks.on("updateItem",item=>{if(item.actor)syncConditionalEffects(item.actor).catch(console.error);});
Hooks.on("deleteItem",item=>{if(item.actor)syncConditionalEffects(item.actor).catch(console.error);});
Hooks.on("updateActor",actor=>syncConditionalEffects(actor).catch(console.error));
Hooks.on("deleteActiveEffect",effect=>{if(effect.parent?.documentName==="Actor")syncConditionalEffects(effect.parent).catch(console.error);});
Hooks.on("updateActiveEffect",effect=>{if(effect.parent?.documentName==="Actor")syncConditionalEffects(effect.parent).catch(console.error);});
Hooks.on("updateWorldTime",async()=>{
 if(!activeGM())return;
 for(const actor of game.actors)for(const item of actor.items){
  if(meta(item).expiresAt&&meta(item).expiresAt<=game.time.worldTime){await item.delete();continue;}
  for(const [id,time] of Object.entries(meta(item).recoverAt??{}))if(time<=game.time.worldTime){await item.update({[`system.activities.${id}.uses.spent`]:0});await item.unsetFlag(ID,"recoverAt."+id);}
 }
});
Hooks.on("dnd5e.restCompleted",async(actor,result)=>{
 if(!result.longRest||!eligibleActor(actor))return;
 for(const target of game.actors)for(const item of target.items)if(meta(item).elixir&&meta(item).creator===actor.uuid&&target.isOwner)await item.delete();
});
Hooks.on("dnd5e.rollSavingThrow",async(_rolls,{subject})=> {
 if(!eligibleActor(subject))return;
 for(const effect of subject.effects.filter(e=>meta(e).expireAfterSave&&!e.disabled))await effect.delete();
});
Hooks.on("updateCombat",(c,d)=>onTurn(c,d).catch(console.error));
Hooks.on("createToken",async token=> {
 if(!activeGM()||!game.combat||!game.settings.get(ID,"insertSummons"))return;
 const source=meta(token.actor).summon?.sourceActor;if(!source)return;
 const parent=game.combat.combatants.find(c=>c.actor?.uuid===source);if(!parent||game.combat.combatants.some(c=>c.tokenId===token.id))return;
 await game.combat.createEmbeddedDocuments("Combatant",[{tokenId:token.id,sceneId:token.parent.id,actorId:token.actorId,initiative:parent.initiative===null?null:parent.initiative-0.01,flags:{[ID]:{summoner:source}}}]);
});
Hooks.on("dnd5e.calculateDamage",(actor,damages,options)=> {
 const ghost=actor.effects.some(e=>!e.disabled&&meta(e).ghostStep);if(!ghost)return;
 const msg=options.originatingMessage;const attack=msg?.flags?.dnd5e?.activity?.type==="attack";
 if(!attack)return;
 let delta=0;
 for(const d of damages)if(physical.has(d.type)&&!d.properties?.has("mgc")&&!d.active?.resistance&&!d.active?.type?.resistance&&!d.active?.all?.resistance) {const previous=d.value;d.value=Math.floor(d.value/2);delta+=previous-d.value;d.active??={};d.active.resistance=true;}
 damages.amount-=delta;
});
Hooks.on("midi-qol.RollComplete",async workflow=> {
 const a=workflow.activity;if(!a||!eligibleActor(a.actor))return;
 if(meta(a).handler==="blood-fury") {
  const damage=(workflow.damageList??[]).reduce((n,d)=>n+Math.max(0,d.appliedDamage??d.hpDamage??0),0);
  if(damage)await actorDamage(a.actor,damage,"healing");
 }
});
