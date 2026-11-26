class_name Bonds
extends RefCounted
## Player-to-player bonds (relationship overhaul, phase 1; owner's brief
## 2026-11-26): close mates, rivals for the spot, mentor and protege,
## leadership allies and family. A sparse map: only active ties are stored, a
## handful per player, and a player with none simply has no entry.
##
## Where it lives: GameState.bonds, saved with the career, plain dictionaries:
##   {"v": 1, "year": <last refreshed season>,
##    "by": {<player id>: {<other id>: {"k": kind, "s": 1..3, "y": since, "rel": family word}}}}
## by[A][B]["k"] is what B is TO A ("mentor": B is A's mentor). Every tie is
## kept on both sides (mate/mate, rival/rival, ally/ally, family/family,
## mentor/protege), so either man's ties are one lookup.
##
## What it does: nothing on its own. fallout() says what a call on one player
## (drop, trade, delist, back) means to the men tied to him, as opinion moves
## with a reason in football words; Opinion and the selection preview read it
## and decide what to apply. Nothing here touches MatchSim or the match dice:
## the seeding rolls its own stream from the career seed, season and club.
## Every club is seeded by the same rule, yours included.
##
## Real players: ties are locker-room ones only (a teammate his age, a senior
## man at his position, the club's named leaders, a teammate competing for his
## spot, sourced family). Nothing off-field is invented about anyone.

const PATH := "res://data/relations/bonds.json"
const VERSION := 1
const KINDS := ["mate", "rival", "mentor", "protege", "ally", "family"]
const MIRROR := {"mate": "mate", "rival": "rival", "mentor": "protege", "protege": "mentor",
		"ally": "ally", "family": "family"}
const ACTIONS := ["drop", "trade", "delist", "back"]
const VERB := {"drop": "You dropped", "trade": "You traded", "delist": "You delisted", "back": "You backed"}
## What a kind reads as in a reason, from his side: "his close mate".
const WHAT := {"mate": "close mate", "rival": "rival for the spot", "mentor": "mentor",
		"protege": "young teammate he mentors", "ally": "fellow leader", "family": "family"}
## PlayerRelations' relation (row says "I am <relation> other") -> what the other is to me.
const FAMILY_WORD := {
	"brother": "brother", "twin brother": "twin brother", "cousin": "cousin",
	"son of": "father", "grandson of": "grandfather", "nephew of": "uncle",
	"father of": "son", "grandfather of": "grandson", "uncle of": "nephew",
}

## Who qualifies for which tie.
const MENTOR_MIN_AGE := 27.0
const MENTOR_MIN_LEADERSHIP := 55
const PROTEGE_MAX_AGE := 21.0
## A protege this old has grown up: the tie becomes a mateship.
const PROTEGE_GRADUATES_AT := 25.0
const MATE_MAX_AGE_GAP := 3.0
const RIVAL_MAX_OVR_GAP := 4
const RIVAL_MAX_AGE_GAP := 6.0
const STRENGTH_MAX := 3

static var _cfg := {}


static func cfg() -> Dictionary:
	if _cfg.is_empty():
		var f := FileAccess.open(PATH, FileAccess.READ)
		var parsed: Variant = JSON.parse_string(f.get_as_text()) if f != null else null
		_cfg = parsed if parsed is Dictionary else {"per_player_cap": 4, "kinds": {}}
	return _cfg


static func kind_cfg(kind: String) -> Dictionary:
	return (cfg().get("kinds", {}) as Dictionary).get(kind, {})


static func label(kind: String) -> String:
	return str(kind_cfg(kind).get("label", kind.capitalize()))


static func cap() -> int:
	return int(cfg().get("per_player_cap", 4))


## A fresh or old-save-safe state: whatever was saved, made whole.
static func ensure(state: Variant) -> Dictionary:
	var s: Dictionary = state if state is Dictionary else {}
	if not (s.get("by") is Dictionary):
		s["by"] = {}
	s["v"] = VERSION
	if not s.has("year"):
		s["year"] = 0
	return s


# ---------------------------------------------------------------------------
# The map
# ---------------------------------------------------------------------------

## His ties as stored: {other id: {"k", "s", "y", "rel"?}}. {} when he has none.
static func of(state: Dictionary, id: String) -> Dictionary:
	return ((state.get("by", {}) as Dictionary).get(id, {}) as Dictionary)


static func kind(state: Dictionary, a: String, b: String) -> String:
	return str((of(state, a).get(b, {}) as Dictionary).get("k", ""))


static func count(state: Dictionary, id: String, with_family := false) -> int:
	var n := 0
	for o in of(state, id):
		if with_family or str(of(state, id)[o]["k"]) != "family":
			n += 1
	return n


## Tie a to b: `k` is what b is to a ("mentor": b mentors a). Both sides are
## written. An existing tie is replaced. Returns false for a bad pair.
static func form(state: Dictionary, a: String, b: String, k: String, s: int, year: int, rel := "") -> bool:
	if a == "" or b == "" or a == b or not MIRROR.has(k):
		return false
	var by: Dictionary = state["by"]
	if not by.has(a):
		by[a] = {}
	if not by.has(b):
		by[b] = {}
	var e := {"k": k, "s": clampi(s, 1, STRENGTH_MAX), "y": year}
	var m := {"k": str(MIRROR[k]), "s": e["s"], "y": year}
	if k == "family":
		e["rel"] = rel
		# A brother's brother is his brother; a father's word comes from _family_back.
		m["rel"] = rel if rel in ["brother", "twin brother", "cousin"] else ""
	by[a][b] = e
	by[b][a] = m
	return true


static func sever(state: Dictionary, a: String, b: String) -> void:
	var by: Dictionary = state["by"]
	for pair in [[a, b], [b, a]]:
		if by.has(pair[0]):
			(by[pair[0]] as Dictionary).erase(pair[1])
			if (by[pair[0]] as Dictionary).is_empty():
				by.erase(pair[0])


## Every tie he is part of goes (he has left the game).
static func forget(state: Dictionary, id: String) -> void:
	for o in of(state, id).keys():
		sever(state, id, str(o))
	(state["by"] as Dictionary).erase(id)


# ---------------------------------------------------------------------------
# Seeding and the season's turn
# ---------------------------------------------------------------------------

## Once a season (and when an older save first loads): drop ties to men who
## have left the game, let ties fade across clubs, let proteges grow up, add
## sourced and generated family, then top every club up to its share by the
## same rule. `lists` is club code -> roster; `leaders` is club code -> ids of
## its named captain and vice-captains (may be empty). Deterministic from
## (career_seed, year, club). Returns how many ties were added.
static func refresh(state: Dictionary, lists: Dictionary, year: int, career_seed: int,
		leaders: Dictionary = {}, extra_live: Array = []) -> int:
	ensure(state)
	var club_of := {}
	var by_id := {}
	for code in lists:
		for p in lists[code]:
			if p is Dictionary and str(p.get("id", "")) != "":
				club_of[str(p["id"])] = str(code)
				by_id[str(p["id"])] = p
	for p in extra_live:
		if p is Dictionary and str(p.get("id", "")) != "":
			by_id[str(p["id"])] = p
	# 1. Men no longer in the game.
	for id in (state["by"] as Dictionary).keys():
		if not by_id.has(str(id)):
			forget(state, str(id))
	# 2. A season has turned: ties apart fade, proteges grow up.
	var last := int(state.get("year", 0))
	if last > 0 and year > last:
		_age(state, club_of, by_id, year - last)
	# 3. Family, wherever each man is listed.
	var added := _family(state, by_id, year)
	# 4. Every club topped up by the same rule.
	var codes: Array = lists.keys()
	codes.sort()
	for code in codes:
		var roster: Array = (lists[code] as Array).filter(func(q): return q is Dictionary and str(q.get("id", "")) != "")
		roster.sort_custom(func(a, b): return str(a["id"]) < str(b["id"]))
		var rng := RandomNumberGenerator.new()
		rng.seed = hash(["bonds", career_seed, year, str(code)])
		added += _seed_club(state, roster, rng, year, leaders.get(code, []))
	state["year"] = year
	return added


static func _age(state: Dictionary, club_of: Dictionary, by_id: Dictionary, seasons: int) -> void:
	var by: Dictionary = state["by"]
	var ids: Array = by.keys()
	ids.sort()
	for a in ids:
		if not by.has(a):
			continue
		var others: Array = (by[a] as Dictionary).keys()
		others.sort()
		for b in others:
			if str(a) > str(b) or not (by.get(a, {}) as Dictionary).has(b):
				continue   # each pair once, from its lower id
			var e: Dictionary = by[a][b]
			var k := str(e["k"])
			if k == "family":
				continue   # family is for life
			if str(club_of.get(a, "")) != str(club_of.get(b, "")):
				var s := int(e["s"]) - seasons
				if s <= 0:
					sever(state, str(a), str(b))
					continue
				e["s"] = s
				(by[b][a] as Dictionary)["s"] = s
			if k == "mentor" or k == "protege":
				var protege := str(a) if k == "mentor" else str(b)
				if float((by_id.get(protege, {}) as Dictionary).get("age", 0.0)) >= PROTEGE_GRADUATES_AT:
					form(state, str(a), str(b), "mate", int(e["s"]), int(e["y"]))


static func _family(state: Dictionary, by_id: Dictionary, year: int) -> int:
	var added := 0
	# Sourced family: data/player_relations.csv, real players only.
	var by_key := {}
	for id in by_id:
		var p: Dictionary = by_id[id]
		if not bool(p.get("generated", false)):
			by_key[PlayerRelations._player_key(p)] = str(id)
	PlayerRelations._load()
	var keys: Array = by_key.keys()
	keys.sort()
	for k in keys:
		var a := str(by_key[k])
		for t in PlayerRelations._by_key.get(k, []):
			var ok := PlayerRelations.key(str(t["first"]), str(t["last"]), str(t["dob"]))
			var b := str(by_key.get(ok, ""))
			if b != "" and kind(state, a, b) != "family":
				form(state, a, b, "family", 3, year, str(FAMILY_WORD.get(str(t["relation"]), "")))
				_family_back(state, a, b, str(t["relation"]))
				added += 1
	# Generated family: FamilyTies' p["family"] on the younger man.
	var ids: Array = by_id.keys()
	ids.sort()
	for a in ids:
		for f in (by_id[a] as Dictionary).get("family", []):
			var b := str((f as Dictionary).get("id", ""))
			if by_id.has(b) and kind(state, str(a), b) != "family":
				var rel := str(f.get("relation", ""))
				form(state, str(a), b, "family", 3, year, str(FAMILY_WORD.get(rel, "")))
				_family_back(state, str(a), b, rel)
				added += 1
	return added


## The other side's word: a son's father sees a son.
static func _family_back(state: Dictionary, a: String, b: String, rel: String) -> void:
	var back := str(PlayerRelations.REVERSE.get(rel, rel))
	(state["by"][b][a] as Dictionary)["rel"] = str(FAMILY_WORD.get(back, ""))


## Pairs of kind `k` inside this roster (each pair once).
static func _club_pairs(state: Dictionary, ids: Dictionary, k: String) -> int:
	var n := 0
	for a in ids:
		for b in of(state, str(a)):
			if ids.has(b) and str(of(state, str(a))[b]["k"]) == k:
				n += 1
	return n if k == "mentor" or k == "protege" else n / 2


static func _room(state: Dictionary, id: String) -> bool:
	return count(state, id) < cap()


static func _free(state: Dictionary, a: String, b: String) -> bool:
	return a != b and not of(state, a).has(b) and _room(state, a) and _room(state, b)


static func _seed_club(state: Dictionary, roster: Array, rng: RandomNumberGenerator, year: int, leader_ids: Array) -> int:
	var ids := {}
	for p in roster:
		ids[str(p["id"])] = true
	var added := 0
	# Leadership allies: the named captain with his vice-captains; without a
	# named group, the club's three most followed men.
	var want := int(kind_cfg("ally").get("per_club", 2)) - _club_pairs(state, ids, "ally")
	var leaders: Array = leader_ids.filter(func(x): return ids.has(str(x)))
	if leaders.size() < 2:
		var by_lead := roster.duplicate()
		by_lead.sort_custom(func(a, b):
			var la := Leadership.of(a)
			var lb := Leadership.of(b)
			return la > lb if la != lb else str(a["id"]) < str(b["id"]))
		leaders = by_lead.slice(0, 3).map(func(q): return str(q["id"]))
	for i in range(1, leaders.size()):
		if want <= 0:
			break
		if _free(state, str(leaders[0]), str(leaders[i])):
			form(state, str(leaders[0]), str(leaders[i]), "ally", 2, year)
			want -= 1
			added += 1
	# Mentors: a young man and a senior one at his position.
	want = int(kind_cfg("mentor").get("per_club", 2)) - _club_pairs(state, ids, "mentor")
	var young := roster.filter(func(q): return float(q.get("age", 30.0)) <= PROTEGE_MAX_AGE)
	_shuffle(young, rng)
	for y in young:
		if want <= 0:
			break
		var yid := str(y["id"])
		if not _has_kind(state, yid, "mentor") and _room(state, yid):
			var seniors := roster.filter(func(q): return float(q.get("age", 0.0)) >= MENTOR_MIN_AGE \
					and str(q.get("role", "")) == str(y.get("role", "")) \
					and not _has_kind(state, str(q["id"]), "protege") and _free(state, yid, str(q["id"])) \
					and Leadership.of(q) >= MENTOR_MIN_LEADERSHIP)
			if not seniors.is_empty():
				var m: Dictionary = seniors[rng.randi() % seniors.size()]
				form(state, yid, str(m["id"]), "mentor", 2, year)
				want -= 1
				added += 1
	# Close mates: men of an age, likelier still from the same draft or state.
	want = int(kind_cfg("mate").get("per_club", 5)) - _club_pairs(state, ids, "mate")
	var order := roster.duplicate()
	_shuffle(order, rng)
	for a in order:
		if want <= 0:
			break
		var aid := str(a["id"])
		if not _room(state, aid):
			continue
		var cands: Array = []
		var weights: Array = []
		for b in roster:
			var bid := str(b["id"])
			if not _free(state, aid, bid) or absf(float(a.get("age", 0.0)) - float(b.get("age", 0.0))) > MATE_MAX_AGE_GAP:
				continue
			var w := 1.0
			if str(a.get("draft_year", "")) != "" and str(a.get("draft_year", "")) == str(b.get("draft_year", "")):
				w += 2.0
			if str(a.get("draft_state", "")) != "" and str(a.get("draft_state", "")) == str(b.get("draft_state", "")):
				w += 1.0
			if str(a.get("role", "")) == str(b.get("role", "")):
				w += 0.5
			cands.append(b)
			weights.append(w)
		if cands.is_empty():
			continue
		var b: Dictionary = cands[_weighted(weights, rng)]
		form(state, aid, str(b["id"]), "mate", 1 + rng.randi() % STRENGTH_MAX, year)
		want -= 1
		added += 1
	# Rivals for the spot: same position, close in standing and age.
	want = int(kind_cfg("rival").get("per_club", 2)) - _club_pairs(state, ids, "rival")
	_shuffle(order, rng)
	for a in order:
		if want <= 0:
			break
		var aid := str(a["id"])
		if not _room(state, aid) or _has_kind(state, aid, "rival"):
			continue
		var ao := int(Rating.ovr(a, 0))
		var cands := roster.filter(func(b): return str(b.get("role", "")) == str(a.get("role", "")) \
				and _free(state, aid, str(b["id"])) and not _has_kind(state, str(b["id"]), "rival") \
				and absi(int(Rating.ovr(b, 0)) - ao) <= RIVAL_MAX_OVR_GAP \
				and absf(float(a.get("age", 0.0)) - float(b.get("age", 0.0))) <= RIVAL_MAX_AGE_GAP)
		if cands.is_empty():
			continue
		var b: Dictionary = cands[rng.randi() % cands.size()]
		form(state, aid, str(b["id"]), "rival", 1 + rng.randi() % 2, year)
		want -= 1
		added += 1
	return added


static func _has_kind(state: Dictionary, id: String, k: String) -> bool:
	for o in of(state, id):
		if str(of(state, id)[o]["k"]) == k:
			return true
	return false


static func _shuffle(arr: Array, rng: RandomNumberGenerator) -> void:
	for i in range(arr.size() - 1, 0, -1):
		var j := rng.randi() % (i + 1)
		var t = arr[i]
		arr[i] = arr[j]
		arr[j] = t


static func _weighted(weights: Array, rng: RandomNumberGenerator) -> int:
	var total := 0.0
	for w in weights:
		total += float(w)
	var r := rng.randf() * total
	for i in weights.size():
		r -= float(weights[i])
		if r <= 0.0:
			return i
	return weights.size() - 1


# ---------------------------------------------------------------------------
# What the game reads
# ---------------------------------------------------------------------------

## His ties for a profile, strongest first: [{"id", "kind", "label", "what",
## "strength", "since", "rel", "same_club"}]. `club_of` maps ids to clubs
## (optional: same_club is false without it).
static func ties(state: Dictionary, id: String, club_of: Dictionary = {}) -> Array:
	var out: Array = []
	var mine := str(club_of.get(id, ""))
	for o in of(state, id):
		var e: Dictionary = of(state, id)[o]
		var k := str(e["k"])
		out.append({"id": str(o), "kind": k, "label": label(k), "what": _what(e),
				"strength": int(e["s"]), "since": int(e.get("y", 0)), "rel": str(e.get("rel", "")),
				"same_club": mine != "" and str(club_of.get(str(o), "")) == mine})
	out.sort_custom(func(a, b):
		return a["strength"] > b["strength"] if a["strength"] != b["strength"] else a["id"] < b["id"])
	return out


static func _what(e: Dictionary) -> String:
	if str(e["k"]) == "family" and str(e.get("rel", "")) != "":
		return str(e["rel"])
	return str(WHAT.get(str(e["k"]), str(e["k"])))


## The opinion move one tie gives for one call: the kind's number, scaled by strength.
static func move(k: String, action: String, s: int) -> int:
	var base := int((kind_cfg(k).get("fallout", {}) as Dictionary).get(action, 0))
	if base == 0:
		return 0
	var scale := float((cfg().get("strength_scale", {}) as Dictionary).get(str(s), 1.0))
	return signi(base) * maxi(1, roundi(absf(float(base)) * scale))


## What a call on player `id` means to the men tied to him, before anything is
## applied: [{"id" (who reacts), "kind" (what `id` is to him), "opinion" (the
## move on the 0-100 scale), "mark" and "scale" (the Opinion mark it lands as,
## and the scale that makes that mark equal "opinion"), "why" ("You dropped his
## close mate, Sam Day")}],
## biggest move first. `club_of` maps ids to clubs: a drop or a backing reaches
## only teammates (and family anywhere); a trade or delisting reaches everyone
## tied to him. `name` is what the reason calls him (GameDB's display name by
## default). Pure: the caller applies what it chooses.
static func fallout(state: Dictionary, id: String, action: String, club_of: Dictionary = {}, name := "") -> Array:
	var out: Array = []
	if not ACTIONS.has(action):
		return out
	if name == "":
		name = GameDB.player_display_name_by_id(id, "a teammate")
	var club := str(club_of.get(id, ""))
	for o in of(state, id):
		var oid := str(o)
		# What he is to the other man: the other man's entry about him.
		var e: Dictionary = of(state, oid).get(id, {})
		if e.is_empty():
			continue
		var k := str(e["k"])
		var near := club == "" or str(club_of.get(oid, "")) == club
		if (action == "drop" or action == "back") and not near and k != "family":
			continue
		var d := move(k, action, int(e["s"]))
		if d == 0:
			continue
		var mark := str((kind_cfg(k).get("marks", {}) as Dictionary).get(action, ""))
		var base := int((cfg().get("mark_base", {}) as Dictionary).get(mark, 0))
		out.append({"id": oid, "kind": k, "opinion": d, "mark": mark,
				"scale": float(d) / float(base) if base != 0 else 1.0,
				"why": "%s his %s, %s" % [VERB[action], _what(e), name]})
	out.sort_custom(func(a, b):
		return absi(a["opinion"]) > absi(b["opinion"]) if absi(a["opinion"]) != absi(b["opinion"]) else a["id"] < b["id"])
	return out


## The net of a fallout list: {"up", "down", "net"} in opinion points, and how
## many men each way ("pleased", "upset"), for a one-line preview.
static func fallout_total(rows: Array) -> Dictionary:
	var t := {"up": 0, "down": 0, "net": 0, "pleased": 0, "upset": 0}
	for r in rows:
		var d := int(r["opinion"])
		t["net"] += d
		if d > 0:
			t["up"] += d
			t["pleased"] += 1
		elif d < 0:
			t["down"] += d
			t["upset"] += 1
	return t


## Card actor roles (story cards' actor_b) -> the bond kind they bind to.
## "incumbent" is the rival for his spot who stands ahead of him (higher OVR).
const ACTOR_ROLES := {"close_mate": "mate", "positional_rival": "rival", "mentor": "mentor",
		"protege": "protege", "brother": "family", "family": "family", "ally": "ally", "incumbent": "rival"}


## The man a card binds as `role` beside player `id`: his strongest tie of that
## kind, a teammate first when `club_of` is given. "" when none fits (the card
## skips). `ovr_of` (id -> OVR) is only read for "incumbent".
static func actor(state: Dictionary, id: String, role: String, club_of: Dictionary = {}, ovr_of: Dictionary = {}) -> String:
	var k := str(ACTOR_ROLES.get(role, ""))
	if k == "":
		return ""
	var best := ""
	var best_score := -1
	var mine := str(club_of.get(id, ""))
	for o in of(state, id):
		var e: Dictionary = of(state, id)[o]
		if str(e["k"]) != k:
			continue
		if role == "brother" and not (str(e.get("rel", "")) in ["brother", "twin brother"]):
			continue
		if role == "incumbent" and int(ovr_of.get(str(o), 0)) <= int(ovr_of.get(id, 0)):
			continue
		var score := int(e["s"]) + (10 if mine != "" and str(club_of.get(str(o), "")) == mine else 0)
		if score > best_score or (score == best_score and str(o) < best):
			best = str(o)
			best_score = score
	return best
