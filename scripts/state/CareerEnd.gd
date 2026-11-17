class_name CareerEnd
extends RefCounted
## A young real player's career end, as a story card (director, 2026-11-17).
## In a Legacy career a real player whose AFL career ended before
## Prospects.REAL_RETIRE_AGE ends it about then (Prospects.real_delisting_due).
## On your list that is never done behind your back: "its not fair on the
## GAMER to trick them into signing deals on a player who is about to reach
## the end of his career without our knowing it". The week your season ends,
## each such player of yours gets a card: "talk to him about his contract and
## gracefully end it, ungracefully delist him or begrudgingly resign him".
## Players 27 and over keep the retirement talk they already get.
##
## 1. Ask him to retire: he agrees 60% of the time, always when one of the
##    retirement reasons applies (Retirement.answer). Agrees: he retires at
##    season's end, nothing owed, the list's morale drops 2. Refuses: a second
##    card asks you to delist him or re-sign him.
## 2. Delist him: half of what is left on his deal stays on next season's cap
##    (ListCosts.dead_money); out of contract, nothing. The list's morale drops 4.
## 3. Re-sign him for a year at his asking price; then his career runs on his
##    form like anyone's.
## Left unanswered, he is let go as before (_real_delistings, _fa_close_plan).

const TID := "career_end"
const TID_AFTER := "career_end_refused"
## Points the rest of the list's morale drops when he is asked to retire and
## agrees, and when he is delisted.
const RETIRE_MORALE := -2
const DELIST_MORALE := -4


## Your players whose real career ends this summer and who have not been asked.
static func due(gs) -> Array:
	var out := []
	var year: int = int(gs.season_year) + 1
	for p in gs.my_list:
		if gs.retiring_now(p) or int((p.get("end_talk", {}) as Dictionary).get("year", 0)) == year:
			continue
		var ending: bool = int(p.get("real_end", 0)) == year if p.has("real_end") \
				else Prospects.real_delisting_due(p, year)
		if ending:
			out.append(p)
	return out


## Your season is over: knocked out, the premiers, the runners-up, or out of
## the finals once they start (as ClubStories.season_end_due reads it).
static func season_over_for_you(gs) -> bool:
	if gs.season == null or not gs.season.is_regular_done():
		return false
	var status: String = gs.my_finals_status()
	if status == "" and not gs.season.finals.is_empty():
		return true
	return ["eliminated", "premier", "runner_up"].has(status)


## The week your season ends: one card for each of your players due.
static func week(gs) -> void:
	if gs.my_club == "" or gs.is_sacked() or not season_over_for_you(gs):
		return
	for p in due(gs):
		p["end_talk"] = {"year": int(gs.season_year) + 1}
		gs.week_events.append(card(gs, p))


static func _who(p: Dictionary) -> String:
	return GameDB.player_display_name(p)


## What half of what is left on his deal comes to, as a line.
static func _delist_rule(p: Dictionary) -> String:
	var left := _seasons_left(p)
	var who := _who(p)
	var pay := int(p.get("salary", 0))
	if left <= 0:
		return "%s is gone at season's end. He is out of contract, so nothing is owed. The list's morale drops %d." % [who, -DELIST_MORALE]
	return "%s is gone at season's end. Half of what's left on his deal stays on next season's cap: %d %s x %s left = %s. The list's morale drops %d." % [
		who, left, "season" if left == 1 else "seasons", Contracts.money(pay),
		Contracts.money(_dead(p)), -DELIST_MORALE]


## Seasons left on his deal after this one, as signed (before the end of a
## real career cut it, _real_delistings).
static func _seasons_left(p: Dictionary) -> int:
	return maxi(0, int(p.get("real_end_years", p.get("contract_years", 1))) - 1)


static func _dead(p: Dictionary) -> int:
	return int(round(float(p.get("salary", 0)) * _seasons_left(p) * ListStings.RELEASE_DEAD_SHARE))


static func _resign_option(p: Dictionary) -> Dictionary:
	var who := _who(p)
	return {"label": "Re-sign him for a year", "effects": [],
		"rule": "%s stays one season at his asking price, %s. After that his career runs on his form like anyone's." % [
			who, Contracts.money(Contracts.asking_salary(p))],
		"result": ""}


static func _delist_option(p: Dictionary) -> Dictionary:
	return {"label": "Delist him", "effects": [], "rule": _delist_rule(p), "result": ""}


## Why he would agree to retire whatever happens ("" when it is the 60% roll).
static func agree_reason(gs, p: Dictionary) -> String:
	return Retirement.no_reason(p, int(gs.season_year), gs.season_games(str(p["id"])), gs.career_facts)


## The card (also for tests and captures).
static func card(gs, p: Dictionary) -> Dictionary:
	var who := _who(p)
	var why := agree_reason(gs, p)
	var agree := 100 if why != "" else int(round((1.0 - ListStings.ASK_AGAIN_YES) * 100.0))
	var ask_rule := ""
	if why != "":
		ask_rule = "He always agrees: %s He retires at season's end, nothing owed. The list's morale drops %d." % [
			why, -RETIRE_MORALE]
	else:
		ask_rule = "%d%% he agrees: he retires at season's end, nothing owed, and the list's morale drops %d. %d%% he refuses: a second card asks you to delist him or re-sign him." % [
			agree, -RETIRE_MORALE, 100 - agree]
	return {"tid": TID, "player_id": str(p["id"]), "title": "%s's future" % who,
		"text": "His contract talk is due. The list manager doesn't see a place for %s next year, and he wants to hear it from you." % who,
		"options": [
			{"label": "Ask him to retire", "effects": [], "rule": ask_rule, "result": ""},
			_delist_option(p),
			_resign_option(p)],
		"unanswered": {"hint": "Leave it and %s is let go at season's end." % who,
			"text": "%s is let go at season's end." % who},
		"coach_only": true, "facts": {}}


## The second card, after he refuses to retire.
static func refused_card(_gs, p: Dictionary) -> Dictionary:
	var who := _who(p)
	return {"tid": TID_AFTER, "player_id": str(p["id"]), "title": "%s won't retire" % who,
		"text": "%s has said no: he wants to play on. It's delist him or re-sign him." % who,
		"options": [_delist_option(p), _resign_option(p)],
		"unanswered": {"hint": "Leave it and %s is let go at season's end." % who,
			"text": "%s is let go at season's end." % who},
		"coach_only": true, "facts": {}}


## The coach's answer (GameState.resolve_card). Returns what happened, or ""
## when the card is not one of these (or he has left the club).
static func answered(gs, c: Dictionary, choice: int) -> String:
	var tid := str(c.get("tid", ""))
	if tid != TID and tid != TID_AFTER or choice < 0:
		return ""
	var p: Dictionary = gs.list_player(str(c.get("player_id", "")))
	if p.is_empty():
		return ""
	var call := ""
	if tid == TID:
		call = (["ask", "delist", "resign"] as Array)[choice]
	else:
		call = (["delist", "resign"] as Array)[choice]
	var who := _who(p)
	var year: int = int(gs.season_year) + 1
	var talk: Dictionary = p.get("end_talk", {})
	talk["year"] = year
	p["end_talk"] = talk
	match call:
		"ask":
			var rng := RandomNumberGenerator.new()
			rng.seed = hash("career_end|%s|%d|%d" % [str(p["id"]), year, int(gs.career_seed)])
			var res := Retirement.answer(p, int(gs.season_year), gs.season_games(str(p["id"])), gs.career_facts, rng.randf())
			if bool(res["stays"]):
				talk["call"] = "refused"
				gs.week_events.append(refused_card(gs, p))
				return "%s says no: he wants to play on. Delist him or re-sign him." % who
			talk["call"] = "retire"
			p["retiring"] = year
			p["retire_talk"] = {"year": year, "stays": false, "reason": str(res["reason"])}
			_list_morale(gs, p, RETIRE_MORALE)
			gs.add_news("retirement", "%s will retire at the end of the season." % who)
			return "%s agrees: %s He retires at season's end, nothing owed." % [who, str(res["reason"])]
		"delist":
			talk["call"] = "delist"
			var dead := _dead(p)
			_list_morale(gs, p, DELIST_MORALE)
			if gs.offseason_open():
				gs.career_end_delist(p)
			if dead > 0:
				return "%s is delisted at season's end. %s stays on next season's cap." % [who, Contracts.money(dead)]
			return "%s is delisted at season's end. He was out of contract, so nothing is owed." % who
		"resign":
			talk["call"] = "resign"
			gs.career_end_resign(p)
			return "%s re-signs for a year at %s." % [who, Contracts.money(int(p.get("salary", 0)))]
	return ""


static func _list_morale(gs, p: Dictionary, d: int) -> void:
	for q in gs.my_list:
		if q != p:
			ClubLife.add_morale(q, d)
