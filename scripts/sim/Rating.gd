class_name Rating
extends RefCounted
## A player's OVR, read through one door (Director Bible 4.2.30a,
## docs/RATING_REBUILD.md §3): "Make OVR Strictly a Read-Only Derived Output".
## OVR at a position = the stretch (STRETCH) of Σ weight × attribute ÷ 100,
## rounded, his AFL position's weights unless a position is named. Worked out
## whenever it is read, never saved, never fed back into anything that sets an
## attribute.
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


## His headline OVR, or `fallback` when he has no attributes: the best of
## his OVR at his AFL position and his OVR in each second or learned line
## (director 2026-11-28, decision 3: "best OVR across his eligible (apos /
## role2 / learned) positions only (never an unplayed line)"). A Unicorn's
## extra lines are not among them. Selection still rates him at the slot
## (at_line). Example: Peter Wright, Ruck 47 with a second line forward,
## reads 64, his Key Forward OVR.
static func ovr(p: Dictionary, fallback: Variant = null) -> Variant:
	var a: Dictionary = p.get("attr", {})
	if a.is_empty():
		return fallback
	var own := apos_of(p)
	var best := of_attrs(a, own)
	if str(p.get("role2", "")) == "" and (p.get("learned", []) as Array).is_empty():
		return best
	for line in second_lines(p):
		best = maxi(best, best_in_line(a, str(line)))
	return best


## His OVR at his own AFL position only (the position of record), or
## `fallback`.
static func ovr_at_own(p: Dictionary, fallback: Variant = null) -> Variant:
	var a: Dictionary = p.get("attr", {})
	if a.is_empty():
		return fallback
	return of_attrs(a, apos_of(p))


## The lines his own AFL position belongs to (LINE_POSITIONS): a
## Mid-Forward's are the midfield and the forward line, everyone else's one.
static func natural_lines(apos: String) -> Array:
	var out := []
	for line in LINE_POSITIONS:
		if (LINE_POSITIONS[line] as Array).has(apos):
			out.append(line)
	return out


## His second line and any learned, other than his position's own lines:
## where he plays with no out-of-position cut and counts as whichever of the
## line's positions he rates best at (director 2026-11-28, decision 2: "0%
## cut in a learned position, and 0% cut in a natural role2 line").
static func second_lines(p: Dictionary) -> Array:
	var own := natural_lines(apos_of(p))
	var out := []
	var r2 := str(p.get("role2", ""))
	if r2 != "" and not own.has(r2):
		out.append(r2)
	for r in p.get("learned", []):
		var l := str(r)
		if l != "" and not own.has(l) and not out.has(l):
			out.append(l)
	return out


## Every line he plays with no cut: his position's lines, then his second
## and learned lines.
static func uncut_lines(p: Dictionary) -> Array:
	return natural_lines(apos_of(p)) + second_lines(p)


## The best OVR these attributes make at any AFL position of `line`, no cut.
static func best_in_line(a: Dictionary, line: String) -> int:
	var best := 0
	for apos in LINE_POSITIONS.get(line, []):
		best = maxi(best, of_attrs(a, str(apos)))
	return best


## His OVR in each line he plays with no cut, {"FWD": 64, "RUCK": 47}: the
## card's per-line ratings (decision 3).
static func line_ovrs(p: Dictionary) -> Dictionary:
	var out := {}
	var a: Dictionary = p.get("attr", {})
	if a.is_empty():
		return out
	var own := apos_of(p)
	for line in natural_lines(own):
		out[line] = of_attrs(a, own)
	for line in second_lines(p):
		out[line] = best_in_line(a, str(line))
	return out


## His OVR at `apos` (one of POSITIONS).
static func at(p: Dictionary, apos: String) -> int:
	return of_attrs(p.get("attr", {}), apos)


## The stretch (director 2026-11-26, question box): "Keep the 17 attributes
## untouched on the 1-99 scale, and apply a clean monotonic stretch curve
## inside Rating.ovr() when computing the derived OVR number". [weighted sum,
## OVR] points, a straight line between each pair and the end segments' slopes
## past the ends, within 1-99: replacement level 53 reads 62, a solid AFL
## regular 60 reads 72, a star or All-Australian 67 reads 81, a generational
## superstar (2025 Bontempelli) "~72+ raw" reads 89-92: from 72 the climb
## flattens to the best season on record (Jonathan Brown 2006, 86.8), 99.
## Example: a weighted sum of 63.5 reads 72 + 3.5 x 9 / 7 = 76.5, OVR 77;
## Wayne Carey's 1999 (82.3) reads 90 + 10.3 x 0.6 = 96.2, OVR 96.
const STRETCH := [[53.0, 62.0], [60.0, 72.0], [67.0, 81.0], [72.0, 90.0], [87.0, 99.0]]


## The OVR these attributes make at `apos`.
static func of_attrs(a: Dictionary, apos: String) -> int:
	return int(round(stretch(raw_of(a, apos))))


## The weighted sum the stretch reads: Σ weight × attribute ÷ 100.
static func raw_of(a: Dictionary, apos: String) -> float:
	var w: Dictionary = WEIGHTS.get(apos, WEIGHTS["Midfielder"])
	var total := 0.0
	for k in w:
		total += float(w[k]) * float(a.get(k, 0))
	return total / 100.0


## The OVR (unrounded) a weighted sum reads.
static func stretch(raw: float) -> float:
	var i := _segment(raw, 0)
	var a: Array = STRETCH[i]
	return clampf(float(a[1]) + (raw - float(a[0])) * _rise(i), 1.0, 99.0)


## The weighted sum that reads `ovr` (the stretch run backwards).
static func unstretch(ovr: float) -> float:
	var i := _segment(ovr, 1)
	var a: Array = STRETCH[i]
	return float(a[0]) + (ovr - float(a[1])) / _rise(i)


## OVR a weighted point is worth at this weighted sum: 1.43 below a solid
## regular, 1.29 up to a star, 1.8 up to a generational one, 0.6 past him.
static func slope(raw: float) -> float:
	return _rise(_segment(raw, 0))


static func _segment(x: float, col: int) -> int:
	var i := 0
	while i < STRETCH.size() - 2 and x > float(STRETCH[i + 1][col]):
		i += 1
	return i


static func _rise(i: int) -> float:
	var a: Array = STRETCH[i]
	var b: Array = STRETCH[i + 1]
	return (float(b[1]) - float(a[1])) / (float(b[0]) - float(a[0]))


## These attributes moved evenly, whole points, every one but Discipline
## (temperament moves only by XP), by the shift that puts their OVR at `apos`
## nearest `target`: the same footballer a level up or down. Used where a
## director's rule fixes the level and the attributes only reshape: the
## Forge's choices (never buy power), an international's code, a career's
## last falls (Growth.FALL) and "Plays like" at a prospect's POT.
## Example: a Midfielder of OVR 60 to 63 moves every attribute but Discipline
## up 3 (97% of his weights), 60 + 2.9 = 62.9, OVR 63.
static func shift_to(a: Dictionary, apos: String, target: float) -> Dictionary:
	var best := {}
	var best_gap := INF
	var lo := -99
	var hi := 99
	# OVR only rises with the shift: find the first shift that reaches the target.
	while lo < hi:
		var mid := (lo + hi) >> 1
		if of_attrs(_shifted(a, mid), apos) < target:
			lo = mid + 1
		else:
			hi = mid
	for d in [lo - 1, lo]:
		var s := _shifted(a, d)
		var gap := absf(float(of_attrs(s, apos)) - target)
		if gap < best_gap:
			best_gap = gap
			best = s
	return best


static func _shifted(a: Dictionary, d: int) -> Dictionary:
	var out := {}
	for k in a:
		out[k] = int(round(float(a[k]))) if k == "discipline" else clampi(int(round(float(a[k]))) + d, 1, 99)
	return out


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


## The cut he plays under in a spot of `line` (the match-day copy's "role"):
## none in his position's lines, his second line or a learned one (decision
## 2), else his own position's cut to the spot.
static func line_cut(p: Dictionary, line: String) -> float:
	if uncut_lines(p).has(line):
		return 0.0
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
## two groups only). In his own line, his OVR there; in a second or learned
## line, his best OVR at the line's positions with no cut (decision 2).
static func at_line(p: Dictionary, line: String) -> int:
	var a: Dictionary = p.get("attr", {})
	if second_lines(p).has(line):
		return best_in_line(a, line)
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
