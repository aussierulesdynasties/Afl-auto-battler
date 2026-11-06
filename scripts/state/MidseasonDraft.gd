class_name MidseasonDraft
extends RefCounted
## The draft year's two mid-season beats (TODO row 54, P-52; director ruling
## 4.44: "Yes, carnival first"; "there should be a mid season draft following
## the afl conventions but no trade period").
##
##   Under-18 carnival week, after round CARNIVAL_AFTER: the hub names three
##   prospects of this year's class who starred, by position and state, with
##   no grades. Words only: it changes no rating, board or pick.
##
##   Mid-season rookie draft, after round DRAFT_AFTER: reverse-ladder order,
##   one pick per club with a free rookie spot (RookieList), your club
##   included. The pool is the unsigned free agents plus the prospects earlier
##   drafts passed over. A pick signs a rookie deal to the end of next season.
##   No trades. When your turn comes the draft waits for you; Sim the week
##   (advance) passes your pick.
##
## Every AI club takes the best-rated player left (younger first, then id),
## the same rating you are shown. Seeded and clock-free.
##
## State: GameState.midseason (saved), {} until the first beat of a season:
##   {"year", "carnival": [{"id","name","pos","state"}], "carnival_seen",
##    "order": [club], "next": int, "picks": [{"club","id","name","from"}],
##    "done": bool}

const CARNIVAL_AFTER := 10
const DRAFT_AFTER := 11
const STARS := 3
const KIND := "midseason"

const STATE_WORDS := {
	"VICM": "Vic Metro", "VICC": "Vic Country", "SA": "South Australia",
	"WA": "Western Australia", "NSW": "New South Wales", "QLD": "Queensland",
	"TAS": "Tasmania", "NT": "the Northern Territory", "ACT": "the ACT",
}


static func state_word(code: String) -> String:
	return str(STATE_WORDS.get(code, code if code != "" else "the Allies"))


## Called from GameState._after_round once a home-and-away round is in.
static func after_round(gs) -> void:
	if gs.season == null or gs.last_phase != "regular":
		return
	var played: int = gs.season.round_index
	if played == CARNIVAL_AFTER:
		_carnival(gs)
	elif played == DRAFT_AFTER:
		_open_draft(gs)


static func _record(gs) -> Dictionary:
	if int(gs.midseason.get("year", 0)) != gs.season_year:
		gs.midseason = {"year": gs.season_year}
	return gs.midseason


# ---------------------------------------------------------------------------
# Under-18 carnival
# ---------------------------------------------------------------------------
static func _class_now(gs) -> Array:
	var out := []
	for p in gs.draftee_pool:
		if int(p.get("draft_year", gs.season_year)) == gs.season_year \
				and not gs.drafted_draftees.has(str(p["id"])):
			out.append(p)
	return out


static func _carnival(gs) -> void:
	var rec := _record(gs)
	if rec.has("carnival"):
		return
	var cls := _class_now(gs)
	# Who starred is a seeded carnival: the better players star more often,
	# but a week of footy is not a rating, so the three are not the top three.
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("carnival|%d|%d" % [gs.career_seed, gs.season_year])
	var scored := []
	for p in cls:
		scored.append([float(p.get("overall", 50)) + rng.randf_range(-10.0, 10.0), str(p["id"]), p])
	scored.sort_custom(func(a, b):
		if a[0] != b[0]:
			return a[0] > b[0]
		return a[1] < b[1])
	var stars := []
	for row in scored.slice(0, STARS):
		var p: Dictionary = row[2]
		stars.append({"id": str(p["id"]), "name": GameDB.player_display_name(p),
				"pos": DraftNight.position_words(p),
				"state": state_word(str(p.get("draft_state", p.get("state", ""))))})
	rec["carnival"] = stars
	rec["carnival_seen"] = false
	if not stars.is_empty():
		gs.add_news("carnival", carnival_news(stars))
	gs.mark_dirty()


static func carnival_news(stars: Array) -> String:
	var bits: PackedStringArray = []
	for s in stars:
		bits.append("%s, a %s from %s" % [s["name"], s["pos"], s["state"]])
	return "Under-18 championships: three who starred this week. %s." % "; ".join(bits)


## The hub's one-off carnival sheet: its lines, or [] once seen.
static func carnival_lines(gs) -> Array:
	if int(gs.midseason.get("year", 0)) != gs.season_year:
		return []
	if bool(gs.midseason.get("carnival_seen", true)):
		return []
	var out := []
	for s in gs.midseason.get("carnival", []):
		out.append("%s: %s, %s." % [s["name"], s["pos"], s["state"]])
	return out


static func close_carnival(gs) -> void:
	gs.midseason["carnival_seen"] = true
	gs.mark_dirty()


# ---------------------------------------------------------------------------
# Rookie draft
# ---------------------------------------------------------------------------
## Everyone a club can take now: unsigned free agents and passed-over
## prospects, best rated first (younger, then id).
static func pool(gs) -> Array:
	var out := []
	for p in gs.free_agents:
		if not gs.retiring_now(p):
			out.append(p)
	for p in gs.draftee_pool:
		if int(p.get("draft_year", gs.season_year)) < gs.season_year \
				and not gs.drafted_draftees.has(str(p["id"])):
			out.append(p)
	out.sort_custom(func(a, b):
		if int(a.get("overall", 0)) != int(b.get("overall", 0)):
			return int(a.get("overall", 0)) > int(b.get("overall", 0))
		if float(a.get("age", 25.0)) != float(b.get("age", 25.0)):
			return float(a.get("age", 25.0)) < float(b.get("age", 25.0))
		return str(a["id"]) < str(b["id"]))
	return out


static func from_word(gs, p: Dictionary) -> String:
	if gs.free_agents.has(p):
		var by := str(p.get("released_by", ""))
		return "free agent, last at %s" % GameDB.club_short(by) if by != "" else "free agent"
	var team := str(p.get("draft_team", ""))
	return "passed over in %d%s" % [int(p.get("draft_year", gs.season_year - 1)),
			", %s" % team if team != "" else ""]


static func _open_draft(gs) -> void:
	var rec := _record(gs)
	if rec.has("order"):
		return
	var order := []
	var ladder: Array = gs.season.ladder_sorted()
	ladder.reverse()
	for row in ladder:
		var code := str(row["code"])
		if not gs.season.lists.has(code):
			continue
		var list: Array = gs.season.lists[code]
		# A pick fills a rookie spot (RookieList).
		if RookieList.rookie_spot_free(list):
			order.append(code)
	rec["order"] = order
	rec["next"] = 0
	rec["picks"] = []
	rec["done"] = false
	_run(gs)


## True while the draft waits on your pick.
static func waiting(gs) -> bool:
	if int(gs.midseason.get("year", 0)) != gs.season_year:
		return false
	var rec: Dictionary = gs.midseason
	if bool(rec.get("done", true)) or not rec.has("order"):
		return false
	var i := int(rec.get("next", 0))
	return i < (rec["order"] as Array).size() and str(rec["order"][i]) == gs.my_club


## AI clubs pick in order until your turn or the end.
static func _run(gs) -> void:
	var rec: Dictionary = gs.midseason
	var order: Array = rec["order"]
	while int(rec["next"]) < order.size():
		var code := str(order[int(rec["next"])])
		if code == gs.my_club:
			gs.mark_dirty()
			return
		var left := pool(gs)
		if not left.is_empty():
			_take(gs, code, left[0])
		rec["next"] = int(rec["next"]) + 1
	_finish(gs)


## Your pick (player id) or "" to pass. False when it is not your turn or he
## has gone.
static func choose(gs, player_id: String) -> bool:
	if not waiting(gs):
		return false
	if player_id != "":
		var hit := {}
		for p in pool(gs):
			if str(p["id"]) == player_id:
				hit = p
		if hit.is_empty():
			return false
		_take(gs, gs.my_club, hit)
	gs.midseason["next"] = int(gs.midseason["next"]) + 1
	_run(gs)
	return true


## Before the next round is played: an unmade pick is passed.
static func settle(gs) -> void:
	if waiting(gs):
		choose(gs, "")


static func _take(gs, code: String, p: Dictionary) -> void:
	var from := from_word(gs, p)
	var id := str(p["id"])
	if gs.free_agents.has(p):
		gs.free_agents.erase(p)
		p.erase("offers")
		p.erase("market_round")
		p.erase("market_log")
		p.erase("talks")
	else:
		gs.draftee_pool.erase(p)
		gs.drafted_draftees[id] = code
		gs._mark_drafted(p, KIND, 0)
	if not p.has("xp"):
		p["xp"] = 0
		p["xp_games"] = 0
	gs._join(code, p)
	# A rookie deal to the end of next season: the rollover takes one off,
	# so two now is "out of contract after next season".
	p["contract_years"] = 2
	p["salary"] = Contracts.indexed_money_2027(Contracts.ROOKIE_MIN_2027, gs.season_year)
	p["rookie_list"] = "A"
	Workload.reset({code: [p]})
	(gs.midseason["picks"] as Array).append({"club": code, "id": id,
			"name": GameDB.player_display_name(p), "from": from})


static func _finish(gs) -> void:
	var rec: Dictionary = gs.midseason
	rec["done"] = true
	var picks: Array = rec.get("picks", [])
	if picks.is_empty():
		gs.add_news("draft", "Mid-season rookie draft: no club took a player.")
	else:
		var bits: PackedStringArray = []
		for k in picks:
			bits.append("%s: %s (%s)" % [GameDB.club_short(str(k["club"])), k["name"], k["from"]])
		gs.add_news("draft", "Mid-season rookie draft, %d pick%s. %s." % [picks.size(),
				"" if picks.size() == 1 else "s", "; ".join(bits)])
	gs.mark_dirty()
