class_name Prospects
extends RefCounted
## End-of-season intake support: draft-class projections, generated future
## classes, and season-over-season development (growth, decline, retirement).
##
## Draftees have no AFL season stats, so their ratings are PROJECTED rather
## than derived: a consensus-rank band sets a target overall, a role template
## and the prospect's reported U18 numbers shape the attribute profile, and a
## bisection fits those attributes to the target through the shipped
## Ratings model. From there the match engine treats prospects exactly like
## real players - same attributes, roles, salary bands and maths.
##
## The 2026 class ships from data/draftees_2026.csv; every later class is
## generated deterministically from its year so careers can loop forever.

const MAX_RETIRE_PER_CLUB := 8
## The youngest a real player of a Legacy start can be in his last real
## season for that season to count as his retirement (should_retire). Younger,
## he was delisted: his contract ends then (real_delisting_due).
const REAL_RETIRE_AGE := 27.0
## Generated forwards run from small (172 cm) to key (203 cm), about a third
## of each by MatchSim.fwd_size, as in a real draft class: from 184 cm there
## were no small forwards, and over a career the league's forward lines
## turned tall (ARD-M3-002).
const FWD_MIN_CM := 172

const ATTR_KEYS := Attributes.KEYS

## Consensus-rank taper: pick 1 projects as an impact rookie, the back half of
## the draft as fringe/development talent. Deliberately below the best 2026
## pros (90s) - a top pick should enter the list around a solid rotation
## player, and the training/development loop carries them up from there.
const RANK_BANDS := [[1, 70.0], [10, 64.0], [20, 61.0], [30, 58.0],
		[40, 55.0], [50, 52.0], [64, 47.0]]

## Future classes differ year to year as a cohort, not only player by
## player. Most years are ordinary; a strong crop lifts the top end most,
## the depth a little and the ceilings of its best prospects; a superdraft
## does that harder; a weak one the reverse. Busts, role spread and ordinary
## late picks stay, because each prospect's own rolls are unchanged.
##   [key, chance, top-end shift, depth shift, ceiling shift]
## The top-end shift is full at pick 1 and tapers to the depth shift by
## CLASS_TOP_RANKS; the ceiling shift (extra POT room) tapers to nothing by
## the same rank. The real 2026 class is data, never tiered.
const CLASS_TIERS := [
	["weak", 0.10, -3.0, -1.5, -3.0],
	["below", 0.20, -1.5, -0.5, -1.5],
	["normal", 0.50, 0.0, 0.0, 0.0],
	["strong", 0.17, 2.0, 1.0, 3.0],
	["super", 0.03, 4.5, 2.0, 9.0],
]
const CLASS_TOP_RANKS := 30

## Draft-night rating scale for every draft class (director 2026-10-14, "A: gentle": young
## draftees arrive lower and climb like real AFL ones; 2026-11-04, 4.Q9 / row 65: picks 1-5
## about 60-62, picks 6-20 about 55-58, POT kept). 1.0 is the old curve. New draft classes use
## it, generated and the real 2026 class alike (`draft_class`); players already on a list are
## not rescaled. The rank-base rating is multiplied by this and the points taken off are added
## back to the prospect's room, so his POT (his ceiling) does not move.
## (static var, not const, only so tools/audit can try arms in one run.)
static var DRAFT_NIGHT_SCALE := 0.87
## Readiness (director 2026-10-13: "some players are more ready-made than others"): with the scale
## below 1, a few prospects keep most of the old draft-night rating (ready-made: senior footy in
## year 1, less climb left), most lose it all, and some lose more (long-term projects, a big
## climb). Over-age prospects are likelier to be ready-made. The class average drop is unchanged.
static var DRAFT_READINESS := true
const READY_DROP := [0.25, 0.93, 1.5]  # share of the drop kept: ready-made, typical, project


## 0 ready-made, 1 typical, 2 project: seeded by the prospect alone.
static func readiness(p: Dictionary) -> int:
	var rng := _rng_for("ready|%s|%s" % [str(p.get("id", "")), str(p.get("draft_year", 2026))])
	var roll := rng.randf()
	var over_age := float(p.get("age", 18.0)) >= 19.0
	var ready_p := 0.40 if over_age else 0.08
	var project_p := 0.10 if over_age else 0.32
	if roll < ready_p:
		return 0
	if roll < ready_p + project_p:
		return 2
	return 1

const ROLE_DELTAS := {
	"MID": {"kicking": 6.0, "handballing": 6.0, "contested": 5.0, "pressure": 3.0, "carry": 4.0,
			"creating": 2.0, "contested_marking": -1.0, "uncontested_marking": -1.0, "goalkicking": -3.0, "intercept": 0.0,
			"accuracy": -4.0, "discipline": -1.0, "star": 0.0, "speed": 0.0, "durability": 0.0,
			"ruck": -30.0},
	"DEF": {"intercept": 8.0, "pressure": 6.0, "contested_marking": 4.0, "uncontested_marking": 4.0, "kicking": 1.0, "handballing": 1.0,
			"accuracy": -5.0, "goalkicking": -8.0, "creating": -4.0, "carry": -3.0,
			"contested": 1.0, "discipline": 0.0, "star": 0.0, "speed": 0.0, "durability": 0.0,
			"ruck": -30.0},
	"FWD": {"goalkicking": 8.0, "contested_marking": 5.0, "uncontested_marking": 5.0, "accuracy": 3.0, "creating": 4.0,
			"kicking": -1.0, "handballing": -1.0, "intercept": -4.0, "pressure": 2.0, "carry": 1.0,
			"contested": 0.0, "discipline": 0.0, "star": 0.0, "speed": 0.0, "durability": 0.0,
			"ruck": -24.0},
	"RUCK": {"ruck": 26.0, "contested": 8.0, "contested_marking": 3.0, "uncontested_marking": 3.0, "kicking": -5.0, "handballing": -5.0,
			"goalkicking": -1.0, "intercept": -3.0, "pressure": 0.0, "carry": -5.0,
			"accuracy": -5.0, "creating": -2.0, "discipline": -2.0, "star": 0.0,
			"speed": 0.0, "durability": 1.0},
}

const JUNIOR_TEAMS := [
	["Sandringham Dragons", "Talent League", "VICM"],
	["Northern Knights", "Talent League", "VICM"],
	["Dandenong Stingrays", "Talent League", "VICC"],
	["Gippsland Power", "Talent League", "VICC"],
	["Eastern Ranges", "Talent League", "VICM"],
	["Calder Cannons", "Talent League", "VICM"],
	["Oakleigh Chargers", "Talent League", "VICM"],
	["GWV Rebels", "Talent League", "VICC"],
	["Bendigo Pioneers", "Talent League", "VICC"],
	["Geelong Falcons", "Talent League", "VICC"],
	["Murray Bushrangers", "Talent League", "VICM"],
	["Swan Districts", "WAFL", "WA"],
	["Claremont", "WAFL", "WA"],
	["East Perth", "WAFL", "WA"],
	["Subiaco", "WAFL", "WA"],
	["South Adelaide", "SANFL", "SA"],
	["North Adelaide", "SANFL", "SA"],
	["Woodville-West Torrens", "SANFL", "SA"],
	["Central District", "SANFL", "SA"],
	["Glenelg", "SANFL", "SA"],
	["West Adelaide", "SANFL", "SA"],
	["Lions Academy", "Talent League", "QLD"],
	["Suns Academy", "Talent League", "QLD"],
	["GIANTS Academy", "Talent League", "NSW"],
	["AS Academies", "Talent League", "NSW"],
	["Tasmania Devils", "Talent League", "TAS"],
]


# ---------------------------------------------------------------------------
# Projection
# ---------------------------------------------------------------------------
## A listed player with under FEW_GAMES senior games is rated from his real
## draft pick on the prospect scale (rank_base_overall); with no pick, 80 in
## 100 are bad (42-47), 18 role players (53-58) and 2 gems (63-68). His skills
## are borrowed from a real player of his role at that level (project), and he
## keeps the rating for life, growing only by XP, like a kid drafted in a save
## (director 2026-11-17).
const FEW_GAMES := 10
const NO_PICK_TIERS := [[80, 42, 47], [18, 53, 58], [2, 63, 68]]


## His senior games before the save: his AFL career, plus the data season's
## games when the career column stops before it. -1 when his career is unknown.
static func senior_games(p: Dictionary, data_season: int) -> int:
	var c = p.get("career")
	if not (c is Dictionary):
		return int(p.get("gm", 0.0))
	if not (c.get("unknown", []) as Array).is_empty():
		return -1
	var last := 0
	for s in c.get("stints", []):
		last = maxi(last, int(s[2]))
	var games := int(c.get("games", 0))
	if last < data_season:
		games += int(p.get("gm", 0.0))
	return games


## The set rating of a player of few games: his pick on the prospect scale,
## or a seeded roll on NO_PICK_TIERS.
static func few_games_rating(p: Dictionary) -> float:
	var pick := int(p.get("drafted_pick", 0))
	if pick > 0:
		return rank_base_overall(pick)
	var rng := _rng_for("%s|nopick" % str(p.get("id", "")))
	var roll := rng.randi_range(1, 100)
	var acc := 0
	for t in NO_PICK_TIERS:
		acc += int(t[0])
		if roll <= acc:
			return float(rng.randi_range(int(t[1]), int(t[2])))
	return float(NO_PICK_TIERS[0][1])


## Rate a player of few games on few_games_rating: projected for life.
static func project_few_games(p: Dictionary) -> void:
	p["fixed_target"] = few_games_rating(p)
	p["draft_rank"] = int(p.get("drafted_pick", 0))
	project(p)
	p.erase("fixed_target")


## Piecewise-linear rank taper with a floor; ranks beyond the list keep
## sliding down so generated classes and bubble names use the same curve.
static func rank_base_overall(rank: int) -> float:
	if rank <= 1:
		return float(RANK_BANDS[0][1])
	var prev_r := int(RANK_BANDS[0][0])
	var prev_v := float(RANK_BANDS[0][1])
	for band in RANK_BANDS.slice(1):
		var r := int(band[0])
		var v := float(band[1])
		if rank <= r:
			return prev_v + (v - prev_v) * float(rank - prev_r) / float(r - prev_r)
		prev_r = r
		prev_v = v
	return maxf(42.0, prev_v - float(rank - prev_r) * 0.18)


## Mutates a prospect dict with projected attr / role / overall / value.
static func project(p: Dictionary) -> void:
	var rng := _rng_for("%s|%s" % [str(p.get("id", "")), str(p.get("draft_year", 2026))])
	var rank := int(p.get("draft_rank", 0))
	var role := str(p.get("role", "MID"))
	var target := rank_base_overall(rank)
	# A listed player of few games is rated on a set number (few_games_rating):
	# no draft night, no junior numbers, no age step or noise on it.
	var fixed := float(p.get("fixed_target", 0.0))
	p.erase("night_drop")
	if DRAFT_NIGHT_SCALE != 1.0 and (p.has("class_shift") or bool(p.get("draft_class", false))):
		var drop := target * (1.0 - DRAFT_NIGHT_SCALE)
		if DRAFT_READINESS:
			var rd := readiness(p)
			drop *= float(READY_DROP[rd])
			p["readiness"] = ["ready", "typical", "project"][rd]
		target -= drop
		p["night_drop"] = drop

	# Reported U18 production lifts the floor, capped so a stat-stuffing
	# Talent League season can never out-project a 20-game AFL pro.
	var gm := float(p.get("u18_gm", 0.0))
	var di := float(p.get("u18_di", 0.0))
	var gl := float(p.get("u18_gl", 0.0))
	var ho := float(p.get("u18_ho", 0.0))
	var tk := float(p.get("u18_tk", 0.0))
	var mk := float(p.get("u18_mk", 0.0))
	if di >= 18.0:
		target += minf(3.0, (di - 18.0) * 0.25)
	if role == "FWD" and gl >= 1.5:
		target += minf(3.0, (gl - 1.5) * 0.8)
	if role == "RUCK" and ho >= 15.0:
		target += minf(3.0, (ho - 15.0) * 0.15)
	if tk >= 5.0:
		target += minf(2.0, (tk - 5.0) * 0.3)
	if (role == "DEF" or role == "FWD") and mk >= 5.0:
		target += minf(2.0, (mk - 5.0) * 0.25)
	var height := float(p.get("height_cm", 0.0))
	if role == "RUCK":
		if height >= 200.0:
			target += 1.5
		elif height > 0.0 and height < 192.0:
			target -= 1.5
	elif height >= 190.0 and (role == "FWD" or role == "DEF"):
		target += 1.0
	var age := float(p.get("age", 18.0))
	if age >= 19.0:
		target += 1.0  # over-age means proven, at a small trade-off in ceiling
	target += rng.randf_range(-1.5, 1.5)
	target += float(p.get("class_shift", 0.0))
	if fixed > 0.0:
		target = fixed
	var unscaled := target + float(p.get("night_drop", 0.0))
	target = clampf(target, 38.0, 74.0)
	if p.has("night_drop"):
		# Only the points actually taken off count (the floor stops the lowest picks).
		p["night_drop"] = clampf(unscaled, 38.0, 74.0) - target

	# Attributes: centre on the target with the shape of a real player of his
	# role (a specialist's spike and weak spot, not a flat template - director,
	# 2026-10-06: "widen player spread"), then let the raw season numbers nudge
	# the parts the projection actually claims. The fit below puts him back on
	# his target, so only the shape is borrowed, never the level.
	var a := {}
	# Borrowed from someone at the level he's expected to grow to (his likely
	# ceiling: Potential's draftee room), since development lifts every
	# attribute alike - a grown prospect then looks like a real player there.
	# The draft-night drop is added back: it lowers where he starts, not where he can grow to.
	var level := target + float(p.get("night_drop", 0.0)) + maxf(6.0, 22.0 - 0.25 * float(clampi(rank, 1, 80) - 1)) \
			+ float(p.get("class_ceiling", 0.0))
	# The game's own generated players copy a real player of 2012-2026 with his
	# fingerprint (director, 2026-11-17); real-list players and a coach's Forge
	# prospect copy from the start's lists as before.
	var shape := _copy_for(role, rng, level, p) if _is_game_made(p) else _shape_for(role, rng, level)
	for key in ATTR_KEYS:
		a[key] = target + float(shape.get(key, 0.0))
	# Temperament is his own: a donor's poor discipline on a lesser prospect
	# made hotheads of half the class. (Star and durability stay borrowed:
	# setting them apart moved the fit, which pulled every skill down.)
	a["discipline"] = target + float((ROLE_DELTAS.get(role, ROLE_DELTAS["MID"]) as Dictionary).get("discipline", 0.0))
	if di > 0.0:
		var use := clampf((di - 16.0) * 0.4, -2.0, 5.0)
		a["kicking"] = float(a["kicking"]) + use
		a["handballing"] = float(a["handballing"]) + use
	if gl > 0.0:
		a["goalkicking"] = float(a["goalkicking"]) + clampf((gl - 1.2) * 1.1, -1.5, 6.0)
	if mk > 0.0:
		a["uncontested_marking"] = float(a["uncontested_marking"]) + clampf((mk - 3.0) * 0.75, -1.0, 4.0)
	if ho > 0.0 and role == "RUCK":
		a["ruck"] = float(a["ruck"]) + clampf((ho - 10.0) * 0.4, 0.0, 7.0)
	if tk > 0.0:
		a["pressure"] = float(a["pressure"]) + clampf((tk - 3.0) * 0.5, 0.0, 4.0)

	# An international's code shapes his game (Gaelic footballers kick, rugby
	# players contest); absent for everyone else, so nothing moves for them.
	var bias: Dictionary = p.get("attr_bias", {})
	for key in bias:
		a[key] = float(a.get(key, target)) + float(bias[key])
	# Only the game's own generated players: real-list players projected from no
	# senior game, the real draft class and a coach's Forge prospect stay as they were.
	if _is_game_made(p):
		_real_trait_rates(a, p, role)

	a = fit_attributes(a, Rating.apos_of(p), target)
	for key in a:
		a[key] = int(a[key])
	p["attr"] = a
	p["projected"] = true
	p["sample"] = 14.0
	p.erase("potential")  # re-projection re-derives it (deterministically)
	Potential.assign(p)


## Row 104 (4.Q10, director): generated players carry each synergy trait at the real
## players' rate at the same overall, contested bulls included, and a real share of
## hotheads (there were none: temperament came from his projected rating, never 20 or
## below).
## Per role, points added to an attribute before the fit puts him back on his target
## (so his overall does not move, only his shape). Sized with tools/audit/gen_traits_impl.gd
## so a grown generated player carries each trait as often as a real player of his overall:
## interceptors and aerial forwards came out too often, lockdown and defensive forwards
## too rarely. (static var, not const, only so tools/audit can try arms in one run.)
static var GEN_NUDGE := {
	"DEF": {"intercept": -6.0, "pressure": -0.5, "accuracy": 1.0, "durability": -1.5},
	"MID": {"contested": -6.0, "kicking": -2.0, "handballing": -2.0, "pressure": -1.0, "durability": -1.5},
	"FWD": {"contested_marking": -3.0, "pressure": 3.5, "accuracy": 1.0, "goalkicking": 1.5, "durability": -1.5},
	"RUCK": {"ruck": -10.0, "contested": -6.0, "durability": -1.5},
}


## Row 104: his temperament is a real player's of his role (each real player's own
## discipline, not relative to his rating), so hotheads come at the real share; and the
## GEN_NUDGE shape correction. Seeded by the prospect alone, on its own dice, so nothing
## else about him rolls differently.
static func _real_trait_rates(a: Dictionary, p: Dictionary, role: String) -> void:
	for key in (GEN_NUDGE.get(role, {}) as Dictionary):
		a[key] = float(a.get(key, 0.0)) + float(GEN_NUDGE[role][key])
	# His temperament is a real 2012-2026 player's too (none before 2012, director 2026-11-17).
	var pool: Array = (_copy_pool().get(role, {}) as Dictionary).get("disc", [])
	if pool.is_empty():
		return
	var rng := _rng_for("disc|%s|%s" % [str(p.get("id", "")), str(p.get("draft_year", 2026))])
	a["discipline"] = float(pool[rng.randi_range(0, pool.size() - 1)])


## Each role's real players' shapes: every attribute less his overall, and that
## overall ("_ovr"), from the 2026 lists (GameDB's own rows, in list order, so
## it's the same every run).
static var _shapes := {}
## How many of the nearest real players, by overall, a shape is drawn from.
const SHAPE_NEAREST := 10


## Forget the cached shapes: a new career rebuilds them from the 2026 players.
## (The 2012-2026 copy pool is fixed data and stays loaded.)
static func forget_cache() -> void:
	_shapes = {}


## The real players a game-made player is copied from (director, 2026-11-17: "im happy
## for generated players to be based on real players, but we have to make sure that they
## arent based on players pre-2012"; which seasons: "every other year"): every player of
## every AFL season 2012-2026, each season rated on its own (tools/wheelo/copy_pool.py).
const COPY_POOL_CSV := "res://data/copy_pool.csv"
## His fingerprint (director, 2026-11-17: "10% different ... to give a fingerprint", then
## "5%"): each of the copied player's skills times its own roll between 0.95 and 1.05.
const FINGERPRINT := 0.05
## Per role: "rows" (each a real player-season's skills, "_ovr", "_year", his Wheelo "_id",
## "_name", "_club" and "_height", 0 when unknown), sorted by overall,
## "ovr" (those overalls, for the search) and "disc" (their disciplines).
static var _copy := {}


## The game's own generated players: a draft class, an expansion list, a state-league
## depth pool. Not a coach's Forge prospect, not a real-list player.
static func _is_game_made(p: Dictionary) -> bool:
	return bool(p.get("generated", false)) and not bool(p.get("user_created", false))


static func _copy_pool() -> Dictionary:
	if not _copy.is_empty():
		return _copy
	var f := FileAccess.open(COPY_POOL_CSV, FileAccess.READ)
	if f == null:
		return _copy
	var head := f.get_csv_line()
	var col := {}
	for i in head.size():
		col[head[i]] = i
	var by_role := {}
	while not f.eof_reached():
		var line := f.get_csv_line()
		if line.size() < head.size():
			continue
		var r := {"_ovr": float(line[col["ovr"]]), "_year": int(line[col["year"]]),
				"_id": str(line[col["id"]]), "_name": str(line[col["name"]]), "_club": str(line[col["club"]]),
				"_height": float(line[col["height_cm"]]) if str(line[col["height_cm"]]) != "" else 0.0,
				"_fit": float(line[col["fit_shift"]]) if col.has("fit_shift") else 0.0}
		for key in ATTR_KEYS:
			r[key] = float(line[col[key]])
		var role := str(line[col["line"]])
		if not by_role.has(role):
			by_role[role] = []
		(by_role[role] as Array).append(r)
	for role in by_role:
		var rows: Array = by_role[role]
		# File order (season, player id) breaks ties, so the pick is the same every run.
		for i in rows.size():
			rows[i]["_i"] = i
		rows.sort_custom(func(x, y): return x["_ovr"] < y["_ovr"] or (x["_ovr"] == y["_ovr"] and x["_i"] < y["_i"]))
		var ovr := PackedFloat32Array()
		var disc := []
		for r in rows:
			ovr.append(float(r["_ovr"]))
			disc.append(float(r["discipline"]))
		_copy[role] = {"rows": rows, "ovr": ovr, "disc": disc}
	return _copy


## The real 2012-2026 player-seasons of `role` whose overall is nearest `level`, the
## SHAPE_NEAREST of them (as _shape_for picks from the start's lists). Fifteen seasons put
## dozens of players on the same whole-number overall, so the last places among equally
## near players go by `rng`'s draw, not file order (which would only ever copy 2012-2014).
static func copy_candidates(role: String, level: float, rng: RandomNumberGenerator) -> Array:
	var got: Dictionary = _copy_pool().get(role, {})
	var rows: Array = got.get("rows", [])
	var want := mini(SHAPE_NEAREST, rows.size())
	if want == 0:
		return []
	var ovr: PackedFloat32Array = got["ovr"]
	# The distance of the SHAPE_NEAREST-th nearest player.
	var hi := ovr.bsearch(level)
	var lo := hi - 1
	var edge := 0.0
	for n in want:
		if hi >= rows.size() or (lo >= 0 and absf(ovr[lo] - level) <= absf(ovr[hi] - level)):
			edge = absf(ovr[lo] - level)
			lo -= 1
		else:
			edge = absf(ovr[hi] - level)
			hi += 1
	# Everyone nearer than that is in; the rest of the places are drawn from those at it.
	var out := []
	var tied := []
	var i := ovr.bsearch(level - edge - 0.5)
	while i < rows.size() and ovr[i] <= level + edge + 0.5:
		var dist := absf(ovr[i] - level)
		if dist < edge - 0.0001:
			out.append(rows[i])
		elif dist <= edge + 0.0001:
			tied.append(rows[i])
		i += 1
	while out.size() < want and not tied.is_empty():
		out.append(tied.pop_at(rng.randi_range(0, tied.size() - 1)))
	return out


## A game-made player's shape: one of the real 2012-2026 players of his role nearest
## `level` (picked by `rng`, as _shape_for), each skill moved by its own fingerprint roll
## (seeded by the player alone, so nothing else about him rolls differently).
## Example: the copied player kicks 70 with an overall of 75; a roll of 1.03 makes it
## 72.1, so the shape is 72.1 - 75 = -2.9 (the fit then sets his level as before).
static func _copy_for(role: String, rng: RandomNumberGenerator, level: float, p: Dictionary) -> Dictionary:
	var near := copy_candidates(role, level, rng)
	if near.is_empty():
		return _shape_for(role, rng, level)
	var d: Dictionary = near[rng.randi_range(0, near.size() - 1)]
	var frng := _rng_for("fp|%s|%s" % [str(p.get("id", "")), str(p.get("draft_year", 2026))])
	var ovr := float(d["_ovr"])
	var out := {}
	for key in ATTR_KEYS:
		out[key] = clampf(float(d[key]) * frng.randf_range(1.0 - FINGERPRINT, 1.0 + FINGERPRINT), 1.0, 99.0) - ovr
	return out


## The shape of one of the real players of `role` nearest `level` overall,
## picked by `rng`; the role template when there are no real players to
## borrow from (a test database).
static func _shape_for(role: String, rng: RandomNumberGenerator, level: float) -> Dictionary:
	if _shapes.is_empty():
		var db = Engine.get_main_loop().root.get_node_or_null("GameDB") if Engine.get_main_loop() is SceneTree else null
		if db != null:
			for code in db.club_order:
				for q in db.club_list(code):
					var at: Dictionary = q.get("attr", {})
					if at.is_empty() or bool(q.get("generated", false)):
						continue
					var d := {}
					for key in ATTR_KEYS:
						d[key] = float(at.get(key, 0)) - float(Rating.ovr(q, 0))
					d["_ovr"] = float(Rating.ovr(q, 0))
					var r := str(q.get("role", "MID"))
					if not _shapes.has(r):
						_shapes[r] = []
					(_shapes[r] as Array).append(d)
	var pool: Array = (_shapes.get(role, []) as Array).duplicate()
	if pool.is_empty():
		return ROLE_DELTAS.get(role, ROLE_DELTAS["MID"])
	pool.sort_custom(func(x, y): return absf(float(x["_ovr"]) - level) < absf(float(y["_ovr"]) - level))
	var d: Dictionary = pool[rng.randi_range(0, mini(SHAPE_NEAREST, pool.size()) - 1)]
	var out := d.duplicate()
	out.erase("_ovr")
	return out


## Shift every attribute by a uniform offset so his OVR at `apos` lands on target.
## Bisection over a monotone function - at most ~14 cheap evaluations.
## Attributes outside the overall rating: a refit leaves them where they are.
const UNRATED_KEYS := ["discipline"]


static func fit_attributes(a: Dictionary, apos: String, target: float) -> Dictionary:
	var lo := -40.0
	var hi := 40.0
	for i in range(14):
		var mid := (lo + hi) * 0.5
		if _shifted_overall(a, apos, mid) < target:
			lo = mid
		else:
			hi = mid
	var offset := (lo + hi) * 0.5
	var out := {}
	for key in a:
		# Temperament isn't in the rating, so refitting the rating must not
		# move it: shifting it with every decline and every league re-anchor
		# made hotheads of a third of the real players by 2034 (backlog 21).
		if key in UNRATED_KEYS:
			out[key] = clampi(int(round(float(a[key]))), 1, 99)
			continue
		out[key] = clampi(int(round(float(a[key]) + offset)), 1, 99)
	return out


static func _shifted_overall(a: Dictionary, apos: String, offset: float) -> float:
	var shifted := {}
	for key in a:
		shifted[key] = float(a[key]) if key in UNRATED_KEYS else clampf(float(a[key]) + offset, 1.0, 99.0)
	return float(Rating.of_attrs(shifted, apos))


# ---------------------------------------------------------------------------
# Season rollover: growth, decline, retirement
# ---------------------------------------------------------------------------
## Ages and redevelops every player on every list in place. Mutates the
## player dicts (they are shared with GameDB; a New Career resets via
## GameDB.reload()). Returns {"retired": [...], "developed": n, "declined": n}.
## `min_left` is the smallest a list may be left at: 0 after a National Draft,
## which refills every list; a rollover with no draft (start_next_season)
## keeps each list at Contracts.min_list(), as nobody drafts in their places.
static func age_league(lists: Dictionary, year: int, min_left := 0) -> Dictionary:
	var retired := []
	var developed := 0
	var declined := 0
	var breakouts := []
	for code in lists:
		var arr: Array = lists[code]
		for p in arr:
			age_player(p, year)
			# The summer after the season just played (Growth, the director's
			# design 2026-11-17): past his peak part of what he trained past
			# his potential goes; once his career is over he falls.
			var delta := Growth.summer(p, year - 1)
			if delta > 0:
				developed += 1
			elif delta < 0:
				declined += 1
		for b in Growth.breakouts(str(code), arr, year):
			breakouts.append([str(code)] + b)
		# Retire/trim pass, original order so it is deterministic.
		var keep: Array = []
		var dropped := 0
		for p in arr:
			# Decided at the off-season (Retirement) when it opened; a player
			# talked round plays one more season.
			var go := should_retire(p, year) or int(p.get("retiring", 0)) == year
			if int(p.get("play_on", 0)) == year:
				go = false
			# After a draft, never held back by the list size: the draft made
			# every club, yours included, fill the places its retirees leave
			# (Draft.leaving), so a list that passes at the minimum still
			# turns over (2026-11-13: a coach who passed every draft kept
			# the same 32 for 36 years).
			if go and dropped < MAX_RETIRE_PER_CLUB and arr.size() - dropped > min_left:
				dropped += 1
				retired.append({"id": str(p["id"]), "name": str(p.get("generic_name", p.get("name", "Player"))),
						"club": str(code), "age": float(p.get("age", 26.0)),
						"overall": int(Rating.ovr(p, 40))})
				p["retired"] = true
			else:
				# Held back by the cap on retirements or the list size: he
				# plays the season, so nothing reads him as retiring in it
				# (Contracts.payroll would leave his salary off the books).
				if int(p.get("retiring", 0)) == year:
					p.erase("retiring")
				keep.append(p)
		lists[code] = keep
	return {"retired": retired, "developed": developed, "declined": declined, "breakouts": breakouts}


static func should_retire(p: Dictionary, year: int) -> bool:
	var age := Potential.retire_age(p)   # Fine Wine: three years later
	var ov := int(Rating.ovr(p, 50))
	# A real player of a Legacy start retires about when he did (director,
	# 2026-11-13: "make all historical players retirement start roughly when
	# it did irl"), a year either side, whatever his age or rating; a coach
	# can still talk him round (Retirement). Still listed in 2025: the sim's.
	# His last real season is a retirement only when he was REAL_RETIRE_AGE or
	# older in it: a younger man's career ended because his club delisted him,
	# so it ends as a delisting (real_delisting_due), not a retirement. (Read as
	# every last season, a 1990 start retired 12 a club, nine of them 26 or younger.)
	var last := int(p.get("real_last", 0))
	# A year early never ends a career before a season he really played for
	# the club that signed him (a new club's foundation man, real_first).
	if last > 0 and float(p.get("age", 26.0)) - float(year - last) >= REAL_RETIRE_AGE:
		return year > maxi(last + real_slack(p), int(p.get("real_first", 0)))
	if ov <= 32:
		return true
	if age >= 37.0:
		return true
	if age >= 35.0:
		return _rng_for("%s|r%d" % [str(p["id"]), year]).randf() < 0.70
	if age >= 33.0 and ov < 42:
		return _rng_for("%s|r%d" % [str(p["id"]), year]).randf() < 0.30
	return false


## A real player of a Legacy start whose real AFL career ended before he was
## REAL_RETIRE_AGE: his club delisted him then (director, 2026-11-13: careers
## end "about when he really did ... whatever the sim makes of his age or
## rating"). Due in the same season his retirement would be (should_retire,
## real_slack), for the off-season before season `year`.
static func real_delisting_due(p: Dictionary, year: int) -> bool:
	var last := int(p.get("real_last", 0))
	if last <= 0 or float(p.get("age", 26.0)) - float(year - last) >= REAL_RETIRE_AGE:
		return false
	return year > last + real_slack(p)


## How far his retirement falls from his real one: -1, 0 or +1 seasons
## (one in four early, one in four late), fixed for him by his id.
static func real_slack(p: Dictionary) -> int:
	var r := _rng_for("%s|real_last" % str(p.get("id", ""))).randf()
	return -1 if r < 0.25 else (1 if r >= 0.75 else 0)


## Age one player by a year. Everyone on a list has now played a full
## simulated season, so the 2026 small-sample confidence shrink lifts. His
## rating moves only by what he earns (Growth): no age step, no free points,
## no growth toward his potential in the summer (director, 2026-11-17).
static func age_player(p: Dictionary, _year: int) -> float:
	p["age"] = float(p.get("age", 26.0)) + 1.0
	if bool(p.get("projected", false)):
		p["sample"] = 16.0
	else:
		p["sample"] = maxf(18.0, float(p.get("gm", 0.0)))
	return 0.0


## Age the undrafted pool between seasons. Prospects re-enter next year's
## draft a year older; past draft age they drop out of the pool.
static func age_pool(pool: Array, year: int, drafted: Dictionary) -> Array:
	var out := []
	for p in pool:
		var id := str(p["id"])
		if drafted.has(id):
			continue
		if int(p.get("draft_year", 0)) == year:
			# A generated class is made a year ahead; that year in the pool ages it but does not
			# develop it, so it is drafted at the rating it was made with, as the real 2026 class
			# is (row 65: one pool year of growth put picks 1-5 at 65-69, above the 4.Q9 bands).
			# A prospect passed over in his own draft grows from then on, like anyone else.
			p["age"] = float(p.get("age", 18.0)) + 1.0
		else:
			age_player(p, year)
		# A real class's mature-age pick (a Legacy career) is in his own draft
		# whatever his age; passed over, he ages out like anyone else.
		var own_real := bool(p.get("real_class", false)) and int(p.get("draft_year", 0)) == year
		# A delisted man put back in the drafts (GameState._relist) waits for
		# the Rookie Draft, then ends his career if nobody takes him.
		var relisted := int(p.get("relisted", 0)) == year - 1
		if float(p.get("age", 18.0)) >= 22.0 and not own_real and not relisted:
			continue  # aged out of draft eligibility
		out.append(p)
	return out


# ---------------------------------------------------------------------------
# Future draft classes
# ---------------------------------------------------------------------------
## Deterministic fictional intake for years after the shipped data ends.
## Same projection pipeline as the real class, so a 2031 career keeps getting
## plausible rookies without inventing anyone real.
## `career_seed` picks the class's quality tier (class_tier); everything
## else about the class is seeded by the year alone, as before.
static func generate_class(year: int, career_seed := 0) -> Array:
	var tier := class_tier(career_seed, year)
	var rng := _rng_for("class-%d" % year)
	var size := 46 + int(rng.randi_range(0, 10))
	# The real lists' mix (director, 2026-10-06: "Match real lists"): about
	# DEF 34%, FWD 30%, MID 28%, RUCK 7%. Every twelfth pick is a ruck (8%);
	# the rest come from this bag, so a class runs DEF 35, FWD 28, MID 28.
	var role_bag := ["DEF", "DEF", "DEF", "DEF", "DEF", "FWD", "FWD", "FWD", "FWD",
			"MID", "MID", "MID", "MID"]
	var out := []
	var rucks := 0
	for r in range(1, size + 1):
		var p := {}
		var role: String = str(role_bag[rng.randi_range(0, role_bag.size() - 1)])
		if r % 12 == 8:
			role = "RUCK"
		if role == "RUCK":
			rucks += 1
		p["role"] = role
		p["role2"] = _generated_secondary(role, rng)
		var height := 0.0
		match role:
			"RUCK": height = float(rng.randi_range(197, 208))
			"FWD": height = float(rng.randi_range(FWD_MIN_CM, 203))
			"DEF": height = float(rng.randi_range(182, 198))
			_: height = float(rng.randi_range(173, 192))
		p["height_cm"] = height
		var over_age := rng.randf() < 0.15
		var birth_year := year - (19 if over_age else 18)
		var m := rng.randi_range(1, 12)
		var dd := rng.randi_range(1, 28)
		p["dob"] = "%04d-%02d-%02d" % [birth_year, m, dd]
		p["age"] = float(days_between(str(p["dob"]), "%d-11-20" % year)) / 365.25
		# ^ drafted mid-November; the whole class shares one reference date.
		var team: Array = JUNIOR_TEAMS[rng.randi_range(0, JUNIOR_TEAMS.size() - 1)]
		p["club"] = str(team[0])
		p["draft_team"] = str(team[0])
		p["draft_league"] = str(team[1])
		p["draft_state"] = str(team[2])
		p["state"] = str(team[2])
		p["tied_club"] = ""
		p["tied_type"] = ""
		p["u18_gm"] = float(rng.randi_range(6, 16))
		p["u18_di"] = float(rng.randi_range(10, 26)) if role != "RUCK" else float(rng.randi_range(8, 18))
		p["u18_gl"] = float(rng.randi_range(3, 26)) / 10.0 if role == "FWD" \
				else float(rng.randi_range(0, 8)) / 10.0
		p["u18_mk"] = float(rng.randi_range(1, 7)) if role != "FWD" else float(rng.randi_range(3, 7))
		p["u18_tk"] = float(rng.randi_range(1, 7))
		p["u18_if50"] = float(rng.randi_range(1, 6))
		p["u18_ho"] = float(rng.randi_range(12, 28)) if role == "RUCK" else 0.0
		p["note"] = ""
		p["id"] = "D%d_%02d" % [year, r]
		p["real_name"] = ""
		p["generic_name"] = ""
		p["name"] = ""
		p["first"] = ""
		p["last"] = ""
		p["src"] = "U18"
		p["data_src"] = "generated"
		p["draft_year"] = year
		p["draft_rank"] = r
		p["generated"] = true
		p["num"] = r
		var shifts := class_shifts(tier, r)
		p["class_shift"] = shifts[0]
		p["class_ceiling"] = shifts[1]
		for key in Ratings.STATS_ZERO_KEYS:
			p[key] = 0.0
		p["weight_kg"] = 0.0
		p["real_pos"] = Ratings.ROLE_SHORT_TO_POS.get(str(p["role"]), "MID")
		project(p)
		out.append(p)
	# Guarantee the pool carries a few rucks without renumbering the class.
	if rucks < 3:
		for p in out:
			if rucks >= 3:
				break
			if float(p.get("height_cm", 0.0)) >= 198.0 and str(p["role"]) != "RUCK":
				p["role"] = "RUCK"
				p["role2"] = "FWD"
				p["u18_ho"] = 18.0
				project(p)
				rucks += 1
	_maybe_unicorn(out, year, career_seed)
	roll_fine_wine(out, "class-%d-%d" % [year, career_seed])
	GameDB.assign_aliases(out)
	InternationalProspects.apply(out, year)
	return out


## About one class in UNICORN_CLASS_CHANCE has a Unicorn (director,
## 2026-10-08): its tallest prospect who isn't a ruck, if he stands 194 cm or
## more - a key-position body with a smaller player's game. Its own dice, so
## the class itself rolls as it always did.
const UNICORN_CLASS_CHANCE := 0.4
const UNICORN_MIN_CM := 194.0


static func _maybe_unicorn(cls: Array, year: int, career_seed: int) -> void:
	var rng := _rng_for("unicorn-%d-%d" % [year, career_seed])
	if rng.randf() >= UNICORN_CLASS_CHANCE:
		return
	var best: Dictionary = {}
	for p in cls:
		if str(p.get("role", "")) == "RUCK" or float(p.get("height_cm", 0.0)) < UNICORN_MIN_CM:
			continue
		if best.is_empty() or float(p["height_cm"]) > float(best["height_cm"]):
			best = p
	if not best.is_empty():
		best["unicorn"] = true
		best["note"] = "%d cm and moves like a much smaller player" % int(best["height_cm"])


## Every generated draftee rolls once for Fine Wine at Traits.FINE_WINE_DRAFTEE_ODDS
## (director, 2026-11-13: "every draftee should have a very slim chance").
## Its own dice, so the class itself rolls as it always did. A real draftee
## rolls too, unless his real career could already show it by the 2026 data
## (born 1991 or earlier, so 60 games at 32+ were within reach by 2025): then his
## record decides (Traits.fine_wine), as for any real player in a Legacy start.
const FINE_WINE_RECORD_BORN := 1991


static func roll_fine_wine(cls: Array, salt: String) -> void:
	var rng := _rng_for("fine-wine-" + salt)
	for p in cls:
		var roll := rng.randf()
		if not bool(p.get("generated", false)):
			var born := str(p.get("dob", "")).substr(0, 4)
			if not born.is_valid_int() or int(born) <= FINE_WINE_RECORD_BORN:
				continue
		if roll < Traits.FINE_WINE_DRAFTEE_ODDS:
			p["fine_wine"] = true


# ---------------------------------------------------------------------------
# A custom prospect (Club Forge, ARD-M7-008)
# ---------------------------------------------------------------------------
## Strengths and weaknesses a coach can name, in football words, and the
## attribute each moves. A play style is two strengths for one role.
const CUSTOM_TRAITS := {
	"marking": "contested_marking", "kicking": "kicking", "goalkicking": "goalkicking",
	"contested": "contested", "pressure": "pressure", "reading": "intercept",
	"running": "carry", "vision": "creating", "ruckwork": "ruck",
}
const CUSTOM_STYLES := {
	"FWD": {"key_forward": ["marking", "goalkicking"], "small_forward": ["goalkicking", "pressure"],
			"defensive_forward": ["pressure", "contested"], "leading_forward": ["running", "marking"]},
	"MID": {"inside": ["contested", "kicking"], "outside": ["running", "kicking"],
			"tagger": ["pressure", "reading"], "playmaker": ["vision", "kicking"]},
	"DEF": {"key_defender": ["marking", "reading"], "rebounder": ["running", "kicking"],
			"lockdown": ["pressure", "contested"], "interceptor": ["reading", "marking"]},
	"RUCK": {"tap_ruck": ["ruckwork", "contested"], "mobile_ruck": ["ruckwork", "running"]},
}
const CUSTOM_HEIGHT := {"RUCK": [197, 210], "FWD": [168, 205], "DEF": [175, 202], "MID": [168, 195]}
## How hard a style, strength or weakness pushes its attribute before the
## projection refits the whole profile to the same overall.
const CUSTOM_STYLE_PUSH := 5.0
const CUSTOM_TRAIT_PUSH := 7.0
## Where a custom prospect sits in his class, rolled once per career: a
## believable spread from late picks to the top three, so most are useful
## role players to good players, a star is uncommon and a generational
## ceiling (a top pick's room plus a good roll) is rare.
const CUSTOM_RANKS := [[1, 1, 1.0], [2, 3, 3.0], [4, 10, 14.0], [11, 20, 22.0], [21, 35, 35.0], [36, 45, 25.0]]


## Whether `spec` is a valid custom prospect: role, secondary, height,
## style, strengths and weaknesses. "" when it is, else what's wrong.
static func custom_problem(spec: Dictionary) -> String:
	var role := str(spec.get("role", ""))
	if not CUSTOM_STYLES.has(role):
		return "Pick a position."
	var role2 := str(spec.get("role2", ""))
	if role2 != "" and (role2 == role or not CUSTOM_STYLES.has(role2)):
		return "The second position must be a different one."
	var h := int(spec.get("height_cm", 0))
	var band: Array = CUSTOM_HEIGHT[role]
	if h < int(band[0]) or h > int(band[1]):
		return "Height for that position is %d to %d cm." % [band[0], band[1]]
	if str(spec.get("style", "")) != "" and not (CUSTOM_STYLES[role] as Dictionary).has(str(spec["style"])):
		return "That play style isn't one for this position."
	var strengths: Array = spec.get("strengths", [])
	var weaknesses: Array = spec.get("weaknesses", [])
	if strengths.size() > 2 or weaknesses.size() > 2:
		return "Up to two strengths and two weaknesses."
	for t in strengths + weaknesses:
		if not CUSTOM_TRAITS.has(str(t)):
			return "Unknown strength or weakness."
	for t in strengths:
		if weaknesses.has(t):
			return "A strength can't also be a weakness."
	if str(spec.get("first", "")).strip_edges() == "" or str(spec.get("last", "")).strip_edges() == "":
		return "He needs a first and last name."
	return ""


## The Club Forge rule on top of custom_problem (T8.Q12): exactly one
## weakness is compulsory and a second is optional. The weaknesses only
## reshape him; _shape_custom refits to the same overall, so no choice buys
## power. Kept apart from custom_problem so a player saved before the rule
## still enters a career; the Forge asks for one the next time he's edited.
static func forge_problem(spec: Dictionary) -> String:
	var weaknesses: Array = spec.get("weaknesses", [])
	if weaknesses.is_empty():
		return "Pick one weakness. A second is optional."
	return custom_problem(spec)

## The custom prospect for the class drafted in `year`, through the same
## projection as every generated prospect (project, Potential.assign). His
## standing in the class - and so his ceiling - is rolled once from the
## career's seed: the coach shapes his profile, never his OVR or POT. Nothing
## about him is special after this: same development, durability, ageing.
static func make_custom(spec: Dictionary, year: int, career_seed: int) -> Dictionary:
	var rng := _rng_for("custom|%d|%d" % [career_seed, year])
	rng.randi()
	var weights := []
	for b in CUSTOM_RANKS:
		weights.append(float(b[2]))
	var band: Array = CUSTOM_RANKS[_weighted_index(rng.randf(), weights)]
	var rank := rng.randi_range(int(band[0]), int(band[1]))
	var role := str(spec["role"])
	var p := {}
	p["id"] = "C%d_%d" % [year, career_seed]
	p["role"] = role
	p["role2"] = str(spec.get("role2", ""))
	p["height_cm"] = float(spec["height_cm"])
	p["dob"] = str(spec.get("dob", "%04d-06-15" % (year - 18)))
	p["age"] = float(days_between(str(p["dob"]), "%d-11-20" % year)) / 365.25
	var team: Array = JUNIOR_TEAMS[rng.randi_range(0, JUNIOR_TEAMS.size() - 1)]
	p["club"] = str(team[0])
	p["draft_team"] = str(team[0])
	p["draft_league"] = str(team[1])
	p["draft_state"] = str(team[2])
	p["state"] = str(team[2])
	p["tied_club"] = ""
	p["tied_type"] = ""
	for key in ["u18_gm", "u18_di", "u18_gl", "u18_mk", "u18_tk", "u18_if50", "u18_ho"]:
		p[key] = 0.0
	p["u18_gm"] = float(rng.randi_range(8, 16))
	p["note"] = ""
	var full := "%s %s" % [str(spec["first"]).strip_edges(), str(spec["last"]).strip_edges()]
	p["first"] = str(spec["first"]).strip_edges()
	p["last"] = str(spec["last"]).strip_edges()
	# A forged prospect has one name: the one you gave him.
	p["real_name"] = full
	p["generic_name"] = full
	p["name"] = full
	p["nickname"] = str(spec.get("nickname", "")).strip_edges()
	# FL-005: the club he grew up following, his choice ("" = not recorded).
	p["fav_club"] = str(spec.get("fav_club", "")).strip_edges()
	p["foot"] = "L" if str(spec.get("foot", "R")) == "L" else "R"
	p["number_pref"] = clampi(int(spec.get("number_pref", 0)), 0, 99)
	if spec.get("look") is Dictionary:
		p["look"] = (spec["look"] as Dictionary).duplicate(true)
	p["src"] = "U18"
	p["data_src"] = "generated"
	p["draft_year"] = year
	p["draft_rank"] = rank
	p["generated"] = true
	p["user_created"] = true
	p["num"] = 0
	p["class_shift"] = 0.0
	p["class_ceiling"] = 0.0
	for key in Ratings.STATS_ZERO_KEYS:
		p[key] = 0.0
	p["weight_kg"] = 0.0
	p["real_pos"] = Ratings.ROLE_SHORT_TO_POS.get(role, "MID")
	project(p)
	_shape_custom(p, spec)
	return p


## Move the projected attributes toward his style and strengths and away from
## his weaknesses, then refit to the same overall: a different footballer,
## not a better one. Potential stays as projected.
static func _shape_custom(p: Dictionary, spec: Dictionary) -> void:
	var role := str(p["role"])
	var a: Dictionary = (p["attr"] as Dictionary).duplicate()
	var style := str(spec.get("style", ""))
	if style != "":
		for t in CUSTOM_STYLES[role][style]:
			var k: String = CUSTOM_TRAITS[str(t)]
			a[k] = float(a[k]) + CUSTOM_STYLE_PUSH
	for t in spec.get("strengths", []):
		var k: String = CUSTOM_TRAITS[str(t)]
		a[k] = float(a[k]) + CUSTOM_TRAIT_PUSH
	for t in spec.get("weaknesses", []):
		var k: String = CUSTOM_TRAITS[str(t)]
		a[k] = float(a[k]) - CUSTOM_TRAIT_PUSH
	var target := float(Rating.ovr(p))
	a = fit_attributes(a, Rating.apos_of(p), target)
	for key in a:
		a[key] = int(a[key])
	p["attr"] = a
	p["potential"] = maxi(int(p.get("potential", Rating.ovr(p))), int(Rating.ovr(p)))


static func _weighted_index(roll: float, weights: Array) -> int:
	var total := 0.0
	for w in weights:
		total += float(w)
	var at := roll * total
	for i in range(weights.size()):
		at -= float(weights[i])
		if at < 0.0:
			return i
	return weights.size() - 1


## The quality tier of the class drafted in `year` in this career: one roll
## per career and year, so a reload never re-rolls it and two careers need
## not share their superdrafts.
static func class_tier(career_seed: int, year: int) -> String:
	var rng := _rng_for("class-tier|%d|%d" % [career_seed, year])
	rng.randi()  # the first draw from near-identical keys runs together
	var roll := rng.randf()
	for t in CLASS_TIERS:
		roll -= float(t[1])
		if roll < 0.0:
			return str(t[0])
	return "normal"


## [overall shift, extra POT room] for the prospect ranked `rank` in a class
## of this tier.
static func class_shifts(tier: String, rank: int) -> Array:
	for t in CLASS_TIERS:
		if str(t[0]) != tier:
			continue
		var fade := clampf(1.0 - float(rank - 1) / float(CLASS_TOP_RANKS - 1), 0.0, 1.0)
		var top := float(t[2])
		var depth := float(t[3])
		return [depth + (top - depth) * fade, float(t[4]) * fade]
	return [0.0, 0.0]


## The full list an expansion club fields in its first season: a real
## expansion roster mixes state-league youngsters with a core of seasoned
## players, so this one spans the full age range (unlike a rookie class) at
## overalls around the league baseline - competitive, but not a dynasty.
## Deterministic per club and year; the club's own state league supplies
## half the list when it has junior teams.
## `salt` (the career's seed, in words) gives each career its own players;
## without it the list is the same one every time, as it always was.
static func generate_expansion_list(code: String, year: int, size := 36, salt := "", first_rank := 1) -> Array:
	var rng := _rng_for("expansion-%s-%d%s" % [code, year, salt])
	var home_teams := []
	for team in JUNIOR_TEAMS:
		if str(team[2]) == str(code):
			home_teams.append(team)
	var role_bag := ["MID", "MID", "MID", "MID", "MID", "MID",
			"DEF", "DEF", "DEF", "DEF", "FWD", "FWD", "FWD", "FWD",
			"RUCK", "RUCK"]
	var out := []
	for r in range(first_rank, first_rank + size):
		var p := {}
		var role: String = str(role_bag[rng.randi_range(0, role_bag.size() - 1)])
		if r % 18 == 10:
			role = "RUCK"
		p["role"] = role
		p["role2"] = _generated_secondary(role, rng)
		var height := 0.0
		match role:
			"RUCK": height = float(rng.randi_range(197, 208))
			"FWD": height = float(rng.randi_range(FWD_MIN_CM, 203))
			"DEF": height = float(rng.randi_range(182, 198))
			_: height = float(rng.randi_range(173, 192))
		p["height_cm"] = height
		var band := rng.randf()
		var birth_year: int
		if band < 0.45:
			birth_year = year - rng.randi_range(18, 21)
		elif band < 0.80:
			birth_year = year - rng.randi_range(22, 26)
		else:
			birth_year = year - rng.randi_range(27, 30)
		p["dob"] = "%04d-%02d-%02d" % [birth_year, rng.randi_range(1, 12),
				rng.randi_range(1, 28)]
		# ^ already the right age for the season the club enters.
		p["age"] = float(days_between(str(p["dob"]), "%d-01-01" % year)) / 365.25
		var team: Array
		if not home_teams.is_empty() and rng.randf() < 0.5:
			team = home_teams[rng.randi_range(0, home_teams.size() - 1)]
		else:
			team = JUNIOR_TEAMS[rng.randi_range(0, JUNIOR_TEAMS.size() - 1)]
		p["club"] = code  # already listed; not a free agent or a draftee
		p["draft_team"] = str(team[0])
		p["draft_league"] = str(team[1])
		p["draft_state"] = str(team[2])
		p["state"] = str(team[2])
		p["tied_club"] = ""
		p["tied_type"] = ""
		p["u18_gm"] = float(rng.randi_range(12, 26))
		p["u18_di"] = float(rng.randi_range(10, 26)) if role != "RUCK" \
				else float(rng.randi_range(8, 18))
		p["u18_gl"] = float(rng.randi_range(3, 26)) / 10.0 if role == "FWD" \
				else float(rng.randi_range(0, 8)) / 10.0
		p["u18_mk"] = float(rng.randi_range(1, 7)) if role != "FWD" \
				else float(rng.randi_range(3, 7))
		p["u18_tk"] = float(rng.randi_range(1, 7))
		p["u18_if50"] = float(rng.randi_range(1, 6))
		p["u18_ho"] = float(rng.randi_range(12, 28)) if role == "RUCK" else 0.0
		p["note"] = "Expansion list, %d" % year
		p["id"] = ("EXP_%s_%02d" % [code, r]) if salt == "" else ("FND_%s_%s_%02d" % [code, salt, r])
		p["real_name"] = ""
		p["generic_name"] = ""
		p["name"] = ""
		p["first"] = ""
		p["last"] = ""
		p["src"] = "U18"
		p["data_src"] = "generated"
		p["draft_year"] = year
		p["draft_rank"] = r
		p["generated"] = true
		p["num"] = r
		for key in Ratings.STATS_ZERO_KEYS:
			p[key] = 0.0
		p["weight_kg"] = 0.0
		p["real_pos"] = Ratings.ROLE_SHORT_TO_POS.get(str(p["role"]), "MID")
		project(p)
		_mature_entry(p)
		out.append(p)
	roll_fine_wine(out, "expansion-%s-%d%s-%d" % [code, year, salt, first_rank])
	GameDB.assign_aliases(out)
	return out


## The state-leaguers who fill out a League redraft: the real players run out
## short of full lists (director, 2026-11-09: "Full-size lists"). Ranked after
## the real class, unlisted until drafted.
const DEPTH_FIRST_RANK := 40

static func generate_depth_pool(count: int, year: int, salt: String) -> Array:
	var out := generate_expansion_list("DEPTH", year, count, salt, DEPTH_FIRST_RANK)
	for p in out:
		p["club"] = ""
		p["note"] = "State league, %d" % year
		p["draft_year"] = GameDB.DATA_SEASON
	return out


## Senior state-league clubs a mature-age expansion recruit comes from, by
## state (WA and SA's junior clubs are already their senior clubs).
## A VFL club is named by its code in data/state_leagues (GameDB.state_clubs),
## so a club that leaves the league (Aspley, 2026) drops out with the data.
## AFL Sydney and the TSL are outside the state leagues and stay named here.
const STATE_LEAGUE_CLUBS := {
	"VICM": ["BOX", "WIL", "PTM", "COB", "WER", "FRA"],
	"VICC": ["WER", "FRA", "WIL"],
	"QLD": ["SOU"],
	"NSW": [["Sydney University", "AFL Sydney"], ["Pennant Hills", "AFL Sydney"]],
	"TAS": [["Clarence", "TSL"], ["Glenorchy", "TSL"], ["North Launceston", "TSL"],
			["Launceston", "TSL"], ["Kingborough", "TSL"]],
}


## [name, league] pairs of the senior clubs a mature-age recruit from `state`
## can come from; a state code the dataset did not load is left out.
static func state_league_clubs(state: String) -> Array:
	var out := []
	for c in STATE_LEAGUE_CLUBS.get(state, []):
		if c is Array:
			out.append(c)
		elif GameDB.is_state_club(str(c)):
			var row: Dictionary = GameDB.state_clubs[str(c)]
			out.append([str(row["name"]), str(row["league"])])
	return out


## An expansion player of 20 or more did not come out of the under-18s in the
## club's first year: his record is a senior state-league season, and past
## draft age (Potential.MAX_PROSPECT_AGE) no draft-class ranking either. Only
## the history changes: his ratings and ceiling were already set by project()
## (a ceiling past 21 is his age's, never his rank's), and the pick of club is
## seeded by his id so no later player's rolls move.
static func _mature_entry(p: Dictionary) -> void:
	var age := float(p.get("age", 18.0))
	if age < 20.0:
		return
	var clubs: Array = state_league_clubs(str(p.get("draft_state", "")))
	if not clubs.is_empty():
		var club: Array = clubs[_rng_for("mature|%s" % str(p["id"])).randi_range(0, clubs.size() - 1)]
		p["draft_team"] = str(club[0])
		p["draft_league"] = str(club[1])
	if age > Potential.MAX_PROSPECT_AGE:
		p["draft_rank"] = 0


static func _generated_secondary(role: String, rng: RandomNumberGenerator) -> String:
	if rng.randf() > 0.30:
		return ""
	match role:
		"MID": return "FWD" if rng.randf() < 0.6 else "DEF"
		"DEF": return "MID"
		"FWD": return "MID" if rng.randf() < 0.7 else "RUCK"
		"RUCK": return "FWD"
	return ""


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
static func _rng_for(key: String) -> RandomNumberGenerator:
	var rng := RandomNumberGenerator.new()
	rng.seed = int(key.hash()) * 2654435761 + 1013904223
	return rng


## Days between two ISO dates (Howard Hinnant's algorithm) - integer-exact,
## no Time API, no timezones.
static func days_between(from_iso: String, to_iso: String) -> int:
	return _days_from_civil(_parse_dto(to_iso)) - _days_from_civil(_parse_dto(from_iso))


static func _parse_dto(iso: String) -> Vector3i:
	if iso.length() < 10:
		return Vector3i(2026, 1, 1)
	return Vector3i(int(iso.substr(0, 4)), int(iso.substr(5, 2)), int(iso.substr(8, 2)))


static func _days_from_civil(d: Vector3i) -> int:
	var y := d.x
	if d.y <= 2:
		y -= 1
	var era := int(floor(float(y) / 400.0))
	var yoe := y - era * 400
	var doy := int(floor((153.0 * float(d.y + (9 if d.y <= 2 else -3)) + 2.0) / 5.0)) + d.z - 1
	var doe := yoe * 365 + int(floor(float(yoe) / 4.0)) - int(floor(float(yoe) / 100.0)) + doy
	return era * 146097 + doe - 719468
