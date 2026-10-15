# Tely’s Tasha’s Cauldron of Everything — 2014

Unofficial conversion of the supplied **Tasha’s Cauldron of Everything** PDF for **Foundry VTT v14** and the **D&D5e 5.3.3 data architecture**, using 2014 rules. The original book’s choices, replacement features, and restrictions take precedence over automation.

**Preview release 0.1.0.** Offline rules, coverage, link, and LevelDB round-trip checks are included. This release has **not been run in a licensed Foundry world**. It does not claim complete automatic adjudication of every feature.

## Install

In Foundry’s **Add-on Modules → Install Module**, paste:

```
https://github.com/Telynor/tely-tashas-2014/releases/latest/download/module.json
```

Enable the module in a D&D5e world. Use the **2014** rules setting and D&D5e 5.3.3. Later system versions need another runtime check. Midi-QOL is recommended for effect application and damage-dependent helpers; native activities and compendiums work without it, with the GM applying some effects manually.

The release ZIP includes the compiled LevelDB packs and all original-page assets. Installing GitHub’s automatically generated source ZIP alone does not install the compiled module.

## Included content

| Compendium | Entries |
|---|---:|
| Classes | 16: Artificer, 12 2014 SRD class wrappers, 3 sidekick classes |
| Subclasses | All 30 |
| Features, styles, maneuvers, infusions, runes | 303 |
| Feats | All 15 |
| Spells | All 21 |
| Magic items | 102: all 47 base items, variants, 20 implanted teeth, Poisoner support |
| Creatures | 39: every source stat block, summon variants, companions, cannons |
| Roll tables | 67: 32 encoded tables; 35 original-page lookup tables |
| Source journals | All 194 PDF pages plus 4 chapter indexes |
| Player handout journals | 4 |
| Custom lineage | 6 variants, enforcing a single selected ability’s +2 |
| Setup and validation macros | 4 |

Group patrons, puzzles, environmental effects, illustrations, nonrandom tables, and ancillary rules remain accessible through the source journals. The entire original-page image is preserved at twice the PDF page resolution as WebP. Searchable prose comes from the PDF’s OCR layer and can contain OCR errors; the linked page image is authoritative.

## Using the content

- Start characters with the matching **2014 + Tasha Options** class wrapper to receive optional feature choices. Subclasses carry their level-based grants. Fighting styles expand the existing choice, and Pact of the Talisman belongs in Pact Boon. Replacement features prompt before removing the original feature.
- Summon spirits and companions through their linked spell or feature’s **Summon** activity. Dragging an unscaled template directly onto the canvas does not apply its creator’s statistics. Slot/class level controls HP, AC, damage, attack/save matching, and spirit multiattack. Cannons scale at artificer level 9.
- Equip and attune magic items as the source requires. Spell bonuses respect the source class; an unassigned spell on a multiclass actor cannot receive a class-restricted bonus until its source class is set.
- Run **Tasha: Configure a Stored Spell** for a Spellwrought Tattoo. Implant entries must be equipped only while implanted and while attuned to the pouch; the GM tracks pouch limits and drawbacks.
- Run **Tasha: Sidekick Builder** on a selected CR 1/2-or-lower base creature, then apply the class’s Advancement tab. The builder copies the original creature’s hit die and configures Mage, Healer, or Prodigy spell lists. The GM checks the source’s language eligibility and conditional weapon proficiencies.
- Run **Tasha: Resolve External Spells** before creating characters, then **Tasha: Validate Installed Content**. The latter checks installed document validity and links, not full combat behavior.

## Automation boundaries

Native activity objects provide attacks, saves, damage, healing, uses, spell casts, enchantments, and advancement. Helpers handle creator-based summon scaling, actor resource binding, spell-item bonuses, stored spells, elixir creation and next-long-rest expiry, temporary crafted items, selected turn effects, and multi-day recovery. Midi-QOL enables additional effect and actual-damage workflows.

Conditional attacks, movement, auras, trigger eligibility, once-per-turn riders, critical cancellation, substituted damage, artifact consequences, and narrative powers often need GM input. **Use / Review** and source-prompt activities are rule cards or supporting controls; they are not finished end-to-end automation. Only a runtime playtest can confirm Foundry/Midi-QOL timing and workflow compatibility.

The **35 source lookup tables roll the correct die and link the original table**, but do not contain separate structured results. The 32 encoded tables contain 182 individual OCR-derived results with source links. Always consult the original image if OCR looks ambiguous.

Twelve referenced spells are defined outside this uploaded sourcebook and the bundled SRD spell compendium: Arcane Gate, Arms of Hadar, Aura of Life, Aura of Purity, Aura of Vitality, Banishing Smite, Circle of Power, Conjure Barrage, Dissonant Whispers, Hunger of Hadar, Phantasmal Force, and Ray of Sickness. The resolver uses your installed 2014 spell entries for subclass grants. Item casting and spellbook helpers resolve installed spells on use. Their definitions are not invented or silently replaced with 2024 rules.

See [the per-entry audit](docs/content-audit.csv), [offline validation](docs/validation-report.json), [pack round-trip report](docs/pack-validation.json), and [runtime acceptance checklist](docs/RUNTIME-TESTS.md).

The recovery pass passed 14 automated regression tests, 7,693 offline data checks, and round-trip compilation of all 805 documents across the 12 packs. Steady Aim now grants advantage only on the next attack while retaining its restriction on every movement speed through the end of the turn. Effects that last through a target's next turn no longer expire during the turn in which they were applied. Installed-content validation checks missing packs, embedded documents, spell casts, advancement choices, and source links.

## Rebuilding

Download **tely-tashas-2014-source.zip** from Releases and extract it into your checkout. It contains the extracted source data and reviewable generated JSON. Install Node.js 22+ and Python 3.12+, then:

```sh
npm install
python -m pip install -r requirements.txt
python tools/build.py
npm run build:packs
npm test
npm run package
```

In the source archive, `source/` contains the extracted inventory, original OCR pages, spell reference index, table extraction, and vendored 2014 SRD class inputs. `content/` contains reviewable generated JSON; `packs-src/` is regenerated by the Python builder. The Git repository holds the code, manifest, tests, documentation, and audit. Pack compilation uses the official Foundry CLI and round-trips every document, including embedded actor items, effects, journal pages, and table results.

Original page artwork is distributed in the release ZIP rather than Git. Extract its `assets/` directory into this checkout before packaging. To regenerate images from the supplied PDF, run `python tools/render_pages.py --pdf /absolute/path/to/source.pdf`. Source extraction also accepts `--pdf`. No sourcebook content is downloaded from other websites during building.

This project is unofficial and is not affiliated with Foundry Gaming or Wizards of the Coast. See [NOTICE.md](NOTICE.md) for content attribution.
