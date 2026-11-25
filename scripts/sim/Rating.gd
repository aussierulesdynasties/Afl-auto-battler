class_name Rating
extends RefCounted
## A player's OVR, read through one door (Director Bible 4.2.30a,
## docs/RATING_REBUILD.md §3): "Make OVR Strictly a Read-Only Derived Output".
## OVR at a position = Σ weight × attribute ÷ 100, rounded, his AFL position's
## weights unless a position is named. Worked out whenever it is read, never
## saved, never fed back into anything that sets an attribute.
## Only player dictionaries come here. A snapshot that keeps an "overall" of
## its own (a match roster row, a draft read, a retirement or medical summary,
## a pick in the draft history) reads its own key.
## Also the out-of-position cut (§2), which the match applies to Technical and
## Footy IQ attributes. Kept free of every autoload.

const POSITIONS := ["Key Defender", "Gen. Defender", "Midfielder", "Mid-Forward", "Gen. Forward",
		"Key Forward", "Ruck"]

## §3, the starting weights (each position sums to 100). Durability weighs 0
## (priced in Worth); Work Rate has none until step 8 measures the weights.
const WEIGHTS := {
	"Key Defender": {"speed": 5, "endurance": 4, "strength": 10, "kicking": 8, "handballing": 3, "marking": 5,
			"contested_marking": 15, "one_on_one": 25, "reading_play": 15, "pressure": 5, "discipline": 5},
	"Gen. Defender": {"speed": 10, "endurance": 6, "kicking": 15, "handballing": 7, "marking": 10,
			"contested_marking": 5, "one_on_one": 12, "vision": 4, "reading_play": 18, "pressure": 8,
			"discipline": 5},
	"Midfielder": {"speed": 6, "endurance": 10, "strength": 6, "kicking": 12, "handballing": 12, "marking": 4,
			"contested_ball": 22, "goalkicking": 3, "vision": 10, "pressure": 12, "discipline": 3},
	"Mid-Forward": {"speed": 8, "endurance": 5, "kicking": 10, "handballing": 6, "marking": 6,
			"contested_ball": 12, "goalkicking": 12, "vision": 12, "pressure": 12, "forward_craft": 14,
			"discipline": 3},
	"Gen. Forward": {"speed": 10, "endurance": 4, "kicking": 5, "marking": 10, "contested_marking": 5,
			"goalkicking": 18, "vision": 10, "pressure": 14, "forward_craft": 20, "discipline": 4},
	"Key Forward": {"endurance": 4, "strength": 10, "kicking": 5, "marking": 10, "contested_marking": 25,
			"goalkicking": 20, "pressure": 4, "forward_craft": 18, "discipline": 4},
	"Ruck": {"endurance": 8, "strength": 12, "handballing": 5, "contested_marking": 10, "contested_ball": 15,
			"ruck": 40, "pressure": 5, "discipline": 5},
}

## Out of position (§2, director 2026-11-25): the share taken off his
## Technical and Footy IQ attributes while he plays at another AFL position.
## 5% a step along KD, GD, Mid, Mid-Fwd, Gen Fwd, KF; into or out of the ruck
## 25%; KD to KF or KF to KD (swingman) 10%; KD or KF moved to Mid 20%.
## Rows are where he is from, columns where he plays (POSITIONS order).
const OUT_OF_POSITION := {
	"Key Defender": [0, 5, 20, 15, 20, 10, 25],
	"Gen. Defender": [5, 0, 5, 10, 15, 20, 25],
	"Midfielder": [10, 5, 0, 5, 10, 15, 25],
	"Mid-Forward": [15, 10, 5, 0, 5, 10, 25],
	"Gen. Forward": [20, 15, 10, 5, 0, 5, 25],
	"Key Forward": [10, 20, 20, 10, 5, 0, 25],
	"Ruck": [25, 25, 25, 25, 25, 25, 0],
}

## His line is his AFL position's (§2, Lines).
const LINE_OF := {"Key Defender": "DEF", "Gen. Defender": "DEF", "Midfielder": "MID", "Mid-Forward": "MID",
		"Gen. Forward": "FWD", "Key Forward": "FWD", "Ruck": "RUCK"}

## The positions a spot in each line can count as (director 2026-11-25,
## question box: "The line decides"): whichever is closest to his own.
const LINE_POSITIONS := {
	"DEF": ["Key Defender", "Gen. Defender"],
	"MID": ["Midfielder", "Mid-Forward"],
	"FWD": ["Mid-Forward", "Gen. Forward", "Key Forward"],
	"RUCK": ["Ruck"],
}

## A player with no AFL position of record takes his line's: key-position
## size (PlayerProfile.KEY_DEF_CM) makes a key defender or key forward.
const KEY_POS_CM := 191.0


## His OVR at his AFL position, or `fallback` when he has no attributes.
static func ovr(p: Dictionary, fallback: Variant = null) -> Variant:
	var a: Dictionary = p.get("attr", {})
	if a.is_empty():
		return fallback
	return of_attrs(a, apos_of(p))


## His OVR at `apos` (one of POSITIONS).
static func at(p: Dictionary, apos: String) -> int:
	return of_attrs(p.get("attr", {}), apos)


## The OVR these attributes make at `apos`.
static func of_attrs(a: Dictionary, apos: String) -> int:
	var w: Dictionary = WEIGHTS.get(apos, WEIGHTS["Midfielder"])
	var total := 0.0
	for k in w:
		total += float(w[k]) * float(a.get(k, 0))
	return int(round(total / 100.0))


## His AFL position: the one of record, else his own line's (a player made
## in game before he has one). A match-day copy's "role" is the line he
## plays in, so his own is "own_role".
static func apos_of(p: Dictionary) -> String:
	var a := str(p.get("apos", ""))
	if a != "":
		return a
	var tall := float(p.get("height_cm", 0.0)) >= KEY_POS_CM
	match str(p.get("own_role", p.get("role", "MID"))):
		"DEF": return "Key Defender" if tall else "Gen. Defender"
		"FWD": return "Key Forward" if tall else "Gen. Forward"
		"RUCK": return "Ruck"
	return "Midfielder"


## The out-of-position cut, 0..0.25, for a player of `from_apos` playing at
## `to_apos`.
static func cut(from_apos: String, to_apos: String) -> float:
	var row = OUT_OF_POSITION.get(from_apos)
	var i := POSITIONS.find(to_apos)
	if row == null or i < 0:
		return 0.0
	return float(row[i]) / 100.0


## The position a player of `own` counts as in a spot of `line`: the line's
## closest to his own ("The line decides"), except that a key defender or
## key forward anywhere in the midfield is a Midfielder (director
## 2026-11-25, question box: "20%, as you ruled"). An unknown line: his own.
static func spot_position(own: String, line: String) -> String:
	var options: Array = LINE_POSITIONS.get(line, [])
	if options.is_empty() or options.has(own):
		return own
	if line == "MID" and own in ["Key Defender", "Key Forward"]:
		return "Midfielder"
	var best := str(options[0])
	for o in options:
		if cut(own, str(o)) < cut(own, best):
			best = str(o)
	return best


## The cut he plays under in a spot of `line` (the match-day copy's "role").
static func line_cut(p: Dictionary, line: String) -> float:
	var own := apos_of(p)
	return cut(own, spot_position(own, line))


## His position's weights as shares of 1: each attribute's part of his OVR.
static func shares(p: Dictionary) -> Dictionary:
	var out := {}
	var w: Dictionary = WEIGHTS.get(apos_of(p), WEIGHTS["Midfielder"])
	for k in w:
		out[k] = float(w[k]) / 100.0
	return out


## True when some AFL position of `line` weighs `key` in its OVR.
static func line_weighs(line: String, key: String) -> bool:
	for apos in POSITIONS:
		if LINE_OF[apos] == line and (WEIGHTS[apos] as Dictionary).has(key):
			return true
	return false


## His OVR in a spot of `line`: the position the spot counts as
## (spot_position), with his Technical and Footy IQ attributes at (1 - cut)
## (blueprint: AI selection uses "OVR at the slot"; out of position cuts those
## two groups only). In his own line, his OVR there.
static func at_line(p: Dictionary, line: String) -> int:
	var a: Dictionary = p.get("attr", {})
	var own := apos_of(p)
	var spot := spot_position(own, line)
	var c := cut(own, spot)
	if c <= 0.0:
		return of_attrs(a, spot)
	var played := a.duplicate()
	for k in Attributes.TECHNICAL + Attributes.FOOTY_IQ:
		played[k] = float(a.get(k, 0)) * (1.0 - c)
	return of_attrs(played, spot)


## His line, from his AFL position.
static func line_of(apos: String) -> String:
	return str(LINE_OF.get(apos, "MID"))
