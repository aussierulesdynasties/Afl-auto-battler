class_name CareerHighs
extends RefCounted
## A player's best game for goals, disposals, marks and tackles, kept on him so
## the match feed and the week's news can say a new one, once (row 121, ruling
## T5.r152): p["highs"] = {"full": bool, "games": int, "last": match key,
##   "goals": {"n", "year", "label"}, "disposals": {...}, "marks": {...}, "tackles": {...}}.
##   full    every senior game he has played is in the record, so its best is
##           his career best. Only a player whose record began before his first
##           game has it; a career on imported season totals never does, as
##           those totals hold no single game.
##   games   the senior games the record has seen (a gap clears "full")
##   last    the last match recorded, so a round run twice says nothing twice
## The record is kept on every player league-wide, so a player who joins you
## brings his bests; only yours are ever said. A high is said only when it is
## strictly above his old best, reaches the stat's floor (a routine game stays
## quiet) and comes after his first MIN_GAMES games.
##
## Pure rules and wording. GameState records after the round; MatchNotes says
## it live. Nothing here touches the match.

const STATS := ["goals", "disposals", "marks", "tackles"]
## The least a career high must be to be worth saying.
const FLOORS := {"goals": 3, "disposals": 20, "marks": 7, "tackles": 6}
## His first games set the baseline; nothing is said before this many.
const MIN_GAMES := 5
## Career-high news items a round, at most.
const MAX_NEWS := 3


## The record, or {} when there is none yet.
static func get_record(p: Dictionary) -> Dictionary:
	var h = p.get("highs")
	return h if h is Dictionary else {}


## Whether his record holds every senior game he has played.
static func complete(p: Dictionary) -> bool:
	return bool(get_record(p).get("full", false))


## His best in one game for `stat`, -1 when nothing is on record.
static func best(p: Dictionary, stat: String) -> int:
	var s = get_record(p).get(stat)
	return int((s as Dictionary).get("n", -1)) if s is Dictionary else -1


## Whether `n` would be a career high worth saying for a player with this record.
static func is_new(p: Dictionary, stat: String, n: int) -> bool:
	return complete(p) and int(get_record(p).get("games", 0)) >= MIN_GAMES \
			and n > best(p, stat) and n >= int(FLOORS.get(stat, 1))


## Records one senior game. `games_before` is his senior games before this one
## (GameState.games_played less this match); `career_full` whether his career
## is on record in full (Career.complete). `stats` is his line from the match.
## Returns the new highs worth saying, as [stat, n], biggest step past its
## floor first. A debut says nothing but sets the baseline. A match already
## recorded (`key` == last) changes nothing.
static func update(p: Dictionary, stats: Dictionary, games_before: int, career_full: bool,
		year: int, label: String, key: String) -> Array:
	var rec := get_record(p)
	if rec.is_empty():
		rec = {"full": career_full and games_before == 0, "games": games_before, "last": ""}
		p["highs"] = rec
	if str(rec.get("last", "")) == key and key != "":
		return []
	# Games he played that the record never saw: his best is no longer known.
	if int(rec.get("games", 0)) != games_before or not career_full:
		rec["full"] = false
	var out := []
	for stat in STATS:
		var n := int(float(stats.get(stat, 0)))
		if is_new(p, stat, n):
			out.append([stat, n])
		if n > best(p, stat):
			rec[stat] = {"n": n, "year": year, "label": label}
	rec["games"] = games_before + 1
	rec["last"] = key
	out.sort_custom(func(a, b): return _step(a) > _step(b))
	return out


## How far past its floor a high is, to pick the one worth saying.
static func _step(h: Array) -> float:
	return float(h[1]) / float(FLOORS.get(str(h[0]), 1))


## "four goals", "34 disposals", "nine marks", "eight tackles".
static func count_text(stat: String, n: int) -> String:
	return "%s %s" % [MatchNotes.count_word(n), stat]


## The feed's line: "Career-best four goals for Calder." A count said at a
## break may still grow: "Career-best 24 disposals for Calder, and counting."
static func feed_line(who: String, stat: String, n: int, counting := false) -> String:
	return "Career-best %s for %s%s." % [count_text(stat, n), who, ", and counting" if counting else ""]


## The news line: "Calder had a career-best 34 disposals against Carlton in Round 7."
static func news_line(who: String, stat: String, n: int, opp: String, label: String) -> String:
	var verb: String = {"goals": "kicked", "marks": "took", "tackles": "laid"}.get(stat, "had")
	var when := Firsts.when_text({"label": label, "year": 0})
	if label == "":
		when = ""
	else:
		when = " " + when.trim_suffix(", 0")
	return "%s %s a career-best %s against %s%s." % [who, verb, count_text(stat, n), GameDB.club_name(opp), when]
