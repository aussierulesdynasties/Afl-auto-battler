extends RefCounted
## Row 74 (T5.Q11a): Gather Round (GatherRound, switch `gather_round`). Off, every
## round is as before. On, one of rounds 3 to 7 is staged at the host's grounds:
## the fixture itself is unchanged, every match of the round is at a host ground,
## a club has its home edge only at its own ground, a club on a bye sits it out,
## the round's name reaches the fixture, the hub and the match, and a seeded
## career plays it live and keeps it across a save and load.
## Run through run_gather_round_tests.gd.

const SUITE_SEED := 2027

var failures: Array[String] = []
var checks := 0
var root: Window
var _tree: SceneTree
var gs


func _check(ok: bool, msg: String) -> void:
	checks += 1
	if not ok:
		failures.append(msg)
		push_error(msg)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func run(tree: SceneTree) -> void:
	root = tree.root
	_tree = tree
	gs = GameState
	failures.clear()
	checks = 0
	root.size = Vector2i(390, 844)
	GameState.replay_seed = SUITE_SEED
	_t("_test_switch_off")
	_t("_test_round_and_grounds")
	_t("_test_odd_club_count")
	await _t("_test_career_live_round")
	Features.set_on(GatherRound.SWITCH, false)
	GameState.replay_seed = 0
	print(Ran.line("Gather round", self))


func _season(codes: Array, seed: int) -> Season:
	var lists := {}
	for c in codes:
		lists[c] = GameDB.club_list(str(c))
	return Season.new(codes, lists, seed)


func _codes() -> Array:
	return GameDB.active_clubs(2026).duplicate()


func _hosts() -> Array:
	var out := []
	for v in GatherRound.VENUES:
		out.append(str(v["ground"]))
	return out


func _test_switch_off() -> void:
	Features.set_on(GatherRound.SWITCH, false)
	var s := _season(_codes(), 7401)
	_check(s.gather_round() == -1, "Switch off: no Gather Round (%d)" % s.gather_round())
	var same := true
	for r in range(s.fixture.size()):
		if s.round_label(r) != "Round %d" % (r + 1):
			same = false
		for m in s.fixture[r]:
			if s.round_venue(r, m["home"], m["away"]) != s.home_ground(m["home"]) \
					or s.round_at_home(r, m["home"], m["away"]) != [true, false]:
				same = false
	_check(s.fixture.size() == Season.REGULAR_ROUNDS and same,
			"Switch off: every round named, staged and edged as before")


func _test_round_and_grounds() -> void:
	Features.set_on(GatherRound.SWITCH, false)
	var off := _season(_codes(), 7402)
	Features.set_on(GatherRound.SWITCH, true)
	var s := _season(_codes(), 7402)
	_check(str(s.fixture) == str(off.fixture), "The fixture itself is unchanged: every pairing and home game as before")
	var g := s.gather_round()
	_check(g >= GatherRound.FIRST and g <= GatherRound.LAST, "Gather Round is one of rounds 3 to 7 (%d)" % (g + 1))
	_check(_season(_codes(), 7402).gather_round() == g, "The same season seed gives the same Gather Round")
	var rounds := {}
	for sd in range(30):
		rounds[_season(_codes(), 9000 + sd).gather_round()] = true
	_check(rounds.size() >= 2, "Not one year's round number: it moves with the season (%s)" % str(rounds.keys()))
	_check(s.round_label(g) == "Round %d · Gather Round" % (g + 1), "Its name: %s" % s.round_label(g))
	_check(s.round_label(g + 1) == "Round %d" % (g + 2), "The next round keeps its plain name")
	var ms: Array = s.fixture[g]
	_check(ms.size() == _codes().size() / 2, "Every club plays in it at an even count (%d matches)" % ms.size())
	var hosts := _hosts()
	var count := {}
	for m in ms:
		var v := s.round_venue(g, m["home"], m["away"])
		count[v] = int(count.get(v, 0)) + 1
		_check(hosts.has(v), "%s v %s is at a host ground (%s)" % [m["home"], m["away"], v])
		var edge := s.round_at_home(g, m["home"], m["away"])
		_check(edge == [s.home_ground(m["home"]) == v, s.home_ground(m["away"]) == v],
				"%s v %s: the home edge only at a club's own ground (%s)" % [m["home"], m["away"], str(edge)])
		for c in [str(m["home"]), str(m["away"])]:
			if s.home_ground(c) == "Adelaide Oval":
				_check(v == "Adelaide Oval", "%s plays at its own ground in Gather Round (%s)" % [c, v])
			else:
				_check(not edge[0 if c == str(m["home"]) else 1], "%s, relocated, has no home edge" % c)
	_check(int(count.get("Adelaide Oval", 0)) == 5 and int(count.get("Norwood Oval", 0)) == 2
			and int(count.get("Barossa Park", 0)) == 2, "The main ground takes the most matches (%s)" % str(count))
	_check(s.weather_for(ms[0]["home"], ms[0]["away"], g) in ["perfect", "wet", "windy", "hot"],
			"The weather is read at the host ground")
	var other := g + 1
	for m in s.fixture[other]:
		_check(s.round_venue(other, m["home"], m["away"]) == s.home_ground(m["home"])
				and s.round_at_home(other, m["home"], m["away"]) == [true, false],
				"Round %d is at home grounds as before" % (other + 1))


func _test_odd_club_count() -> void:
	Features.set_on(GatherRound.SWITCH, true)
	var codes := _codes()
	codes.append("TAS")
	_check(codes.size() % 2 == 1, "An odd club count (%d)" % codes.size())
	var s := _season(codes, 7403)
	var g := s.gather_round()
	_check(g >= GatherRound.FIRST and g <= GatherRound.LAST, "Odd count: Gather Round still in rounds 3 to 7 (%d)" % (g + 1))
	var out := func(r: int) -> Array:
		var playing := {}
		for m in s.fixture[r]:
			playing[str(m["home"])] = true
			playing[str(m["away"])] = true
		return codes.filter(func(c): return not playing.has(str(c)))
	var sitting: Array = out.call(g)
	_check(sitting.size() >= 1, "Odd count: a club sits Gather Round out (%s)" % str(sitting))
	for r in range(GatherRound.FIRST, GatherRound.LAST + 1):
		_check((out.call(r) as Array).size() >= sitting.size(),
				"The round with the fewest byes is chosen (round %d: %d out)" % [r + 1, (out.call(r) as Array).size()])
	var hosts := _hosts()
	for m in s.fixture[g]:
		_check(not sitting.has(str(m["home"])) and not sitting.has(str(m["away"])), "No fixture invented for a club on the bye")
		_check(hosts.has(s.round_venue(g, m["home"], m["away"])), "Odd count: every match at a host ground")


func _test_career_live_round() -> void:
	Features.set_on(GatherRound.SWITCH, true)
	gs.reset()
	gs.start_season("GEE", GameDB.club_list("GEE"))
	gs.set_setting("seen_weekly_loop_intro", true)
	var g: int = gs.season.gather_round()
	_check(g >= GatherRound.FIRST, "The career has a Gather Round (%d)" % (g + 1))
	var guard := 0
	while gs.season.round_index < g and guard < 30:
		gs.advance()
		guard += 1
	_check(gs.season.round_index == g, "Played to Gather Round (round %d)" % (gs.season.round_index + 1))
	_check(gs.save_career(), "Saved before Gather Round")
	Features.set_on(GatherRound.SWITCH, true)
	_check(gs.load_career(), "Loaded")
	_check(gs.season.gather_round() == g, "After a load it is the same round, from the saved season")
	# The hub's fixture list names it.
	var pages: Array = StatsFixture.pages(gs.season)
	_check(str(pages[g]["event"]) == GatherRound.NAME and str(pages[g]["title"]) == "Round %d" % (g + 1),
			"Fixture list: %s, named Gather Round" % str(pages[g]["title"]))
	_check(str(pages[g + 1]["event"]) == "", "Fixture list: the next round is not")
	var on_bye: bool = not gs.season.fixture[g].any(func(m): return m["home"] == "GEE" or m["away"] == "GEE")
	_check(not on_bye, "Geelong plays in Gather Round")
	_check(gs.prepare_interactive_match(), "Gather Round is played live")
	var pm: Dictionary = gs.pending_match
	_check(str(pm.get("label", "")).ends_with("Gather Round"), "The match is named: %s" % str(pm.get("label", "")))
	var v := str(pm.get("venue", ""))
	_check(_hosts().has(v), "The match carries its host ground (%s)" % v)
	var sim: MatchSim = gs.pending_sim
	var mine := 0 if str(pm["home"]) == "GEE" else 1
	_check(not sim.squads[mine].home, "Geelong, relocated to %s, has no home edge" % v)
	var opp := str(pm["away"] if mine == 0 else pm["home"])
	_check(bool(sim.squads[1 - mine].home) == (gs.season.home_ground(opp) == v),
			"%s has its edge only at its own ground (%s)" % [opp, v])
	var res: Dictionary = sim.run()
	res["venue"] = v
	gs.finish_interactive_match(res)
	var played: Array = gs.season.results[g]
	_check(played.size() == gs.season.fixture[g].size(), "Every match of the round is recorded (%d)" % played.size())
	for r in played:
		_check(_hosts().has(str(r.get("venue", ""))) and str(r.get("label", "")).ends_with("Gather Round"),
				"%s v %s kept its host ground and name (%s, %s)" % [r["home"], r["away"], r.get("venue", ""), r.get("label", "")])
	gs.advance()
	_check(gs.season.round_index == g + 2 or gs.season.round_index == g + 1, "The season goes on after Gather Round")
	_check(str(gs.season.round_label(gs.season.round_index - 1)) == "Round %d" % gs.season.round_index,
			"The round after is a plain round")
