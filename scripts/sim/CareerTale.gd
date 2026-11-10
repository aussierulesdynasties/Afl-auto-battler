class_name CareerTale
extends RefCounted
## A player's career told as a short story, from facts the save already keeps
## (procedural copy research, docs/research/PROCEDURAL_COPY_RESEARCH_2026-11-10.md
## §8; director 2026-11-10: on his sheet and on Brownlow night, up to five
## sentences, the senior coach's voice, nothing at all when there is no story
## yet, plain about a pick that fell short).
##
## Three layers kept apart. _facts reads the player and the record and builds
## one beat per angle it can prove; _choose keeps the strongest; _say writes each
## from the phrase bank (data/tales/career.json). Pure rules and wording: it
## never writes to the player or the save, invents nothing and reads no clock,
## so one save always tells one story.
##
## tell() returns [{"text", "angle", "year", "facts": {slot: value}, "key"}],
## oldest first. Every number in a sentence is one of its facts. `key` is what
## the sentence already says, in CareerRecord's skip words ("debut",
## "flag:2031", "brownlow:2032", "games:100"), so the sheet says a fact once.
##
## ctx (context() builds it from GameState):
##   name         the name the game shows for him (GameDB.player_display_name)
##   honour_roll  GameState.honour_roll
##   milestones   GameState.milestone_log
##   coached      {season: club code} for every season you coached
##   year         the season now; you coach `club` from it on
##   club         your club
##   club_name    Callable(code) -> the club's name
##   skip         what the sheet says elsewhere ("debut" in his "With us" lines)

const FILE := "res://data/tales/career.json"
## The most sentences a story runs to (director 2026-11-10: "Up to 5, like the almanac").
const MAX_SENTENCES := 5
## A pick this late or later is a risk taken; the rookie, mid-season and
## pre-season drafts always are.
const LATE_PICK := 20
## A pick this early carries a club's hopes: few games from it is a pick that fell short.
const EARLY_PICK := 20
## Fewer games than this at the club that drafted him, and gone, is falling short.
const FELL_SHORT_GAMES := 30
## A career best worth a sentence: well past the floors CareerHighs reports at.
const HIGH_FLOORS := {"goals": 6, "disposals": 35, "marks": 12, "tackles": 12}
## Story beats beyond the draft and the debut: without one there is no story yet.
const SPINE := ["draft_us", "draft_us_nopick", "draft_club", "draft_club_nopick", "debut_us", "debut_club"]
## How much each angle matters when there is more to say than room.
const WEIGHT := {
	"draft_us": 9, "draft_us_nopick": 9, "draft_club": 9, "draft_club_nopick": 9,
	"brownlow": 10, "brownlow_late": 10, "brownlow_multi": 10, "fell_short_us": 9, "fell_short_club": 9,
	"flag_us": 8, "flag_club": 8, "award": 7, "backed_done": 6, "backed_broken": 6,
	"milestone_games": 5, "milestone_goals": 4, "debut_us": 3, "debut_club": 3, "high": 2,
}
const AWARDS := [["coleman", "Coleman Medal"], ["norm_smith", "Norm Smith Medal"], ["rising_star", "Rising Star"]]
const DRAFT_WORDS := {"national": "national draft", "rookie": "rookie draft", "midseason": "mid-season draft",
		"preseason": "pre-season draft"}

static var _bank: Dictionary = {}


## The phrase bank's angles, loaded once.
static func bank() -> Dictionary:
	if _bank.is_empty():
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(FILE))
		if parsed is Dictionary and (parsed as Dictionary).get("angles") is Dictionary:
			_bank = parsed["angles"]
	return _bank


## Problems with a phrase bank, [] when it is sound: an angle with no phrase, a
## phrase using a slot its angle does not declare, or one left unclosed.
static func validate(angles: Dictionary) -> Array:
	var out := []
	var slot_re := RegEx.create_from_string("\\{([a-z_]+)\\}")
	for a in angles:
		var def = angles[a]
		if not (def is Dictionary) or not ((def as Dictionary).get("slots") is Array) \
				or not ((def as Dictionary).get("coach") is Array) or (def["coach"] as Array).is_empty():
			out.append("%s: needs slots and at least one coach phrase" % a)
			continue
		for ph in def["coach"]:
			var line := str(ph)
			for m in slot_re.search_all(line):
				if not (def["slots"] as Array).has(m.get_string(1)):
					out.append("%s: undeclared slot {%s}" % [a, m.get_string(1)])
			if slot_re.sub(line, "", true).contains("{") or slot_re.sub(line, "", true).contains("}"):
				out.append("%s: stray brace in \"%s\"" % [a, line])
	return out


## The story's context from the running career.
static func context(skip := {}) -> Dictionary:
	var coached := {}
	for e in GameState.honour_roll:
		if e is Dictionary and str(e.get("my_club", "")) != "":
			coached[int(e.get("year", 0))] = str(e["my_club"])
	return {"honour_roll": GameState.honour_roll, "milestones": GameState.milestone_log,
			"coached": coached, "year": int(GameState.season_year), "club": str(GameState.my_club),
			"club_name": func(code): return GameDB.club_name(code), "skip": skip}


## His story for the sheet or the awards night: the sentences, or [] when there
## is no story yet.
static func tell(p: Dictionary, ctx: Dictionary) -> Array:
	var beats := _facts(p, ctx)
	return _say(_choose(beats), str(p.get("id", "")))


## The story as one passage ("" when there is none).
static func text(story: Array) -> String:
	return " ".join(PackedStringArray(story.map(func(s): return str(s["text"]))))


## What the story says, as CareerRecord's skip keys.
static func keys(story: Array) -> Dictionary:
	var out := {}
	for s in story:
		for k in str(s.get("key", "")).split(",", false):
			out[k] = true
	return out


# ---------------------------------------------------------------------------
# Facts: one beat for each angle the record proves
# ---------------------------------------------------------------------------
static func _facts(p: Dictionary, ctx: Dictionary) -> Array:
	var id := str(p.get("id", ""))
	if id == "":
		return []
	var beats := []
	var name_call: Callable = ctx.get("club_name", func(code): return str(code))
	var first := str(ctx.get("name", p.get("name", ""))).strip_edges().get_slice(" ", 0)
	var career: Dictionary = p.get("career", {}) if p.get("career") is Dictionary else {}
	var stints: Array = career.get("stints", []) if career.get("stints") is Array else []
	var complete: bool = not career.is_empty() and (career.get("unknown", []) as Array).is_empty()
	var skip: Dictionary = ctx.get("skip", {})

	# The draft: who took him, where and when.
	var dy := int(p.get("drafted_year", 0))
	var pick := int(p.get("drafted_pick", 0))
	var dtype := str(p.get("drafted_type", ""))
	var dclub := str(p.get("drafted_club", ""))
	var drafted_by_us := false
	var late := false
	if dy > 0 and first != "" and (pick > 0 or DRAFT_WORDS.has(dtype)):
		var draft := str(DRAFT_WORDS.get(dtype, "draft"))
		drafted_by_us = dclub != "" and _picked_by_us(dclub, dy, dtype, ctx)
		late = pick >= LATE_PICK or (pick <= 0 and dtype in ["rookie", "midseason", "preseason"])
		var f := {"first": first, "year": dy, "draft": draft}
		if pick > 0:
			f["pick"] = pick
		var angle := "draft_us" if drafted_by_us else "draft_club"
		if not drafted_by_us:
			if dclub == "":
				angle = ""
			f["club"] = str(name_call.call(dclub))
		if angle != "":
			beats.append(_beat(angle if pick > 0 else angle + "_nopick", dy, f))

	# His debut: for you (Firsts), or his first season on a full record.
	var deb = (p.get("firsts", {}) as Dictionary).get("debut") if p.get("firsts") is Dictionary else null
	if deb is Dictionary and not skip.has("debut"):
		beats.append(_beat("debut_us", int(deb.get("year", 0)),
				{"when": Firsts.when_text(deb), "year": int(deb.get("year", 0)), "label": str(deb.get("label", ""))}, "debut"))
	elif complete and not stints.is_empty() and not skip.has("debut") and int(stints[0][1]) > Career.BEFORE_GAME:
		var c0 := str(stints[0][0])
		var y0 := int(stints[0][1])
		if not _coached(ctx, y0, c0):
			beats.append(_beat("debut_club", y0, {"club": str(name_call.call(c0)), "year": y0}, "debut"))

	# The promise of a run: the first one kept or broken.
	var led = p.get("backed", [])
	for b in (led if led is Array else []):
		if not (b is Dictionary):
			continue
		var st := str(b.get("state", ""))
		var games := int(b.get("games", 0))
		if st == "done":
			beats.append(_beat("backed_done", int(b.get("year", 0)),
					{"games": _n(games, "game"), "games_n": games, "year": int(b.get("year", 0))}))
			break
		if st == "broken":
			var played := int(b.get("played", 0))
			beats.append(_beat("backed_broken", int(b.get("year", 0)),
					{"games": _n(games, "game"), "games_n": games, "year": int(b.get("year", 0)),
					"played": _n(played, "game"), "played_n": played}))
			break

	# His biggest milestone game and goal, as your match recorded it.
	var top := {}
	var ml = ctx.get("milestones", {})
	for e in ((ml as Dictionary).get("log", []) if ml is Dictionary else []):
		if not (e is Dictionary) or str(e.get("who", "")) != "player" or str(e.get("id", "")) != id:
			continue
		var k := str(e.get("kind", ""))
		if k in ["games", "goals"] and int(e.get("value", 0)) > int((top.get(k, {}) as Dictionary).get("value", 0)):
			top[k] = e
	for k in top:
		var e: Dictionary = top[k]
		var v := int(e.get("value", 0))
		if skip.has("%s:%d" % [k, v]):
			continue
		var when := {"year": int(e.get("year", 0)), "label": str(e.get("label", ""))}
		var b := _beat("milestone_" + k, int(when["year"]), {"nth": _ordinal(v), "value": v,
				"when": Firsts.when_text(when), "year": when["year"], "label": when["label"]}, "%s:%d" % [k, v])
		b["weight"] = float(WEIGHT[b["angle"]]) + v / 100.0
		beats.append(b)

	# The Brownlow: the votes when he won it once; from his pick when it was late.
	var roll: Array = ctx.get("honour_roll", [])
	var won := _award_years(roll, id, "brownlow")
	var awarded := not won.is_empty()
	if won.size() == 1:
		var y: int = won[0]
		var votes := _brownlow_votes(roll, id, y)
		var f := {"year": y, "votes": _n(votes, "vote"), "votes_n": votes}
		var angle := "brownlow"
		if late and dy > 0:
			angle = "brownlow_late"
			f["from"] = "pick %d" % pick if pick > 0 else "the %s" % DRAFT_WORDS.get(dtype, "draft")
			if pick > 0:
				f["pick"] = pick
		if votes > 0:
			beats.append(_beat(angle, y, f, "brownlow:%d" % y))
		else:
			beats.append(_beat("award", y, {"award": "Brownlow Medal", "years": str(y), "year": y}, "brownlow:%d" % y))
	elif won.size() > 1:
		beats.append(_beat("brownlow_multi", int(won[0]), {"years": _and_years(won), "list": won},
				",".join(PackedStringArray(won.map(func(y): return "brownlow:%d" % y)))))
	for pair in AWARDS:
		var ys := _award_years(roll, id, pair[0])
		if ys.is_empty():
			continue
		awarded = true
		beats.append(_beat("award", int(ys[0]), {"award": pair[1], "years": _and_years(ys), "list": ys},
				",".join(PackedStringArray(ys.map(func(y): return "%s:%d" % [pair[0], y])))))

	# Premierships at the clubs he was on the list of that season.
	var flags := {}
	var order := []
	for e in roll:
		if not (e is Dictionary):
			continue
		var y := int(e.get("year", 0))
		var premier := str(e.get("premier", ""))
		if premier == "":
			continue
		for st in stints:
			if str(st[0]) == premier and y >= int(st[1]) and y <= int(st[2]):
				var us := _coached(ctx, y, premier)
				var key := "us" if us else premier
				if not flags.has(key):
					flags[key] = []
					order.append(key)
				(flags[key] as Array).append(y)
				break
	for key in order:
		var ys: Array = flags[key]
		var f := {"years": _and_years(ys), "list": ys, "flags": "premiership" if ys.size() == 1 else "premierships"}
		var keys_said := ",".join(PackedStringArray(ys.map(func(y): return "flag:%d" % y)))
		if key == "us":
			beats.append(_beat("flag_us", int(ys[0]), f, keys_said))
		else:
			f["club"] = str(name_call.call(key))
			beats.append(_beat("flag_club", int(ys[0]), f, keys_said))

	# An early pick that fell short: few games at the club that took him, and
	# he has left it. Never beside an award: then the pick paid elsewhere.
	if pick > 0 and pick <= EARLY_PICK and dtype in ["national", ""] and not awarded \
			and not stints.is_empty() and str(stints[0][0]) == dclub:
		var games := int(stints[0][3])
		var left := stints.size() > 1 or str(p.get("club", "")) != dclub
		if left and games < FELL_SHORT_GAMES:
			var last := int(stints[0][2])
			var f := {"games": _n(games, "game"), "games_n": games, "year": last}
			if drafted_by_us:
				beats.append(_beat("fell_short_us", last, f))
			else:
				f["club"] = str(name_call.call(dclub))
				beats.append(_beat("fell_short_club", last, f))

	# His best day, on a record that has seen every game he played.
	var highs = p.get("highs", {})
	if highs is Dictionary and bool((highs as Dictionary).get("full", false)):
		var best := ""
		var best_r := 0.0
		for s in HIGH_FLOORS:
			var h = highs.get(s)
			if h is Dictionary and int(h.get("n", 0)) >= int(HIGH_FLOORS[s]):
				var r := float(h["n"]) / float(HIGH_FLOORS[s])
				if r > best_r:
					best_r = r
					best = s
		if best != "":
			var h: Dictionary = highs[best]
			var n := int(h["n"])
			var when := {"year": int(h.get("year", 0)), "label": str(h.get("label", ""))}
			beats.append(_beat("high", int(when["year"]), {"stat": _n(n, best.trim_suffix("s")), "n": n,
					"when": Firsts.when_text(when), "year": when["year"], "label": when["label"]}))
	return beats


## Did you make this pick: you coached the club that took him in the season the
## pick was for. A mid-season pick is for the season it is made in; every other
## draft is held after a season, for the next one.
static func _picked_by_us(dclub: String, dy: int, dtype: String, ctx: Dictionary) -> bool:
	return _coached(ctx, dy if dtype == "midseason" else dy + 1, dclub)


## Did you coach `code` in season `y`: the honour roll's seasons, and from this
## season on, your club now.
static func _coached(ctx: Dictionary, y: int, code: String) -> bool:
	if y >= int(ctx.get("year", 0)):
		return code != "" and code == str(ctx.get("club", ""))
	return str((ctx.get("coached", {}) as Dictionary).get(y, "")) == code


static func _award_years(roll: Array, id: String, key: String) -> Array:
	var ys := []
	for e in roll:
		if not (e is Dictionary):
			continue
		var rows = e.get(key, [])
		if rows is Array and not (rows as Array).is_empty() and rows[0] is Dictionary \
				and str((rows[0] as Dictionary).get("id", "")) == id:
			ys.append(int(e.get("year", 0)))
	return ys


static func _brownlow_votes(roll: Array, id: String, y: int) -> int:
	for e in roll:
		if e is Dictionary and int(e.get("year", 0)) == y:
			var rows: Array = e.get("brownlow", [])
			if not rows.is_empty() and str(rows[0].get("id", "")) == id:
				return int(rows[0].get("votes", 0))
	return 0


static func _beat(angle: String, year: int, facts: Dictionary, key := "") -> Dictionary:
	return {"angle": angle, "year": year, "facts": facts, "key": key, "weight": float(WEIGHT.get(angle, 1))}


# ---------------------------------------------------------------------------
# Choose: no story without a beat past the draft and debut; the strongest five
# ---------------------------------------------------------------------------
static func _choose(beats: Array) -> Array:
	if beats.filter(func(b): return not SPINE.has(b["angle"])).is_empty():
		return []
	# Stable: weight first, then the order the facts were read in.
	for i in beats.size():
		beats[i]["i"] = i
	var ranked := beats.duplicate()
	ranked.sort_custom(func(a, b):
		if float(a["weight"]) != float(b["weight"]):
			return float(a["weight"]) > float(b["weight"])
		return int(a["i"]) < int(b["i"]))
	var kept := ranked.slice(0, MAX_SENTENCES)
	# Told in time order; the draft always opens it.
	kept.sort_custom(func(a, b):
		var da: bool = str(a["angle"]).begins_with("draft")
		var db: bool = str(b["angle"]).begins_with("draft")
		if da != db:
			return da
		if int(a["year"]) != int(b["year"]):
			return int(a["year"]) < int(b["year"])
		return int(a["i"]) < int(b["i"]))
	return kept


# ---------------------------------------------------------------------------
# Say: one phrase per angle, picked from his id
# ---------------------------------------------------------------------------
static func _say(beats: Array, id: String) -> Array:
	var out := []
	var angles := bank()
	for b in beats:
		var def: Dictionary = angles.get(b["angle"], {})
		var phrases: Array = def.get("coach", [])
		if phrases.is_empty():
			continue
		var ph := str(phrases[absi(hash("tale|%s|%s" % [id, b["angle"]])) % phrases.size()])
		var slots := {}
		for s in def.get("slots", []):
			slots[s] = str(b["facts"].get(s, ""))
		var said := ph.format(slots)
		out.append({"text": said.substr(0, 1).to_upper() + said.substr(1), "angle": b["angle"],
				"year": b["year"], "facts": b["facts"], "key": b["key"]})
	return out


# ---------------------------------------------------------------------------
# Words for numbers
# ---------------------------------------------------------------------------
## "1 game", "14 games"
static func _n(n: int, noun: String) -> String:
	return "%d %s%s" % [n, noun, "" if n == 1 else "s"]


static func _ordinal(n: int) -> String:
	var suffix := "th"
	if n % 100 < 11 or n % 100 > 13:
		suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
	return "%d%s" % [n, suffix]


## "2030", "2030 and 2032", "2028, 2030 and 2032"
static func _and_years(ys: Array) -> String:
	if ys.size() == 1:
		return str(ys[0])
	var head := ", ".join(PackedStringArray(ys.slice(0, ys.size() - 1).map(func(y): return str(y))))
	return "%s and %d" % [head, int(ys[-1])]
