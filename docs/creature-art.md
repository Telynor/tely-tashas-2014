# Creature artwork in 0.1.2

All 39 creature entries have official D&D artwork with an alpha channel, assigned to both the actor portrait and prototype token. The release includes 29 illustration files. D&D Beyond was searched first; 23 files come from its public monster pages and official articles, four from the supplied Tasha's sourcebook, one from original illustrator Christopher Burdett, and one from a mirror of the official 2014 Monster Manual Red Slaad illustration after its D&D Beyond page redirected to the marketplace.

The complete [asset manifest](official-creature-art.json) maps every creature name to its installed `modules/tely-tashas-2014/assets/creatures/` path. It records original URLs, sourcebook page and image references, identified artists, processing methods, and original/final SHA-256 hashes. The per-entry [image audit](icon-audit.csv) includes portraits, tokens and embedded images.

Open-ended spirits and companions use official art of an allowed representative form. Land and air companions share wolf and eagle illustrations with the corresponding bestial spirits; water companions share the shark cutout. Beholderkin use a spectator, the Slaad form uses a red slaad, and the Star Spawn form uses a mangler. The Dancing Item uses animated armor. Golems, elementals, fiends, undead, and the juvenile mimic use the matching official form. Mood and equipment variants can share one illustration. Artwork selection changes no creature statistics, document IDs, or 2014 rules.

Seventeen original files retain their existing transparency and pixels. Twelve illustrations were edited with the built-in **imagegen** tool, using `transparent_background: true`, one request per subject. Those cutouts are AI-edited derivatives of the cited official illustrations; they are not publisher-supplied transparent files. The original illustrations remain copyright Wizards of the Coast and their respective artists. Identified artists include Michael Broussard, John Thacker, and Christopher Burdett.

## Background-extraction prompt set

Every request used `Use case: background-extraction`, identified the supplied image as the edit target, requested a single transparent PNG for a Foundry portrait/token, and required preservation of the existing subject, pose, palette, brushwork, lighting and anatomy. Each requested actual alpha transparency with no added border, badge or ground shadow. The subject-specific requests were:

| Output file | Extraction request |
|---|---|
| `steel-defender.png` | Extract only the mechanical dog in the lower foreground. Remove the human Battle Smith, room and frame. Keep the blue eye, metal plates, curled tail and original portrait crop; invent no missing limbs. |
| `homunculus-servant.png` | Extract only the top-center brass-and-wood owl, preserving both spread wings, owl head, torso, feet and tail. Remove the other three servants and paper/paint backdrop. |
| `wildfire-spirit.png` | Extract only the glowing orange fox on the right. Remove the druid, staff, ground shadow and white backdrop. Preserve its pose, tail, ears, flame wisps and translucent edges. |
| `celestial-spirit.png` | Extract only the glowing-eyed angel on the left. Remove the elf, clouds, scenery, rules text and scanned-page artifacts. Preserve its wings, gold-edged garment and visible anatomy. |
| `shadow-spirit.png` | Extract only the huge three-faced foreground spirit, including both long arms and lower body. Remove the warlock, cathedral, floor, paint border and caption. Preserve all screaming faces and mottled surface. |
| `eldritch-cannon.png` | Extract only the brass cannon with its blue chamber. Remove the Artillerist and hands, room and frame. Preserve the visible mechanical detail and original barrel crop; add no machinery or legs. |
| `mighty-servant-of-leuk-o.png` | Remove the paper, purple paint backdrop and floor shadow. Preserve the complete black-and-gold construct, pose, fists, barrel torso, short legs and attached purple energy. |
| `land-beast.png` | Remove only the snow/ground strip and shadow beneath the wolf. Preserve the entire existing animal, fur, face, ears, four legs and tail. |
| `water-beast.png` | Extract only the large foreground shark. Remove the four smaller sharks, water, bubbles, plants and scenery. Preserve its open mouth, teeth, fins, curved tail and painted details. |
| `star-spawn.png` | Remove the white backdrop. Preserve the mangler's six separate arms and six clawed hands, both legs, head, loincloth and mottled skin. Frame out outer credit margins; preserve the nearby artist signature where it remains in the subject area. Retain the artist credit in the asset manifest. |
| `slaad.png` | Preserve the existing crouched red slaad, clawed arms, legs, face and green mottling. Remove remaining background and rectangular decoding artifacts outside its silhouette; produce a clean transparent PNG. |
| `fey-spirit.png` | Remove only the rock platform, floor and shadow. Preserve the satyr's horns, face, red waistcoat, panpipes, belt, sheath, bent leg and visible hoof shapes. |

The builder requires a mapping for every creature. Offline validation checks source provenance, file hashes, real alpha channels, visible foreground, clear background area and portrait/token parity. Visual review covers the images on light and dark surfaces. The source archive contains the artwork manifest; reuse the installation ZIP's `assets/` directory when rebuilding.
