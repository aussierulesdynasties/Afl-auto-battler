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
##   3. The ratings at max potential. Each man's attributes are moved evenly
##      to his level (Rating.shift_to) and compared attribute by attribute, as
##      raw points. Durability is left out: it says how
##      often he plays, not how. An attribute the prospect is strong in (above
##      his own average) counts for more, so the named player has his
##      strengths. The distance is that weighted root-mean-square gap, plus
##      LEVEL_POINTS for each point between POT and peak, plus CM_POINTS for
##      each centimetre, plus FAR_POINTS for each point beyond NEAR_LEVEL and
##      each centimetre beyond NEAR_CM.
## Lowest distance wins; a tie goes to the lower id, so the answer never moves.
## In a draft class, each real player is named once (PER_CLASS, for_class()).
##
## The real players are the launch lists as loaded (GameDB.plays_like_pool, a
## copy taken before a career ages anyone) and every other AFL season from 2012
## to 2025 as rated (data/league_seasons.csv, tools/wheelo/league.py; director,
## 2026-11-17: "drop the year from the copy just 'plays like Mitch Duncan'"): a
## past season is compared at that season's OVR and shown by his name alone. So
## a prospect in 2060 is still likened to a real player and a reload gives the
## same name. Display only: nothing in the sim reads it, and every club sees
## the same line.

## The attributes compared: those in the overall rating that say how he plays
## (not durability, and not temperament, which is not in the rating).
const KEYS := Attributes.PLAY_STYLE_KEYS
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
## How many prospects of one draft class can carry the same real player's name
## (director, 2026-11-27, "Once per class": without it the new Endurance named one
## real defender for 18 of 569 prospects, over the 3% the suite allows).
const PER_CLASS := 1


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
	var peak := float(p.get("potential", Rating.ovr(p, 0)))
	if real:
		peak = maxf(peak, Potential.recent_peak(p))
	peak = maxf(peak, float(Rating.ovr(p, 0)))
	# The peak is on the headline scale; shift_to sets his own position, so
	# take off what the headline adds over it (a hybrid's best line).
	peak -= maxf(0.0, float(Rating.ovr(p, 0)) - float(Rating.ovr_at_own(p, 0)))
	var at_peak := Rating.shift_to(attr, Rating.apos_of(p), peak)
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


## Every rated AFL season but `launch_season` (the launch lists' own, already
## in `pool`) added to `pool` as entries like profile()'s: each player-season with a
## height, at that season's OVR ("peak"), with "person" his Wheelo id so his
## seasons are one man. The launch lists' entries get their "person" too.
static func add_past_seasons(pool: Array, launch_season: int) -> void:
	for e in pool:
		var who := person_of(str(e["real_name"]), str(e["club"]))
		if who != "":
			e["person"] = who
	if not _past.has(launch_season):
		var past := []
		for r in _seasons():
			if int(r["year"]) == launch_season or float(r["height_cm"]) <= 0.0:
				continue
			var apos := str(r["apos"])
			var vec := PackedFloat32Array()
			for key in KEYS:
				vec.append(float(r["attr"][key]))
			past.append({"id": "%s|%d" % [str(r["id"]), int(r["year"])], "person": str(r["id"]),
					"real_name": str(r["name"]), "generic_name": str(r["name"]), "role": Rating.line_of(apos),
					"club": str(r["club"]), "height": float(r["height_cm"]),
					"peak": float(Rating.of_attrs(r["attr"], apos)), "vec": vec})
		_past[launch_season] = past
	pool.append_array(_past[launch_season])


## The past seasons' entries by launch season: fixed data, built once a run.
static var _past := {}

## Every rated player-season, 2012-25: {year, id, name, club, apos, height_cm,
## attr}.
const SEASONS_CSV := "res://data/league_seasons.csv"
static var _rows := []


static func _seasons() -> Array:
	if not _rows.is_empty():
		return _rows
	var f := FileAccess.open(SEASONS_CSV, FileAccess.READ)
	if f == null:
		return _rows
	var head := f.get_csv_line()
	var col := {}
	for i in head.size():
		col[head[i]] = i
	while not f.eof_reached():
		var r := f.get_csv_line()
		if r.size() < head.size() or str(r[0]) == "":
			continue
		var attr := {}
		for key in Attributes.KEYS:
			attr[key] = float(r[col[key]])
		_rows.append({"year": int(r[col["year"]]), "id": str(r[col["id"]]), "name": str(r[col["name"]]),
				"club": str(r[col["club"]]), "apos": str(r[col["apos"]]),
				"height_cm": float(r[col["height_cm"]]) if str(r[col["height_cm"]]) != "" else 0.0, "attr": attr})
	return _rows


## The Wheelo id of the 2012-2025 player named `name`: the only one of that name, or
## of two or more, the one who played at `club`. "" when none or still unclear.
static func person_of(name: String, club: String) -> String:
	if name.strip_edges() == "":
		return ""
	if _people.is_empty():
		for r in _seasons():
			var ids: Dictionary = _people.get(str(r["name"]), {})
			var clubs: Dictionary = ids.get(str(r["id"]), {})
			clubs[str(r["club"])] = true
			ids[str(r["id"])] = clubs
			_people[str(r["name"])] = ids
	var ids: Dictionary = _people.get(name, {})
	if ids.size() == 1:
		return str(ids.keys()[0])
	var at_club := []
	for id in ids:
		if (ids[id] as Dictionary).has(club):
			at_club.append(id)
	return str(at_club[0]) if at_club.size() == 1 else ""


## name -> {Wheelo id: {club: true}} over the 2012-2025 seasons (person_of).
static var _people := {}


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
	var c := _candidates(p, pool)
	return {} if c.is_empty() else _closest(c["me"], c["near"], {})


## nearest()'s working for `p`: {"me": his profile, "near": the real players he
## is compared with, "wide": whether those are his whole position because nobody
## is inside both bands, "himself": the test for his own entries}; {} when he has
## no ratings.
static func _candidates(p: Dictionary, pool: Array) -> Dictionary:
	var me := profile(p)
	if me.is_empty():
		return {}
	var own_name := str(p.get("real_name", "")).strip_edges()
	# His own seasons of 2012-2026 are himself too.
	var own_person := person_of(own_name, str(p.get("club", ""))) if own_name != "" else ""
	var himself := func(e: Dictionary) -> bool:
		return str(e["id"]) == str(me["id"]) or (own_name != "" and str(e["real_name"]) == own_name
				and is_equal_approx(float(e["height"]), float(me["height"]))) \
				or (own_person != "" and str(e.get("person", "")) == own_person)
	# Most often a player of his position inside both bands exists: look only there.
	var near := []
	var idx := _index(pool)
	var role := str(me["role"])
	var rows: Array = (idx["by_role"] as Dictionary).get(role, [])
	var peaks: PackedFloat32Array = (idx["peaks"] as Dictionary).get(role, PackedFloat32Array())
	var top := float(me["peak"]) + NEAR_LEVEL + 0.01
	for i in range(peaks.bsearch(float(me["peak"]) - NEAR_LEVEL - 0.01), rows.size()):
		if peaks[i] > top:
			break
		if _inside_both(me, rows[i]) and not himself.call(rows[i]):
			near.append(rows[i])
	var wide := near.is_empty()
	if wide:
		near = _nearest_wider(me, pool, himself)
	return {"me": me, "near": near, "wide": wide, "himself": himself}


## The entry of `near` closest to `me` whose real player is named fewer than
## PER_CLASS times in `used` ({real name: times}); {} when every one is taken.
static func _closest(me: Dictionary, near: Array, used: Dictionary) -> Dictionary:
	var best := {}
	var best_d := INF
	for e in near:
		if int(used.get(str(e["real_name"]), 0)) >= PER_CLASS:
			continue
		var d := distance(me, e)
		if d < best_d or (d == best_d and str(e["id"]) < str(best["id"])):
			best = e
			best_d = d
	return best


## The real player each prospect of one draft class plays like, {prospect id:
## pool entry}: nearest()'s rule, with each real player named for at most
## PER_CLASS prospects of the class (director, 2026-11-27). The class chooses in
## order of POT, highest first (a tie to the lower id); a prospect whose closest
## player is taken gets the closest one left, inside both bands while any is,
## then from the rest of his position. With nobody left he keeps his closest.
static func for_class(cls: Array, pool: Array) -> Dictionary:
	var order := []
	for p in cls:
		var c := _candidates(p, pool)
		if not c.is_empty():
			order.append({"id": str(p.get("id", "")), "c": c})
	order.sort_custom(func(x, y): return float(x["c"]["me"]["peak"]) > float(y["c"]["me"]["peak"]) \
			or (float(x["c"]["me"]["peak"]) == float(y["c"]["me"]["peak"]) and str(x["id"]) < str(y["id"])))
	var used := {}
	var out := {}
	for row in order:
		var c: Dictionary = row["c"]
		var e := _closest(c["me"], c["near"], used)
		if e.is_empty() and not bool(c["wide"]):
			e = _closest(c["me"], _nearest_wider(c["me"], pool, c["himself"]), used)
		if e.is_empty():
			e = _closest(c["me"], c["near"], {})
		if e.is_empty():
			continue
		out[row["id"]] = e
		used[str(e["real_name"])] = int(used.get(str(e["real_name"]), 0)) + 1
	return out


## nearest()'s candidates when no player of his position is inside both bands: his
## position's players, or anyone when his position has nobody.
static func _nearest_wider(me: Dictionary, pool: Array, himself: Callable) -> Array:
	var same := []
	var others := []
	for e in pool:
		if himself.call(e):
			continue
		others.append(e)
		if str(e["role"]) == str(me["role"]):
			same.append(e)
	return others if same.is_empty() else same


## A pool entry's name as this career shows names (his real name, or his
## generated one when the coach chose generated names). Two real players who
## share that name are told apart by club: "Bailey Williams (Eagles)". One man's
## seasons are one player ("person").
static func shown_name(e: Dictionary, pool: Array) -> String:
	var n := GameDB.player_display_name(e)
	var people: Dictionary = (_index(pool)["names"] as Dictionary).get(n, {})
	if people.size() > 1 or (people.size() == 1 and not people.has(str(e.get("person", e["id"])))):
		return "%s (%s)" % [n, GameDB.club_short(str(e["club"]))]
	return n


## `pool` sorted for nearest() and shown_name(), rebuilt when the pool changes:
## "by_role" {role: [entries by peak]}, "peaks" {role: their peaks}, "names" {shown
## name: {person: true}}.
static func _index(pool: Array) -> Dictionary:
	if not is_same(pool, _indexed) or int(_by.get("size", -1)) != pool.size():
		var by_role := {}
		var names := {}
		for e in pool:
			var role := str(e["role"])
			if not by_role.has(role):
				by_role[role] = []
			(by_role[role] as Array).append(e)
			var n := GameDB.player_display_name(e)
			if not names.has(n):
				names[n] = {}
			names[n][str(e.get("person", e["id"]))] = true
		# Each position by level, so nearest() reads only the players near his.
		var peaks := {}
		for role in by_role:
			(by_role[role] as Array).sort_custom(func(x, y): return float(x["peak"]) < float(y["peak"]))
			var got := PackedFloat32Array()
			for e in by_role[role]:
				got.append(float(e["peak"]))
			peaks[role] = got
		_indexed = pool
		_by = {"size": pool.size(), "by_role": by_role, "peaks": peaks, "names": names}
	return _by


static var _indexed: Array = []
static var _by := {}


## The compared player's name as this career shows it. "" when there is none.
static func name_of(p: Dictionary) -> String:
	var pool: Array = GameDB.plays_like_pool
	var e := _in_class(p, pool)
	return "" if e.is_empty() else shown_name(e, pool)


## The name `p`'s draft class gives him (for_class): his class is the career's
## prospects of his draft year (GameState.draftee_pool keeps the drafted ones
## until the season turns, so a pick never moves another prospect's name).
## Anyone outside a class (a state league player) gets nearest().
static func _in_class(p: Dictionary, pool: Array) -> Dictionary:
	var year := int(p.get("draft_year", 0))
	var pid := str(p.get("id", ""))
	var cls := []
	var ids := PackedStringArray()
	var pots := 0.0
	var found := false
	if year != 0 and pid != "":
		for q in GameState.draftee_pool:
			if int(q.get("draft_year", 0)) != year:
				continue
			cls.append(q)
			ids.append(str(q.get("id", "")))
			pots += float(q.get("potential", 0.0))
			found = found or str(q.get("id", "")) == pid
	if not found:
		return _nearest_memoised(p, pool)
	var key := [year, ids, pots, pool.size()].hash()
	var got: Dictionary = _classes.get(year, {})
	if not is_same(pool, _classes_pool) or int(got.get("key", 0)) != key \
			or int((got.get("facts", {}) as Dictionary).get(pid, 0)) != _facts(p):
		if not is_same(pool, _classes_pool):
			_classes.clear()
			_classes_pool = pool
		var facts := {}
		for q in cls:
			facts[str(q.get("id", ""))] = _facts(q)
		got = {"key": key, "facts": facts, "names": for_class(cls, pool)}
		_classes[year] = got
	return (got["names"] as Dictionary).get(pid, {})


## for_class() by draft year, kept while the class, its POTs, the pool and the
## asking prospect's facts are unchanged.
static var _classes := {}
static var _classes_pool: Array = []


## nearest() for `p` against `pool`, kept for as long as the pool and the facts
## it reads from him are unchanged: a draft board asks for the same prospects at
## every pick, and a search of thousands of real seasons each time froze a phone.
static func _nearest_memoised(p: Dictionary, pool: Array) -> Dictionary:
	if not is_same(pool, _memo_pool) or _memo_size != pool.size() or _memo.size() > MEMO_MAX:
		_memo.clear()
		_memo_pool = pool
		_memo_size = pool.size()
	var key := _facts(p)
	if _memo.has(key):
		return _memo[key]
	var e := nearest(p, pool)
	_memo[key] = e
	return e


## The facts about `p` the name is read from, as one hash.
static func _facts(p: Dictionary) -> int:
	return [str(p.get("id", "")), str(p.get("role", "")), p.get("potential"), Rating.ovr(p),
			p.get("height_cm"), str(p.get("real_name", "")), str(p.get("club", "")),
			(p.get("attr", {}) as Dictionary).hash()].hash()


const MEMO_MAX := 20000
static var _memo := {}
static var _memo_pool: Array = []
static var _memo_size := -1


## "Plays like: Marcus Bontempelli", or "" when there is nobody to compare.
static func line(p: Dictionary) -> String:
	var n := name_of(p)
	return "" if n == "" else LABEL + n
