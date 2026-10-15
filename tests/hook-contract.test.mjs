import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const hooks=new Map(),warnings=[];
globalThis.Hooks={on:(name,fn)=>{const list=hooks.get(name)??[];list.push(fn);hooks.set(name,list);},once:(name,fn)=>{const list=hooks.get(name)??[];list.push(fn);hooks.set(name,list);}};
globalThis.ui={notifications:{warn:m=>warnings.push(m)}};
globalThis.foundry={utils:{deepClone:structuredClone}};
const {applySummonScaling,validate}=await import("../scripts/main.mjs");
const preUse=hooks.get("dnd5e.preUseActivity")[0];
const content=pack=>JSON.parse(fs.readFileSync(new URL(`../content/${pack}.json`,import.meta.url)));
const ID="tely-tashas-2014";
const feature=(parent,name)=>content("features").find(d=>d.name===name&&d.flags[ID].parent===parent);
test("native pre-use hook binds portable resource identifiers to actual actor item IDs",()=>{
 const items=[{id:"cccccccccccccccc",name:"Ki",system:{identifier:"ki"}}];items.get=id=>items.find(i=>i.id===id);
 const activity={name:"Hand of Harm",type:"utility",flags:{},actor:{items},consumption:{targets:[{type:"itemUses",target:"ki",value:"1"}]},updateSource(data){this.consumption=data.consumption;}};
 assert.equal(preUse(activity,{}),undefined);assert.equal(activity.consumption.targets[0].target,"cccccccccccccccc");
 activity.consumption.targets[0].target="wild-shape";assert.equal(preUse(activity,{}),false);assert.match(warnings.at(-1),/wild-shape/);
});
test("pre-summon hook writes creator-dependent changes without changing the template",()=>{
 const data=content("creatures").find(d=>d.name==="Celestial Spirit (Avenger)");
 const item=data.items.find(i=>i.name==="Radiant Bow"),attack=Object.values(item.system.activities)[0];
 const template={flags:data.flags,system:data.system,items:[{id:item._id,flags:item.flags,_source:item,system:{activities:[{...attack,id:attack._id}]}}]};
 const actor={uuid:"Actor.creator",classes:{},system:{abilities:{wis:{mod:4}},attributes:{spellcasting:"wis",prof:4}}};
 const config={actor:template,actorUpdates:{}};
 applySummonScaling({actor,relevantLevel:7,getRollData:()=>({mod:4}),match:{ability:"wis"}},null,config);
 assert.equal(config.actorUpdates["system.attributes.hp.max"],60);assert.equal(config.actorUpdates["system.attributes.ac.flat"],18);
 assert.equal(config.actorUpdates.items[0][`system.activities.${attack._id}.damage.parts.0.bonus`],"9");
 assert.equal(config.actorUpdates[`flags.${ID}.summon`].multiattack,3);assert.equal(attack.damage.parts[0].bonus,"2");
});
const evaluate=(formula,level)=>Function("min","max","floor","ceil",`return (${formula.replace(/@classes\.[a-z]+\.levels/g,String(level))});`)(Math.min,Math.max,Math.floor,Math.ceil);
test("generated resource formulas match source breakpoints",()=>{
 const elixir=feature("Alchemist","Experimental Elixir").system.uses.max;
 assert.deepEqual([3,5,6,14,15,20].map(l=>evaluate(elixir,l)),[1,1,2,2,3,3]);
 for(const [parent,levels,expected] of [["Cleric",[2,5,6,17,18,20],[1,1,2,2,3,3]],["Paladin",[3,6,7,14,15,20],[1,1,2,2,3,3]]]){
  const formula=feature(parent,"Harness Divine Power").system.uses.max;assert.deepEqual(levels.map(l=>evaluate(formula,l)),expected);
 }
 for(const [parent,cls] of [["Psi Warrior","fighter"],["Soulknife","rogue"]]){
  const act=Object.values(feature(parent,"Psionic Power").system.activities).find(a=>a.name==="Psionic Energy Die");const denom=act.roll.formula.slice(3,-1);
  assert.deepEqual([3,4,5,10,11,16,17,20].map(l=>evaluate(denom,l)),[6,6,8,8,10,10,12,12],cls);
 }
});
test("Cast component fields remove exactly the components waived by each source feature",()=>{
 assert.deepEqual(Object.values(feature("Alchemist","Chemical Mastery").system.activities).find(a=>a.type==="cast").spell.properties,["material"]);
 assert.deepEqual(Object.values(feature("Warlock","Undying Servitude").system.activities).find(a=>a.type==="cast").spell.properties,[]);
 for(const d of content("magic-items"))for(const a of Object.values(d.system.activities))if(a.type==="cast"){
  assert.equal(a.range.override,false,`${d.name}: inherit range`);assert.equal(a.target.override,false,`${d.name}: inherit targets`);
 }
});
test("Steady Aim benefits one attack while retaining every movement restriction",async()=>{
 const data=feature("Rogue","Steady Aim").effects[0];
 assert.deepEqual(data.changes.map(c=>c.key).sort(),["burrow","climb","fly","swim","walk"].map(s=>`system.attributes.movement.${s}`).sort());
 const effect={disabled:false,flags:structuredClone(data.flags),async setFlag(scope,key,value){this.flags[scope][key]=value;}};
 const activity={item:{type:"feat"},actor:{isOwner:true,effects:[effect]}};
 const before=hooks.get("dnd5e.preRollAttackV2")[0],after=hooks.get("dnd5e.rollAttackV2")[0];
 const first={subject:activity,rolls:[{parts:[],options:{}}]};before(first);assert.equal(first.rolls[0].options.advantage,true);
 await after([],{subject:activity});assert.equal(effect.flags[ID].nextAttackAdvantage,true,"cancelling a roll must preserve advantage");
 await after([{}],{subject:activity});assert.equal(effect.flags[ID].nextAttackAdvantage,false);assert.equal(activity.actor.effects.length,1);
 const second={subject:activity,rolls:[{parts:[],options:{}}]};before(second);assert.equal(second.rolls[0].options.advantage,undefined);
});
test("installed validation reports missing packs, embedded errors and unresolved choice/cast references",async()=>{
 const priorGame=globalThis.game,priorFromUuid=globalThis.fromUuid,priorApplications=foundry.applications;
 try{
  const names=["classes","subclasses","features","feats","spells","magic-items","creatures","tables","reference","handouts","macros","origins"];
  const packs=new Map(names.filter(n=>n!=="handouts").map(n=>[`${ID}.${n}`,{async getDocuments(){return [];}}]));
  packs.set(`${ID}.creatures`,{async getDocuments(){return [{name:"Spirit",items:[{name:"Attack",invalid:true,validationFailures:{system:"bad data"}}],_source:{items:[{system:{advancement:{choice:{configuration:{pool:[{uuid:"Compendium.example.features.MissingChoice"}]}}},activities:{cast:{spell:{uuid:"Compendium.example.spells.MissingSpell"}}}}}]}}];}});
  globalThis.game={user:{isGM:true},packs,version:"14",system:{version:"5.3.3"},modules:new Map()};
  const seen=[];globalThis.fromUuid=async uuid=>{seen.push(uuid);return null;};
  foundry.applications={api:{DialogV2:{wait:async()=>null}}};
  const result=await validate();
  assert.equal(result.failures.length,4);assert.ok(result.failures.some(x=>x.includes("Missing compendium")&&x.includes("handouts")));
  assert.ok(result.failures.some(x=>x.includes("Spirit / Attack")));assert.equal(seen.length,2);
 }finally{globalThis.game=priorGame;globalThis.fromUuid=priorFromUuid;foundry.applications=priorApplications;}
});
