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
##   2. Level and height together. The prospect's level is his POT; a real
##      player's is his peak (the higher of his POT and his best rated season
##      on record). Real players who are BOTH within NEAR_LEVEL of that POT and
##      within NEAR_CM of his height are compared if there is at least one;
##      otherwise the whole position is, and step 3 charges the excess.
##   3. The ratings at max potential. Each man's ratings are lifted evenly
##      toward his level (as development lifts them) and compared attribute by
##      attribute, as raw rating points. Durability is left out: it says how
##      often he plays, not how. An attribute the prospect is strong in (above
##      his own average) counts for more, so the named player has his
##      strengths. The distance is that weighted root-mean-square gap, plus
##      LEVEL_POINTS for each point between POT and peak, plus CM_POINTS for
##      each centimetre, plus FAR_POINTS for each point beyond NEAR_LEVEL and
##      each centimetre beyond NEAR_CM.
## Lowest distance wins; a tie goes to the lower id, so the answer never moves.
##
## The real players are the launch lists as loaded (GameDB.plays_like_pool, a
## copy taken before a career ages anyone), so a prospect in 2060 is still
## likened to a 2026 player and a reload gives the same name. Display only:
## nothing in the sim reads it, and every club sees the same line.

## The attributes compared: those in the overall rating that say how he plays
## (not durability, and not temperament, which is not in the rating).
const KEYS := ["disposal", "contested", "marking", "pressure", "intercept", "carry",
		"goalkicking", "accuracy", "creating", "ruck", "star"]
## "Similar height": real players this close are preferred over all others.
const NEAR_CM := 4.0
## "About his level": real players whose peak overall is this close to the
## prospect's POT are preferred over all others.
const NEAR_LEVEL := 5.0
## Rating points one centimetre of height difference is worth.
const CM_POINTS := 0.5
## Rating points one point between the prospect's POT and the real player's
## peak is worth, on top of the attribute gap (which carries the level too).
const LEVEL_POINTS := 1.5
## Extra rating points for each centimetre beyond NEAR_CM and each level point
## beyond NEAR_LEVEL, when nobody is inside both.
const FAR_POINTS := 2.0
## Each point an attribute sits above the prospect's own average adds this much
## to that attribute's weight in the gap.
const STRENGTH_WEIGHT := 0.3
const LABEL := "Plays like: "


## A player's ratings at his peak: {id, real_name, generic_name, role, club,
## height, peak, vec}. `peak` is his level: a prospect's POT; for `real`, a
## listed player's best season on record when that is higher. {} when he has
## no ratings.
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
			"club": str(p.get("club", "")), "height": float(p.get("height_cm", 0.0)),
			"peak": peak, "vec": vec}


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


## The gap between two profiles' ratings, in rating points: root-mean-square
## over KEYS, each attribute weighted by how far above `a`'s own average it is.
static func rating_gap(a: Dictionary, b: Dictionary) -> float:
	var va: PackedFloat32Array = a["vec"]
	var vb: PackedFloat32Array = b["vec"]
	var mean := 0.0
	for x in va:
		mean += x
	mean /= float(va.size())
	var sq := 0.0
	var weights := 0.0
	for i in range(va.size()):
		var w := 1.0 + STRENGTH_WEIGHT * maxf(0.0, va[i] - mean)
		sq += w * (va[i] - vb[i]) * (va[i] - vb[i])
		weights += w
	return sqrt(sq / weights)


## The distance from prospect `a` to real player `b`, in rating points (see the header).
static func distance(a: Dictionary, b: Dictionary) -> float:
	var level := absf(float(a["peak"]) - float(b["peak"]))
	var cm := absf(float(a["height"]) - float(b["height"]))
	return rating_gap(a, b) + LEVEL_POINTS * level + CM_POINTS * cm \
			+ FAR_POINTS * (maxf(0.0, level - NEAR_LEVEL) + maxf(0.0, cm - NEAR_CM))


## Whether real player `e` is within NEAR_LEVEL of `me`'s POT and within NEAR_CM of his height.
static func _inside_both(me: Dictionary, e: Dictionary) -> bool:
	return absf(float(e["peak"]) - float(me["peak"])) <= NEAR_LEVEL 			and absf(float(e["height"]) - float(me["height"])) <= NEAR_CM


## The real player `p` plays like, as a pool entry; {} when there is nobody to
## compare him with. Never himself: his own id, or his own real name at his own
## height (two different real players can share a name).
static func nearest(p: Dictionary, pool: Array) -> Dictionary:
	var me := profile(p)
	if me.is_empty():
		return {}
	var own_name := str(p.get("real_name", "")).strip_edges()
	var same := []
	var others := []
	for e in pool:
		if str(e["id"]) == str(me["id"]) or (own_name != "" and str(e["real_name"]) == own_name
				and is_equal_approx(float(e["height"]), float(me["height"]))):
			continue
		others.append(e)
		if str(e["role"]) == str(me["role"]):
			same.append(e)
	if same.is_empty():
		same = others
	var near := same.filter(func(e): return _inside_both(me, e))
	if near.is_empty():
		near = same
	var best := {}
	var best_d := INF
	for e in near:
		var d := distance(me, e)
		if d < best_d or (d == best_d and str(e["id"]) < str(best["id"])):
			best = e
			best_d = d
	return best


## A pool entry's name as this career shows names (his real name, or his
## generated one when the coach chose generated names). Two real players who
## share that name are told apart by club: "Bailey Williams (Eagles)".
static func shown_name(e: Dictionary, pool: Array) -> String:
	var n := GameDB.player_display_name(e)
	for other in pool:
		if str(other["id"]) != str(e["id"]) and GameDB.player_display_name(other) == n:
			return "%s (%s)" % [n, GameDB.club_short(str(e["club"]))]
	return n


## The compared player's name as this career shows it. "" when there is none.
static func name_of(p: Dictionary) -> String:
	var e := nearest(p, GameDB.plays_like_pool)
	return "" if e.is_empty() else shown_name(e, GameDB.plays_like_pool)


## "Plays like: Marcus Bontempelli", or "" when there is nobody to compare.
static func line(p: Dictionary) -> String:
	var n := name_of(p)
	return "" if n == "" else LABEL + n
