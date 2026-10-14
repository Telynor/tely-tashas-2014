"""Build all categories before deterministic packaging and validation."""
import json
def build(b):
 import creatures,spells,magic_items,feats,options,features,reference,teeth
 actors=creatures.build(b)
 spellitems=spells.build(b,actors)
 magic_items.build(b)
 teeth.build(b)
 feats.build(b)
 options.build(b)
 features.build(b,actors,spellitems)
 reference.build(b)
 (b.ROOT/'source/external-spells-required.json').write_text(json.dumps(sorted(b.EXTERNAL_MISSING),indent=2))
