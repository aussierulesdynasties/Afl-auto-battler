class_name Ambitions
extends RefCounted
## What a player wants from his season (relationship overhaul, ambitions;
## director 2026-11-26, Crusader Kings the inspiration).
##
## When a season starts, every club's players are read by the same rules
## (2026-11-09): the facts of his career (age, games, his place in the side,
## his contract, his Leadership) say which ambitions fit him, and his
## temperament leans him toward some (data/relations/ambitions.json). An
## eligible player may hold one, for the season:
##   senior_spot      a kid who wants senior games
##   bigger_role      a fringe man who wants to be a regular
##   milestone_push   a man near 50, 100, 150... games who wants it this year
##   win_now          a veteran who wants the club to win now
##   leadership_role  a man with Leadership who wants the leadership group
##   big_contract     a man in his last year who wants his club to sign him on
##
## After every round, at every club, each ambition moves: games played, the
## club's wins, the leadership group, a new contract. Met, he thinks more of
## his coach (a lasting opinion mark) and the coach's Respect grows. Once the
## rounds left cannot get him there, it sours: a lasting grievance (tag
## "ambition") that the fringe faction reads (Factions.gd), and at season's
## end he may ask to be traded (GameState._collect_trade_requests). Injured,
## it lapses with no hard feelings.
##
## State, on the player (saved with him): p["ambition"] = {"k": kind, "y":
## season, "state": active|met|soured|lapsed, "have": n, "need": n, "target":
## milestone, "c0": contract years when set}. Nothing here reaches MatchSim:
## only opinion, Respect and (through opinion) morale drift, as at every club.

const PATH := "res://data/relations/ambitions.json"
const KEY := "ambition"
const STATES := ["active", "met", "soured", "lapsed"]
const GOALS := ["games", "milestone", "wins", "leader", "contract"]
## The career games milestones an ambition can chase (AFL convention).
const MILESTONES := [50, 100, 150, 200, 250, 300, 350, 400]

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


## What is wrong with the file, one line each ([] when nothing is).
static func check(c: Dictionary) -> Array:
	var bad := []
	var hc := float(c.get("hold_chance", -1))
	if hc <= 0.0 or hc > 1.0:
		bad.append("hold_chance must be above 0 and at most 1")
	var ao := float(c.get("ask_out", -1))
	if ao < 0.0 or ao > 1.0:
		bad.append("ask_out must be from 0 to 1")
	var order: Array = c.get("order", [])
	var ks: Dictionary = c.get("kinds", {})
	if order.size() != ks.size():
		bad.append("order must list every kind once")
	for k in ks:
		if not order.has(k):
			bad.append("%s: not in order" % k)
		var e: Dictionary = ks[k]
		for f in ["label", "want", "goal"]:
			if str(e.get(f, "")) == "":
				bad.append("%s: no %s" % [k, f])
		var goal := str(e.get("goal", ""))
		if not GOALS.has(goal):
			bad.append("%s: unknown goal %s" % [k, goal])
		if (goal == "games" or goal == "wins") and int(e.get("need", 0)) <= 0:
			bad.append("%s: a %s goal needs a need above 0" % [k, goal])
		if goal == "milestone" and int(e.get("window", 0)) <= 0:
			bad.append("%s: a milestone goal needs a window above 0" % k)
		if float(e.get("weight", 0)) <= 0.0:
			bad.append("%s: weight must be above 0" % k)
		for t in (e.get("temper", {}) as Dictionary):
			if not Temperament.is_key(str(t)):
				bad.append("%s: unknown temperament %s" % [k, str(t)])
		if str(e.get("want", "")).ends_with("."):
			bad.append("%s: want is words with no full stop" % k)
	return bad


# ---------------------------------------------------------------------------
# Reading him
# ---------------------------------------------------------------------------

## His ambition this season, or {} (none, or last season's).
static func of(p: Dictionary, year: int) -> Dictionary:
	var a: Variant = p.get(KEY, {})
	if not (a is Dictionary) or int((a as Dictionary).get("y", 0)) != year:
		return {}
	return a


static func active(p: Dictionary, year: int) -> bool:
	return str(of(p, year).get("state", "")) == "active"


## Did his ambition sour this season (the trade requests read it)?
static func soured(p: Dictionary, year: int) -> bool:
	return str(of(p, year).get("state", "")) == "soured"


## The next career milestone above `games`.
static func next_milestone(games: int) -> int:
	for m in MILESTONES:
		if int(m) > games:
			return int(m)
	return 0


## The facts the kinds' "who" reads, for one player at the season's start.
## `games`: his career games; `in_side`: in his club's best 22; `leader`: in
## its leadership group.
static func fits(p: Dictionary, k: String, games: int, in_side: bool, leader: bool) -> bool:
	var e := kind_cfg(k)
	if e.is_empty():
		return false
	var who: Dictionary = e.get("who", {})
	var age := float(p.get("age", 25.0))
	if who.has("age_min") and age < float(who["age_min"]):
		return false
	if who.has("age_max") and age > float(who["age_max"]) + 0.99:
		return false
	if who.has("career_min") and games < int(who["career_min"]):
		return false
	if who.has("career_max") and games > int(who["career_max"]):
		return false
	if bool(who.get("out_of_side", false)) and in_side:
		return false
	if bool(who.get("in_side", false)) and not in_side:
		return false
	if bool(who.get("not_leader", false)) and leader:
		return false
	if who.has("leadership_min") and Leadership.of(p) < int(who["leadership_min"]):
		return false
	if who.has("contract_max") and int(p.get("contract_years", 2)) > int(who["contract_max"]):
		return false
	if str(e.get("goal", "")) == "milestone":
		var m := next_milestone(games)
		if m == 0 or m - games > int(e.get("window", 0)):
			return false
	return true


## How strongly a kind pulls him: its weight times his temperaments' lean.
static func pull(p: Dictionary, k: String) -> float:
	var e := kind_cfg(k)
	var w := float(e.get("weight", 1.0))
	var temper: Dictionary = e.get("temper", {})
	for t in Temperament.of(p):
		w *= float(temper.get(str(t), 1.0))
	return w


## A roll in [0, 1) that is the same for him in a season, however often asked.
static func roll(year: int, id: String, why: String) -> float:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash([year, "ambition", why, id])
	return rng.randf()


## Pick his ambition for the season ("" for none): whether he holds one at all
## (hold_chance), then a kind by pull.
static func pick(p: Dictionary, year: int, games: int, in_side: bool, leader: bool) -> String:
	var id := str(p.get("id", ""))
	var pool := []
	var total := 0.0
	for k in kinds():
		if fits(p, str(k), games, in_side, leader):
			var w := pull(p, str(k))
			pool.append([str(k), w])
			total += w
	if pool.is_empty() or roll(year, id, "hold") >= float(cfg().get("hold_chance", 0.5)):
		return ""
	var r := roll(year, id, "kind") * total
	for x in pool:
		r -= float(x[1])
		if r < 0.0:
			return str(x[0])
	return str(pool[-1][0])


## Set his ambition for the season. `games` his career games now.
static func start(p: Dictionary, k: String, year: int, games: int) -> Dictionary:
	var e := kind_cfg(k)
	var a := {"k": k, "y": year, "state": "active", "have": 0, "need": int(e.get("need", 1)),
			"c0": int(p.get("contract_years", 1))}
	match str(e.get("goal", "")):
		"milestone":
			a["target"] = next_milestone(games)
			a["need"] = int(a["target"]) - games
		"leader", "contract":
			a["need"] = 1
	p[KEY] = a
	return a


# ---------------------------------------------------------------------------
# Every club: the season's start, each round, the season's close
# ---------------------------------------------------------------------------

## Give every club's players their ambitions for this season, the same rule at
## every club. A player who already has one for this season keeps it. Run when
## a season starts and on load. Returns how many were set (tests).
static func ensure(gs) -> int:
	if gs.season == null:
		return 0
	var year := int(gs.season_year)
	var n := 0
	for code in gs.season.lists:
		var list: Array = gs.season.lists[code]
		var side := {}
		for q in Ratings.select_22(list)["ground"]:
			side[str(q["id"])] = true
		var lead: Dictionary = ClubStories.leader_ids(gs, str(code), list) if gs.has_method("captaincy_record") else {}
		for p in list:
			var a: Variant = p.get(KEY, {})
			if a is Dictionary and int((a as Dictionary).get("y", 0)) == year:
				continue
			var id := str(p["id"])
			var games: int = gs.games_played(p) if gs.has_method("games_played") else 0
			var k := pick(p, year, games, side.has(id), lead.has(id))
			if k == "":
				p[KEY] = {"y": year, "state": "none"}
				continue
			start(p, k, year, games)
			n += 1
	return n


## A round is played: every club's ambitions move. `results` are the round's
## matches with their rosters and scores (GameState). Returns [{"club", "p",
## "e": "met"|"soured"|"lapsed"}] for the caller's news.
static func after_round(gs, results: Array) -> Array:
	var out := []
	if gs.season == null:
		return out
	var year := int(gs.season_year)
	var left := maxi(0, int(gs.season.regular_rounds()) - int(gs.season.round_index))
	for res in results:
		var roster: Array = (res as Dictionary).get("roster", [[], []])
		var score: Array = (res as Dictionary).get("score", [0, 0])
		for side in range(2):
			var club := str(res.get("home" if side == 0 else "away", ""))
			if club == "" or not gs.season.lists.has(club):
				continue
			var played := {}
			if roster.size() > side:
				for r in roster[side]:
					played[str(r["id"])] = true
			var won := score.size() > 1 and int(score[side]) > int(score[1 - side])
			var list: Array = gs.season.lists[club]
			var lead: Dictionary = {}
			for p in list:
				var a := of(p, year)
				if str(a.get("state", "")) != "active":
					continue
				var goal := str(kind_cfg(str(a["k"])).get("goal", ""))
				match goal:
					"games", "milestone":
						if played.has(str(p["id"])):
							a["have"] = int(a["have"]) + 1
					"wins":
						if won:
							a["have"] = int(a["have"]) + 1
					"leader":
						if lead.is_empty() and gs.has_method("captaincy_record"):
							lead = ClubStories.leader_ids(gs, club, list)
							lead["_read"] = true
						if lead.has(str(p["id"])):
							a["have"] = 1
					"contract":
						if int(p.get("contract_years", 1)) > int(a.get("c0", 1)):
							a["have"] = 1
				var e := ""
				if int(a["have"]) >= int(a["need"]):
					e = "met"
				elif (goal == "games" or goal == "milestone" or goal == "wins") \
						and int(a["need"]) - int(a["have"]) > left:
					e = "lapsed" if goal != "wins" and int(p.get("injury_weeks", 0)) > 0 else "soured"
				if e != "":
					settle(gs, club, p, e)
					out.append({"club": club, "p": p, "e": e})
	return out


## The season is over: an ambition still open is judged where it stands. A
## contract waits for the off-season's signings (contract_signed); everything
## else that was not met sours (or lapses, for a man out injured).
static func season_end(gs) -> Array:
	var out := []
	if gs.season == null:
		return out
	var year := int(gs.season_year)
	for code in gs.season.lists:
		for p in gs.season.lists[code]:
			var a := of(p, year)
			if str(a.get("state", "")) != "active":
				continue
			if str(kind_cfg(str(a["k"])).get("goal", "")) == "contract":
				continue
			var e := "lapsed" if int(p.get("injury_weeks", 0)) > 0 and str(a["k"]) != "win_now" else "soured"
			settle(gs, str(code), p, e)
			out.append({"club": str(code), "p": p, "e": e})
	return out


## His club signed him on (GameState._resign): a contract ambition is met.
static func contract_signed(gs, club: String, p: Dictionary) -> bool:
	var a := of(p, int(gs.season_year))
	if str(a.get("state", "")) != "active" or str(kind_cfg(str(a["k"])).get("goal", "")) != "contract":
		return false
	a["have"] = 1
	settle(gs, club, p, "met")
	return true


## Close an ambition: met lifts his opinion and the coach's Respect; soured
## leaves a lasting grievance; lapsed leaves nothing.
static func settle(gs, club: String, p: Dictionary, how: String) -> void:
	var a: Dictionary = p.get(KEY, {})
	if a.is_empty():
		return
	a["state"] = how
	var year := int(gs.season_year)
	var when := str(gs.last_label) if str(gs.last_label) != "" else "Round %d" % int(gs.season.round_index)
	var key := Opinion.player_key(str(p["id"]))
	var label := str(kind_cfg(str(a["k"])).get("label", "")).to_lower()
	match how:
		"met":
			Opinion.add(gs.relations, key, "ambition_met", year, when, club, Temperament.scale(p, "backed"),
					"ambition", Temperament.scale(p, "decay"), "He got what he wanted this season: %s" % label)
			var r := int(cfg().get("met_respect", 0))
			if r != 0:
				Promises.move(gs, r, 0, "%s got what he wanted this season" % GameDB.player_display_name(p),
						"" if club == str(gs.my_club) else club)
		"soured":
			Opinion.add(gs.relations, key, "ambition_soured", year, when, club, Temperament.scale(p, "dropped"),
					"ambition", Temperament.scale(p, "decay"), "He did not get what he wanted this season: %s" % label)


## Would he ask out at season's end over an ambition gone sour? Rolled once a
## season, times his temperament's "faction" lever.
static func asks_out(p: Dictionary, year: int) -> bool:
	if not soured(p, year):
		return false
	var chance := float(cfg().get("ask_out", 0.0)) * Temperament.scale(p, "faction")
	return roll(year, str(p.get("id", "")), "ask_out") < chance


# ---------------------------------------------------------------------------
# Words
# ---------------------------------------------------------------------------

## His ambition as the profile says it: {"label", "want", "status", "state"}
## or {} for none. "Wants to reach 100 games this season" / "3 of 6 games so
## far, 9 rounds left."
static func profile(p: Dictionary, year: int, rounds_left: int) -> Dictionary:
	var a := of(p, year)
	if a.is_empty() or str(a.get("state", "none")) == "none":
		return {}
	var e := kind_cfg(str(a["k"]))
	var want := str(e.get("want", "")).replace("{target}", str(int(a.get("target", 0))))
	var goal := str(e.get("goal", ""))
	var status := ""
	match str(a["state"]):
		"met":
			status = "He got it. He thinks more of you for it."
		"soured":
			status = "It has gone sour. He holds it against you."
		"lapsed":
			status = "Injury took it away. He does not blame you."
		_:
			var have := int(a["have"])
			var need := int(a["need"])
			match goal:
				"games":
					status = "%d of %d games so far, %d rounds left." % [have, need, rounds_left]
				"milestone":
					status = "%d games to go, %d rounds left." % [need - have, rounds_left]
				"wins":
					status = "%d of %d wins so far, %d rounds left." % [have, need, rounds_left]
				"leader":
					status = "Name him captain or vice-captain before the season ends."
				"contract":
					status = "Sign him on and it is met."
	return {"label": str(e.get("label", "")), "want": want, "status": status, "state": str(a["state"])}
