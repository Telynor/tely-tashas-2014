/** JournalEntry has no native img field in v14; persist its thumbnail in flags. */
const ID="tely-tashas-2014";
export async function renderJournalIcons(app,html) {
 const pack=app.collection;
 if(pack?.metadata?.packageName!==ID||pack.documentName!=="JournalEntry")return;
 const root=html?.querySelectorAll?html:html?.[0]??app.element;
 if(!root?.querySelectorAll)return;
 await pack.getIndex({fields:[`flags.${ID}.icon`]});
 for(const row of root.querySelectorAll("[data-entry-id], [data-document-id]")) {
  const entry=pack.index.get(row.dataset.entryId??row.dataset.documentId);
  const src=entry?.flags?.[ID]?.icon;
  if(!src)continue;
  let img=row.querySelector("img.thumbnail, img");
  if(!img){img=document.createElement("img");img.className="thumbnail";row.prepend(img);}
  img.src=src;if(img.dataset.src!==undefined)img.dataset.src=src;
  img.alt=entry.name;img.loading="lazy";img.decoding="async";img.width=48;img.height=48;
  Object.assign(img.style,{objectFit:"cover",objectPosition:"top",flex:"0 0 48px"});
 }
}
Hooks.once("init",()=>{
 const field=`flags.${ID}.icon`,fields=CONFIG.JournalEntry.compendiumIndexFields??=[];
 if(fields instanceof Set)fields.add(field);
 else if(!fields.includes(field))fields.push(field);
});
Hooks.on("renderCompendium",(app,html)=>renderJournalIcons(app,html).catch(console.error));
