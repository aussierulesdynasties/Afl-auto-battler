extends SceneTree
## Scratch probe (never commit): why GEE's 2026 list ends a draft under the
## minimum in test_list_turnover.

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	gs.autosave_enabled = false
	gs.save_path = "user://test_career.save"
	gs.settings_path = "user://test_settings.cfg"
	var C = load("res://scripts/sim/Contracts.gd")
	gs.reset("2026")
	gs.replay_seed = 2027
	gs.career_seed = 2027
	gs.start_season("GEE", db.club_list("GEE"))
	for _i in range(10):
		var season = gs.season
		season.round_index = season.fixture.size()
		var before: int = gs.my_list.size()
		if not gs.begin_intake_draft():
			print("PROBE %d no intake draft" % gs.season_year)
			break
		var draft = gs.draft
		var guard := 0
		var at_pass := ""
		draft.auto_until_user_turn()
		while not draft.is_finished() and guard < 4000:
			guard += 1
			if draft.is_user_turn():
				var why: String = draft.pass_block_reason()
				if why == "":
					at_pass = "existing=%d count_for=%d leaving=%d wage=%d room=%d min=%d" % [
						int(draft.existing_sizes.get("GEE", 0)), draft.count_for("GEE"), int(draft.leaving.get("GEE", 0)),
						draft.pick_wage(), draft.room_left("GEE"), C.min_list()]
					draft.user_pass()
					continue
			var cand: Dictionary = draft._best_ai_pick(draft.current_club())
			if cand.is_empty() or not draft._draft_pick(draft.current_club(), cand):
				draft._skip_current_pick()
			draft.auto_until_user_turn()
		var mid: int = gs.my_list.size()
		if not gs.finish_intake_draft():
			print("PROBE %d finish failed" % gs.season_year)
			break
		var retired: Array = gs.intake_summary.get("retired", [])
		print("PROBE year=%d before=%d after_draft=%d after_finish=%d min=%d retired=%d pass[%s] keys=%s" % [
			gs.season_year, before, mid, gs.my_list.size(), C.min_list(), retired.size(), at_pass,
			str(gs.intake_summary.keys())])
	quit(0)
