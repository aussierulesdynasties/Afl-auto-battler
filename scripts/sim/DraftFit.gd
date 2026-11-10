class_name DraftFit
extends RefCounted
## Draft fit (row 127, director 2026-11-08): the prospects in a National Draft
## class who suit the way your coach wants to play, by his two archetypes
## (row 119). A mark states the fit as a fact, with your scouts' read and its
## uncertainty as a range, in a recruiter's words (director 2026-11-10):
## "Presses like your side: pressure 72-84".
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

## The lines a Strategic archetype's plan counts (PlanFit.NEEDS): a ruck is
## never marked for the pressing game. Philosophical marks read every line.
const LINES := {
	"DS": ["MID", "FWD"], "TA": ["MID", "FWD", "DEF"],
	"CC": ["MID", "RUCK"], "PC": ["DEF", "MID", "FWD"],
}

## The mark's words, as a recruiter says them (director 2026-11-10): the fit,
## then the rating's name ("" when the fit already names it).
const SUITS := {
	"DS": ["Presses like your side", "pressure"],
	"TA": ["Runs and carries like your side", ""],
	"CC": ["Wins it in close", "contested ball"],
	"PC": ["Looks after the ball", "ball use"],
	"HARD": ["Plays to your standards", "discipline"],
	"ANA": ["Reads the play", ""],
	"FATH": ["A kid to bring on", ""],
	"GAMB": ["A punt", ""],
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
			if LINES.has(id) and not (LINES[id] as Array).has(str(p.get("role", ""))):
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
					"text": "%s: one of the class's highest ceilings" % SUITS[id][0]}
		return {"arch": id, "value": pot, "rated": ov, "half": half, "rank": float(pot - ov),
				"text": "%s: rated %s now, ceiling %s" % [SUITS[id][0],
						DraftScouting.range_text(view["overall"]), DraftScouting.range_text(view["potential"])]}
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
			"text": _text(id, value, half)}


## "Presses like your side: pressure 72-84": the read as a range, as OVR and POT are.
static func _text(id: String, value: int, half: int) -> String:
	var what := str(SUITS[id][1])
	return "%s: %s%d-%d" % [SUITS[id][0], (what + " ") if what != "" else "",
			clampi(value - half, 1, 99), clampi(value + half, 1, 99)]
