/** Pure, independently testable rules. No Foundry globals or document writes. */
export const ID = "tely-tashas-2014";
export const physical = new Set(["bludgeoning", "piercing", "slashing"]);
export function compendiumReferences(value, references=new Set()) {
  if (typeof value === "string") {
    if (/^Compendium\.[\w.-]+$/.test(value)) references.add(value);
    for (const match of value.matchAll(/@UUID\[(Compendium\.[^\]#]+)(?:#[^\]]*)?\]/g)) references.add(match[1]);
  } else if (Array.isArray(value)) {
    for (const child of value) compendiumReferences(child,references);
  } else if (value && typeof value === "object") {
    for (const child of Object.values(value)) compendiumReferences(child,references);
  }
  return references;
}
export function summonStats(scale, { level=1, classLevel=1, abilityMod=0, proficiency=2, cannonImproved=false }={}) {
  let hp, ac;
  if (scale.spell) {
    hp = scale.hpBase + scale.hpPerSlot * (level - (scale.hpReferenceSlot ?? scale.spell));
    ac = scale.acBase + level;
  } else {
    hp = scale.hpBase + scale.hpPerLevel * classLevel + (scale.hpAbility ? abilityMod : 0);
    ac = scale.acPB ? 13 + proficiency : scale.improvedAC ? 15 + (classLevel >= 15 ? 2 : 0) : null;
  }
  return {
    hp: Math.max(1,hp), ac,
    damageBonus: scale.damage === "level" ? level : scale.damage === "pb" ? proficiency : 0,
    multiattack: scale.spell ? Math.floor(level/2) : 1,
    hitDieCount: scale.hitDie ? classLevel : null,
    cannonDice: scale.cannon ? (classLevel >= 9 ? 3 : 2) : null,
    cannonHealingBonus: scale.cannon === "Protector" ? Math.max(1,abilityMod) : null
  };
}
export function cantripDice(level) { return level >= 17 ? 4 : level >= 11 ? 3 : level >= 5 ? 2 : 1; }
export function psionicDie(level) { return level>=17 ? 12 : level>=11 ? 10 : level>=5 ? 8 : 6; }
export function boundedRestore(spent, maximum, amount) { return Math.max(0,Math.min(maximum,spent)-Math.max(0,amount)); }
export function spellClass(item, actor) {
  const source=item?.system?.sourceItem ?? "";
  if (source.startsWith("class:")) return source.slice(6);
  if (source.startsWith("subclass:")) {
    const subclass=actor?.items?.find?.(i=>i.type==="subclass" && i.system.identifier===source.slice(9));
    if(subclass) return subclass.system.classIdentifier;
  }
  const classes=Object.keys(actor?.classes ?? {});
  return classes.length===1 ? classes[0] : "";
}
export function isEquipped(item) {
  return !!item?.system?.equipped && (item.system.attunement!=="required" || !!item.system.attuned);
}
export function itemSpellBonus(actor, item) {
  const cls=spellClass(item,actor);let attack=0,dc=0;
  for(const gear of actor?.items ?? []) {
    if(isEquipped(gear))attack+=Number(gear.flags?.[ID]?.focusAttackBonus??0);
    const bonus=gear.flags?.[ID]?.spellBonus;
    if(!bonus || !isEquipped(gear)) continue;
    if(bonus.classes?.length && !bonus.classes.includes(cls)) continue;
    attack+=bonus.attack ?? 0;dc+=bonus.dc ?? 0;
  }
  return {attack,dc};
}
export function eligibleSlotLevels(slots, maximum) {
  return Object.entries(slots ?? {}).filter(([k,s])=>/^spell[1-9]$/.test(k) && +k.slice(5)<=maximum && s.value<s.max).map(([k])=>k);
}
export function resourceItem(actor, target) {
  if (!target) return null;
  const exact=actor?.items?.get?.(target);
  if (exact) return exact;
  const normalized=s=>String(s??"").toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");
  return actor?.items?.find?.(i=>i.system.identifier===target || normalized(i.name)===target
    || (target==="channel-divinity" && i.system.identifier?.startsWith("channel-divinity-"))) ?? null;
}
export function storedSpellData(data, modifier) {
 const copy=structuredClone(data),replace=value=>typeof value==="string"?value.replace(/@mod\b/g,String(modifier)):value;
 for(const activity of Object.values(copy.system?.activities??{})) {
  for(const part of [...(activity.damage?.parts??[]),...(activity.healing?[activity.healing]:[])]) {
   if(part.bonus!==undefined)part.bonus=replace(part.bonus);
   if(part.custom?.formula!==undefined)part.custom.formula=replace(part.custom.formula);
  }
 }
 return copy;
}
export function expiredAtTurn(rule, created, previous, current, sourceId, targetId) {
  if(!rule || !created || !current) return false;
  const next=(current.round>created.round || current.round===created.round && current.turn>created.turn);
  if(rule==="start-source-next-turn") return next && current.actorId===sourceId;
  if(rule==="end-source-next-turn") return previous?.actorId===sourceId && (previous.round>created.round || previous.round===created.round && previous.turn>created.turn);
  if(rule==="end-source-turn") return previous?.actorId===sourceId;
  if(rule==="end-target-next-turn") return previous?.actorId===targetId && (previous.round>created.round || previous.round===created.round && previous.turn>created.turn);
  return false;
}
export function classThresholds(level) {
  return {
    experimentalElixirs:level>=15?3:level>=6?2:1,
    haloDie:level>=14?10:level>=10?8:level>=6?6:4,
    favoredFoeDie:level>=14?8:level>=6?6:4,
    giantMightDie:level>=18?10:level>=10?8:6,
    clericHarness:level>=18?3:level>=6?2:1,
    paladinHarness:level>=15?3:level>=7?2:1,
  };
}
