class_name LeagueStories
extends RefCounted
## The round's big stories for the league news feed, from every match and not
## only yours (director, 2026-11-10: "use procedural stories in the news too to
## highlight big comebacks, huge margins, injury stories etc").
##
## Same three layers as the career story (CareerTale.gd, data/tales/career.json):
## _facts reads one result and proves the angles it can; _pick ranks them and
## keeps the biggest MAX_STORIES; _say writes each beat from the phrase bank
## (data/tales/league.json). A story is told only when the match's own facts
## support it, and every number in it is one of those facts.
##
## Angles, one per match (the strongest that is true):
##  - blown:    the loser led by Headlines.BLOWN or more at a break;
##  - comeback: the winner trailed by Headlines.COMEBACK or more at a break;
##  - held_on:  the winner led by BLOWN or more at a break and won by CLOSE_WIN or less;
##  - huge:     won by HUGE or more;
##  - close:    won by Headlines.CLOSE or less, or drawn.
## Injuries are their own stories: a player of INJURY_OVR or better out for
## INJURY_WEEKS or more, who he is, what it is, how long and where it happened.
##
## Pure reading: never writes to a result, a player or the save, and reads no
## clock. The phrase is chosen from a hash of the career seed and the match, so
## one round always reads the same, and the sim is never touched.
##
## round_stories() returns [{kind, angle, club, headline, beats, weight, key, id}],
## biggest first. GameState files each as a "league_story" news item.

const FILE := "res://data/tales/league.json"
## At most this many stories in a round, so the feed is never flooded.
const MAX_STORIES := 4
## A win by this much or more is a thrashing (ten goals).
const HUGE := 60
## Injury stories: out this many weeks or more, and a player of this overall or
## better (GameState's own floor for injury news, NEWS_MIN_OVR).
const INJURY_WEEKS := 4
const INJURY_OVR := 72
## A close game's lead changes are worth a line from this many.
const CHANGES := 4
## A player is named for a run home with this many goals after the break.
const TURN_GOALS := 2
## A thrashing names its top kicker from this many goals.
const KICKER_GOALS := 4
## A thrashed side's goals are worth a line at this many or fewer.
const HELD_GOALS := 6
const BREAKS := ["quarter time", "half-time", "three-quarter time"]
const QUARTERS := ["first", "second", "third", "last"]
const WORDS := ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
		"eleven", "twelve"]
const PLACES := ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth",
		"tenth", "11th", "12th", "13th", "14th", "15th", "16th", "17th", "18th", "19th", "20th"]
## The finals places (the top ten, with the wildcard round).
const TEN := 10

static var _bank: Dictionary = {}


## The phrase bank's angles, loaded once.
static func bank() -> Dictionary:
	if _bank.is_empty():
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(FILE))
		if parsed is Dictionary and (parsed as Dictionary).get("angles") is Dictionary:
			_bank = parsed["angles"]
	return _bank


## Problems with a phrase bank, [] when it is sound: an angle with no phrase, a
## phrase using a slot its angle does not declare, or a stray brace. (The same
## rule as CareerTale.validate; see the PR note on sharing it.)
static func validate(angles: Dictionary) -> Array:
	var out := []
	var slot_re := RegEx.create_from_string("\\{([a-z_]+)\\}")
	for a in angles:
		var def = angles[a]
		if not (def is Dictionary) or not ((def as Dictionary).get("slots") is Array) \
				or not ((def as Dictionary).get("news") is Array) or (def["news"] as Array).is_empty():
			out.append("%s: needs slots and at least one news phrase" % a)
			continue
		for ph in def["news"]:
			var text := str(ph)
			for m in slot_re.search_all(text):
				if not (def["slots"] as Array).has(m.get_string(1)):
					out.append("%s: undeclared slot {%s}" % [a, m.get_string(1)])
			var bare := slot_re.sub(text, "", true)
			if bare.contains("{") or bare.contains("}"):
				out.append("%s: stray brace in \"%s\"" % [a, text])
	return out


## The context from the running career (GameState is passed in, so tests can
## build their own).
static func context(gs: Object) -> Dictionary:
	var season = gs.get("season")
	var ladder: Dictionary = season.ladder if season != null else {}
	return {
		"seed": int(season.seed) if season != null else int(gs.get("replay_seed")),
		"year": int(gs.get("season_year")),
		"my_club": str(gs.get("my_club")),
		"ladder": ladder,
		"injuries": gs.get("last_injuries"),
		"named": gs.get("_named_this_round"),
		"player": func(id): return gs.call("_find_player", id),
	}


## The round's stories, biggest first, at most MAX_STORIES.
static func round_stories(results: Array, ctx: Dictionary) -> Array:
	var before := _ladder_before(ctx.get("ladder", {}), results)
	var after := _order(ctx.get("ladder", {}))
	var cands := []
	for res in results:
		var st := _match_story(res, ctx, before, after)
		if not st.is_empty():
			cands.append(st)
	for inj in ctx.get("injuries", []):
		var st := _injury_story(inj, results, ctx)
		if not st.is_empty():
			cands.append(st)
	# Biggest first; equal weights keep the fixture's order, so a round always
	# gives the same page.
	for i in cands.size():
		cands[i]["i"] = i
	cands.sort_custom(func(a, b):
		if int(a["weight"]) != int(b["weight"]):
			return int(a["weight"]) > int(b["weight"])
		return int(a["i"]) < int(b["i"]))
	var out := cands.slice(0, MAX_STORIES)
	for st in out:
		st.erase("i")
	return out


## The story as one passage: the headline, then its beats.
static func text(st: Dictionary) -> String:
	return "%s. %s" % [str(st["headline"]), " ".join(PackedStringArray(st["beats"]))]


# ---------------------------------------------------------------------------
# A match
# ---------------------------------------------------------------------------
static func _match_story(res: Dictionary, ctx: Dictionary, before: Array, after: Array) -> Dictionary:
	var s: Array = res.get("score", [0, 0])
	if s.size() < 2:
		return {}
	var home := str(res.get("home", ""))
	var away := str(res.get("away", ""))
	var margin := absi(int(s[0]) - int(s[1]))
	var key := "%d|%s|%s|%s" % [int(ctx.get("year", 0)), str(res.get("label", res.get("round", ""))), home, away]
	var me := -1
	var my := str(ctx.get("my_club", ""))
	if my != "" and my == home:
		me = 0
	elif my != "" and my == away:
		me = 1
	# The headline already over your own result is never said again here.
	var avoid := ""
	if me >= 0:
		avoid = Headlines.for_match(res, me).trim_suffix(".").to_lower()
	var sb := _Say.new(ctx, key, avoid)
	if margin == 0:
		var hd := sb.line("draw_head", {"home": _nick(home), "away": _nick(away)})
		var beats := [sb.line("scoreline", {"line": _scoreline(res)})]
		var ch := _lead_changes(res)
		if ch >= CHANGES:
			beats.append(sb.line("close_changes", {"n": _word(ch)}))
		return _story("close", home, hd, beats, 58, key)
	var w := 0 if int(s[0]) > int(s[1]) else 1
	var l := 1 - w
	var win := str(res["home"] if w == 0 else res["away"])
	var lose := str(res["away"] if w == 0 else res["home"])
	var leads: Array = Headlines._break_leads(res, w)   # the winner's lead at each break
	var worst := 0
	var worst_at := -1
	var best := 0
	var best_at := -1
	for i in range(leads.size()):
		if int(leads[i]) < worst:
			worst = int(leads[i])
			worst_at = i
		if int(leads[i]) > best:
			best = int(leads[i])
			best_at = i
	var names := {"win": _nick(win), "lose": _nick(lose), "win_club": GameDB.club_name(win),
			"lose_club": GameDB.club_name(lose)}
	var beats := []
	# Before a club's first game the ladder order means nothing: only "top" is said.
	var lrow: Dictionary = (ctx.get("ladder", {}) as Dictionary).get(win, {})
	var first := int(lrow.get("pf", 0)) - int(s[w]) <= 0
	var ladder := _ladder_beat(sb, win, before, after, res, first)
	if -worst >= Headlines.COMEBACK:
		var down := -worst
		var since: String = BREAKS[worst_at]
		var angle := "blown" if down >= Headlines.BLOWN else "comeback"
		var hd := sb.line(angle + "_head", names.merged({"deficit": _pts(down), "lead": _pts(down), "brk": since,
				"deficit_adj": _pt_adj(down), "lead_adj": _pt_adj(down)}))
		beats.append(sb.line(angle + "_lead", names.merged({"deficit": _pts(down), "lead": _pts(down), "brk": since})))
		beats.append_array(_run_home(sb, res, w, worst_at, names["win_club"], names["lose_club"], since, ctx))
		beats.append(sb.line("scoreline", {"line": _scoreline(res)}))
		if ladder != "":
			beats.append(ladder)
		return _story(angle, lose if angle == "blown" else win, hd, beats,
				(60 if angle == "blown" else 56) + down / 3, key)
	if best >= Headlines.BLOWN and margin <= Headlines.CLOSE_WIN:
		var since: String = BREAKS[best_at]
		var hd := sb.line("held_on_head", names.merged({"lead": _pts(best), "lead_adj": _pt_adj(best),
				"margin": _pts(margin)}))
		beats.append(sb.line("held_on_lead", names.merged({"lead": _pts(best), "brk": since})))
		var gb := _after(res, best_at)
		beats.append(sb.line("held_on_turn", {"lose_club": names["lose_club"], "gb": gb[l],
				"opp_gb": gb[w], "since": since}))
		beats.append(sb.line("scoreline", {"line": _scoreline(res)}))
		if ladder != "":
			beats.append(ladder)
		return _story("held_on", win, hd, beats, 48 + best / 4, key)
	if margin >= HUGE:
		var hd := sb.line("huge_head", names.merged({"margin": _pts(margin)}))
		beats.append(sb.line("scoreline", {"line": _scoreline(res)}))
		var top := _top_kicker(res, w, 0)
		var named: Dictionary = ctx.get("named", {}) if ctx.get("named") is Dictionary else {}
		if int(top.get("goals", 0)) >= KICKER_GOALS and not named.has(str(top["id"])):
			var nm := _name(ctx, str(top["id"]))
			if nm != "":
				beats.append(sb.line("huge_kicker", {"name": nm, "goals": _goals(int(top["goals"]))}))
		var lg := int((res.get("goals", [0, 0]) as Array)[l])
		if lg <= HELD_GOALS:
			beats.append(sb.line("huge_held", {"lose_club": names["lose_club"], "goals": _goals(lg)}))
		if ladder != "":
			beats.append(ladder)
		return _story("huge", win, hd, beats, 44 + (margin - HUGE) / 3, key)
	if margin <= Headlines.CLOSE:
		var hd := sb.line("close_head", names.merged({"margin": _pts(margin)}))
		beats.append(sb.line("scoreline", {"line": _scoreline(res)}))
		var ga := _go_ahead(res, w)
		if int(ga.get("q", 0)) == 4 and bool(ga.get("goal", false)):
			var nm := _name(ctx, str(ga["id"]))
			if nm != "":
				beats.append(sb.line("close_winner", {"name": nm, "win_club": names["win_club"]}))
		var ch := _lead_changes(res)
		if ch >= CHANGES:
			beats.append(sb.line("close_changes", {"n": _word(ch)}))
		if ladder != "":
			beats.append(ladder)
		return _story("close", win, hd, beats, 46 + (Headlines.CLOSE - margin) * 2, key)
	return {}


static func _story(angle: String, club: String, headline: String, beats: Array, weight: int, key: String,
		id := "") -> Dictionary:
	return {"kind": "league_story", "angle": angle, "club": club, "headline": headline,
			"beats": beats.filter(func(b): return str(b) != ""), "weight": weight, "key": key, "id": id}


## The run home after break `at`: the goals and behinds each way, and the
## winner's top kicker in it when he kicked TURN_GOALS or more.
static func _run_home(sb: _Say, res: Dictionary, w: int, at: int, win_club: String, lose_club: String,
		since: String, ctx: Dictionary) -> Array:
	var out := []
	var gb := _after(res, at)
	out.append(sb.line("turn", {"win_club": win_club, "lose_club": lose_club, "gb": gb[w], "opp_gb": gb[1 - w], "since": since}))
	var top := _top_kicker(res, w, at + 1)
	if int(top.get("goals", 0)) >= TURN_GOALS:
		var nm := _name(ctx, str(top["id"]))
		if nm != "":
			out.append(sb.line("turn_player", {"name": nm, "goals": _word(int(top["goals"])), "since": since}))
	return out


## Each side's goals.behinds after break `at` (0: quarter time), extra time included.
static func _after(res: Dictionary, at: int) -> Array:
	var qg: Array = res.get("q_goals", [])
	var qb: Array = res.get("q_behinds", [])
	var g := [0, 0]
	var b := [0, 0]
	for q in range(at + 1, qg.size()):
		for sd in 2:
			g[sd] += int(qg[q][sd])
			b[sd] += int(qb[q][sd]) if q < qb.size() else 0
	return ["%d.%d" % [g[0], b[0]], "%d.%d" % [g[1], b[1]]]


## The side's top goalkicker in quarters after `from_q` (1-based quarters in
## the scoring log): {id, goals}, {} when nobody kicked one. Ties go to the
## first to reach the tally.
static func _top_kicker(res: Dictionary, side: int, from_q: int) -> Dictionary:
	var tally := {}
	var best := {}
	for e in res.get("scoring", []):
		var row: Array = e
		if row.size() < 5 or int(row[2]) != side or int(row[3]) != 1 or int(row[0]) <= from_q:
			continue
		var id := str(row[4])
		if id == "":
			continue
		tally[id] = int(tally.get(id, 0)) + 1
		if best.is_empty() or int(tally[id]) > int(best["goals"]):
			best = {"id": id, "goals": int(tally[id])}
	return best


## The score after which the winner stayed in front for good: {id, q, goal}.
static func _go_ahead(res: Dictionary, w: int) -> Dictionary:
	var took := {}
	var was_ahead := false
	for ev in res.get("events", []):
		var kind := str(ev.get("kind", ""))
		if kind != "goal" and kind != "behind":
			continue
		var sc: Array = ev.get("score", [0, 0])
		var ahead := int(sc[w]) > int(sc[1 - w])
		if ahead and not was_ahead:
			took = {"id": str(ev.get("player_id", "")), "q": int(ev.get("q", 0)), "goal": kind == "goal"}
		was_ahead = ahead
	return took


## How many times the lead changed hands (level scores don't count).
static func _lead_changes(res: Dictionary) -> int:
	var leader := -1
	var n := 0
	for ev in res.get("events", []):
		var kind := str(ev.get("kind", ""))
		if kind != "goal" and kind != "behind":
			continue
		var sc: Array = ev.get("score", [0, 0])
		var now := -1
		if int(sc[0]) > int(sc[1]):
			now = 0
		elif int(sc[1]) > int(sc[0]):
			now = 1
		if now >= 0:
			if leader >= 0 and now != leader:
				n += 1
			leader = now
	return n


## "Melbourne 21.12 (138) beat St Kilda 6.8 (44)", winner first.
static func _scoreline(res: Dictionary) -> String:
	var s: Array = res["score"]
	var g: Array = res.get("goals", [0, 0])
	var b: Array = res.get("behinds", [0, 0])
	var w := 0 if int(s[0]) >= int(s[1]) else 1
	var codes := [str(res["home"]), str(res["away"])]
	var verb := "drew with" if int(s[0]) == int(s[1]) else "beat"
	return "%s %d.%d (%d) %s %s %d.%d (%d)" % [GameDB.club_name(codes[w]), int(g[w]), int(b[w]), int(s[w]),
			verb, GameDB.club_name(codes[1 - w]), int(g[1 - w]), int(b[1 - w]), int(s[1 - w])]


# ---------------------------------------------------------------------------
# The ladder
# ---------------------------------------------------------------------------
## The winner's ladder line after the round, "" in finals or when the ladder
## doesn't know the club.
static func _ladder_beat(sb: _Say, code: String, before: Array, after: Array, res: Dictionary,
		first := false) -> String:
	if res.has("tag") or after.is_empty():
		return ""
	var now := after.find(code)
	var was := before.find(code)
	if now < 0 or was < 0:
		return ""
	var slots := {"club": GameDB.club_name(code), "pos": PLACES[mini(now, PLACES.size() - 1)]}
	if now == 0 and was != 0:
		return sb.line("ladder_top", slots)
	if first:
		return ""
	if now < TEN and was >= TEN:
		return sb.line("ladder_into", slots)
	if now >= TEN and was < TEN:
		return sb.line("ladder_out", slots)
	if now < was:
		return sb.line("ladder_up", slots)
	return sb.line("ladder_stay", slots)


## Club codes in ladder order: points, then percentage, then points for (as
## Season.ladder_sorted).
static func _order(ladder: Dictionary) -> Array:
	var rows := []
	for c in ladder:
		var r: Dictionary = ladder[c]
		var pa := int(r.get("pa", 0))
		rows.append({"code": str(c), "pts": int(r.get("pts", 0)), "pf": int(r.get("pf", 0)),
				"pct": (100.0 * int(r.get("pf", 0)) / pa) if pa > 0 else 0.0})
	rows.sort_custom(func(a, b):
		if int(a["pts"]) != int(b["pts"]):
			return int(a["pts"]) > int(b["pts"])
		if not is_equal_approx(float(a["pct"]), float(b["pct"])):
			return float(a["pct"]) > float(b["pct"])
		if int(a["pf"]) != int(b["pf"]):
			return int(a["pf"]) > int(b["pf"])
		return str(a["code"]) < str(b["code"]))
	return rows.map(func(r): return r["code"])


## The ladder before this round's results: each played match taken back off.
static func _ladder_before(ladder: Dictionary, results: Array) -> Array:
	var copy := {}
	for c in ladder:
		copy[c] = (ladder[c] as Dictionary).duplicate()
	for res in results:
		if res.has("tag"):
			continue
		var s: Array = res.get("score", [0, 0])
		var h := str(res.get("home", ""))
		var a := str(res.get("away", ""))
		if not copy.has(h) or not copy.has(a):
			continue
		copy[h]["pf"] = int(copy[h]["pf"]) - int(s[0])
		copy[h]["pa"] = int(copy[h]["pa"]) - int(s[1])
		copy[a]["pf"] = int(copy[a]["pf"]) - int(s[1])
		copy[a]["pa"] = int(copy[a]["pa"]) - int(s[0])
		var hp := 4 if int(s[0]) > int(s[1]) else (2 if int(s[0]) == int(s[1]) else 0)
		copy[h]["pts"] = int(copy[h]["pts"]) - hp
		copy[a]["pts"] = int(copy[a]["pts"]) - (4 - hp)
	return _order(copy)


# ---------------------------------------------------------------------------
# An injury
# ---------------------------------------------------------------------------
static func _injury_story(inj: Dictionary, results: Array, ctx: Dictionary) -> Dictionary:
	var id := str(inj.get("id", ""))
	var weeks := int(inj.get("weeks", 0))
	if id == "" or weeks < INJURY_WEEKS:
		return {}
	var player: Callable = ctx.get("player", func(_i): return {})
	var p: Dictionary = player.call(id)
	if p.is_empty() or int(p.get("overall", 0)) < INJURY_OVR:
		return {}
	var nm := GameDB.player_display_name(p)
	var club := str(inj.get("club", ""))
	var kind := Injuries.wording(str(inj.get("kind", "")))
	var key := "%d|inj|%s" % [int(ctx.get("year", 0)), id]
	var sb := _Say.new(ctx, key, "")
	var slots := {"name": nm, "weeks": _weeks(weeks), "kind": kind, "club": GameDB.club_name(club)}
	var hd := sb.line("injury_head", slots)
	var beats := [sb.line("injury_what", slots)]
	# Where it happened: the match he was hurt in, and its quarter when kept.
	for res in results:
		var side := -1
		var q := 0
		for r in res.get("injuries", []):
			if str(r.get("id", "")) == id:
				side = int(r.get("side", -1))
				q = int(r.get("q", 0))
		if side < 0:
			continue
		var s: Array = res.get("score", [0, 0])
		var opp := GameDB.club_name(str(res["away"] if side == 0 else res["home"]))
		var diff := int(s[side]) - int(s[1 - side])
		var result := "a draw" if diff == 0 else "%s %d-point %s" % [_an(absi(diff)), absi(diff),
				"win" if diff > 0 else "loss"]
		if q >= 1 and q <= 4:
			beats.append(sb.line("injury_when", {"quarter": QUARTERS[q - 1], "opp": opp, "result": result}))
		else:
			beats.append(sb.line("injury_when_plain", {"opp": opp, "result": result}))
		break
	return _story("injury", club, hd, beats, 40 + 3 * weeks, key, id)


# ---------------------------------------------------------------------------
# Words
# ---------------------------------------------------------------------------
static func _nick(code: String) -> String:
	return GameDB.club_short(code)


static func _name(ctx: Dictionary, id: String) -> String:
	if id == "":
		return ""
	var player: Callable = ctx.get("player", func(_i): return {})
	var p: Dictionary = player.call(id)
	return "" if p.is_empty() else GameDB.player_display_name(p)


static func _word(n: int) -> String:
	return WORDS[n] if n >= 0 and n < WORDS.size() else str(n)


## "1 point", "30 points"
static func _pts(n: int) -> String:
	return "%d point%s" % [n, "" if n == 1 else "s"]


## "one goal", "seven goals"
## "32-point", the form before a noun ("a 32-point lead").
static func _pt_adj(n: int) -> String:
	return "%d-point" % n


## The article before a number said aloud: "an 8", "an 11", "an 18", "an 80-odd".
static func _an(n: int) -> String:
	return "an" if n == 8 or n == 11 or n == 18 or (n >= 80 and n <= 89) else "a"


static func _goals(n: int) -> String:
	return "%s goal%s" % [_word(n), "" if n == 1 else "s"]


## "six weeks", "14 weeks"
static func _weeks(n: int) -> String:
	return "%s week%s" % [_word(n), "" if n == 1 else "s"]


static func _cap(s: String) -> String:
	return s.substr(0, 1).to_upper() + s.substr(1)


## One story's phrase picker: each angle's phrase comes from a hash of the
## career seed, the match and the angle, so a round always reads the same; a
## phrase that would repeat your own match's headline is passed over.
class _Say:
	var ctx: Dictionary
	var key: String
	var avoid: String

	func _init(c: Dictionary, k: String, a: String) -> void:
		ctx = c
		key = k
		avoid = a

	func line(angle: String, slots: Dictionary) -> String:
		var def: Dictionary = LeagueStories.bank().get(angle, {})
		var phrases: Array = def.get("news", [])
		if phrases.is_empty():
			return ""
		var start := absi(hash("league|%d|%s|%s" % [int(ctx.get("seed", 0)), key, angle])) % phrases.size()
		var fill := {}
		for s in def.get("slots", []):
			fill[s] = str(slots.get(s, ""))
		for k in phrases.size():
			var said := LeagueStories._cap(str(phrases[(start + k) % phrases.size()]).format(fill))
			if avoid == "" or not said.to_lower().contains(avoid):
				return said
		return ""
