class_name Opinion
extends RefCounted
## What a person thinks of his coach, and why (relationship overhaul, Phase 1,
## director 2026-11-26, DIRECTOR_BIBLE 5.167-5.170). Grown out of Trust.gd,
## which is now a name for this class so every older caller keeps working.
##
## One map, GameState.relations, keyed "p:<id>" for players (Culture keeps its
## "k:<club>:<strand>" strands in the same shape). An entry has two parts:
##
##   t     the permanent part, -100..100 trust, moved by Opinion.change with a
##         reason kept in `log`. It never drifts on its own: a broken promise or
##         a deep betrayal stays (5.170, "permanent scars").
##   mods  the live part: a short list of tagged marks, each in opinion points
##         (the 0..100 number the game shows), each fading towards 0 by its own
##         amount every round. A mark with fade 0 is permanent too.
##         {"k": key, "v": points, "f": fade a round, "tag", "why", "y", "w",
##          "c": the club he was at when it happened, "src": who caused it}
##
## The opinion the game shows is 50 + t / 2 + the live marks, 0..100. A key
## with no entry is neutral, an entry with no "mods" (every save before
## 2026-11-26) has no live part, so an older save loads exactly as it was.
##
## Whose opinion: "t" is his opinion of you. The live marks are about his
## current senior coach, which for your players is you: a rival club's player
## takes his own coach's calls the same way (every club, 2026-11-09), and his
## marks are cleared when he changes clubs (`drop_other_clubs`), so a man who
## joins you arrives with nothing live against you.
##
## Marks are defined in data/relations/modifiers.json (`def`). A caller adds
## one by its key (`add`), optionally scaled (a temperament, the coach's
## standing): the scale is the caller's, so this class needs nothing from them.

const LOWEST := -100
const HIGHEST := 100
## The most one moment can move the permanent part, either way (StoryDeck checks every card).
const STEP_MAX := 20
## Reasons kept per person, newest last.
const LOG_KEEP := 8
## Live marks kept per person: the smallest goes first when a new one arrives.
const MODS_KEEP := 8
## The most one live mark can be worth, either way, in opinion points.
const MOD_MAX := 40

## Bands, highest first: [floor, key, words]. Neutral says nothing.
const BANDS := [
	[50, "close", "Trusts you completely"],
	[20, "trusts", "Trusts you"],
	[-19, "neutral", ""],
	[-49, "wary", "Wary of you"],
	[LOWEST, "lost", "Stopped listening"],
]

## What trust does to a lift that depends on it (a talk, a promise): it lands
## harder with a player who trusts you, softer with one who doesn't.
const LIFT_SCALE := {"close": 1.4, "trusts": 1.2, "neutral": 1.0, "wary": 0.7, "lost": 0.4}

## Trust per point of the opinion the game shows (opinion()).
const PER_POINT := 2
const OPINION_LINE := "%s's opinion of you: %d out of 100"
## The same line where no name is to hand: never a bare "His" (director, bug bash rule).
const OPINION_LINE_ANY := "The player's opinion of you: %d out of 100"
## A reason's move, in the opinion the game shows.
const OPINION_MOVE := "Opinion of you %+d."

const DEFS_PATH := "res://data/relations/modifiers.json"
static var _defs: Dictionary = {}


static func player_key(id: String) -> String:
	return "p:" + id


# ---------------------------------------------------------------------------
# The marks' definitions
# ---------------------------------------------------------------------------

## Every mark the game can add: key -> {v, fade, tag, why, scar?}.
static func defs() -> Dictionary:
	if _defs.is_empty():
		var f := FileAccess.open(DEFS_PATH, FileAccess.READ)
		if f != null:
			var parsed: Variant = JSON.parse_string(f.get_as_text())
			if parsed is Dictionary:
				_defs = (parsed as Dictionary).get("modifiers", {})
	return _defs


static func def(k: String) -> Dictionary:
	return defs().get(k, {})


## What is wrong with the definitions, one line each ([] when nothing is):
## the tests and the data check call it.
static func check_defs(d: Dictionary) -> Array:
	var bad := []
	for k in d:
		var e: Dictionary = d[k] if d[k] is Dictionary else {}
		var v := float(e.get("v", 0.0))
		if v == 0.0 or absf(v) > MOD_MAX:
			bad.append("%s: v must be non-zero and at most %d either way" % [k, MOD_MAX])
		if float(e.get("fade", -1.0)) < 0.0:
			bad.append("%s: fade must be 0 (permanent) or more" % k)
		if str(e.get("tag", "")) == "":
			bad.append("%s: no tag" % k)
		var why := str(e.get("why", ""))
		if why == "" or why.ends_with("."):
			bad.append("%s: why must be words with no full stop" % k)
		if bool(e.get("scar", false)) and float(e.get("fade", 0.0)) > 0.5:
			bad.append("%s: a scar fades by half a point a round at most" % k)
	return bad


# ---------------------------------------------------------------------------
# Reading it
# ---------------------------------------------------------------------------

## The permanent part alone (what Opinion.change moves).
static func base(rel: Dictionary, key: String) -> int:
	return int((rel.get(key, {}) as Dictionary).get("t", 0))


## His live marks, oldest first (the stored list: do not change it).
static func mods(rel: Dictionary, key: String) -> Array:
	var e: Dictionary = rel.get(key, {})
	return e.get("mods", []) if e.get("mods") is Array else []


## What his live marks add up to, in opinion points.
static func live(rel: Dictionary, key: String) -> float:
	var s := 0.0
	for m in mods(rel, key):
		s += float((m as Dictionary).get("v", 0.0))
	return s


## Trust, -100..100, with his live marks counted: what every rule reads
## (bands, talks, refusing to re-sign) and what opinion() turns into the
## number the game shows.
static func value(rel: Dictionary, key: String) -> int:
	return clampi(base(rel, key) + roundi(live(rel, key) * PER_POINT), LOWEST, HIGHEST)


## His opinion of you as the game shows it, 0..100 (director 2026-11-08).
static func opinion(t: int) -> int:
	return roundi(50.0 + float(t) / float(PER_POINT))


## His opinion of the coach at his club, 0..100: for your player, his opinion of
## you (value); for a rival's player, 50 and his live marks only, because his
## permanent part is about you, not his own coach.
static func coach_opinion(rel: Dictionary, key: String, mine: bool) -> int:
	if mine:
		return opinion(value(rel, key))
	return clampi(roundi(50.0 + live(rel, key)), 0, 100)


## What a trust move of `d` does to the opinion the game shows, from trust `t`
## (after one moment's limit and the ends of the scale). An even move is always
## half its size; an odd one depends on where he starts.
static func opinion_move(t: int, d: int) -> int:
	return opinion(clampi(t + clampi(d, -STEP_MAX, STEP_MAX), LOWEST, HIGHEST)) - opinion(t)


## "<name>'s opinion of you: 62 out of 100", or "The player's opinion of you: 62 out of 100".
static func opinion_line(t: int, who := "") -> String:
	return OPINION_LINE % [who, opinion(t)] if who != "" else OPINION_LINE_ANY % opinion(t)


## The lowest opinion a band starts at ("trusts" is 60).
static func band_opinion(key: String) -> int:
	for b in BANDS:
		if str(b[1]) == key:
			return opinion(int(b[0]))
	return 0


static func band(t: int) -> String:
	for b in BANDS:
		if t >= int(b[0]):
			return str(b[1])
	return "lost"


## A lift that depends on trust, scaled by his band. Only lifts scale; a cost
## is the same whoever pays it.
static func scaled(d: int, t: int) -> int:
	if d <= 0:
		return d
	return maxi(1, roundi(float(d) * float(LIFT_SCALE[band(t)])))


# ---------------------------------------------------------------------------
# The permanent part
# ---------------------------------------------------------------------------

## Move trust by `d` (clamped to one moment's limit) and keep the reason.
## Returns what actually changed.
static func change(rel: Dictionary, key: String, d: int, why: String, year: int, when: String) -> int:
	if d == 0:
		return 0
	var entry: Dictionary = rel.get(key, {})
	var before := int(entry.get("t", 0))
	var after := clampi(before + clampi(d, -STEP_MAX, STEP_MAX), LOWEST, HIGHEST)
	if after == before:
		return 0   # already at the end of the scale: nothing moved, nothing to keep
	entry["t"] = after
	var log: Array = entry.get("log", [])
	# "o": what the opinion the game shows moved, kept so the reason says it exactly.
	log.append({"y": year, "w": when, "d": after - before, "o": opinion(after) - opinion(before), "why": why})
	while log.size() > LOG_KEEP:
		log.pop_front()
	entry["log"] = log
	rel[key] = entry
	return after - before


## His reasons, newest first: [{"y", "w", "d", "o", "why"}] ("o" from 2026-11-08 on).
static func reasons(rel: Dictionary, key: String) -> Array:
	var log: Array = ((rel.get(key, {}) as Dictionary).get("log", []) as Array).duplicate()
	log.reverse()
	return log


## One reason as the profile lists it: "Round 5, 2026. You promised him a game
## and left him out. Opinion of you -4." A reason kept before the opinion was
## shown has only the trust move: half of it, rounded away from zero.
static func reason_text(r: Dictionary) -> String:
	var why := str(r.get("why", "")).strip_edges()
	if why != "" and not why.ends_with("."):
		why += "."
	var d := int(r.get("d", 0))
	var o := int(r.get("o", signi(d) * ceili(absf(float(d)) / 2.0)))
	var head := "%s, %d. %s" % [str(r.get("w", "")), int(r.get("y", 0)), why]
	return head if o == 0 else "%s %s" % [head, OPINION_MOVE % o]


# ---------------------------------------------------------------------------
# The live part
# ---------------------------------------------------------------------------

## Add the mark `k` from data/relations/modifiers.json, its size times `scale`
## (a temperament, the coach's standing: the caller's to give). `club` is where
## he is now; `src` who caused it (a player id for a mate's fallout, "" for the
## coach). The same mark from the same source does not stack: it is renewed at
## the larger of the two sizes, so a man left out four weeks running carries
## one "left out" at full size, not four. Returns the opinion points it moved,
## 0 for an unknown key or a scale of 0.
static func add(rel: Dictionary, key: String, k: String, year: int, when: String, club := "",
		scale := 1.0, src := "") -> float:
	var d := def(k)
	if d.is_empty():
		push_warning("Opinion.add: no mark called %s in %s" % [k, DEFS_PATH])
		return 0.0
	return add_raw(rel, key, k, float(d["v"]) * scale, float(d.get("fade", 1.0)), str(d.get("tag", "")),
			str(d.get("why", "")), year, when, club, src)


## The same with every part given (tests, and a card that sizes its own mark).
static func add_raw(rel: Dictionary, key: String, k: String, v: float, fade: float, tag: String,
		why: String, year: int, when: String, club := "", src := "") -> float:
	v = clampf(v, -MOD_MAX, MOD_MAX)
	if absf(v) < 0.5:
		return 0.0
	var entry: Dictionary = rel.get(key, {})
	var list: Array = entry.get("mods", []) if entry.get("mods") is Array else []
	var before := live(rel, key)
	var m := {"k": k, "v": v, "f": maxf(0.0, fade), "tag": tag, "why": why, "y": year, "w": when}
	if club != "":
		m["c"] = club
	if src != "":
		m["src"] = src
	var found := -1
	for i in list.size():
		var o: Dictionary = list[i]
		if str(o.get("k", "")) == k and str(o.get("src", "")) == src:
			found = i
			break
	if found >= 0:
		var old: Dictionary = list[found]
		if signf(float(old["v"])) == signf(v) and absf(float(old["v"])) > absf(v):
			m["v"] = float(old["v"])   # renewed, never made smaller
		list[found] = m
	else:
		list.append(m)
		while list.size() > MODS_KEEP:
			list.remove_at(_smallest(list))
	entry["mods"] = list
	rel[key] = entry
	return live(rel, key) - before


static func _smallest(list: Array) -> int:
	var at := 0
	for i in list.size():
		if absf(float((list[i] as Dictionary)["v"])) < absf(float((list[at] as Dictionary)["v"])):
			at = i
	return at


## One round passes: every live mark in the map fades by its own amount and is
## gone at 0. A permanent mark (fade 0) stays. Every club's players, once a round.
static func fade_round(rel: Dictionary) -> void:
	for key in rel:
		var entry: Variant = rel[key]
		if not (entry is Dictionary) or not (entry as Dictionary).has("mods"):
			continue
		var kept := []
		for m in (entry as Dictionary)["mods"]:
			var v := float(m["v"])
			var f := float(m.get("f", 0.0))
			if f > 0.0:
				v = maxf(0.0, v - f) if v > 0.0 else minf(0.0, v + f)
			if absf(v) >= 0.5:
				m["v"] = v
				kept.append(m)
		if kept.is_empty():
			(entry as Dictionary).erase("mods")
		else:
			(entry as Dictionary)["mods"] = kept


## A player who changed clubs keeps his opinion of you, but the marks his old
## coach left on him are gone: `club_of` is id -> his club now.
static func drop_other_clubs(rel: Dictionary, club_of: Dictionary) -> void:
	for key in rel:
		if not str(key).begins_with("p:"):
			continue
		var entry: Variant = rel[key]
		if not (entry is Dictionary) or not (entry as Dictionary).has("mods"):
			continue
		var now := str(club_of.get(str(key).substr(2), ""))
		var kept := []
		for m in (entry as Dictionary)["mods"]:
			if str((m as Dictionary).get("c", now)) == now:
				kept.append(m)
		if kept.is_empty():
			(entry as Dictionary).erase("mods")
		else:
			(entry as Dictionary)["mods"] = kept


## How many more rounds a live mark lasts: -1 for one that never fades.
static func weeks_left(m: Dictionary) -> int:
	var f := float(m.get("f", 0.0))
	if f <= 0.0:
		return -1
	# It is gone once under half a point.
	return maxi(1, ceili((absf(float(m["v"])) - 0.5) / f + 0.0001))


## His live marks as the profile lists them, biggest first:
## [{"why", "points", "weeks", "tag", "k", "src"}] (weeks -1: it stays).
static func breakdown(rel: Dictionary, key: String) -> Array:
	var out := []
	for m in mods(rel, key):
		out.append({"why": str(m.get("why", "")), "points": roundi(float(m["v"])), "weeks": weeks_left(m),
				"tag": str(m.get("tag", "")), "k": str(m.get("k", "")), "src": str(m.get("src", ""))})
	out.sort_custom(func(a, b): return absi(int(a["points"])) > absi(int(b["points"])))
	return out


## One live mark in words: "Left out while fit: -4. Gone in 4 weeks." or
## "Left out of a final: -20. It stays."
static func mark_text(b: Dictionary) -> String:
	var tail := "It stays." if int(b["weeks"]) < 0 else ("Gone next week." if int(b["weeks"]) == 1
			else "Gone in %d weeks." % int(b["weeks"]))
	return "%s: %+d. %s" % [str(b["why"]), int(b["points"]), tail]


## The mark a fit man left out takes: in a final, or as one of the club's best
## (rated `star_ovr` or more, the morale sting's line), or plain.
static func drop_mark(ovr: int, final: bool, star_ovr := 78) -> String:
	return "dropped_final" if final else ("dropped_star" if ovr >= star_ovr else "dropped")


## What adding mark `k` would move his shown opinion by, without adding it
## (the selection preview): renewing a mark he already carries can move it by
## less, or not at all.
static func preview(rel: Dictionary, key: String, k: String, scale := 1.0, src := "") -> int:
	var copy := {key: (rel.get(key, {}) as Dictionary).duplicate(true)}
	var before := opinion(value(copy, key))
	add(copy, key, k, 0, "", "", scale, src)
	return opinion(value(copy, key)) - before
