extends SceneTree
## Scratch probe (never commit): the contracts suite in order up to
## _test_trade_market, then why the rebuilding club's starter is off the
## contender's pool.

const BEFORE := ["_test_initial_contracts", "_test_first_contracts_fit_the_cap", "_test_rivals_keep_their_stars_2010",
	"_test_real_money_scale", "_test_offseason_flow", "_test_offseason_books_are_next_seasons",
	"_test_real_retirements_are_retirements", "_test_real_delistings", "_test_career_end_card", "_test_list_costs",
	"_test_fa_weights", "_test_market_test", "_test_negotiation_rules", "_test_negotiation", "_test_refuse_to_resign",
	"_test_opinion_never_drifts", "_test_free_agent_terms", "_test_free_agents", "_test_market_marks",
	"_test_compensation_rules", "_test_compensation_draft_order", "_test_compensation_flow", "_test_trade_value",
	"_test_trade_packages_and_needs", "_test_phase_cache", "_test_trade_picks", "_test_future_picks",
	"_test_draft_night_trades", "_test_night_trades_never_name_called_picks", "_test_mixed_packages"]


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
	for f in BEFORE:
		await suite._t(f)
	print("PROBE before: replay_seed=%d failures=%s" % [gs.replay_seed, str(suite.failures)])
	suite._new_season()
	suite._to_offseason()
	var R = load("res://scripts/sim/Ratings.gd")
	var me: String = gs.my_club
	var by_phase := {}
	for code in gs.season.lists:
		if code != me and not by_phase.has(gs.club_phase(code)):
			by_phase[gs.club_phase(code)] = code
	print("PROBE by_phase=%s career_seed=%d" % [str(by_phase), gs.career_seed])
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
		print("PROBE con %s phase=%s reb phase=%s pool has ground[0]=%s pool size=%d list size=%d" % [con,
				gs.club_phase(con), gs.club_phase(reb), str(pool_ids.has(str(ground[0]["id"]))),
				pool_ids.size(), (gs.season.lists[reb] as Array).size()])
	quit(0)
