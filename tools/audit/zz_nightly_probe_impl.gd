extends RefCounted
## Throwaway probe for the nightly trace. Never merged.


func run() -> void:
	GameState.autosave_enabled = false
	GameState.save_path = "user://probe.save"
	GameState.settings_path = "user://probe.cfg"
	_preseason()
	for s in [11, 12, 13]:
		_future(s)
	_tas_cap()


func _preseason() -> void:
	PreSeason.reload()
	GameState.reset()
	GameState.career_seed = 4127
	GameState.replay_seed = 4127
	GameState.start_season("FRE", GameDB.club_list("FRE"))
	GameState.open_preseason()
	var guard := 0
	while GameState.preseason_stop() != "practice" and guard < 8:
		guard += 1
		GameState.preseason_advance()
	var pros: Array = GameState.preseason_prospects()
	print("PS year ", GameState.season_year, " prospects ", pros.size())
	var ss := {}
	for p in pros:
		var st := str(p.get("state", ""))
		ss[st] = int(ss.get(st, 0)) + 1
	print("PS states ", ss)
	print("PS first ", pros.slice(0, 8).map(func(p): return [p["id"], p.get("state", ""), p.get("draft_year", 0), p.get("tied_club", "")]))
	var seen_id := str(pros[3]["id"])
	print("PS invite ", GameState.toggle_practice_invite(seen_id))
	GameState.sim_practice_match()
	guard = 0
	while GameState.preseason_active() and guard < 12:
		guard += 1
		GameState.preseason_advance()
	GameState.season.round_index = GameState.season.fixture.size()
	var ok: bool = GameState.begin_intake_draft()
	print("PS drafting ", ok, " draft ", GameState.draft != null)
	var in_pool := false
	for p in GameState.draft.pool:
		if str(p["id"]) == seen_id:
			in_pool = true
			print("PS pool seen ", p.get("seen", {}), " line=", PreSeason.seen_line(p, "FRE"))
	print("PS in pool ", in_pool, " picked ", GameState.draft.picked.has(seen_id), " pool ", GameState.draft.pool.size())
	for row in GameState.intake_assignments:
		if str(row).contains(seen_id):
			print("PS assigned ", row)
	var kinds := {}
	for row in GameState.intake_assignments:
		var k := "%s/%s" % [str(row.get("club", "")), str(row.get("kind", ""))]
		kinds[k] = int(kinds.get(k, 0)) + 1
	print("PS assign ", kinds)
	for q in GameState.draftee_pool:
		if str(q["id"]) == seen_id:
			print("PS draftee seen ", q.get("seen", {}), " line=", PreSeason.seen_line(q, "FRE"))


func _offseason() -> void:
	GameState.season.round_index = GameState.season.fixture.size()
	GameState.ensure_finals()
	while not GameState.season.is_season_over():
		GameState.advance()


func _run_draft() -> void:
	var d: Draft = GameState.draft
	while not d.is_finished():
		var c := d._best_ai_pick(d.current_club())
		if c.is_empty() or not d._draft_pick(d.current_club(), c):
			d._skip_current_pick()


func _future(s: int) -> void:
	GameState.reset()
	GameState.career_seed = s
	GameState.replay_seed = s
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	_offseason()
	var me := GameState.my_club
	var next: int = GameState.season_year + 1
	var rival := "COL"
	var my_future := GameState.pick_id(next, 1, me)
	var sorted_mine := GameState.my_list.duplicate()
	sorted_mine.sort_custom(func(a, b): return int(a["overall"]) < int(b["overall"]))
	var theirs := (GameState.season.lists[rival] as Array).duplicate()
	theirs.sort_custom(func(a, b): return int(a["overall"]) < int(b["overall"]))
	var t := GameState.make_trade(rival, [my_future], [str(theirs[0]["id"])])
	if not bool(t["ok"]):
		t = GameState.make_trade(rival, [my_future, str(sorted_mine[0]["id"])], [str(theirs[0]["id"])])
	print("FP%d trade ok=%s owner=%s" % [s, str(t["ok"]), GameState.pick_owner_of(next, 1, me)])
	print("FP%d draft1 %s" % [s, str(GameState.begin_intake_draft())])
	_run_draft()
	print("FP%d finish %s year=%d owner=%s" % [s, str(GameState.finish_intake_draft()), GameState.season_year, GameState.pick_owner_of(next, 1, me)])
	_offseason()
	print("FP%d after season year=%d offyear=%d owner=%s" % [s, GameState.season_year, GameState.offseason_year, GameState.pick_owner_of(next, 1, me)])
	var now := GameState.pick_asset(GameState.pick_id(next, 1, me))
	print("FP%d asset %s" % [s, str(now)])
	print("FP%d active TAS %s lists TAS %s" % [s, str(GameDB.active_clubs(GameState.season_year).has("TAS")), str(GameState.season.lists.has("TAS"))])
	for e in GameState.offseason_log:
		if str(e.get("text", "")).contains(GameDB.club_name(me)) or str(e).contains(my_future) or str(e).contains("pick:%d:1:%s" % [next, me]):
			print("FP%d log %s" % [s, str(e).left(200)])
	print("FP%d draft2 %s" % [s, str(GameState.begin_intake_draft())])
	var d: Draft = GameState.draft
	for k in range(d.pick_sequence.size()):
		if str(d.pick_origin[k]) == me and int(d.pick_rounds[k]) == 1:
			print("FP%d slot k=%d seq=%s comp=%s" % [s, k, str(d.pick_sequence[k]), str(d.comp_at(k))])
	print("FP%d first 14 seq=%s" % [s, str(d.pick_sequence.slice(0, 14))])
	print("FP%d first 14 origin=%s" % [s, str(d.pick_origin.slice(0, 14))])


func _tas_cap() -> void:
	for s in [21, 22, 23]:
		GameState.reset()
		GameState.career_seed = s
		GameState.replay_seed = s
		GameState.start_season("GEE", GameDB.club_list("GEE"))
		_offseason()
		GameState.open_offseason()
		GameState._close_contracts()
		var by := {}
		for e in GameState.offseason_log:
			if str(e.get("kind", "")) == "signed":
				var c := str(e["club"])
				by[c] = int(by.get(c, 0)) + 1
		print("CAP%d signed %s" % [s, str(by)])
		for code in ["TAS"]:
			if GameState.expansion.has(code):
				var list: Array = ExpansionBuild.list_of(GameState, code)
				print("CAP%d %s list %d payroll %d cap_for %d cap %d relief %d" % [s, code, list.size(), Contracts.payroll(list), GameState.cap_for(code), GameState.salary_cap, ExpansionBuild.relief(GameState, code)])
