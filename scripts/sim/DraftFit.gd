class_name DraftFit
extends RefCounted
## Draft fit (row 127, director 2026-11-08): the prospects in a National Draft
## class who suit the way your coach wants to play, by his two archetypes
## (row 119). A mark states the fit as a fact, with your scouts' read and its
## uncertainty: "Suits your pressing game: pressure 78, scout's read, +/-6".
## It never says take him. Pure rules: the board and the prospect sheet show it.
##
## Each held archetype marks MARKED prospects (director 2026-11-10: 6 a class),
## the top of the class by your scouts' read of what that archetype values, so
## a prospect can carry one mark from each set. Your read uses the same noise
## as the Combine report (DraftScouting), narrowed by your recruiting budget
## and by seeing him in your pre-season match.

const MARKED := 6

## What each archetype values: attribute weights (Strategic weights are
## PlanFit.NEEDS for his plan). FATH and GAMB read the projection instead.
const WEIGHTS := {
	"DS": {"pressure": 1.0},
	"TA": {"carry": 0.6, "disposal": 0.4},
	"CC": {"contested": 1.0},
	"PC": {"disposal": 0.65, "discipline": 0.35},
	"HARD": {"discipline": 1.0},
	"ANA": {"intercept": 0.5, "creating": 0.5},
}

## The mark's words: what it suits, then the rating's name.
const SUITS := {
	"DS": ["Suits your pressing game", "pressure"],
	"TA": ["Suits your territory game", "run and carry"],
	"CC": ["Suits your contested game", "contested ball"],
	"PC": ["Suits your possession game", "ball use"],
	"HARD": ["Suits your standards", "discipline"],
	"ANA": ["Suits how you read the game", "reads the play"],
	"FATH": ["Suits how you bring kids on", "potential"],
	"GAMB": ["Suits your appetite for risk", ""],
}


## The marks in a class for a coach holding `held` ({"s", "p"}), as your club
## `club` reads them: prospect id -> [mark, ...] in set order (Strategic
## first). A mark is {"arch", "value", "half", "text"} (and "rated" for the
## Gambler). Only National Draft prospects (projected) are marked.
static func marks(pool: Array, held: Dictionary, club: String, seed: int, mult := 1.0) -> Dictionary:
	var out := {}
	for set_key in ["s", "p"]:
		var id := str(held.get(set_key, ""))
		if not SUITS.has(id):
			continue
		var reads := []
		for p in pool:
			if not (p is Dictionary) or not bool(p.get("projected", false)):
				continue
			var r := read(p, id, club, seed, mult)
			if not r.is_empty():
				reads.append([p, r])
		reads.sort_custom(func(a, b):
			var ka := float(a[1]["rank"])
			var kb := float(b[1]["rank"])
			if not is_equal_approx(ka, kb):
				return ka > kb
			return str(a[0].get("id", "")) < str(b[0].get("id", "")))
		for pair in reads.slice(0, MARKED):
			var pid := str(pair[0].get("id", ""))
			if not out.has(pid):
				out[pid] = []
			var m: Dictionary = pair[1]
			m.erase("rank")
			out[pid].append(m)
	return out


## Your scouts' read of one prospect for archetype `id`: {"arch", "value",
## "half", "text", "rank"}; {} when he has no football model to read.
static func read(p: Dictionary, id: String, club: String, seed: int, mult := 1.0) -> Dictionary:
	var u := maxf(0.25, float(mult) * DraftScouting.seen_mult(p, club))
	if id == "FATH" or id == "GAMB":
		var view := DraftScouting.projection(p, club, seed, mult)
		var pot := int(view["potential_mid"])
		var ov := int(view["overall_mid"])
		var half := maxi(1, int(round(float(int(view["potential"][1]) - int(view["potential"][0])) / 2.0)))
		if id == "FATH":
			return {"arch": id, "value": pot, "half": half, "rank": float(pot),
					"text": _text(id, "%s %d" % [SUITS[id][1], pot], half)}
		return {"arch": id, "value": pot, "rated": ov, "half": half, "rank": float(pot - ov),
				"text": _text(id, "rated %d, could be %d" % [ov, pot], half)}
	var a: Dictionary = p.get("attr", {})
	if a.is_empty() or not WEIGHTS.has(id):
		return {}
	var score := 0.0
	for k in WEIGHTS[id]:
		score += float(WEIGHTS[id][k]) * float(a.get(k, 50.0))
	var seen := clampf(score + DraftScouting._normal(DraftScouting._key(p, club, seed, "fit_" + id))
			* DraftScouting.COMBINE_NOISE * u, 1.0, 99.0)
	var value := int(round(seen))
	var half := maxi(2, int(round(1.5 * DraftScouting.COMBINE_NOISE * u)))
	return {"arch": id, "value": value, "half": half, "rank": seen,
			"text": _text(id, "%s %d" % [SUITS[id][1], value], half)}


static func _text(id: String, rating: String, half: int) -> String:
	return "%s: %s, scout's read, +/-%d" % [SUITS[id][0], rating, half]
