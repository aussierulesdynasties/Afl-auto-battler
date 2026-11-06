class_name Challenge
extends RefCounted
## Challenge starts (TODO row 114, Director Bible ruling 115): a career can
## begin with one constraint, said up front at New career, beside League
## redraft and Real 2026 lists.
##   Youth only - no trades for, or signings of, players over 24.
##   Rebuild    - the bottom club of the real 2026 ladder, its three best gone.
##   Your goal  - a goal the coach sets himself; the club annual marks the
##                season it is met. No goal is recommended or preselected.
##
## GameState.challenge holds it (saved; older saves have none and load as {}):
##   {} - no challenge
##   {"kind": "youth"}
##   {"kind": "rebuild", "club": code, "gone": [{id, name, generic_name, real_name}]}
##   {"kind": "goal", "goal": id, "met_year": 0 until the season it is met}
## Only your club is bound. Rival clubs recruit as they always do.

const KINDS := ["youth", "rebuild", "goal"]
## Youth only: a player is over the line at 25 or older at the time of the move.
const MAX_AGE := 24
## Rebuild: how many of the bottom club's best leave before you start.
const REBUILD_GONE := 3
const COACH_GAMES := 300
## The goals on offer, in the order shown. Ruling 115 asks for a self-set
## goal and names none; these two are the examples in proposal P-56.
const GOAL_ORDER := ["flag_homegrown", "coach_300"]
const GOALS := {
	"flag_homegrown": "Win a flag with a home-grown 22",
	"coach_300": "Coach 300 games",
}


static func kind(gs) -> String:
	var c = gs.challenge
	return str(c.get("kind", "")) if c is Dictionary else ""


static func label(k: String) -> String:
	match k:
		"youth":
			return "Youth only"
		"rebuild":
			return "Rebuild"
		"goal":
			return "Your goal"
	return "None"


## The rule, said once at New career, before anything is chosen.
static func rule_line(k: String) -> String:
	match k:
		"youth":
			return "Youth only: you cannot trade for, sign or draft a player over 24. Re-signing your own players is fine. Rival clubs are not bound."
		"rebuild":
			var bottom := bottom_club(GameDB.active_clubs(GameDB.START_YEAR))
			var who := GameDB.club_name(bottom) if bottom != "" else "the club that finished last"
			return "Rebuild: you take over %s, last in 2026, and its three best players walk out before you start. Real 2026 lists only." % who
		"goal":
			return "Your goal: pick one. Nothing changes in the game; the club annual marks the season you reach it."
	return "A normal career, with no extra rule."


static func goal_words(id: String) -> String:
	return str(GOALS.get(id, ""))


static func goal_detail(id: String) -> String:
	match id:
		"flag_homegrown":
			return "Win a premiership with every player in your Grand Final side first drafted by your club."
		"coach_300":
			return "Coach 300 games, finals included, across your career."
	return ""


## Is he 25 or older? Picks and empty entries never are.
static func over_age(p: Dictionary) -> bool:
	if p.is_empty() or Contracts.is_pick(p):
		return false
	return int(floor(float(p.get("age", 0)))) > MAX_AGE


## The age cap your drafts carry (Draft.user_max_age): 0 for none.
static func max_age(gs) -> int:
	return MAX_AGE if kind(gs) == "youth" else 0


## Why your club cannot bring him in under your challenge ("" when it can).
## Called wherever your club acquires a player: trades, free agency and every
## draft. Re-signing your own players never comes through here.
static func block_reason(gs, p: Dictionary) -> String:
	if p.is_empty() or Contracts.is_pick(p):
		return ""
	match kind(gs):
		"youth":
			if over_age(p):
				return "Youth only: %s is %d, and you cannot bring in a player over %d." % [
						surname(p), int(floor(float(p.get("age", 0)))), MAX_AGE]
		"rebuild":
			var id := str(p.get("id", ""))
			for g in gs.challenge.get("gone", []):
				if str(g.get("id", "")) == id:
					return "Rebuild: %s walked out when you took over and will not come back." % surname(p)
	return ""


## The player's surname, so the reason never leans on an unnamed "he".
static func surname(p: Dictionary) -> String:
	var parts := str(p.get("name", "")).strip_edges().split(" ", false)
	return parts[parts.size() - 1] if parts.size() > 0 else "This player"


## The few words on a disabled button for a player your challenge bars
## ("" when it doesn't): "Over 24", or "Walked out" for a Rebuild player.
static func short_tag(gs, p: Dictionary) -> String:
	if block_reason(gs, p) == "":
		return ""
	return "Over %d" % MAX_AGE if kind(gs) == "youth" else "Walked out"


# ---------------------------------------------------------------------------
# Rebuild
# ---------------------------------------------------------------------------
## The club that finished last on the real 2026 ladder among `active`.
static func bottom_club(active: Array) -> String:
	var ladder: Array = GameDB.ladder_2026()
	for i in range(ladder.size() - 1, -1, -1):
		var code := str(ladder[i]["club"])
		if active.has(code):
			return code
	return ""


## Take the `n` best (by overall) off `code`'s starting list and put them in
## free agency, as the delisted are: any rival may sign them, your club never
## can. The 2026 draftees are not on a list yet, so they never count.
## Returns their name records, best first.
static func strip_best(gs, code: String, n: int = REBUILD_GONE) -> Array:
	var arr: Array = gs.league_lists.get(code, [])
	var ranked := arr.duplicate()
	ranked.sort_custom(func(a, b):
		if int(a.get("overall", 0)) != int(b.get("overall", 0)):
			return int(a.get("overall", 0)) > int(b.get("overall", 0))
		return str(a["id"]) < str(b["id"]))
	var gone := []
	for p in ranked.slice(0, mini(n, ranked.size())):
		arr.erase(p)
		p["released_by"] = code
		p["comp_eligible"] = false
		p["contract_years"] = 0
		gs.free_agents.append(p)
		gone.append({"id": str(p["id"]), "name": str(p.get("name", "")),
				"generic_name": str(p.get("generic_name", "")), "real_name": str(p.get("real_name", ""))})
	return gone


## The 2026 National Draft is done and 2027 is set up: the players who walked
## out go to market among the rival clubs, as free agents do at the close of
## free agency (GameState._open_market and _decide_fa), so they play 2027
## somewhere. A player no rival can fit stays a free agent. Their deals start
## now, with no rollover tick ahead of 2027, so the extra year _resign adds
## for that tick comes off.
static func place_gone(gs) -> void:
	if kind(gs) != "rebuild" or gs.season == null:
		return
	var ids := {}
	for g in gs.challenge.get("gone", []):
		ids[str(g.get("id", ""))] = true
	var left := []
	for p in gs.free_agents:
		if ids.has(str(p.get("id", ""))):
			left.append(p)
	gs._targets_signed = {}
	for _pass in range(10):
		if left.is_empty():
			break
		for p in left:
			p.erase("offers")
		gs._open_market(left)
		var signed := 0
		for p in left.duplicate():
			if gs._decide_fa(p) != "":
				p["contract_years"] = maxi(1, int(p.get("contract_years", 1)) - 1)
				left.erase(p)
				signed += 1
		if signed == 0:
			break
	for p in left:
		p.erase("offers")


static func gone_names(gs) -> String:
	var names := []
	for g in gs.challenge.get("gone", []):
		names.append(GameDB.player_display_name(g))
	return _and(names)


static func _and(names: Array) -> String:
	if names.size() <= 1:
		return "" if names.is_empty() else str(names[0])
	return ", ".join(names.slice(0, names.size() - 1)) + " and " + str(names[-1])


# ---------------------------------------------------------------------------
# Your goal, marked in the club annual
# ---------------------------------------------------------------------------
## Mark the goal on this season's annual entry (before it is appended) the
## first season it is met. Once met it stays met; it is never marked again.
static func mark_season(gs, entry: Dictionary) -> void:
	if kind(gs) != "goal" or int(gs.challenge.get("met_year", 0)) > 0:
		return
	var id := str(gs.challenge.get("goal", ""))
	if not goal_met(gs, id, entry):
		return
	gs.challenge["met_year"] = int(entry.get("year", gs.season_year))
	entry["challenge_met"] = goal_words(id)


## Is goal `id` met with `entry` (this season, not yet in gs.almanac)?
static func goal_met(gs, id: String, entry: Dictionary) -> bool:
	match id:
		"coach_300":
			return coach_games(gs.almanac + [entry]) >= COACH_GAMES
		"flag_homegrown":
			return bool(entry.get("flag", false)) and homegrown_flag(gs)
	return false


## Home-and-away games your club has played this season, before its annual
## page is written (0 once it is). Finals count when the season closes.
static func season_games(gs) -> int:
	if gs.season == null:
		return 0
	for e in gs.almanac:
		if int(e.get("year", 0)) == int(gs.season_year):
			return 0
	return int((gs.season.ladder.get(str(gs.my_club), {}) as Dictionary).get("p", 0))


static func coach_games(seasons: Array) -> int:
	var t := Almanac.coach_record(seasons)
	return int(t["w"]) + int(t["l"]) + int(t["d"]) + int(t["finals_w"]) + int(t["finals_l"])


## Every player your club sent out in this season's Grand Final was first
## drafted by your club (p["drafted_club"]). Players who came with the starting
## lists, by trade or in free agency are not home-grown.
static func homegrown_flag(gs) -> bool:
	var res: Dictionary = gs._grand_final_result()
	var roster: Array = res.get("roster", [])
	if roster.size() < 2:
		return false
	var side := 0 if str(res.get("home", "")) == str(gs.my_club) else 1
	if side == 1 and str(res.get("away", "")) != str(gs.my_club):
		return false
	var by_id := {}
	for p in gs.my_list:
		by_id[str(p["id"])] = p
	var ids: Array = roster[side]
	if ids.is_empty():
		return false
	for r in ids:
		var p: Dictionary = by_id.get(str(r["id"]), {})
		if p.is_empty() or str(p.get("drafted_club", "")) != str(gs.my_club):
			return false
	return true


# ---------------------------------------------------------------------------
# Said on screen
# ---------------------------------------------------------------------------
## One line naming the challenge, for the draft board and the off-season
## screens ("" with no challenge).
static func stated_line(gs) -> String:
	match kind(gs):
		"youth":
			return "Youth only: no trades for, signings of or picks of players over %d." % MAX_AGE
		"rebuild":
			var who := gone_names(gs)
			var club := GameDB.club_name(str(gs.challenge.get("club", "")))
			return "Rebuild: %s, without %s." % [club, who] if who != "" else "Rebuild: %s." % club
		"goal":
			return "Your goal: %s." % goal_words(str(gs.challenge.get("goal", "")))
	return ""


## The goal and where it stands, for the annual's coach card ("" without one).
static func status_line(gs) -> String:
	if kind(gs) != "goal":
		return ""
	var id := str(gs.challenge.get("goal", ""))
	var met := int(gs.challenge.get("met_year", 0))
	if met > 0:
		return "%s. Met in %d." % [goal_words(id), met]
	if id == "coach_300":
		return "%s. %d so far." % [goal_words(id), coach_games(gs.almanac) + season_games(gs)]
	return "%s. Not met yet." % goal_words(id)
