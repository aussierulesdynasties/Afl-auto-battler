class_name Rating
extends RefCounted
## A player's OVR, read through one door (Director Bible 4.2.30a,
## docs/RATING_REBUILD.md): "Make OVR Strictly a Read-Only Derived Output".
## Phase 1 returns the stored value exactly as p["overall"] and
## p.get("overall", fallback) did, so nothing plays or shows differently.
## Phase 4 works it out from his attributes for his position, and the stored
## field goes; every reader of a player's OVR already comes through here.
## Only player dictionaries come here. A snapshot that keeps an "overall" of
## its own (a match roster row, a draft read, a retirement or medical summary,
## a pick in the draft history) reads its own key.
## Writes of the stored OVR do not come here; Phase 4 removes them.
## Kept free of every autoload.


## His OVR: today the stored value, or `fallback` when he has none.
static func ovr(p: Dictionary, fallback: Variant = null) -> Variant:
	return p.get("overall", fallback)
