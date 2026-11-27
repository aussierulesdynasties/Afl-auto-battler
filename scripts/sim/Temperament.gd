class_name Temperament
extends RefCounted
## A player's football temperament: one or two of eight (relationship
## overhaul, phase 1; director 2026-11-26). It is how he takes what you do:
## being dropped, backed, disciplined or praised, a promise kept or broken,
## what happens to his mates, and your Respect and Authority as coach.
##
## Every player in the league has one, real-named and generated, at every
## club. A real player's comes from his football record (a named captain
## leads, a long one-club career makes a clubman, poor discipline a fiery
## one, three clubs a mercenary), with his id breaking the ties, so it is
## the same every time the career is started. Nothing off the field is ever
## invented for him.
##
## It is kept on the player dictionary as p["temperament"] (an Array of keys)
## and saved with him. GameState.ensure_temperaments() fills every list when
## a season is built, and of() gives a player who has none (a new draftee)
## his on first read. It never touches MatchSim: other systems read it only through
## scale() to size their own moves (Opinion, Bonds, Promises).
##
## The data, words and multipliers live in data/relations/temperaments.json.

const PATH := "res://data/relations/temperaments.json"
const KEY := "temperament"
## The levers other systems may ask about. Anything else is 1.0.
const LEVERS := ["dropped", "backed", "promise_kept", "promise_broken", "discipline",
		"praised", "bond", "decay", "respect", "authority", "faction"]
## How a lever reads in a drill-down line: [what happens, "hits him" words].
const LEVER_WORDS := {
	"dropped": "Being dropped",
	"backed": "Being backed",
	"promise_kept": "A promise kept",
	"promise_broken": "A broken promise",
	"discipline": "Discipline from the coach",
	"praised": "Praise",
	"bond": "What happens to his mates and rivals",
	"respect": "Your Respect as coach",
	"authority": "Your Authority as coach",
}

static var _data: Dictionary = {}
static var _loaded := false


static func reload() -> void:
	_loaded = false
	_data = {}


static func _load() -> void:
	if _loaded:
		return
	_loaded = true
	_data = {}
	if not FileAccess.file_exists(PATH):
		push_error("Temperament: %s is missing" % PATH)
		return
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	if parsed is Dictionary:
		_data = parsed


static func _defs() -> Dictionary:
	_load()
	return _data.get("temperaments", {})


## Every temperament key, in the order the game lists them.
static func keys() -> Array:
	_load()
	var out: Array = []
	for k in _data.get("order", []):
		if _defs().has(str(k)):
			out.append(str(k))
	return out


static func is_key(key: String) -> bool:
	return _defs().has(key)


## "Quiet achiever"; "" for an unknown key.
static func label(key: String) -> String:
	return str((_defs().get(key, {}) as Dictionary).get("label", ""))


## One line in football words of how he takes things.
static func describe(key: String) -> String:
	return str((_defs().get(key, {}) as Dictionary).get("describe", ""))


## What a player of this temperament wants from his football (for ambitions).
static func ambition(key: String) -> String:
	return str((_defs().get(key, {}) as Dictionary).get("ambition", ""))


## The temperaments that never sit together on one player.
static func clashes(key: String) -> Array:
	return (_defs().get(key, {}) as Dictionary).get("clashes", [])


## His one or two temperament keys. Assigns and stores them the first time a
## player without any is read (a new draftee).
static func of(p: Dictionary) -> Array:
	var have = p.get(KEY)
	if have is Array:
		var clean: Array = []
		for k in have:
			if is_key(str(k)) and not clean.has(str(k)):
				clean.append(str(k))
		if not clean.is_empty() and clean.size() <= 2:
			if clean.size() != (have as Array).size():
				p[KEY] = clean
			return clean
	var got := assign(p)
	p[KEY] = got
	return got


static func has(p: Dictionary, key: String) -> bool:
	return of(p).has(key)


## Gives every player in `players` a temperament if he has none. Returns how
## many were newly given one.
static func ensure_all(players: Array) -> int:
	var n := 0
	for p in players:
		if p is Dictionary and not ((p as Dictionary).get(KEY) is Array):
			of(p)
			n += 1
	return n


## The product of his temperaments' multipliers for `lever`, held between
## the file's scale_min and scale_max. 1.0 when none of his cares.
static func scale(p: Dictionary, lever: String) -> float:
	var v := 1.0
	for k in of(p):
		v *= float(((_defs()[k] as Dictionary).get("levers", {}) as Dictionary).get(lever, 1.0))
	return clampf(v, float(_data.get("scale_min", 0.5)), float(_data.get("scale_max", 2.0)))


## Exactly what his temperaments do, for a drill-down: one entry per lever
## one of his temperaments moves, [{key, label, lever, mult, text}], in the
## order of his temperaments then LEVERS.
static func reactions(p: Dictionary) -> Array:
	var out: Array = []
	for k in of(p):
		var levers: Dictionary = (_defs()[k] as Dictionary).get("levers", {})
		for lever in LEVERS:
			if not levers.has(lever):
				continue
			var m := float(levers[lever])
			if is_equal_approx(m, 1.0):
				continue
			out.append({"key": k, "label": label(k), "lever": lever, "mult": m, "text": reaction_text(lever, m)})
	return out


## "A broken promise counts 40% more with him." / "He holds on to things 20% longer."
static func reaction_text(lever: String, mult: float) -> String:
	var pct := roundi(absf(mult - 1.0) * 100.0)
	if lever == "faction":
		return ("He is %d%% quicker to stand with unhappy teammates." if mult > 1.0
				else "He is %d%% slower to stand with unhappy teammates.") % pct
	if lever == "decay":
		return ("He gets over things %d%% faster." if mult > 1.0 else "He holds on to things %d%% longer.") % pct
	var what := str(LEVER_WORDS.get(lever, lever))
	return "%s counts %d%% %s with him." % [what, pct, "more" if mult > 1.0 else "less"]


## The temperaments he would be given now, from his record and his id. Pure:
## stores nothing (of() stores it).
static func assign(p: Dictionary) -> Array:
	var all := keys()
	if all.is_empty():
		return []
	var w := weights(p)
	var rng := RandomNumberGenerator.new()
	rng.seed = ("temperament|" + str(p.get("id", p.get("real_name", "")))).hash()
	# A club's named captain leads: that is the record, not a roll.
	var first := "leader" if Leadership.role_2026(p) == "captain" and all.has("leader") else _pick(w, all, rng)
	var out: Array = [first]
	var roll := rng.randf()
	if roll < float(_data.get("second_chance", 0.5)):
		var rest: Array = []
		for k in all:
			if k != first and not clashes(first).has(k) and not clashes(k).has(first):
				rest.append(k)
		if not rest.is_empty():
			out.append(_pick(w, rest, rng))
	return out


static func _pick(w: Dictionary, from: Array, rng: RandomNumberGenerator) -> String:
	var total := 0.0
	for k in from:
		total += float(w.get(k, 0.0))
	var r := rng.randf() * total
	for k in from:
		r -= float(w.get(k, 0.0))
		if r <= 0.0:
			return str(k)
	return str(from[from.size() - 1])


## How strongly his record points at each temperament (every one starts at
## 1.0, or the file's start_weight, so anyone can be anything; the record
## tilts the odds). Leader starts low: it is for the voices in the rooms,
## about four or five a club (director 2026-11-26).
static func weights(p: Dictionary) -> Dictionary:
	var w := {}
	var all := keys()   # loads the file
	var start: Dictionary = _data.get("start_weight", {}) if _data.get("start_weight") is Dictionary else {}
	for k in all:
		w[k] = float(start.get(k, 1.0))
	var a: Dictionary = p.get("attr", {}) if p.get("attr") is Dictionary else {}
	var disc := float(a.get("discipline", 50))
	var star := float(a.get("star", 50))
	var age := float(p.get("age", 23))
	var games := float(Leadership.games(p))
	var tenure := float(Leadership.tenure_years(p))
	var clubs := _clubs_played(p)
	var role := str(p.get("role", ""))
	# A vice-captain or leadership-group player leans to leading; so does a
	# long-serving voice (a named captain always leads: assign()).
	var lead := float(Leadership.of(p))
	w["leader"] += maxf(0.0, lead - float(_data.get("leader_from", 55.0))) / 12.0
	w["leader"] += {"vice": 4.0, "group": 2.0}.get(Leadership.role_2026(p), 0.0)
	# Years at one club.
	if clubs <= 1:
		w["clubman"] += maxf(0.0, tenure - 4.0) * 0.4 + (1.0 if games >= 100.0 else 0.0)
	# Moving clubs.
	w["mercenary"] += maxf(0.0, float(clubs) - 1.0) * 0.9
	# Big-game quality.
	w["competitor"] += maxf(0.0, star - 60.0) / 10.0
	# Discipline: poor makes him fiery, good makes him a professional.
	w["fiery"] += maxf(0.0, 40.0 - disc) / 6.0
	w["professional"] += maxf(0.0, disc - 60.0) / 15.0 + maxf(0.0, age - 26.0) * 0.15
	w["quiet_achiever"] += maxf(0.0, disc - 55.0) / 20.0 + (minf(games, 200.0) / 200.0 if star < 60.0 else 0.0)
	# Flair and inconsistency: a young forward with a big-game streak and loose discipline.
	w["mercurial"] += maxf(0.0, star - 60.0) / 15.0 * (1.5 if disc < 45.0 else 0.5)
	if role == "FWD":
		w["mercurial"] += 0.3
	if age <= 22.0:
		w["mercurial"] += 0.3
	return w


## How many clubs his senior record has him at (his current club counts).
static func _clubs_played(p: Dictionary) -> int:
	var seen := {}
	var c = p.get("career")
	if c is Dictionary:
		for s in (c as Dictionary).get("stints", []):
			if s is Array and not (s as Array).is_empty():
				seen[str(s[0])] = true
	var now := str(p.get("club", ""))
	if now != "":
		seen[now] = true
	return seen.size()
