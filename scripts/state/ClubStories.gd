class_name ClubStories
extends RefCounted
## GameState's side of the week's story cards: the facts a card may read about
## your club and players, and a choice's effects applied through levers the
## game already has (morale, development, the board, trust, selection,
## contracts). The rules of what comes up live in StoryEngine; the cards in
## data/stories. `gs` is GameState.

## Trust lost when a promise made on a card is broken after the match.
const BROKEN_PROMISE_TRUST := StoryEngine.BROKEN_PROMISE_TRUST
const BROKEN_RUN_TRUST := StoryEngine.BROKEN_RUN_TRUST


## Your week of the season: the round, then the finals weeks after it.
static func week_in_season(gs) -> int:
	if gs.season == null:
		return 0
	# The pre-season's stops sit just before Round 1 on the calendar: week 3 is -5,
	# inside the pre-season's own block (StoryEngine.PRESEASON_WEEKS), never in last season's weeks.
	if gs.preseason_active():
		return maxi(gs.preseason_week() - PreSeason.weeks(), 1 - StoryEngine.PRESEASON_WEEKS)
	if not gs.season.is_regular_done():
		return gs.season.round_index + 1
	return gs.season.regular_rounds() + (gs.season.finals.get("weeks", []) as Array).size() + 1


static func phase(gs) -> String:
	if gs.preseason_active():
		return "preseason"
	return "finals" if gs.season != null and gs.season.is_regular_done() else "regular"


## This week's cards. In the finals, only while you are still in it: playing,
## or on the week off a qualifying final or a top-six finish earns.
static func pick(gs) -> Array:
	if season_end_due(gs):
		return _season_end_pick(gs)
	if phase(gs) == "finals" and (gs.season.is_season_over() or not ["alive", "bye"].has(gs.my_finals_status())):
		return []
	var cards: Array = StoryEngine.pick_week(StoryDeck.all(), context(gs), gs.story)
	_mark_run_asks(gs, cards)
	# The result of a role trial comes first, the week after it ends.
	if not gs.trial_result.is_empty():
		var tr: Dictionary = gs.trial_result
		var who: Dictionary = gs.list_player(str(tr.get("id", "")))
		if not who.is_empty():
			var c := card_for(gs, "media_trial_worked" if bool(tr.get("ok", false)) else "media_trial_not_yet", who)
			if not c.is_empty():
				cards.push_front(c)
		gs.trial_result = {}
	# A new club has asked about one of your players: that comes first.
	var asked := ExpansionBuild.card(gs)
	if not asked.is_empty():
		cards.push_front(asked)
	return cards


## The week your season ends: knocked out, or the Grand Final
## played. One card, once a season (the story's season counts hold the mark).
const SEASON_END_MARK := "_season_end"


static func season_end_due(gs) -> bool:
	if gs.season == null or not gs.season.is_regular_done():
		return false
	if not ["eliminated", "premier", "runner_up"].has(gs.my_finals_status()):
		return false
	StoryEngine.ensure(gs.story)
	return not (gs.story["season"] as Dictionary).has(SEASON_END_MARK)


static func _season_end_pick(gs) -> Array:
	(gs.story["season"] as Dictionary)[SEASON_END_MARK] = 1
	var cards: Array = StoryEngine.pick_week(StoryDeck.all(), context(gs, "season_end"), gs.story)
	_mark_run_asks(gs, cards)
	return cards


## A card that offers a player a run counts as asking him (Backing.ASK_GAP):
## whatever the answer, he is not asked again for a while.
static func _mark_run_asks(gs, cards: Array) -> void:
	for c in cards:
		var p: Dictionary = gs.list_player(str((c as Dictionary).get("player_id", "")))
		if p.is_empty():
			continue
		for o in (c.get("options", []) as Array):
			for e in ((o as Dictionary).get("effects", []) as Array):
				if str((e as Dictionary).get("op", "")) == "start_backing":
					Backing.mark_asked(p, gs.story_week())


static func context(gs, ph_override := "") -> Dictionary:
	var week := week_in_season(gs)
	var ph := phase(gs) if ph_override == "" else ph_override
	return {"seed": int(gs.season.seed), "year": int(gs.season_year), "week": week, "phase": ph,
			"big": ph == "finals" or (ph == "regular" and (week == 1 or week == gs.season.regular_rounds())),
			"club": club_facts(gs, week, ph), "players": player_facts(gs)}


## The finals week as the cards count it, the wildcard series' weeks: 1 the
## wildcard round, 2 the qualifying and elimination finals ... 5 the Grand
## Final (6 once it is played). A four-week series (a past year's final five,
## six or eight) starts at 2, so its Grand Final is 5 too; a replayed final's
## week counts as the week it replays.
static func finals_stage(gs, week: int) -> int:
	return week - gs.season.regular_rounds() - int(gs.season.finals.get("replays", 0)) \
			+ (5 - gs.season.finals_weeks())


static func club_facts(gs, week: int, ph: String) -> Dictionary:
	var fit := 0
	for p in gs.my_list:
		if int(p.get("injury_weeks", 0)) <= 0:
			fit += 1
	var facts := {"club": GameDB.club_name(gs.my_club), "opp": _opponent_name(gs), "round": maxi(week, 0),
			"year": int(gs.season_year), "losing_run": int(gs.losing_streak), "winning_run": _winning_run(gs),
			"ladder": gs.my_position(), "board": gs.board_confidence(), "fit_count": fit,
			"run_games": MatchNotes.count_word(Backing.RUN_GAMES),
			"finals_week": finals_stage(gs, week) if ph == "finals" or ph == "season_end" else 0,
			"pre_week": gs.preseason_week() if ph == "preseason" else 0, "premiers": _premiers_last_year(gs)}
	facts.merge(_leader_facts(gs), true)
	facts.merge(_finals_facts(gs, ph), true)
	facts.merge(papers_facts(gs), true)
	if ph == "preseason" and gs.preseason_active():
		# The camp's levers in real terms: the running the plan adds up to and
		# where the plan a card drills stands (StoryEngine _running_words, _drill_words).
		var plan: String = gs.card_drill_plan()
		facts["pre_run"] = gs.preseason_run_forecast()
		facts["drill_plan"] = CoachReport.plan_label(plan)
		facts["drill_level"] = gs.plan_fluency(gs.my_club, plan)
		facts["drill_credit"] = float(gs.my_drill_credit().get(plan, 0.0))
	return facts


## The pre-season papers: who wrote it, the finish they tipped, the finish you
## named (if you did), and how far below your own words the club sits now.
static func papers_facts(gs) -> Dictionary:
	var out := {"paper": "", "writer": "", "pred_word": "", "pred_rank": 0, "claim_word": "",
			"claim_rank": 0, "goal_line": "", "words_word": "", "words_behind": 0, "ladder_word": ""}
	var rec: Dictionary = gs.papers_record()
	if rec.is_empty() or int(gs.preseason.get("year", 0)) != int(gs.season_year):
		return out
	var kind := str(rec.get("kind", ""))
	var j: Dictionary = MediaConference.JOURNALISTS.get(str(PreSeason.PAPER_WRITER.get(kind, "stats")), {})
	var pred := int(rec.get("pred", 0))
	var claim := int(rec.get("claim", 0))
	var goal := str((gs.board.get("goal", {}) as Dictionary).get("text", ""))
	out["paper"] = str(j.get("outlet", "The papers"))
	out["writer"] = str(j.get("name", "A columnist"))
	out["pred_rank"] = pred
	out["pred_word"] = PreSeason.ordinal(pred) if pred > 0 else ""
	out["claim_rank"] = claim if claim > 0 else PreSeason.claim_rank(pred)
	out["claim_word"] = PreSeason.ordinal(int(out["claim_rank"])) if pred > 0 else ""
	out["goal_line"] = goal.substr(0, 1).to_lower() + goal.substr(1) if goal != "" else ""
	if claim > 0:
		out["words_word"] = PreSeason.ordinal(claim)
		out["words_behind"] = PreSeason.places_behind(gs.my_position(), claim)
	out["ladder_word"] = PreSeason.ordinal(gs.my_position())
	return out


## Won the flag last year, by the honour roll this save holds.
static func _premiers_last_year(gs) -> bool:
	if gs.honour_roll.is_empty():
		return false
	var last: Dictionary = gs.honour_roll[gs.honour_roll.size() - 1]
	return int(last.get("year", 0)) == int(gs.season_year) - 1 and str(last.get("premier", "")) == gs.my_club


## Where you stand in September (and on the ten before it).
static func _finals_facts(gs, ph: String) -> Dictionary:
	var out := {"finals_math": "", "finals_bye": false, "lost_last_final": false, "gf_run": 0,
			"gf_run_word": "", "gf_again": "", "rival": false}
	if ph == "preseason":
		return out
	if ph == "regular":
		out["finals_math"] = gs.season.finals_math(gs.my_club)
		return out
	out.merge(finals_2_facts(gs, ph), true)
	out["finals_bye"] = gs.my_finals_status() == "bye"
	var slots: Dictionary = gs.season.finals.get("slots", {})
	out["lost_last_final"] = false
	for tag in gs.season.finals_tags():
		if str(tag).begins_with("QF") and str(slots.get("L_" + str(tag), "")) == gs.my_club:
			out["lost_last_final"] = true
	if int(gs.season.finals.get("week", 0)) == gs.season.finals_weeks():
		out.merge(_grand_final_story(gs), true)
	return out


## The finals cards' second slice. Only in-save history and
## data/club_premierships.csv are read (director, 2026-11-03).
const FINAL_WORDS := {"WC": "wildcard final", "EF": "elimination final", "SF": "semi-final",
		"PF": "preliminary final", "QF": "qualifying final", "GF": "Grand Final"}
## A flag or a Grand Final this many seasons ago or longer is a drought.
const DROUGHT_YEARS := 10
const RUN_WORDS := {2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten"}
const FORECAST := {"perfect": "Not a cloud forecast for tomorrow.", "wet": "Rain's forecast for tomorrow.",
		"windy": "A gusty northerly is forecast for tomorrow.", "hot": "It's going to be a hot one tomorrow."}


static func finals_2_facts(gs, ph: String) -> Dictionary:
	var year := int(gs.season_year)
	var out := {"underdog": false, "years_since_final": 0, "last_final_year": 0, "forecast_line": "",
			"result": "", "lost_final": "", "lost_prelim": false, "margin": 0, "margin_line": "",
			"history_line": "", "best_line": ""}
	# The last season this save saw you play finals (the board's record of each finish).
	var last := 0
	for h in gs.board.get("history", []):
		var y := int((h as Dictionary).get("year", 0))
		if y < year and int(h.get("position", 99)) <= int(SeasonRules.for_year(y)["finalists"]) and y > last:
			last = y
	if last > 0:
		out["last_final_year"] = last
		out["years_since_final"] = year - last - 1
	if ph == "finals":
		var opp := _this_week_opponent(gs)
		if opp != "":
			var pos := _ladder_positions(gs.season)
			out["underdog"] = int(pos.get(opp, 99)) < int(pos.get(gs.my_club, 99))
		if int(gs.season.finals.get("week", 0)) == gs.season.finals_weeks():
			out["forecast_line"] = _forecast_line(gs)
		return out
	if ph != "season_end":
		return out
	var status: String = gs.my_finals_status()
	out["result"] = status
	var slots: Dictionary = gs.season.finals.get("slots", {})
	for tag in gs.season.finals_tags():
		if str(slots.get("L_" + tag, "")) == gs.my_club and not gs.season.loser_goes_on(tag, gs.my_club):
			out["lost_final"] = str(FINAL_WORDS.get(tag.substr(0, 2), "final"))
			out["lost_prelim"] = tag.begins_with("PF")
	if status == "premier" or status == "runner_up":
		var gf := _grand_final_result(gs)
		if not gf.is_empty():
			var side := 0 if str(gf["home"]) == gs.my_club else 1
			var sc: Array = gf.get("score", [0, 0])
			out["margin"] = absi(int(sc[0]) - int(sc[1]))
			out["best_line"] = _best_line(gs, gf, side, status == "premier")
		out["margin_line"] = margin_line(int(out["margin"]), status == "premier")
		out["history_line"] = history_line(gs.my_club, year, gs.honour_roll, status == "premier")
	return out


static func _this_week_opponent(gs) -> String:
	for m in gs.season.finals_week_matches():
		if str(m["home"]) == gs.my_club:
			return str(m["away"])
		if str(m["away"]) == gs.my_club:
			return str(m["home"])
	return ""


static func _ladder_positions(sea) -> Dictionary:
	var out := {}
	var rows: Array = sea.ladder_sorted()
	for i in range(rows.size()):
		out[str(rows[i]["code"])] = i + 1
	return out


## The Grand Final's seeded weather: the weather it is played in (GameState plays it with the same call).
static func _forecast_line(gs) -> String:
	for m in gs.season.finals_week_matches():
		if str(m["home"]) == gs.my_club or str(m["away"]) == gs.my_club:
			var w: String = gs.season.weather_for(str(m["home"]), str(m["away"]), gs.season.finals_round(), m)
			return str(FORECAST.get(w, FORECAST["perfect"]))
	return ""


static func _grand_final_result(gs) -> Dictionary:
	for week in gs.season.finals.get("weeks", []):
		for res in week:
			if str((res as Dictionary).get("tag", "")) == "GF":
				return res
	return {}


## The final margin only: no line claims how the game unfolded.
static func margin_line(m: int, won: bool) -> String:
	if m == 1:
		return "By 1 point. A kick in it at the siren." if won else "Beaten by 1 point. Under a goal."
	if won:
		if m <= 6:
			return "By %d points. A kick in it at the siren." % m
		if m <= 24:
			return "By %d points." % m
		if m <= 39:
			return "By %d points, comfortably." % m
		return "By %d points. A thumping." % m
	if m <= 6:
		return "Beaten by %d points. Under a goal." % m
	if m <= 24:
		return "Beaten by %d points." % m
	if m <= 39:
		return "Beaten by %d points, well held." % m
	return "Beaten by %d points. A hiding." % m


## A club's flags before `year`: {flags: {year: true}, lost: {year: true} (Grand
## Finals lost, from the save only), last_flag (0 for none), known (the record before
## the save is on file)}. Flags come from the save's honour roll and, before the
## save, data/club_premierships.csv. Shared with the league news layer (LeagueNews).
static func flag_record(club: String, year: int, roll: Array) -> Dictionary:
	var flags := {}
	var lost := {}
	var save_from := year
	for h in roll:
		var y := int((h as Dictionary).get("year", 0))
		if y >= year:
			continue
		save_from = mini(save_from, y)
		if str(h.get("premier", "")) == club:
			flags[y] = true
		elif str(h.get("runner_up", "")) == club:
			lost[y] = true
	var before := ClubHistory.before_career(club)
	for y in before["years"]:
		if int(y) < save_from:
			flags[int(y)] = true
	var last_flag := 0
	for y in flags:
		last_flag = maxi(last_flag, int(y))
	return {"flags": flags, "lost": lost, "last_flag": last_flag, "known": bool(before["known"])}


## The club's history, with this year's Grand Final the newest entry. Flags come
## from the save's honour roll and, before the save, data/club_premierships.csv;
## Grand Finals lost only from the save. Where the record cannot know, the line says nothing it can't.
static func history_line(club: String, year: int, roll: Array, won: bool) -> String:
	var rec := flag_record(club, year, roll)
	var flags: Dictionary = rec["flags"]
	var lost: Dictionary = rec["lost"]
	var before := {"known": rec["known"]}
	var last_flag := int(rec["last_flag"])
	if won:
		if flags.is_empty() and bool(before["known"]):
			return "The club's first premiership. Ever."
		var run := 1
		while flags.has(year - run):
			run += 1
		if run == 2:
			return "Back-to-back."
		if run >= 3:
			return "%s in a row." % str(RUN_WORDS.get(run, str(run)))
		if lost.has(year - 1):
			return "A year after losing one, they've won one."
		if last_flag > 0 and year - last_flag >= DROUGHT_YEARS:
			return "The first flag since %d." % last_flag
		return "Another flag for the club."
	var losses := 1
	while lost.has(year - losses):
		losses += 1
	if losses == 2:
		return "Two Grand Finals, two losses."
	if losses >= 3:
		return "%s Grand Finals lost in a row." % str(RUN_WORDS.get(losses, str(losses)))
	if flags.has(year - 1):
		return "Last year's premiers, beaten on the day."
	var last_gf := last_flag
	for y in lost:
		last_gf = maxi(last_gf, int(y))
	if last_gf > 0 and year - last_gf >= DROUGHT_YEARS:
		return "The first Grand Final since %d, and it got away." % last_gf
	return "So close to a flag."


## Your best player in the Grand Final by influence (the Norm Smith's own measure),
## and whether he was best on ground.
static func _best_line(gs, gf: Dictionary, side: int, won: bool) -> String:
	var stats_all: Dictionary = gf.get("players", {})
	var roster: Array = gf.get("roster", [])
	if roster.size() <= side:
		return ""
	var best_id := ""
	var best_inf := -INF
	for r in roster[side]:
		var id := str(r["id"])
		if stats_all.has(id):
			var inf := CoachReport.influence(stats_all[id])
			if inf > best_inf:
				best_inf = inf
				best_id = id
	if best_id == "":
		return ""
	var who: String = gs.award_name({"id": best_id})
	if not won:
		return "%s gave everything." % who
	var bog: Dictionary = Awards.norm_smith(gf)
	if str(bog.get("id", "")) == best_id:
		return "%s was best on ground." % who
	return "%s was your best." % who


## The Grand Final against this opponent: how many in a row (this one included),
## what happened in last year's if it was them too, and whether they are a
## long-standing rival. From the honour roll this save holds, nothing older.
static func _grand_final_story(gs) -> Dictionary:
	var opp := ""
	for m in gs.season.finals_week_matches():
		if str(m["home"]) == gs.my_club:
			opp = str(m["away"])
		elif str(m["away"]) == gs.my_club:
			opp = str(m["home"])
	if opp == "":
		return {}
	var run := 1
	var again := ""
	var year := int(gs.season_year) - 1
	for i in range(gs.honour_roll.size() - 1, -1, -1):
		var h: Dictionary = gs.honour_roll[i]
		if int(h.get("year", 0)) != year:
			break
		var pair := [str(h.get("premier", "")), str(h.get("runner_up", ""))]
		if not (pair.has(gs.my_club) and pair.has(opp)):
			break
		if run == 1:
			again = "won" if pair[0] == gs.my_club else "lost"
		run += 1
		year -= 1
	var words := {2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth"}
	return {"gf_run": run, "gf_run_word": str(words.get(run, "%dth" % run)), "gf_again": again,
			"rival": not Rivalries.established(gs.my_club, opp).is_empty()}


## Your captain, your best-rated vice-captain, and the young player a captain
## would put forward (fewer than ten senior games, not in the side, the most
## potential): names and ids for the captain's cards.
static func _leader_facts(gs) -> Dictionary:
	var rec: Dictionary = gs.captaincy_record(gs.my_club)
	var cap := {}
	var vice := {}
	for p in gs.my_list:
		var role := Captaincy.role_of(rec, str(p["id"]))
		if role == "captain" and cap.is_empty():
			cap = p
		elif role == "vice" and (vice.is_empty() or Leadership.of(p) > Leadership.of(vice)):
			vice = p
	var in_side := {}
	var side: Dictionary = gs.current_side()
	for k in side:
		for id in side[k]:
			in_side[str(id)] = true
	var kid := {}
	for p in gs.my_list:
		if in_side.has(str(p["id"])) or gs.games_played(p) >= 10 or float(p.get("age", 30.0)) > 21.0:
			continue
		if kid.is_empty() or int(p.get("potential", p.get("overall", 0))) > int(kid.get("potential", kid.get("overall", 0))):
			kid = p
	return {"captain_name": GameDB.player_display_name(cap) if not cap.is_empty() else "",
			"vice_name": GameDB.player_display_name(vice) if not vice.is_empty() else "",
			"vice_id": str(vice.get("id", "")), "has_vice": not vice.is_empty(),
			"kid_name": GameDB.player_display_name(kid) if not kid.is_empty() else "",
			"kid_id": str(kid.get("id", "")), "has_kid": not kid.is_empty()}


static func _opponent_name(gs) -> String:
	var opp: Dictionary = gs.my_next_opponent()
	if not opp.is_empty():
		return GameDB.club_name(str(opp["code"]))
	if gs.season.is_regular_done() and not gs.season.is_season_over():
		for m in gs.season.finals_week_matches():
			if str(m["home"]) == gs.my_club:
				return GameDB.club_name(str(m["away"]))
			if str(m["away"]) == gs.my_club:
				return GameDB.club_name(str(m["home"]))
	return "the opposition"


## Your wins in a row this season, from the season's results.
static func _winning_run(gs) -> int:
	var n := 0
	for i in range(gs.season_log.size() - 1, -1, -1):
		var res: Dictionary = gs.season_log[i]
		var side := 0 if str(res.get("home", "")) == gs.my_club else (1 if str(res.get("away", "")) == gs.my_club else -1)
		if side < 0:
			continue
		var score: Array = res.get("score", [0, 0])
		if int(score[side]) <= int(score[1 - side]):
			break
		n += 1
	return n


static func player_facts(gs) -> Array:
	var selected := {}
	var starting := {}
	var side: Dictionary = gs.current_side()
	for k in side:
		for id in side[k]:
			selected[str(id)] = true
			if k != "BENCH":
				starting[str(id)] = true
	var info: Dictionary = gs.talk_info(selected)
	var fit := []
	for p in gs.my_list:
		if int(p.get("injury_weeks", 0)) <= 0:
			fit.append(p)
	fit.sort_custom(func(a, b): return int(a["overall"]) > int(b["overall"]))
	var rank := {}
	for i in range(fit.size()):
		rank[str(fit[i]["id"])] = i + 1
	var cap_room: int = gs.cap_for(str(gs.my_club)) - gs.my_payroll()
	# By rating on the whole list, the injured included (ties by id, so the same list ranks the same way).
	var everyone: Array = gs.my_list.duplicate()
	everyone.sort_custom(func(a, b): return int(a["overall"]) > int(b["overall"]) 			or (int(a["overall"]) == int(b["overall"]) and str(a["id"]) < str(b["id"])))
	var all_rank := {}
	for i in range(everyone.size()):
		all_rank[str(everyone[i]["id"])] = i + 1
	var out := []
	for p in gs.my_list:
		var id := str(p["id"])
		var f := player_fact(gs, p, selected.has(id), info.get(id, {}), int(rank.get(id, 99)), cap_room,
				int(all_rank.get(id, 99)))
		f["starting"] = starting.has(id)
		if not selected.has(id) and bool(f["fit"]) and not bool(f["back_wait"]):
			f["back_out"] = gs.backing_drop_name(p, side)
		# Picked in his second position already: a role trial there is no trial.
		var line := ""
		for k in side:
			if k != "BENCH" and (side[k] as Array).has(id):
				line = str(k)
		if line != "" and GameState._in_trial_line(line, trial_role(p)):
			f["has_role2"] = false
		out.append(f)
	# Form in the bottom half of the side: his last games' rating is lower than
	# at least half of the starters' who have three games of it.
	var forms := []
	for f in out:
		if bool(f["starting"]) and int(f["form_games"]) >= 3:
			forms.append(int(f["form"]))
	for f in out:
		var below := 0
		for x in forms:
			if int(x) < int(f["form"]):
				below += 1
		f["form_low"] = int(f["form_games"]) >= 3 and float(below) < float(forms.size()) / 2.0
	return out


## Everything a card may say or test about one of your players (the names
## match StoryDeck.PLAYER_FACTS). Money and odds come already in words.
static func player_fact(gs, p: Dictionary, selected: bool, i: Dictionary, fit_rank: int, cap_room: int, all_rank := 99) -> Dictionary:
	var id := str(p["id"])
	var name := GameDB.player_display_name(p)
	var fit := int(p.get("injury_weeks", 0)) <= 0
	var case := ClubLife.talk_case(p, i) if fit else ""
	var kpi := str(i.get("kpi", ""))
	var need_line := "What a %s has to show: %s." % [str(i.get("job", "player")), str(i.get("need", ""))]
	var sore := p.duplicate()
	sore["sore"] = true
	var early := ClubLife.early_price(p)
	var more := ClubLife.early_years(p) - 1
	var t := Trust.value(gs.relations, Trust.player_key(id))
	var ovr := int(p.get("overall", 0))
	var pot := int(p.get("potential", ovr))
	var recent: Array = (gs.form_log.get(id, {}) as Dictionary).get("last", [])
	var form := 0
	for x in recent:
		form += int(x)
	form = int(round(float(form) / float(recent.size()))) if not recent.is_empty() else 0
	var miss := preseason_miss(gs, p)
	var lead := Leadership.of(p)
	var band := Trust.band(t)
	var holds: bool = lead >= StoryDeck.HOLDS_AT or (lead >= StoryDeck.HOLDS_WITH_TRUST and (band == "trusts" or band == "close"))
	var out := {"id": id, "name": name, "first": name.split(" ")[0], "age": float(p.get("age", 25.0)),
			"games": gs.games_played(p), "fit": fit, "selected": selected, "overall": ovr, "potential": pot,
			"pot_gap": pot - ovr, "contract_years": int(p.get("contract_years", 2)), "morale": ClubLife.morale(p),
			"trust": t, "trust_band": Trust.band(t), "opinion": Trust.opinion(t),
			# Under 50 he may refuse to re-sign (director 2026-11-08); "" at 50 or over.
			"refuse_line": Contracts.REFUSE_ODDS % [Trust.opinion(t), gs.resign_refuse_chance(p)]
					if gs.resign_refuse_chance(p) > 0 else "",
			"discipline": int((p.get("attr", {}) as Dictionary).get("discipline", 50)),
			# Recent form: his last games' Player Rating, averaged (the form the
			# game already keeps and shows); form_games counts them (0 to 3).
			"form": form, "form_games": recent.size(), "has_role2": trial_role(p) != "", "form_low": false,
			"role_avg": gs.position_average(str(p.get("role", ""))), "role_word": CoachPathway.position_word({"pos": str(p.get("role", ""))}),
			"trial_word": CoachPathway.position_word({"pos": trial_role(p)}), "trial_home": CoachPathway.position_word({"pos": str(p.get("role", ""))}), "trial_avg": 0, "trial_par": 0, "trial_tail": "",
			"starting": false,   # player_facts sets it from the side
			"backed": Backing.is_active(p), "back_wait": not Backing.may_ask(p, gs.story_week()),
			# Who makes way if he is backed now (player_facts fills it: a card that
			# promises him a run says so).
			"back_out": "",
			"fit_rank": fit_rank, "talk_case": case, "kpi": kpi,
			"kpi_or_need": kpi if kpi != "" else need_line,
			"explain_label": ("Talk %s through his season" if kpi != "" else "Tell %s what he has to show") % name.split(" ")[0],
			"talk_text": ClubLife.talk_text(case, i), "verdict": str(i.get("verdict", "")),
			"job": str(i.get("job", "")), "need": str(i.get("need", "")),
			"sore_odds": ClubLife.odds(Injuries.chance(sore)),
			"sore_pct": _about_pct(roundi(Injuries.chance(sore) * 100.0)),
			"injury_pct": _about_pct(roundi(Injuries.chance(p) * 100.0)),
			# How he rates in the spot a role trial would play him (his usual rating when he has none).
			"trial_ovr": gs.rating_as(p, trial_role(p)) if trial_role(p) != "" and p.has("attr") else ovr,
			"ask": Contracts.money(Contracts.asking_salary(p)), "early_price": Contracts.money(early),
			"more_seasons": "%s more season%s" % [MatchNotes.count_word(more), "" if more == 1 else "s"],
			"extension_ok": ClubLife.extension_wanted(p, {}) and early - int(p.get("salary", 0)) <= cap_room,
			"intl_extension_ok": ClubLife.extension_wanted(p, {}, ClubLife.INTL_EXTENSION_MIN_OVR),
			# Shown under his real name: no card invents a private life or
			# misconduct for a real person (story research §4).
			"real_named": str(p.get("real_name", "")).strip_edges() != "",
			# A dispute left to the captain: held when his Leadership is high enough, or
			# fairly high and he trusts you (the rule is printed on the choice).
			"leadership": lead, "captain": Captaincy.role_of(gs.captaincy_record(gs.my_club), id) == "captain",
			"delegate_holds": holds, "holds_at": StoryDeck.HOLDS_AT, "holds_trust_at": StoryDeck.HOLDS_WITH_TRUST,
			"holds_opinion_at": Trust.band_opinion("trusts"),
			"last_season": _last_season(gs, p), "finals_games": int(p.get("finals_games", 0)),
			"save_debut": gs.save_saw_every_game(p), "debut_year": _debut_year(gs, p),
			"milestone_next": _milestone_next(gs, p), "injured_weeks": int(p.get("injury_weeks", 0)),
			"rushable": int(p.get("injury_weeks", 0)) > 0 and str(p.get("injury_kind", "")) != "concussion",
			"overall_rank": all_rank, "told_players": gs.story_flag_set(id, "farewell_told"),
			"new_here": _new_here(gs, p), "out_of_side": out_of_side(gs, p), "trial_place": _trial_place(gs, id),
			"injury_kind": str(p.get("injury_kind", "")),
			"injury_word": Injuries.wording(str(p.get("injury_kind", ""))) if int(p.get("injury_weeks", 0)) > 0 else "",
			# Injured in the pre-season: what the physio's plan costs him (preseason_miss).
			"pre_miss_xp": int(miss["xp"]), "pre_miss_heavy": int(miss["heavy"]), "pre_miss_rounds": int(miss["rounds"])}
	# International prospects' cards: where he comes from and how far into his career he is.
	var country: Dictionary = InternationalProspects.country(str(p.get("intl", "")))
	var career := Career.of(p)
	var career_goals := int(career.get("goals", 0))
	if int(career.get("through", 0)) < int(gs.season_year):
		career_goals += int((gs.season_tally.get(id, {}) as Dictionary).get("goals", 0))
	out["intl"] = not country.is_empty()
	out["intl_region"] = str(country.get("region", ""))
	out["from"] = str(country.get("from", country.get("name", "")))
	out["demonym"] = str(country.get("demonym", ""))
	out["home_club"] = str(p.get("draft_team", ""))
	out["seasons_listed"] = int(gs.season_year) - int(p.get("drafted_year", int(gs.season_year) - 99))
	out["goals"] = career_goals
	# What waiting on an early extension can cost: the rise training can still
	# bring his price this season (read on a copy: the ceiling marks the player).
	out["wait_price"] = ClubLife.wait_words(p, gs.season_ceiling(p.duplicate()))
	# His learning project, for the development talk (T5.r93).
	out.merge(project_facts(gs, p), true)
	# The result of his role trial, for the card that reports it.
	var tr: Dictionary = gs.trial_result
	if not tr.is_empty() and str(tr.get("id", "")) == id:
		out["trial_word"] = str(tr["word"])
		out["trial_avg"] = int(tr["avg"])
		out["trial_par"] = int(tr["par"])
		var back := "He goes back to his usual spot."
		if tr.has("promised"):
			# The games you promised him in a development talk: he has had them.
			out["trial_tail"] = "You promised him this chance in Round %d. %s" % [int(tr["promised"]), back]
		elif bool(tr["ok"]):
			out["trial_tail"] = ("%s He starts training as a %s with three weeks already banked." % [back, str(tr["word"])]
					if bool(tr["trained"]) else "%s He cannot start training there just now." % back)
		else:
			out["trial_tail"] = back
	return out



## Not getting senior games: out of your last side and either left out of the
## two rounds before it as well, or picked in fewer than half of this season's
## rounds. Before your first round only the last side counts. A regular who
## sat out one week is not "pushing for games", and nor is one who lost his
## spot to an injury: he is judged on the rounds before he was hurt (the
## "where do I stand" sit-down is his story).
const OUT_WEEKS := 2

## "about a 12%" / "about an 18%".
static func _about_pct(n: int) -> String:
	return "about %s %d%%" % [LeagueStories.an(n), n]


static func out_of_side(gs, p: Dictionary) -> bool:
	var id := str(p.get("id", ""))
	if gs.last_side.has(id):
		return false
	if gs.season == null:
		return true
	var rounds := int(gs.season.round_index)
	if rounds <= 0:
		return true
	var played := int((gs.season_tally.get(id, {}) as Dictionary).get("games", 0))
	var hurt := _hurt_in_round(gs, p)
	if hurt > 0:
		return played * 2 < hurt
	if gs.weeks_without_game(p) >= OUT_WEEKS:
		return true
	return played * 2 < rounds


## The round this season he was hurt in, when the injury came in his last game
## or the round after it (he lost his spot to it); 0 otherwise.
static func _hurt_in_round(gs, p: Dictionary) -> int:
	var lg = p.get("last_game", [])
	if not (lg is Array and (lg as Array).size() == 2 and int(lg[0]) == int(gs.season_year)):
		return 0
	var inj := CareerFacts.of(gs.career_facts, str(p.get("id", "")), "injury")
	if inj.is_empty():
		return 0
	var f: Dictionary = inj[-1]
	if int(f["y"]) != int(gs.season_year) or not str(f["at"]).begins_with("Round"):
		return 0
	var hurt := str(f["at"]).trim_prefix("Round ").to_int()
	var last := int(lg[1])
	return hurt if hurt >= last and hurt <= last + 1 else 0


## Arrived this summer: signed or traded in last off-season, or drafted in it.
static func _new_here(gs, p: Dictionary) -> bool:
	var last: int = int(gs.season_year) - 1
	return int(p.get("joined", 0)) == last or int(p.get("drafted_year", 0)) == last


## What the physio's plan costs a player injured in the pre-season, on the club's
## blocks as set: the development of the weeks he sits out (a week passes for him,
## then the week is trained, as GameState.preseason_step_week does; PreSeason.week_xp,
## before his coaches' touch), the Heavy weeks among them, and the injury weeks still
## to run at Round 1. All 0 outside the pre-season or for a concussion.
static func preseason_miss(gs, p: Dictionary) -> Dictionary:
	var out := {"xp": 0, "heavy": 0, "rounds": 0}
	var left := int(p.get("injury_weeks", 0))
	if not gs.preseason_active() or left <= 0 or str(p.get("injury_kind", "")) == "concussion":
		return out
	var blocks: Array = gs.preseason_blocks()
	for w in range(gs.preseason_week() + 1, PreSeason.weeks() + 1):
		left -= 1
		var i := PreSeason.block_of_week(w)
		var block: Array = blocks[i] if i >= 0 and i < blocks.size() else []
		if not block.is_empty() and str(block[0]) == "light":
			left -= int(PreSeason.tune("light_heal_extra"))
		if left <= 0:
			return out
		if not block.is_empty():
			out["xp"] = int(out["xp"]) + PreSeason.week_xp(str(block[0]), str(block[1]))
			out["heavy"] = int(out["heavy"]) + (1 if str(block[0]) == "heavy" else 0)
	out["rounds"] = left
	return out


## Where he finished in this pre-season's time trial: "best", "worst" or "".
static func _trial_place(gs, id: String) -> String:
	var tr: Dictionary = gs.preseason_trial()
	if (tr.get("best", []) as Array).has(id):
		return "best"
	if (tr.get("worst", []) as Array).has(id):
		return "worst"
	return ""


## The ageing rule retires him at this rollover (Retirement.intends, read-only: the
## coach can still talk him round at the rollover, so a card only says "could be").
static func _last_season(gs, p: Dictionary) -> bool:
	if int(p.get("play_on", 0)) == int(gs.season_year) + 1:
		return false
	# A player without his ratings (a bare test fixture) can't be aged by the rule.
	var rated: Dictionary = p.get("attr", {})
	var role: String = str(p.get("role", "MID"))
	var needs: Array = (Ratings.ROLE_WEIGHTS.get(role, Ratings.ROLE_WEIGHTS["MID"]) as Dictionary).keys() + ["star", "durability"]
	for k in needs:
		if not rated.has(k):
			return false
	return Retirement.intends(p, int(gs.season_year) + 1)


## His first season of senior football: no game before this year, one or more in it,
## and a career this save has seen in full.
static func _debut_year(gs, p: Dictionary) -> bool:
	var this_year: int = gs.season_games(str(p["id"]))
	return Career.complete(p) and this_year >= 1 and gs.games_played(p) - this_year == 0


## The milestone his next game is, from the banner rule (GameState.milestone_notes);
## 0 when it is not a game worth a banner.
static func _milestone_next(gs, p: Dictionary) -> int:
	if not Career.complete(p):
		return 0
	var next: int = gs.games_played(p) + 1
	return next if [100, 150, 200, 250, 300, 350].has(next) else 0


## Where a line plays, as a coach says where a player goes ("up forward").
const LINE_WHERE := {"FWD": "up forward", "DEF": "down back", "MID": "in the middle", "RUCK": "in the ruck"}


## His learning project as the development talk reads it (T5.r93): due, the
## job's word, the week, both ratings, the pass rule and the odds it takes.
static func project_facts(gs, p: Dictionary) -> Dictionary:
	var out := {"dev_talk_due": false, "proj_word": "", "proj_week": 0, "proj_weeks": GameState.PROJECT_WEEKS,
			"proj_there": 0, "proj_own": int(p.get("overall", 0)), "proj_pass": GameState.PROJECT_PASS,
			"take_odds": "", "proj_line": ""}
	var job: String = gs.project_job(p)
	if job == "" or (p.get("attr", {}) as Dictionary).is_empty():
		return out
	var role: String = gs.project_role(p)
	out["dev_talk_due"] = gs.dev_talk_due(p) and int(p.get("injury_weeks", 0)) <= 0
	out["proj_word"] = str(GameState.LEARN_JOBS[job]["word"])
	out["proj_week"] = int((p["project"] as Dictionary).get("weeks", 0))
	out["proj_there"] = gs.rating_as(p, role)
	out["take_odds"] = gs.take_odds(p)
	out["proj_line"] = str(LINE_WHERE.get(role, ""))
	return out


## One card from the deck about `p` (or the club), built for this week whether
## or not it would come up: for tests and captures.
static func card_for(gs, tid: String, p: Dictionary = {}, extra: Dictionary = {}) -> Dictionary:
	var deck := StoryDeck.all()
	var t := StoryDeck.by_id(deck, tid)
	if t.is_empty():
		return {}
	var end_card := (t.get("phase", []) as Array).has("season_end")
	var ctx := context(gs, "season_end" if end_card else "") if gs.season != null else {"club": {}, "players": []}
	var subj := {"kind": "club"}
	if not p.is_empty():
		subj = {}
		for f in ctx["players"]:
			if str(f["id"]) == str(p["id"]):
				subj = f
		if subj.is_empty():
			subj = player_fact(gs, p, false, {}, 99, 0)
	if tid == "contracts_new_club_approach" and extra.is_empty() and not p.is_empty():
		extra = ExpansionBuild.card_facts(gs, p, ExpansionBuild.asking_club(gs))
	if not extra.is_empty():
		subj = subj.duplicate()
		subj.merge(extra, true)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(tid)
	return StoryEngine.build(deck, t, subj, ctx["club"], rng, gs.story_week())


## Apply a choice. Returns the result line: what happened (an effect that
## has something to report speaks first, else the card's own result), then
## what changed in his trust and the board's mood.
static func apply_choice(gs, card: Dictionary, choice: int) -> String:
	var opt: Dictionary = (card.get("options", []) as Array)[choice]
	var pid := str(card.get("player_id", ""))
	var p: Dictionary = gs.list_player(pid) if pid != "" else {}
	if pid != "" and p.is_empty():
		return "The moment has passed: he is no longer at the club."
	var facts: Dictionary = (card.get("facts", {}) as Dictionary).duplicate()
	facts["_tid"] = str(card.get("tid", ""))
	facts["_result"] = str(opt.get("result", ""))
	var applied := {}
	var said: PackedStringArray = []
	# A role trial that cannot start (he is not in the side now, or is picked
	# there already) costs nothing: no trust, morale or board either.
	for e in opt.get("effects", []):
		if str(e.get("op", "")) == "role_trial":
			var started: String = gs.start_role_trial(p, int(e.get("weeks", 3)))
			if started == "":
				return "%s is not in the side to try in a new role, so nothing changes." % GameDB.player_display_name(p)
			said.append(started)
	for e in opt.get("effects", []):
		if str(e.get("op", "")) == "role_trial":
			continue
		var line := _apply(gs, e, p, facts, applied)
		if line != "":
			said.append(line)
	var out := " ".join(said) if not said.is_empty() else str(opt.get("result", ""))
	# A promise made on a card that has its own result line: the line first, then what he now expects.
	if bool(applied.get("_lead_result", false)) and not said.is_empty() and str(opt.get("result", "")) != "":
		out = str(opt["result"]) + " " + out
	out = StoryEngine.fill_ranked(out, running_fitness(gs))
	if out == "":
		out = "Business as usual."
	return (out + " " + StoryEngine.aftermath(applied)).strip_edges()


## Your players who could run a time trial, fittest first. The rating is the
## one the match uses for running fitness: durability sets how fast a player
## tires on the ground and how he recovers between games. An injured player
## sits it out; ties go to the name, so the same list gives the same answer.
static func running_fitness(gs) -> Array:
	var rows := []
	for p in gs.my_list:
		if int(p.get("injury_weeks", 0)) > 0:
			continue
		rows.append({"id": str(p["id"]), "name": GameDB.player_display_name(p),
				"v": int((p.get("attr", {}) as Dictionary).get("durability", 0))})
	rows.sort_custom(func(a, b): return int(a["v"]) > int(b["v"]) or (int(a["v"]) == int(b["v"]) and str(a["id"]) < str(b["id"])))
	return rows


## The position a role trial would try him in: his second position, or one he
## has learned, that is not the one he is listed at. "" when he has none.
static func trial_role(p: Dictionary) -> String:
	for r in Ratings.second_positions(p):
		if str(r) != "" and str(r) != str(p.get("role", "")):
			return str(r)
	return ""


static func _targets(gs, e: Dictionary, p: Dictionary, facts := {}) -> Array:
	match str(e.get("who", "subject")):
		"subject":
			return [p] if not p.is_empty() else []
		"others":
			return gs.my_list.filter(func(q): return q != p)
		"side":
			var ids := {}
			var side: Dictionary = gs.current_side()
			for k in side:
				for id in side[k]:
					ids[str(id)] = true
			return gs.my_list.filter(func(q): return ids.has(str(q["id"])))
		"vice":
			# The vice-captain the card named when it was dealt, even if the armbands
			# have moved since (the card points at the Captaincy page).
			var vid := str(facts.get("vice_id", ""))
			return gs.my_list.filter(func(q): return vid != "" and str(q["id"]) == vid)
	return gs.my_list


static func _apply(gs, e: Dictionary, p: Dictionary, facts: Dictionary, applied: Dictionary) -> String:
	var d := StoryEngine.effect_d(e, facts)
	var name := str(facts.get("name", ""))
	match str(e.get("op", "")):
		"morale":
			for q in _targets(gs, e, p, facts):
				ClubLife.add_morale(q, d)
			applied["morale"] = int(applied.get("morale", 0)) + d
		"xp":
			for q in _targets(gs, e, p):
				q["xp"] = int(q.get("xp", 0)) + d
			if str(e.get("who", "subject")) == "subject":
				gs.apply_plan_to(p)
			else:
				gs.apply_train_plans()
		"board":
			if not gs.board.is_empty():
				gs.board["confidence"] = clampi(gs.board_confidence() + d, 0, 100)
			applied["board"] = int(applied.get("board", 0)) + d
		"trust":
			var when := "Round %d" % int(facts.get("round", 0)) if int(facts.get("finals_week", 0)) == 0 else "Finals"
			if int(facts.get("pre_week", 0)) > 0:
				when = "Pre-season"
			var key := Trust.player_key(str(p["id"]))
			var before := Trust.opinion(Trust.value(gs.relations, key))
			applied["trust"] = int(applied.get("trust", 0)) + Trust.change(gs.relations, key,
					d, StoryEngine.fill(str(e.get("why", "")), facts), int(gs.season_year), when)
			# His opinion of you before the first move and after the last.
			applied["opinion"] = [int((applied.get("opinion", [before]) as Array)[0]),
					Trust.opinion(Trust.value(gs.relations, key))]
		"rest":
			p["rested"] = true
		"slow_start":
			# A small chance, rolled once for the whole group (or the one player), from the
			# save's seed: the same save answers the same way. The card names the chance; the roll shows on the day.
			var hit := StoryEngine.risk_hit(int(gs.season.seed), int(facts.get("year", 0)), int(facts.get("round", 0)),
					"%s|slow|%s|%s" % [facts.get("_tid", ""), e.get("who", "subject"), name], int(e.get("chance", 0)))
			if hit:
				for q in _targets(gs, e, p):
					q["slow_start"] = true
		"loss_sting":
			# Waits for the result (GameState._settle_loss_sting).
			for q in _targets(gs, e, p):
				q["loss_sting"] = [int(e.get("chance", 0)), int(e.get("d", 0))]
		"culture":
			gs._culture_move(gs.my_club, str(e.get("strand", "")), d, StoryEngine.fill(str(e.get("why", "")), facts))
		"running":
			if str(facts.get("result", "")) != "" and not gs.preseason_active():
				# The week the season ends (B8): next pre-season starts behind.
				gs.preseason_run_debt += float(d)
			else:
				gs.preseason_add_running(float(d))
		"drill":
			gs.preseason_add_drill(d)
		"news":
			gs.add_news("retirement", StoryEngine.fill(str(e.get("text", "")), facts))
		"rush_back":
			if str(p.get("injury_kind", "")) == "concussion":
				return "%s stays out: a concussion keeps him out under the protocols." % name
			p["injury_weeks"] = 0
			p.erase("injury_kind")
			p["sore"] = true
			if gs.preseason_active():
				return "%s is cleared and trains with the group from now." % name
			return "%s is cleared to play. Name him in the side." % name
		"on_record":
			gs.papers_on_record(int(facts.get("claim_rank", 0)))
		"role_trial":
			return gs.start_role_trial(p, int(e.get("weeks", 3)))
		"sore":
			if int(p.get("injury_weeks", 0)) > 0:
				return "%s has since been ruled out anyway." % name
			p["sore"] = true
		"fresh", "heavy_legs":
			for q in _targets(gs, e, p):
				q[str(e["op"])] = true
		"expects_game":
			# The game you promised: a side you named takes him in now, as a run
			# does (director, 2026-11-12: "he should show as on the team the
			# moment you accept the event"); auto-pick names him by itself.
			var was_in: bool = gs.in_current_side(p)
			var made_way: String = gs.name_promised(p)
			p["expects_game"] = int(e.get("sting", 12))
			# Named just now (not injured or suspended): say who made way.
			var came_in: bool = not was_in and gs.in_current_side(p)
			# Fit, but every place is held by a player owed a game: say so.
			var no_room: bool = not was_in and not came_in and Ratings.available(p)
			if str(facts.get("_result", "")) != "":
				# The card's own result line speaks; on Auto-pick he is named anyway, so
				# only a side you picked yourself needs the reminder.
				if gs.my_selection().is_empty():
					return ""
				applied["_lead_result"] = true
				if no_room:
					return gs.NO_ROOM_WORDS
				return gs.backed_in_words(made_way) if came_in else "He expects a game this week."
			if no_room:
				return "%s feels heard. %s" % [name, gs.NO_ROOM_WORDS]
			if gs.my_selection().is_empty():
				return "%s feels heard. He's in the side this week." % name
			if came_in:
				return "%s feels heard. %s" % [name, gs.backed_in_words(made_way)]
			return "%s feels heard, and expects a game this week." % name
		"start_backing":
			# His chance: a run of senior games (Backing). Leaving him out
			# while fit breaks the promise, and that stings.
			var was_in: bool = gs.in_current_side(p)
			var dropped: String = gs._start_backing(p)
			var run := MatchNotes.count_word(Backing.RUN_GAMES)
			var told := "%s is told he has a run of %s games." % [name, run]
			return told + " " + gs.promised_in_words(p, "" if was_in else dropped)
		"extend_early":
			return _extend(gs, p, name)
		"new_club_keep":
			return ExpansionBuild.keep(gs, p)
		"new_club_go":
			return ExpansionBuild.let_go(gs, p)
		"promise_win":
			gs.board["promise"] = true
		"explain":
			return gs._explain_outcome(name, facts)
		"talk_note":
			gs._note_talk(p, str(e.get("said", "")), str(facts.get("talk_case", "")))
		# The development talk (T5.r93): what you told him his new position is for.
		"dev_promise":
			gs.dev_talk(p, "promise")
		"no_promise":
			gs.dev_talk(p, "depth")
		"delegate":
			# Left to the captain: his Leadership and his trust in you decide, by the
			# rule the choice printed. No dice.
			var held := bool(facts.get("delegate_holds", false))
			var parts: PackedStringArray = []
			for ne in (e.get("held" if held else "failed", []) as Array):
				var said_line := _apply(gs, ne, p, facts, applied)
				if said_line != "":
					parts.append(said_line)
			var res := StoryEngine.fill(str(e.get("held_result" if held else "failed_result", "")), facts)
			return (res + " " + " ".join(parts)).strip_edges()
		"back_kid":
			var kid: Dictionary = gs.list_player(str(facts.get("kid_id", "")))
			if kid.is_empty():
				return "%s is no longer at the club." % str(facts.get("kid_name", "He"))
			var kid_in: bool = gs.in_current_side(kid)
			var kid_out: String = gs._start_backing(kid)
			var kid_told := "%s is told he has a run of %s games." % [str(facts.get("kid_name", "")),
					MatchNotes.count_word(Backing.RUN_GAMES)]
			return kid_told + " " + gs.promised_in_words(kid, "" if kid_in else kid_out)
		"captaincy_swap":
			var vice: Dictionary = gs.list_player(str(facts.get("vice_id", "")))
			if vice.is_empty() or p.is_empty():
				return "The captaincy stays as it is."
			# The card may be older than the captaincy: if you have changed it since, do nothing.
			var now: Dictionary = gs.captaincy_record(gs.my_club)
			if Captaincy.role_of(now, str(p["id"])) != "captain" or Captaincy.role_of(now, str(vice["id"])) != "vice":
				return "The captaincy has changed since this came up, so nothing changes."
			var slots := [{"id": str(vice["id"]), "role": "captain"}, {"id": str(p["id"]), "role": "vice"}]
			for s in Captaincy.slots(gs.captaincy_record(gs.my_club)):
				var sid := str((s as Dictionary)["id"])
				if sid != str(vice["id"]) and sid != str(p["id"]) and slots.size() < Captaincy.MAX_LEADERS:
					slots.append(s)
			var pv: Dictionary = gs.set_captaincy(slots)
			if not bool(pv.get("ok", false)):
				return str(pv.get("why_not", "The captaincy can't change this week."))
			return "%s takes the armband. %s hands it over and stays in the leadership group." % [str(facts.get("vice_name", "")), name]
	return ""


static func _extend(gs, p: Dictionary, name: String) -> String:
	var cost := ClubLife.early_price(p)
	var years := ClubLife.early_years(p)
	if int(p.get("contract_years", 1)) > 1:
		return "%s is already signed beyond this season." % name
	if gs.my_payroll() - int(p.get("salary", 0)) + cost > gs.cap_for(str(gs.my_club)):
		# The cap moved since the card was drawn: nobody's fault.
		return "The cap no longer has room to extend %s now; it waits for the off-season." % name
	# Under 50, he may refuse you (director 2026-11-08): the draw talks use.
	if gs.resign_refused(p):
		return gs.refuse_resign(p, Contracts.REFUSED_SEASON_END)
	p["salary"] = cost
	p["contract_years"] = years
	ClubLife.add_morale(p, StoryEngine.EXTEND_MORALE)
	return "%s signs on for %d more season%s at %s a season." % [name, years - 1,
			"" if years == 2 else "s", Contracts.money(cost)]
