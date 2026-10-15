# 0.1.2

Replace every creature portrait and prototype token image with official D&D artwork on a transparent background: 39 entries, 29 illustrations. Prioritize D&D Beyond, preserve its original alpha files, and extract creature cutouts from scene illustrations using the built-in imagegen tool. Document sources, artist credits, output hashes and representative form choices. Check complete actor mapping, token parity, asset integrity and actual alpha channels during validation. All document IDs and rules data remain unchanged.

# 0.1.1

Assign themed images to all 805 compendium entries. Prefer the official printed illustrations for magic items and their variants: 13 illustrations cover 15 base items, with the collection artwork also used on implanted teeth. Include icons on creature items, activities, active effects, token textures, and roll-table results. Use original page artwork for reference and handout thumbnails, with a v14-compatible journal-index render helper. Verify every selected icon against the official D&D5e 5.3.3 source catalog, generate a full image audit, and reject missing or placeholder images during validation. Document IDs and rules data remain unchanged.

# 0.1.0

Initial preview conversion of the supplied 2014 Tasha’s Cauldron of Everything PDF. Twelve LevelDB compendiums, all original pages, class advancement, spell and item activities, creature attacks, companion scaling, and audited supporting controls.

Static validation and compiler round-trip completed; live Foundry v14 and Midi-QOL acceptance testing remains outstanding. Complex GM-adjudicated powers and source lookup tables are explicitly identified in the README and audit.

Publication recovery: restored the installable archive and complete rebuild sources. Fixed Steady Aim's one-attack limit and all movement restrictions, next-turn expiration during the target's current turn, and conditional-effect refresh after deleting equipment. Expanded installed-content validation to detect missing packs, invalid embedded documents, and unresolved choice, spell, summon, and journal references. Fourteen regression tests, 7,693 offline checks, and all 805 LevelDB round trips pass.
