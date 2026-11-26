class_name Factions
extends RefCounted
## Groups of unhappy players who act together (relationship overhaul, the
## factions phase; director 2026-11-26, Crusader Kings the inspiration).
##
## A player whose opinion of his coach has fallen under the line, with a
## grievance that fits a kind of group (left out, a broken promise, or a
## senior man who no longer rates the coach), stands with others like him.
## Enough of them together make a group; the group's pressure builds each
## round it stands, until it asks for something (a demand), and then gives its
## final word (an ultimatum). Answered, it settles; refused, it hardens; left
## too long, or broken up, its leader asks to be traded at season's end.
##
## Every club by the same rules (2026-11-09): a rival's coach answers his own
## groups by his own Respect and Authority (Promises.standing), and you hear
## of it only through the news. Your groups come to you as cards
## (data/stories/leadership.json, the faction_* cards), on the leader.
##
## It reaches the game only through morale and Togetherness: a member's morale
## settles a little lower while his group is pushing (morale_shift, read by
## ClubLife.drift_morale), and a demand, an answer or a break moves the club's
## Togetherness. MatchSim, Ratings and Traits read nothing here.
##
## State, saved with the career: gs.factions = {club: [group, ...]}, a group
##   {"k": kind, "members": [ids], "leader": id, "pressure": 0..100,
##    "since": week, "state": forming|demanding|ultimatum, "ult": week,
##    "refused": bool}
## and gs.factions["_past"] = {club: {kind: week it ended}} so the same kind
## waits reform_wait played rounds before it forms again. A save without the
## key has no groups.
##
## The Council (its own phase) plugs in at council_sway: the pressure a club's
## staff adds to or takes off a group each round. It is 0 until that lands.
## Card options may name the seat whose voice pitches them (pitched_by).

const PATH := "res://data/relations/factions.json"
const STATES := ["forming", "demanding", "ultimatum"]
const ANSWERS := ["meet", "refuse", "split"]
const PAST := "_past"

static var _cfg: Dictionary = {}


static func cfg() -> Dictionary:
	if _cfg.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(PATH))
		_cfg = parsed if parsed is Dictionary else {}
	return _cfg


static func reload() -> void:
	_cfg = {}


static func kind_cfg(k: String) -> Dictionary:
	return (cfg().get("kinds", {}) as Dictionary).get(k, {})


static func kinds() -> Array:
	return cfg().get("order", [])


static func num(key: String) -> int:
	return int(cfg().get(key, 0))


## What is wrong with the file, one line each ([] when nothing is).
static func check(c: Dictionary) -> Array:
	var bad := []
	for key in ["join_line", "leave_line", "join_need", "min_members", "max_members", "per_member",
			"demand_at", "ultimatum_at", "ultimatum_rounds", "pressure_max", "reform_wait"]:
		if int(c.get(key, 0)) <= 0:
			bad.append("%s must be above 0" % key)
	if int(c.get("leave_line", 0)) <= int(c.get("join_line", 0)):
		bad.append("leave_line must be above join_line, or a man would join and leave in one round")
	if int(c.get("demand_at", 0)) >= int(c.get("ultimatum_at", 0)) \
			or int(c.get("ultimatum_at", 0)) > int(c.get("pressure_max", 0)):
		bad.append("demand_at < ultimatum_at <= pressure_max")
	if int(c.get("min_members", 0)) > int(c.get("max_members", 0)):
		bad.append("min_members must be at most max_members")
	var order: Array = c.get("order", [])
	var ks: Dictionary = c.get("kinds", {})
	if order.size() != ks.size():
		bad.append("order must list every kind once")
	for k in ks:
		if not order.has(k):
			bad.append("%s: not in order" % k)
		var e: Dictionary = ks[k]
		for f in ["label", "group_word", "grievance", "who", "demand", "seat"]:
			if str(e.get(f, "")) == "":
				bad.append("%s: no %s" % [k, f])
		if not StoryEngine.ADVISOR_SEATS.has(str(e.get("seat", ""))):
			bad.append("%s: unknown council seat %s" % [k, str(e.get("seat", ""))])
	for s in ["demanding", "ultimatum"]:
		if int((c.get("morale_shift", {}) as Dictionary).get(s, 0)) > 0:
			bad.append("morale_shift.%s lifts morale: a group pushing never does" % s)
	return bad


# ---------------------------------------------------------------------------
# Reading the state
# ---------------------------------------------------------------------------

## A club's groups (the stored list: do not change it from outside).
static func of_club(gs, club: String) -> Array:
	if not (gs.factions is Dictionary):
		gs.factions = {}
	var v: Variant = gs.factions.get(club, [])
	return v if v is Array else []


## The group he stands with at his club, or {}.
static func of_player(gs, club: String, id: String) -> Dictionary:
	for f in of_club(gs, club):
		if (f["members"] as Array).has(id):
			return f
	return {}


## How much lower his morale settles while his group pushes (0 or less).
static func morale_shift(gs, club: String, id: String) -> int:
	var f := of_player(gs, club, id)
	if f.is_empty():
		return 0
	return mini(0, int((cfg().get("morale_shift", {}) as Dictionary).get(str(f["state"]), 0)))


## The Council's say on a group this round (+ pushes it on, - calms it). The
## Council phase replaces this body with Council.faction_sway(gs, club, f);
## until then a club's staff have no say.
static func council_sway(_gs, _club: String, _f: Dictionary) -> int:
	return 0


# ---------------------------------------------------------------------------
# Who stands with a group
# ---------------------------------------------------------------------------

## His opinion of his coach, 0..100 (yours, for your player).
static func opinion_of(gs, p: Dictionary, mine: bool) -> int:
	return Opinion.coach_opinion(gs.relations, Opinion.player_key(str(p["id"])), mine)


## Does he carry a live mark of this grievance (a cost, not a lift)?
static func grieves(rel: Dictionary, id: String, tag: String) -> bool:
	if tag == "any":
		return true
	for m in Opinion.mods(rel, Opinion.player_key(id)):
		if str((m as Dictionary).get("tag", "")) == tag and float(m["v"]) < 0.0:
			return true
	return false


## Is he one of a kind's men? (Apart from his opinion: see readiness.)
static func fits(gs, p: Dictionary, k: String, games: int) -> bool:
	var e := kind_cfg(k)
	if e.is_empty():
		return false
	if not grieves(gs.relations, str(p["id"]), str(e.get("grievance", "any"))):
		return false
	if k == "senior":
		return float(p.get("age", 0.0)) >= float(e.get("senior_age", 27)) or games >= int(e.get("senior_games", 120))
	return true


## How ready he is to stand with others: how far his opinion sits under the
## line, times his temperament's "faction" lever. He joins at join_need.
static func readiness(opinion: int, p: Dictionary) -> float:
	return float(num("join_line") - opinion) * Temperament.scale(p, "faction")


# ---------------------------------------------------------------------------
# One round
# ---------------------------------------------------------------------------

## A round passes at `club`: members whose opinion has come back (or who have
## left the list) drop out; aggrieved men join a group of their kind or form
## one; pressure builds; a group reaches its demand, its ultimatum, or breaks.
## `players` is the club's list; `games_of` id -> career games; `week` the
## played-week index (StoryEngine). Returns what happened, for the caller to
## act on: [{"e": "formed"|"demand"|"ultimatum"|"broken"|"faded", "f": group}].
static func round_tick(gs, club: String, players: Array, mine: bool, games_of: Dictionary, week: int) -> Array:
	var out := []
	var by_id := {}
	var op := {}
	for p in players:
		var id := str(p["id"])
		by_id[id] = p
		op[id] = opinion_of(gs, p, mine)
	var groups := of_club(gs, club)
	# Who leaves.
	for f in groups.duplicate():
		var kept := []
		for id in f["members"]:
			# He leaves once he thinks well of the coach again, or once his
			# grievance has faded and he is back over the joining line.
			if not by_id.has(id) or int(op[id]) >= num("leave_line"):
				continue
			if int(op[id]) >= num("join_line") and not fits(gs, by_id[id], str(f["k"]), int(games_of.get(id, 0))):
				continue
			kept.append(id)
		f["members"] = kept
		if kept.size() < num("min_members"):
			groups.erase(f)
			_ended(gs, club, str(f["k"]), week)
			out.append({"e": "faded", "f": f})
			continue
		if not kept.has(str(f["leader"])):
			f["leader"] = _pick_leader(kept, by_id)
	# Who joins, kind by kind (one group each man).
	var taken := {}
	for f in groups:
		for id in f["members"]:
			taken[id] = true
	var joined := {}
	for k in kinds():
		var ready := []
		for p in players:
			var id := str(p["id"])
			if taken.has(id):
				continue
			if not fits(gs, p, k, int(games_of.get(id, 0))):
				continue
			var r := readiness(int(op[id]), p)
			if r >= float(num("join_need")):
				ready.append([id, r])
		ready.sort_custom(func(a, b): return float(a[1]) > float(b[1]) if float(a[1]) != float(b[1]) else str(a[0]) < str(b[0]))
		var f := _group(groups, k)
		if f.is_empty():
			if ready.size() < num("min_members") or not _may_form(gs, club, k, week):
				continue
			f = {"k": k, "members": [], "leader": "", "pressure": 0, "since": week, "state": "forming"}
			groups.append(f)
			out.append({"e": "formed", "f": f})
		for x in ready:
			if (f["members"] as Array).size() >= num("max_members"):
				break
			(f["members"] as Array).append(str(x[0]))
			taken[str(x[0])] = true
			joined[str(f["k"])] = int(joined.get(str(f["k"]), 0)) + 1
		if str(f["leader"]) == "":
			f["leader"] = _pick_leader(f["members"], by_id)
	# Pressure, and where it takes each group.
	for f in groups.duplicate():
		var step := num("per_member") * (f["members"] as Array).size() + council_sway(gs, club, f)
		if not joined.has(str(f["k"])) and int(f["since"]) != week:
			step -= num("ease")
		f["pressure"] = clampi(int(f["pressure"]) + step, 0, num("pressure_max"))
		var st := str(f["state"])
		if st == "forming" and int(f["pressure"]) >= num("demand_at"):
			f["state"] = "demanding"
			out.append({"e": "demand", "f": f})
		elif st == "demanding" and int(f["pressure"]) >= num("ultimatum_at"):
			f["state"] = "ultimatum"
			f["ult"] = week
			out.append({"e": "ultimatum", "f": f})
		elif st == "ultimatum" and week - int(f.get("ult", week)) >= num("ultimatum_rounds"):
			groups.erase(f)
			_ended(gs, club, str(f["k"]), week)
			out.append({"e": "broken", "f": f})
	if groups.is_empty():
		gs.factions.erase(club)
	else:
		gs.factions[club] = groups
	return out


static func _group(groups: Array, k: String) -> Dictionary:
	for f in groups:
		if str(f["k"]) == k:
			return f
	return {}


## The member the group looks to: a Leader by temperament first, then the
## highest Leadership, then the id (the same answer every time).
static func _pick_leader(ids: Array, by_id: Dictionary) -> String:
	var best := ""
	var best_score := -1.0
	for id in ids:
		var p: Dictionary = by_id.get(id, {})
		var score := float(Leadership.of(p)) + (100.0 if Temperament.has(p, "leader") else 0.0)
		if score > best_score or (score == best_score and str(id) < best):
			best = str(id)
			best_score = score
	return best


static func _past(gs, club: String) -> Dictionary:
	if not (gs.factions.get(PAST) is Dictionary):
		gs.factions[PAST] = {}
	if not (gs.factions[PAST].get(club) is Dictionary):
		gs.factions[PAST][club] = {}
	return gs.factions[PAST][club]


static func _ended(gs, club: String, k: String, week: int) -> void:
	_past(gs, club)[k] = week


static func _may_form(gs, club: String, k: String, week: int) -> bool:
	var past := _past(gs, club)
	return not past.has(k) or week - int(past[k]) >= num("reform_wait")


## Every club's groups, without the bookkeeping key.
static func clubs(gs) -> Array:
	if not (gs.factions is Dictionary):
		return []
	return gs.factions.keys().filter(func(c): return str(c) != PAST)


# ---------------------------------------------------------------------------
# Answers
# ---------------------------------------------------------------------------

## The coach answers a group: "meet" (gives it what it asks), "refuse" (holds
## the line: it hardens), or "split" (breaks it up: its leader is told he can
## go); "broken" is the group giving up on an ultimatum nobody answered. `answer` itself moves the members' opinion and the coach's standing;
## the caller moves Togetherness and, on a split, the leader's trade ask
## (apply_answer below does both for GameState). Returns the effect sizes:
## {"together": d, "standing": [r, a], "mark": key, "ended": bool}.
static func answer(gs, club: String, f: Dictionary, how: String, year: int, when: String, week: int) -> Dictionary:
	var late := str(f["state"]) == "ultimatum"
	var key := how
	if how == "meet" and late:
		key = "met_late"
	elif how == "meet":
		key = "met"
	elif how == "refuse":
		key = "refused"
	var mark: String = {"met": "faction_heard", "met_late": "faction_heard", "refused": "faction_rebuffed",
			"split": "faction_split", "broken": "faction_split"}.get(key, "")
	var together := int((cfg().get("together", {}) as Dictionary).get(key, 0))
	var st: Array = (cfg().get("standing", {}) as Dictionary).get(key, [0, 0])
	var players := _players(gs, club)
	for id in f["members"]:
		var p: Dictionary = players.get(id, {})
		if p.is_empty() or mark == "":
			continue
		# A late answer is worth half to the men who had to push for it.
		var size := Temperament.scale(p, "backed" if key.begins_with("met") else "dropped") * (0.5 if key == "met_late" else 1.0)
		Opinion.add(gs.relations, Opinion.player_key(str(id)), mark, year, when, club, size, "", Temperament.scale(p, "decay"))
	Promises.move(gs, int(st[0]), int(st[1]), why_line(f, key), "" if club == str(gs.my_club) else club)
	var ended := key != "refused"
	if ended:
		of_club(gs, club).erase(f)
		if of_club(gs, club).is_empty():
			gs.factions.erase(club)
		_ended(gs, club, str(f["k"]), week)
	else:
		f["refused"] = true
		f["pressure"] = clampi(int(f["pressure"]) + num("refused_jump"), 0, num("pressure_max"))
	return {"together": together, "standing": st, "mark": mark, "ended": ended, "key": key}


## How a rival club's coach answers his group: by his own standing. One whose
## Authority leads his Respect holds the line, then breaks it up; one whose
## Respect leads hears it out. The same rule at every club but yours.
static func ai_answer(gs, club: String, f: Dictionary) -> String:
	var r := Promises.respect(gs, club)
	var a := Promises.authority(gs, club)
	if str(f["state"]) == "ultimatum":
		return "split" if a > r else "meet"
	return "refuse" if a > r and not bool(f.get("refused", false)) else "meet"


static func why_line(f: Dictionary, key: String) -> String:
	var who := str(kind_cfg(str(f["k"])).get("group_word", "a group of players"))
	match key:
		"met", "met_late":
			return "You gave %s what they asked for" % who
		"refused":
			return "You knocked back %s" % who
		"split":
			return "You broke up %s" % who
	return "%s gave up on you" % who.capitalize()


static func _players(gs, club: String) -> Dictionary:
	var out := {}
	if gs.season == null or not gs.season.lists.has(club):
		return out
	for p in gs.season.lists[club]:
		out[str(p["id"])] = p
	return out


# ---------------------------------------------------------------------------
# Words
# ---------------------------------------------------------------------------

## His group as the profile says it, or "": "Stands with the fringe players
## (4 of them, led by Sam Day). They want a fair go at selection, with one of
## them picked next week."
static func profile_line(gs, club: String, id: String, name_of: Callable) -> String:
	var f := of_player(gs, club, id)
	if f.is_empty():
		return ""
	var e := kind_cfg(str(f["k"]))
	var n := (f["members"] as Array).size()
	var lead := "he leads them" if str(f["leader"]) == id else "led by %s" % str(name_of.call(str(f["leader"])))
	var head := "Stands with %s (%d of them, %s)." % [str(e["label"]).to_lower(), n, lead]
	var state: String = {"forming": "They are talking among themselves.",
			"demanding": "They want %s." % str(e["demand"]),
			"ultimatum": "Their last word: they want %s, or their leader goes." % str(e["demand"])}.get(str(f["state"]), "")
	return "%s %s" % [head, state]


## A rival's group ending, for the league's news, or "".
static func news_line(club_name: String, f: Dictionary, how: String, leader_name: String) -> String:
	var who := str(kind_cfg(str(f["k"])).get("group_word", "a group of players"))
	match how:
		"split", "broken":
			return "%s's coach has lost %s. %s is expected to ask for a trade." % [club_name, who, leader_name]
		"meet":
			return "%s's coach has met %s halfway." % [club_name, who] if str(f["state"]) == "ultimatum" else ""
	return ""


## What an answer does, as a card's choice lists it ([kind, words], "gain" or
## "cost"): the sizes come from the files, so the gate says exactly what
## happens. Each man's temperament sizes his own mark, hence "about".
static func effect_parts(how: String, size: int, late: bool) -> Array:
	var key: String = {"meet": "met_late" if late else "met", "refuse": "refused", "split": "split"}.get(how, "")
	if key == "":
		return []
	var mark: String = {"met": "faction_heard", "met_late": "faction_heard", "refused": "faction_rebuffed", "split": "faction_split"}[key]
	var d := Opinion.def(mark)
	var pts := roundi(float(d.get("v", 0)) * (0.5 if key == "met_late" else 1.0))
	var weeks := ceili(absf(float(pts)) / maxf(0.01, float(d.get("fade", 1.0))))
	var each := "Each of the %d players in the group: opinion of you %s about %d, gone in about %d weeks." % [
			size, "up" if pts > 0 else "down", absi(pts), weeks]
	var t := int((cfg().get("together", {}) as Dictionary).get(key, 0))
	var st: Array = (cfg().get("standing", {}) as Dictionary).get(key, [0, 0])
	var out := [["gain" if pts > 0 else "cost", each]]
	if t != 0:
		out.append(["gain" if t > 0 else "cost", "Togetherness %s %d." % ["up" if t > 0 else "down", absi(t)]])
	for pair in [[int(st[0]), "Your Respect"], [int(st[1]), "Your Authority"]]:
		if int(pair[0]) != 0:
			out.append(["gain" if int(pair[0]) > 0 else "cost", "%s %s %d." % [pair[1], "up" if int(pair[0]) > 0 else "down", absi(int(pair[0]))]])
	match key:
		"met", "met_late":
			out.append(["gain", "The group is settled."])
		"refused":
			out.append(["cost", "The group pushes on, %d closer to its final word." % num("refused_jump")
					if not late else "The group has said its final word."])
		"split":
			out.append(["cost", "{name} asks to be traded when the season ends."])
			out.append(["gain", "The group is finished."])
	return out
