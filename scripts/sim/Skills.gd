class_name Skills
extends RefCounted
## The 16 skills (director's interview, 2026-11-15, docs/DIRECTOR_BIBLE.md):
## each one is a player's real stats against players of his AFL position.
## Kept free of every autoload, so a save or a trait can read a skill without
## pulling GameDB in (tools/lint/autoload_reach.py).

const KEYS := ["kicking", "handballing", "contested_marking", "uncontested_marking",
		"contested", "pressure", "intercept", "speed", "carry", "goalkicking", "accuracy",
		"creating", "ruck", "discipline", "durability", "star"]

## Handballs' share of AFL disposals (the engine's Ratings.T.handball_share).
const HANDBALL_SHARE := 0.44


## Ball use where the engine does not say kick or handball: each weighted by
## its share of AFL disposals.
static func disposal_of(a: Dictionary, fallback := 50.0) -> float:
	return (1.0 - HANDBALL_SHARE) * float(a.get("kicking", fallback)) 			+ HANDBALL_SHARE * float(a.get("handballing", fallback))


## One skill by key, where "disposal" is the derived ball use above (the
## engine's word for kicking and handballing together, never stored).
static func value(a: Dictionary, key: String, fallback := 50.0) -> float:
	if key == "disposal":
		return disposal_of(a, fallback)
	return float(a.get(key, fallback))


## A save from before the 16 skills (2026-11-15): disposal becomes kicking and
## handballing, marking both markings, and speed starts at the middle.
static func migrate(a: Dictionary) -> void:
	if a.has("disposal"):
		for k in ["kicking", "handballing"]:
			if not a.has(k):
				a[k] = a["disposal"]
		a.erase("disposal")
	if a.has("marking"):
		for k in ["contested_marking", "uncontested_marking"]:
			if not a.has(k):
				a[k] = a["marking"]
		a.erase("marking")
	for k in KEYS:
		if not a.has(k):
			a[k] = 50
