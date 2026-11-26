class_name Skills
extends RefCounted
## The 16 skills (director's interview, 2026-11-15, docs/DIRECTOR_BIBLE.md):
## each one is a player's real stats against players of his AFL position.
## Kept free of every autoload, so a save or a trait can read a skill without
## pulling GameDB in (tools/lint/autoload_reach.py).

const KEYS := Attributes.KEYS   # the one list (scripts/sim/Attributes.gd)

## Handballs' share of AFL disposals (the engine's Ratings.T.handball_share).
const HANDBALL_SHARE := 0.44


## Ball use where the engine does not say kick or handball: each weighted by
## its share of AFL disposals.
static func disposal_of(a: Dictionary, fallback := 50.0) -> float:
	return (1.0 - HANDBALL_SHARE) * float(a.get("kicking", fallback)) 			+ HANDBALL_SHARE * float(a.get("handballing", fallback))


## One skill by key, where "disposal" is the derived ball use above (the
## engine's word for kicking and handballing together, never stored).
## What the match engine rolls against (2026-11-16): the skill a coach sees is
## against the player's AFL position, so the engine reads it league-wide, as
## data/engine_scale.csv gives it for his position (tools/wheelo/engine_scale.py:
## his rank in the league on the same stats, on the scale the engine was tuned
## on). A key forward's contested marking 70 out-marks a small defender's 70.
const ENGINE_SCALE_CSV := "res://data/engine_scale.csv"
const KEY_POS_CM := 191.0   # PlayerProfile.KEY_DEF_CM: a player with no AFL position of record
static var _scale := {}


static func engine(p: Dictionary, key: String, fallback := 50.0) -> float:
	var v := value(p.get("attr", {}), key, fallback)
	if _scale.is_empty():
		_load_scale()
	var knots = _scale.get(apos_of(p) + "|" + key)
	if knots == null:
		return v
	var x := clampf(v, 0.0, 100.0) / 10.0
	var i := mini(int(x), 9)
	return lerpf(float(knots[i]), float(knots[i + 1]), x - float(i))


## His AFL position: the one of record, else his line's (a generated or older
## player): key-position size makes a key defender or key forward.
static func apos_of(p: Dictionary) -> String:
	var a := str(p.get("apos", ""))
	if a != "":
		return a
	var tall := float(p.get("height_cm", 0.0)) >= KEY_POS_CM
	match str(p.get("role", "MID")):
		"DEF": return "Key Defender" if tall else "Gen. Defender"
		"FWD": return "Key Forward" if tall else "Gen. Forward"
		"RUCK": return "Ruck"
	return "Midfielder"


static func _load_scale() -> void:
	_scale = {"": null}
	var f := FileAccess.open(ENGINE_SCALE_CSV, FileAccess.READ)
	if f == null:
		return
	f.get_csv_line()
	while not f.eof_reached():
		var row := f.get_csv_line()
		if row.size() < 13:
			continue
		var knots := []
		for i in range(2, 13):
			knots.append(float(row[i]))
		_scale[row[0] + "|" + row[1]] = knots


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
