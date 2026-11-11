class_name RookieList
extends RefCounted
## The rookie list (TODO row 88, director 2026-11-06: "National Draft picks
## are draftees, not rookies. Add a real rookie list").
##
## Every club carries two lists inside its one list array:
##   senior list   everyone without a `rookie_list` key, up to SENIOR_SPOTS.
##                 National Draft picks, trades and free-agent signings go here.
##   rookie list   players with p["rookie_list"] == "A" (Category A), up to
##                 CAT_A_SPOTS, on the rookie wage. The Rookie Draft and the
##                 mid-season rookie draft fill it.
##                 A real-lists career also starts its real Category B rookies
##                 there ("B"), up to CAT_B_SPOTS of their own: as in the AFL,
##                 a Category B rookie takes no Category A spot and sits
##                 outside the 44 (list_size). No draft signs one.
## Senior and Category A spots together never pass Contracts.MAX_LIST, except
## where a real-lists career starts a club over it, as the real club was
## (seed_lists): it then signs no rookie, and makes no trade that leaves it
## over, until it is back under.
##
## An old save has no key on anyone, so every existing player is on the
## senior list: the migration is the default, nothing is rewritten.
##
## Rookie Draft, right after the National Draft (it opens once the rollover
## has aged the league, so a retirement has already freed its spot):
##   1. every rival club with a free senior spot upgrades its best rookies
##      into it (the coach upgrades his own from the list screen, any time
##      a senior spot is free);
##   2. the clubs pick in the National Draft's order (the ladder reversed,
##      the premiers last), round after round. A club picks while it has a
##      rookie spot; a club that passes is out of the rest of the draft.
##      The pool is the mid-season draft's: unsigned free agents and the
##      prospects every earlier draft passed over.
##   A pick goes on the rookie list on the rookie wage: two seasons for a
##   player under 21, one for anyone older. Every rival takes the best-rated
##   player left (younger first, then id), the same rating you are shown,
##   until AI_LEAVES players are left: those stay for the mid-season draft.
##   When your turn comes the draft waits for you; starting the pre-season
##   week or the season without picking passes.
##
## State: GameState.rookie_draft (saved only once it exists), {} until the
## first Rookie Draft:
##   {"year", "order": [club], "next": int, "round": int,
##    "passed": {club: true}, "picks": [{"club","id","name","from","round"}],
##    "upgrades": [{"club","id","name"}], "done": bool}

const CAT_A_SPOTS := 6
## Category B rookies, outside the Category A spots and the 44 (the AFL's rule).
const CAT_B_SPOTS := 2
const SENIOR_SPOTS := Contracts.MAX_LIST - CAT_A_SPOTS
const KIND := "rookie"
const NOBODY_LEFT_NEWS := "Rookie Draft: nobody was left when your pick came up, so your draft ended."
## Nobody to take from the start: one line instead of two.
const NOBODY_AT_ALL_NEWS := "Rookie Draft: there was nobody to take, so no club made a pick, yours included."
## Under this age a Rookie Draft pick signs for two seasons, otherwise one.
const TWO_YEAR_UNDER := 21.0
## Rival clubs leave their last Rookie Draft picks unused (the director,
## 2026-11-11): once this many players are left in the pool no rival takes
## another, so they are still there for the mid-season draft. You may still
## take any of them.
const AI_LEAVES := 12


static func is_rookie(p: Dictionary) -> bool:
	return str(p.get("rookie_list", "")) != ""


static func rookies(list: Array) -> Array:
	return list.filter(func(p): return is_rookie(p))


static func seniors(list: Array) -> Array:
	return list.filter(func(p): return not is_rookie(p))


static func rookie_count(list: Array) -> int:
	return rookies(list).size()


static func is_cat_b(p: Dictionary) -> bool:
	return str(p.get("rookie_list", "")) == "B"


static func cat_b_count(list: Array) -> int:
	return list.filter(func(p): return is_cat_b(p)).size()


## Category A rookies: the spots the Rookie Draft and mid-season draft fill.
static func cat_a_count(list: Array) -> int:
	return rookie_count(list) - cat_b_count(list)


## The list as the 44 counts it: senior and Category A, not Category B.
static func list_size(list: Array) -> int:
	return list.size() - cat_b_count(list)


static func senior_count(list: Array) -> int:
	return list.size() - rookie_count(list)


## How full a club's list is for the National Draft: the senior list.
static func draft_size(list: Array) -> int:
	return senior_count(list)


static func senior_spot_free(list: Array) -> bool:
	return senior_count(list) < SENIOR_SPOTS


static func rookie_spot_free(list: Array) -> bool:
	return cat_a_count(list) < CAT_A_SPOTS and list_size(list) < Contracts.MAX_LIST


## The rookie wage in a season (the 2027 rookie minimum, indexed).
static func wage(year: int) -> int:
	return Contracts.indexed_money_2027(Contracts.ROOKIE_MIN_2027, year)


## The senior minimum an upgraded rookie moves up to.
static func senior_wage(year: int) -> int:
	return Contracts.indexed_money_2027(Contracts.SENIOR_MIN_2027, year)


static func deal_years(p: Dictionary) -> int:
	return 2 if float(p.get("age", 20.0)) < TWO_YEAR_UNDER else 1


# ---------------------------------------------------------------------------
# A new career
# ---------------------------------------------------------------------------
## Split every club's starting list into its senior and rookie lists (a new
## career only). With `real_types` (a real-lists career), the players the real
## lists had as rookies (`list_type`, from data/list_types_2026.csv and
## data/list_additions_2026.csv) go on the rookie list: Category A rookies
## ("A") and Category B rookies ("B"), every one of them, never onto the
## senior list. Category B rookies take their own spots, never a Category A
## one. A club whose real Category A list is over CAT_A_SPOTS (West Coast
## 2026: injury replacements signed mid-season) starts over it, as the real
## club did before the rookie delisting period, and takes no Rookie Draft pick
## until it is back under; its senior list, and so its National Draft picks,
## are as the real club had them. Then, while a club has more than SENIOR_SPOTS seniors and a rookie spot
## left, its youngest senior goes on the rookie list (younger first, then id).
## A club still over SENIOR_SPOTS after that takes no National Draft pick
## until its senior list is back under the cap. Same rule for every club.
static func seed_lists(lists: Dictionary, real_types := true) -> void:
	for code in lists:
		var list: Array = lists[code]
		if real_types:
			for p in list:
				var kind := str(p.get("list_type", ""))
				if is_rookie(p):
					continue
				if kind == "rookie":
					p["rookie_list"] = "A"
				elif kind == "cat_b" or kind == "catb":
					p["rookie_list"] = "B"
		var young := seniors(list)
		young.sort_custom(func(a, b):
			if float(a.get("age", 0.0)) != float(b.get("age", 0.0)):
				return float(a.get("age", 0.0)) < float(b.get("age", 0.0))
			return str(a["id"]) < str(b["id"]))
		for p in young:
			if senior_count(list) <= SENIOR_SPOTS or cat_a_count(list) >= CAT_A_SPOTS:
				break
			p["rookie_list"] = "A"


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------
## Why this player cannot be upgraded now ("" when he can).
static func upgrade_block(gs, code: String, player_id: String) -> String:
	var list: Array = _list_of(gs, code)
	var p := _find(list, player_id)
	if p.is_empty():
		return "He is not on the list."
	if not is_rookie(p):
		return "He is already on the senior list."
	if not senior_spot_free(list):
		return "The senior list is full (%d). A senior spot opens when a player retires, is delisted or traded." % SENIOR_SPOTS
	return ""


## Move a rookie to the senior list: he takes a senior spot and his wage
## rises to the senior minimum. Same rule for every club.
static func upgrade(gs, code: String, player_id: String) -> bool:
	if upgrade_block(gs, code, player_id) != "":
		return false
	var p := _find(_list_of(gs, code), player_id)
	p.erase("rookie_list")
	p["salary"] = maxi(int(p.get("salary", 0)), senior_wage(gs.season_year))
	if code == gs.my_club:
		gs.add_news("draft", "%s is upgraded to the senior list." % GameDB.player_display_name(p))
	gs.mark_dirty()
	return true


## Rivals fill a free senior spot with their best rookie, as a list manager
## would before the Rookie Draft. Your club is never touched.
static func ai_upgrades(gs) -> Array:
	var done := []
	for code in GameDB.active_clubs(gs.season_year):
		if str(code) == gs.my_club:
			continue
		var list: Array = _list_of(gs, str(code))
		var rk := rookies(list)
		rk.sort_custom(func(a, b):
			if int(a.get("overall", 0)) != int(b.get("overall", 0)):
				return int(a.get("overall", 0)) > int(b.get("overall", 0))
			return str(a["id"]) < str(b["id"]))
		for p in rk:
			if not senior_spot_free(list):
				break
			if upgrade(gs, str(code), str(p["id"])):
				done.append({"club": str(code), "id": str(p["id"]), "name": GameDB.player_display_name(p)})
	return done


# ---------------------------------------------------------------------------
# Rookie Draft
# ---------------------------------------------------------------------------
## Open the Rookie Draft for the season that has just been rolled to.
## `order` is the National Draft's club order (worst club first).
static func open_draft(gs, order: Array) -> void:
	if gs.season == null:
		return
	if int(gs.rookie_draft.get("year", 0)) == gs.season_year:
		return
	var clubs := []
	for code in order:
		if gs.season.lists.has(str(code)) and not clubs.has(str(code)):
			clubs.append(str(code))
	# A club playing its first season was on no ladder, so the National Draft
	# order may not name it: it takes a seat at the end of the order, the same
	# rules as every other club.
	for code in GameDB.active_clubs(gs.season_year):
		if gs.season.lists.has(str(code)) and not clubs.has(str(code)):
			clubs.append(str(code))
	gs.rookie_draft = {"year": gs.season_year, "order": clubs, "next": 0, "round": 1,
			"passed": {}, "picks": [], "upgrades": ai_upgrades(gs), "done": false}
	_run(gs)


static func _current(gs) -> Dictionary:
	if int(gs.rookie_draft.get("year", 0)) != gs.season_year:
		return {}
	return gs.rookie_draft


## True while the Rookie Draft waits on your pick.
static func waiting(gs) -> bool:
	var rec := _current(gs)
	if rec.is_empty() or bool(rec.get("done", true)):
		return false
	var order: Array = rec.get("order", [])
	var i := int(rec.get("next", 0))
	return i < order.size() and str(order[i]) == gs.my_club


## The round your pick is in (0 when nothing waits).
static func round_now(gs) -> int:
	return int(gs.rookie_draft.get("round", 0)) if waiting(gs) else 0


static func _can_pick(gs, rec: Dictionary, code: String) -> bool:
	if (rec["passed"] as Dictionary).has(code):
		return false
	if code != gs.my_club and MidseasonDraft.pool(gs).size() <= AI_LEAVES:
		return false
	return rookie_spot_free(_list_of(gs, code))


## Clubs pick in order, round after round, until your turn or the end.
static func _run(gs) -> void:
	var rec: Dictionary = gs.rookie_draft
	var order: Array = rec["order"]
	var guard := 0
	while guard < 2000:
		guard += 1
		if int(rec["next"]) >= order.size():
			# A round ends: another follows while any club can still pick.
			var any := false
			for code in order:
				if _can_pick(gs, rec, str(code)):
					any = true
			if not any or MidseasonDraft.pool(gs).is_empty():
				break
			rec["next"] = 0
			rec["round"] = int(rec["round"]) + 1
		var code := str(order[int(rec["next"])])
		if _can_pick(gs, rec, code):
			if code == gs.my_club:
				if not MidseasonDraft.pool(gs).is_empty():
					gs.mark_dirty()
					return
				# Nobody left to take: no choice to make, so the draft ends
				# without stopping you, and the news says so.
				rec["nobody_left"] = true
			var left := MidseasonDraft.pool(gs)
			if left.is_empty():
				break
			_take(gs, code, left[0])
		rec["next"] = int(rec["next"]) + 1
	_finish(gs)


## Your pick (player id), or "" to pass, which ends your Rookie Draft. False
## when it is not your turn or that player has gone.
static func choose(gs, player_id: String) -> bool:
	if not waiting(gs):
		return false
	var rec: Dictionary = gs.rookie_draft
	if player_id == "":
		(rec["passed"] as Dictionary)[gs.my_club] = true
	else:
		var hit := {}
		for p in MidseasonDraft.pool(gs):
			if str(p["id"]) == player_id:
				hit = p
		if hit.is_empty() or Challenge.block_reason(gs, hit) != "":
			return false
		_take(gs, gs.my_club, hit)
	rec["next"] = int(rec["next"]) + 1
	_run(gs)
	return true


## Your pick waits but nobody is left to take: pass it, and the draft news
## says why. True if passed.
static func pass_if_nobody_left(gs) -> bool:
	if not waiting(gs) or not MidseasonDraft.pool(gs).is_empty():
		return false
	gs.rookie_draft["nobody_left"] = true
	return choose(gs, "")


## Before the pre-season week or the next round: an unmade pick is a pass.
static func settle(gs) -> void:
	if waiting(gs):
		choose(gs, "")


static func _take(gs, code: String, p: Dictionary) -> void:
	var rec: Dictionary = gs.rookie_draft
	var from := MidseasonDraft.from_word(gs, p)
	var id := str(p["id"])
	var drafted: bool = not gs.free_agents.has(p)
	if gs.free_agents.has(p):
		gs.free_agents.erase(p)
		p.erase("offers")
		p.erase("market_round")
		p.erase("market_log")
		p.erase("talks")
	else:
		gs.draftee_pool.erase(p)
		gs.drafted_draftees[id] = code
		gs._mark_drafted(p, KIND, 0, code)
	if not p.has("xp"):
		p["xp"] = 0
		p["xp_games"] = 0
	gs._join(code, p)
	if drafted:
		TeamFamiliarity.arrive_draftee(p)
	p["rookie_list"] = "A"
	p["contract_years"] = deal_years(p)
	p["salary"] = wage(gs.season_year)
	Workload.reset({code: [p]})
	(rec["picks"] as Array).append({"club": code, "id": id, "round": int(rec["round"]),
			"name": GameDB.player_display_name(p), "from": from})


static func _finish(gs) -> void:
	var rec: Dictionary = gs.rookie_draft
	if bool(rec.get("done", false)):
		return
	rec["done"] = true
	var picks: Array = rec.get("picks", [])
	var mine := picks.filter(func(k): return str(k["club"]) == gs.my_club)
	var nobody := bool(rec.get("nobody_left", false))
	if picks.is_empty():
		gs.add_news("draft", NOBODY_AT_ALL_NEWS if nobody else "Rookie Draft: no club took a player.")
	else:
		var line := "Rookie Draft, %d pick%s across the league." % [picks.size(), "" if picks.size() == 1 else "s"]
		if not mine.is_empty():
			var bits: PackedStringArray = []
			for k in mine:
				bits.append("%s (%s)" % [k["name"], k["from"]])
			line += " Your rookies: %s." % ", ".join(bits)
		gs.add_news("draft", line)
		if nobody:
			gs.add_news("draft", NOBODY_LEFT_NEWS)
	gs.mark_dirty()


# ---------------------------------------------------------------------------
static func _list_of(gs, code: String) -> Array:
	if gs.season != null and gs.season.lists.has(code):
		return gs.season.lists[code]
	return gs.league_lists.get(code, [])


static func _find(list: Array, player_id: String) -> Dictionary:
	for p in list:
		if str(p.get("id", "")) == player_id:
			return p
	return {}
