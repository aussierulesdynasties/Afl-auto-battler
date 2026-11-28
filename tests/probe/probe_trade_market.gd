extends SceneTree
## Scratch probe (never commit): why "A contender can go after a rebuilding
## club's starter" fails in _test_trade_market.

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
	gs.replay_seed = 2027
	suite._new_season()
	suite._to_offseason()
	var R = load("res://scripts/sim/Ratings.gd")
	var me: String = gs.my_club
	var by_phase := {}
	for code in gs.season.lists:
		if code != me and not by_phase.has(gs.club_phase(code)):
			by_phase[gs.club_phase(code)] = code
	print("PROBE by_phase=%s" % str(by_phase))
	if by_phase.has("contending") and by_phase.has("rebuilding"):
		var reb := str(by_phase["rebuilding"])
		var con := str(by_phase["contending"])
		var ground: Array = R.select_22(gs.season.lists[reb])["ground"]
		for i in range(mini(4, ground.size())):
			var q: Dictionary = ground[i]
			var id := str(q["id"])
			print("PROBE reb %s ground[%d] %s %s retiring=%s request=%s" % [reb, i, id, str(q.get("name", "")),
					str(gs.retiring_now(q)), str(gs.trade_requests.get(id, "none"))])
		var pool_ids: Array = gs._trade_pool(con, reb).map(func(q): return str(q["id"]))
		print("PROBE con %s pool has ground[0]=%s pool size=%d list size=%d" % [con, str(pool_ids.has(str(ground[0]["id"]))),
				pool_ids.size(), (gs.season.lists[reb] as Array).size()])
	quit(0)
