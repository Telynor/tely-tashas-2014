import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import {ID,summonStats,cantripDice,psionicDie,classThresholds,boundedRestore,itemSpellBonus,eligibleSlotLevels,expiredAtTurn,resourceItem,storedSpellData} from "../scripts/mechanics.mjs";
const actors=JSON.parse(fs.readFileSync(new URL("../content/creatures.json",import.meta.url)));
const scale=name=>actors.find(d=>d.name===name).flags[ID].summonScale;
test("printed summon HP and AC at base and higher slots",()=>{
 for(const [name,level,hp,ac] of [["Aberrant Spirit (Slaad)",4,40,15],["Aberrant Spirit (Slaad)",8,80,19],["Bestial Spirit (Air)",2,20,13],["Bestial Spirit (Land)",4,40,15],["Celestial Spirit (Defender)",5,40,18],["Celestial Spirit (Defender)",9,80,22],["Construct Spirit (Metal)",4,55,17],["Construct Spirit (Metal)",6,85,19],["Fey Spirit (Tricksy)",3,30,15],["Shadow Spirit (Fury)",5,65,16]]){
  const actual=summonStats(scale(name),{level});assert.equal(actual.hp,hp,name);assert.equal(actual.ac,ac,name);assert.equal(actual.damageBonus,level);assert.equal(actual.multiattack,Math.floor(level/2));
 }
});
test("class companions use creator level, ability, and PB",()=>{
 for(const [name,level,mod,pb,hp,ac] of [["Steel Defender",3,3,2,20,15],["Steel Defender",15,5,5,82,17],["Homunculus Servant",2,3,2,6,null],["Dancing Item",6,4,3,40,null],["Wildfire Spirit",2,3,2,15,null],["Beast of the Land",3,3,2,20,15],["Beast of the Sky",15,5,5,64,18]]){
  const s=summonStats(scale(name),{classLevel:level,abilityMod:mod,proficiency:pb});assert.equal(s.hp,hp,name);assert.equal(s.ac,ac,name);assert.equal(s.damageBonus,pb);
 }
 assert.equal(summonStats(scale("Eldritch Cannon (Flamethrower)"),{classLevel:8}).cannonDice,2);
 assert.equal(summonStats(scale("Eldritch Cannon (Flamethrower)"),{classLevel:9}).cannonDice,3);
 assert.equal(summonStats(scale("Eldritch Cannon (Protector)"),{classLevel:3,abilityMod:-1}).cannonHealingBonus,1);
});
test("thresholds change at the printed levels and do not overscale",()=>{
 assert.deepEqual([1,4,5,10,11,16,17,20].map(cantripDice),[1,1,2,2,3,3,4,4]);
 assert.deepEqual([3,4,5,10,11,16,17,20].map(psionicDie),[6,6,8,8,10,10,12,12]);
 assert.deepEqual([3,5,6,14,15,20].map(l=>classThresholds(l).experimentalElixirs),[1,1,2,2,3,3]);
 assert.deepEqual([2,5,6,9,10,13,14,20].map(l=>classThresholds(l).haloDie),[4,4,6,6,8,8,10,10]);
 assert.deepEqual([1,5,6,13,14,20].map(l=>classThresholds(l).favoredFoeDie),[4,4,6,6,8,8]);
 assert.deepEqual([3,9,10,17,18,20].map(l=>classThresholds(l).giantMightDie),[6,6,8,8,10,10]);
});
test("restricted magic-item spell bonuses respect class, equipment and attunement",()=>{
 const gear=(classes,attack,dc,equipped=true,attuned=true)=>({system:{equipped,attunement:"required",attuned},flags:{[ID]:{spellBonus:{classes,attack,dc}}}});
 const actor={classes:{wizard:{},cleric:{}},items:[gear(["wizard"],2,2),gear([],1,1),gear(["cleric"],3,3,false),gear(["wizard"],3,3,true,false)]};
 assert.deepEqual(itemSpellBonus(actor,{system:{sourceItem:"class:wizard"}}),{attack:3,dc:3});
 assert.deepEqual(itemSpellBonus(actor,{system:{sourceItem:"class:cleric"}}),{attack:1,dc:1});
 assert.deepEqual(itemSpellBonus(actor,{system:{sourceItem:""}}),{attack:1,dc:1});
});
test("restoration respects caps and eligible slots",()=>{
 assert.equal(boundedRestore(3,6,5),0);assert.equal(boundedRestore(6,6,2),4);assert.equal(boundedRestore(6,6,-1),6);
 assert.deepEqual(eligibleSlotLevels({spell1:{value:1,max:4},spell2:{value:3,max:3},spell3:{value:0,max:2},spell4:{value:0,max:1},pact:{value:0,max:2}},3),["spell1","spell3"]);
 const items=[{id:"aaaaaaaaaaaaaaaa",name:"Ki",system:{identifier:"ki"}},{id:"bbbbbbbbbbbbbbbb",name:"Channel Divinity",system:{identifier:"channel-divinity-cleric"}}];items.get=id=>items.find(i=>i.id===id);
 assert.equal(resourceItem({items},"ki").id,"aaaaaaaaaaaaaaaa");assert.equal(resourceItem({items},"channel-divinity").id,"bbbbbbbbbbbbbbbb");assert.equal(resourceItem({items},"missing"),null);
});
test("next-turn effects survive the present turn and expire at the named boundary",()=>{
 const made={round:1,turn:2,actorId:"S"},same={...made},next={round:2,turn:2,actorId:"S"},following={round:2,turn:3,actorId:"T"};
 assert.equal(expiredAtTurn("start-source-next-turn",made,null,same,"S","T"),false);
 assert.equal(expiredAtTurn("start-source-next-turn",made,same,next,"S","T"),true);
 assert.equal(expiredAtTurn("end-source-next-turn",made,same,following,"S","T"),false);
 assert.equal(expiredAtTurn("end-source-next-turn",made,next,following,"S","T"),true);
});
test("stored spells use tattoo modifier without changing the actor or original spell",()=>{
 const original={system:{activities:{heal:{healing:{bonus:"@mod",custom:{enabled:false,formula:""}}},damage:{damage:{parts:[{bonus:"2 + @mod",custom:{enabled:false,formula:""}},{custom:{enabled:true,formula:"1d8 + @mod"}}]}}}}};
 const result=storedSpellData(original,4);assert.equal(result.system.activities.heal.healing.bonus,"4");assert.equal(result.system.activities.damage.damage.parts[0].bonus,"2 + 4");assert.equal(result.system.activities.damage.damage.parts[1].custom.formula,"1d8 + 4");assert.equal(original.system.activities.heal.healing.bonus,"@mod");
});
