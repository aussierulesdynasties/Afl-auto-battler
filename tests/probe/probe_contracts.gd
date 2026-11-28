extends SceneTree
## Scratch probe (never commit): why the two contracts checks fail at this commit.

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	gs.autosave_enabled = false
	gs.save_path = "user://test_career.save"
	gs.settings_path = "user://test_settings.cfg"
	var suite = load("res://tests/test_contracts.gd").new()
	db.reload()
	gs.replay_seed = 2027
	# Same order as the suite up to the free-agent check.
	for f in ["_test_initial_contracts", "_test_first_contracts_fit_the_cap", "_test_rivals_keep_their_stars_2010", "_test_real_money_scale"]:
		suite.call(f)
	suite._new_season()
	suite._to_offseason()
	var C = load("res://scripts/sim/Contracts.gd")
	print("PROBE my_list=%d max=%d min=%d fa=%d" % [gs.my_list.size(), C.MAX_LIST, C.min_list(), gs.free_agents.size()])
	var mine: Array = C.expiring(gs.my_list)
	if mine.size() > 0:
		gs.resign_player(str(mine[0]["id"]), 3)
	gs.salary_cap += 5000000
	var n := 0
	for fa in gs.free_agents.duplicate():
		var rel := str(fa.get("released_by", ""))
		var offers: Array = fa.get("offers", [])
		var terms: Dictionary = gs.free_agent_terms(str(fa["id"]))
		if n < 12:
			print("PROBE fa %s rel=%s offers=%d refuse=%s" % [str(fa["id"]), rel, offers.size(), str(terms.get("refuse"))])
		n += 1
		if rel != gs.my_club and offers.is_empty() and not bool(terms["refuse"]):
			var res: Dictionary = gs.sign_free_agent(str(fa["id"]), int(C.wants(fa)["years"]))
			print("PROBE sign %s -> %s" % [str(fa["id"]), str(res)])
			break
	quit(0)
