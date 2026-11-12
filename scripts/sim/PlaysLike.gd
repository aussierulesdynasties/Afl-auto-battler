class_name PlaysLike
## "Plays like: <real AFL player>" for a draft prospect (director, 2026-11-12:
## "that way if people go far into the future they can still visualise how a
## player will perform even if theyre a fictional player"; "this is not just
## for flavour, it has to be based on facts"; "not just the rating spread but
## also the position and height"; "level must be included").
##
## Three facts decide the name, and nothing else (no dice, no club, no year):
##   1. Position. Only real players of the prospect's own position (DEF, MID,
##      RUCK, FWD) are compared. A database with no real player of that
##      position falls back to every real player.
##   2. The ratings at max potential, level included. The prospect's ratings
##      are lifted evenly until his overall is his POT (as development lifts
##      them); each real player's are set the same way to his own peak (the
##      higher of his POT and his best rated season on record). Real players
##      whose peak overall is within NEAR_LEVEL of the prospect's POT are
##      compared if there is at least one; otherwise the whole position is.
##      The distance is the root-mean-square gap over the rated attributes,
##      in rating points, plus LEVEL_POINTS for each point between the two
##      peak overalls.
##   3. Height. Of those, real players within NEAR_CM of the prospect are
##      compared if there is at least one; otherwise all of them are. Either
##      way each centimetre of difference adds CM_POINTS to the distance.
## Lowest distance wins; a tie goes to the lower id, so the answer never moves.
##
## The real players are the launch lists as loaded (GameDB.plays_like_pool, a
## copy taken before a career ages anyone), so a prospect in 2060 is still
## likened to a 2026 player and a reload gives the same name. Display only:
## nothing in the sim reads it, and every club sees the same line.

## The attributes in the overall rating; temperament is not one of them.
const KEYS := ["disposal", "contested", "marking", "pressure", "intercept", "carry",
		"goalkicking", "accuracy", "creating", "ruck", "durability", "star"]
## "Similar height": real players this close are preferred over all others.
const NEAR_CM := 4.0
## "About his level": a real player whose peak overall is this close to the
## prospect's POT is preferred over all others, of any height.
const NEAR_LEVEL := 5.0
## Rating points one centimetre of height difference is worth.
const CM_POINTS := 0.5
## Rating points one point of peak-overall difference is worth, on top of the
## attribute gap (which already carries the level).
const LEVEL_POINTS := 2.0
const LABEL := "Plays like: "


## A player's ratings at his peak: {id, real_name, generic_name, role, height,
## peak, vec}. `real` uses a listed player's best season on record as well as
## his POT; a prospect's peak is his POT. {} when he has no ratings.
static func profile(p: Dictionary, real := false) -> Dictionary:
	var attr: Dictionary = p.get("attr", {})
	if attr.is_empty():
		return {}
	for key in KEYS:
		if not attr.has(key):
			return {}
	var role := str(p.get("role", "MID"))
	var peak := float(p.get("potential", p.get("overall", 0)))
	if real:
		peak = maxf(peak, Potential.recent_peak(p))
	peak = maxf(peak, float(p.get("overall", 0)))
	var at_peak := Prospects.fit_attributes(attr, role, peak)
	var vec := PackedFloat32Array()
	for key in KEYS:
		vec.append(float(at_peak[key]))
	return {"id": str(p.get("id", "")), "real_name": str(p.get("real_name", "")),
			"generic_name": str(p.get("generic_name", p.get("name", ""))), "role": role,
			"height": float(p.get("height_cm", 0.0)),
			"peak": float(Ratings.rate_overall(at_peak, role, 14.0)), "vec": vec}


## The real players a prospect can be likened to: everyone on the launch lists
## with a real name, a height and ratings from senior games (a list player
## projected from no senior game has a borrowed spread, not his own).
static func build_pool(players: Array) -> Array:
	var out := []
	for p in players:
		if str(p.get("real_name", "")).strip_edges() == "" or bool(p.get("generated", false)) \
				or bool(p.get("projected", false)) or float(p.get("height_cm", 0.0)) <= 0.0:
			continue
		var e := profile(p, true)
		if not e.is_empty():
			out.append(e)
	return out


## The distance between two profiles, in rating points (see the header).
static func distance(a: Dictionary, b: Dictionary) -> float:
	var va: PackedFloat32Array = a["vec"]
	var vb: PackedFloat32Array = b["vec"]
	var sq := 0.0
	for i in range(va.size()):
		sq += (va[i] - vb[i]) * (va[i] - vb[i])
	return sqrt(sq / float(va.size())) + LEVEL_POINTS * absf(float(a["peak"]) - float(b["peak"])) \
			+ CM_POINTS * absf(float(a["height"]) - float(b["height"]))


## The real player `p` plays like, as a pool entry; {} when there is nobody to
## compare him with. Never himself: a real player is not likened to his own name.
static func nearest(p: Dictionary, pool: Array) -> Dictionary:
	var me := profile(p)
	if me.is_empty():
		return {}
	var own_name := str(p.get("real_name", "")).strip_edges()
	var same := []
	var others := []
	for e in pool:
		if str(e["id"]) == str(me["id"]) or (own_name != "" and str(e["real_name"]) == own_name):
			continue
		others.append(e)
		if str(e["role"]) == str(me["role"]):
			same.append(e)
	if same.is_empty():
		same = others
	var level := same.filter(func(e): return absf(float(e["peak"]) - float(me["peak"])) <= NEAR_LEVEL)
	if level.is_empty():
		level = same
	var near := level.filter(func(e): return absf(float(e["height"]) - float(me["height"])) <= NEAR_CM)
	if near.is_empty():
		near = level
	var best := {}
	var best_d := INF
	for e in near:
		var d := distance(me, e)
		if d < best_d or (d == best_d and str(e["id"]) < str(best["id"])):
			best = e
			best_d = d
	return best


## The compared player's name as this career shows names (his real name, or his
## generated one when the coach chose generated names). "" when there is none.
static func name_of(p: Dictionary) -> String:
	var e := nearest(p, GameDB.plays_like_pool)
	return "" if e.is_empty() else GameDB.player_display_name(e)


## "Plays like: Marcus Bontempelli", or "" when there is nobody to compare.
static func line(p: Dictionary) -> String:
	var n := name_of(p)
	return "" if n == "" else LABEL + n
