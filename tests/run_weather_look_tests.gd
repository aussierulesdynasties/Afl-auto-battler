extends SceneTree
## godot --headless --path . --script tests/run_weather_look_tests.gd
## The weather and the time of day as the match scenes draw them (TODO row 166; director,
## 2026-11-12): the wind shows in flags and a scoreboard arrow, never as lines over the
## grass; a match is a day, twilight or night game by its ground's real 2026 share, the
## same every time it is asked; a Grand Final is a day game and a hot day never a night
## game; a hot day's light and turf differ from a mild day's by a set margin; the night
## look is the one every scene had before; and none of it reaches the match: the same
## seed gives the same match under every sky and weather drawn.

const Ran := preload("res://tests/functions_ran.gd")
const WEATHERS := ["perfect", "wet", "windy", "hot"]

var _checks := 0
var _failures: Array[String] = []
var _state: Node
# Loaded after the autoloads exist (they name GameDB and UiKit).
var Ground
var Wx
var Kickoff
var Grade
var Ball


## A bare scene that draws the ground through a camera, as the match scenes do.
class Stage extends Control:
	var ground
	var cam
	var weather := ""
	var board := {}
	var drawn := 0

	func _draw() -> void:
		ground.draw_ground(self, cam, Rect2(Vector2.ZERO, size), [[Color.PURPLE, Color.WHITE], [Color.RED, Color.BLUE]],
				7, board, weather, 1.5)
		drawn += 1


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_state.autosave_enabled = false
	_state.save_path = "user://test_career.save"
	_state.settings_path = "user://test_settings.cfg"
	_state.replay_seed = 8128
	Ground = load("res://scripts/ui/match/VignetteGround.gd")
	Wx = load("res://scripts/ui/match/VignetteWeather.gd")
	Kickoff = load("res://scripts/ui/match/VignetteKickoff.gd")
	Grade = load("res://scripts/ui/match/VignetteGrade.gd")
	Ball = load("res://scripts/ui/match/VignetteBall.gd")
	_t("_test_no_wind_lines")
	_t("_test_flags_and_arrow_point_to_the_breeze_end")
	_t("_test_slot_rules")
	_t("_test_slot_follows_the_ground")
	_t("_test_slot_of_a_match")
	_t("_test_night_look_is_unchanged")
	_t("_test_hot_differs_from_perfect")
	_t("_test_ball")
	await _t("_test_same_match_under_every_sky")
	Kickoff.forced_slot = ""
	Grade.forced_weather = ""
	print(Ran.line("Weather look", self))
	for f in _failures:
		print("  FAIL: ", f)
	quit(1 if _failures.size() > 0 else 0)


func _cam() -> Object:
	# Behind the centre, looking down the ground at the +y end.
	return Ground.looking(Vector2(0.0, -60.0), 14.0, Vector2(0.0, 40.0), 500.0, 195.0, 260.0)


func _names(script: Script) -> Array:
	var out := []
	for m in script.get_script_method_list():
		out.append(str(m["name"]))
	return out


# ---------------------------------------------------------------------------
func _test_no_wind_lines() -> void:
	_check(not _names(Wx).has("draw_wind"), "The wind lines over the ground are gone (VignetteWeather.draw_wind)")
	var src: String = (Ground as Script).source_code
	_check(src.length() > 1000 and not src.contains("draw_wind"), "The ground draws no wind lines of any kind")
	# What draws the wind now is there: the flags' direction and the screen's arrow.
	_check(_names(Wx).has("flag_stream") and _names(Ground).has("wind_arrow"),
			"The wind is drawn by the flags and the big screen's arrow")


func _test_flags_and_arrow_point_to_the_breeze_end() -> void:
	var cam = _cam()
	var spots := [Vector2(80.0, 0.0), Vector2(-80.0, 10.0), Vector2(60.0, 40.0), Vector2(-40.0, 70.0), Vector2(10.0, 60.0)]
	var ok_far := 0
	var ok_near := 0
	for p: Vector2 in spots:
		var at: Vector3 = cam.oval(p, 20.0)
		for end in [1, -1]:
			var board := {"wind": end}
			_check(Wx.wind_end(board) == end, "The board's wind is the end the breeze blows to (%d)" % end)
			var world: Vector2 = Wx.wind_world(Wx.wind_end(board))
			var s: Vector3 = Wx.flag_stream(cam, p, 20.0, world)
			_check(absf(Vector2(s.x, s.y).length() - 1.0) < 0.001 and s.z >= 0.3 and s.z <= 1.0,
					"A flag's stream is a direction and a share of its length (%s)" % str(s))
			# World: the flag's free end is nearer the breeze end than its pole.
			var goal_world := Vector2(0.0, Ground.GOAL_Y * end)
			_check((p + world * 3.0).distance_to(goal_world) < p.distance_to(goal_world),
					"The wind at %s blows toward the %s end" % [str(p), "far" if end > 0 else "near"])
			# Screen: the flag's free end points at where the wind is going, 30 m downwind.
			var down: Vector3 = cam.oval(p + world * 30.0, 20.0)
			if down.z > 0.0 and Vector2(s.x, s.y).dot(Vector2(down.x - at.x, down.y - at.y)) > 0.0:
				if end > 0:
					ok_far += 1
				else:
					ok_near += 1
	_check(ok_far == spots.size(), "Every flag streams toward the far end when the breeze blows there (%d of %d)" % [ok_far, spots.size()])
	_check(ok_near == spots.size(), "Every flag streams back toward the near end when it blows there (%d of %d)" % [ok_near, spots.size()])
	_check(Wx.wind_end({}) == 1, "A scene that does not say gets the far end, as before")
	# The arrow: up when the breeze blows to that screen's end.
	_check(Ground.wind_arrow(1, 1) == 1 and Ground.wind_arrow(-1, 1) == -1, "The far screen's arrow points up for a breeze to the far end, down for the near end")
	_check(Ground.wind_arrow(-1, -1) == 1 and Ground.wind_arrow(1, -1) == -1, "The other screen's arrow is the other way up")
	# Only a windy day stirs them.
	_check(Wx.wind("windy") == 1.0 and Wx.wind("hot") == 0.0 and Wx.wind("perfect") == 0.0,
			"Flags stream only on a windy day")


func _test_slot_rules() -> void:
	var grounds: Array = Ground.ground_names()
	_check(grounds.size() >= 10, "The grounds are there to ask about (%d)" % grounds.size())
	var stable := true
	var gf_day := true
	var hot_night := 0
	var valid := true
	for g in grounds + ["", "Somewhere Else"]:
		for k in range(300):
			var key: int = Kickoff.key_of(2026, "Round %d" % (k % 24 + 1), "FRE", "MEL") + k
			for w in WEATHERS:
				var s: String = Kickoff.slot(str(g), w, key)
				if s != Kickoff.slot(str(g), w, key):
					stable = false
				if not Kickoff.SLOTS.has(s):
					valid = false
				if w == "hot" and s == Kickoff.NIGHT:
					hot_night += 1
				if Kickoff.slot(str(g), w, key, "Grand Final") != Kickoff.DAY:
					gf_day = false
	_check(valid, "Every match is a day, twilight or night game")
	_check(stable, "The same match gets the same time of day every time it is asked")
	_check(gf_day, "A Grand Final is a day game at every ground, in every weather")
	_check(hot_night == 0, "A hot day is never a night game (%d were)" % hot_night)
	_check(Kickoff.key_of(1, "Round 1", "FRE", "MEL") == Kickoff.key_of(1, "Round 1", "FRE", "MEL")
			and Kickoff.key_of(1, "Round 1", "FRE", "MEL") != Kickoff.key_of(1, "Round 2", "FRE", "MEL")
			and Kickoff.key_of(1, "Round 1", "FRE", "MEL") != Kickoff.key_of(2, "Round 1", "FRE", "MEL"),
			"A match's key is its own: the season, the round and the two clubs")
	# Its own generator: asking never moves the shared one.
	seed(4242)
	var want := randi()
	seed(4242)
	for k in range(50):
		Kickoff.slot("MCG", "perfect", k)
	_check(randi() == want, "Picking a time of day never touches the shared random numbers")


func _test_slot_follows_the_ground() -> void:
	var share: Dictionary = Kickoff.shares("MCG")
	_check(int(share.get("games", 0)) >= 40 and absf(float(share["day"]) + float(share["twilight"]) + float(share["night"]) - 1.0) < 0.01,
			"The MCG's 2026 matches are counted and its shares add up (%s)" % str(share))
	var counts := {Kickoff.DAY: 0, Kickoff.TWILIGHT: 0, Kickoff.NIGHT: 0}
	var n := 4000
	for k in range(n):
		counts[Kickoff.slot("MCG", "perfect", hash("mcg|%d" % k))] += 1
	for s in Kickoff.SLOTS:
		_check(absf(float(counts[s]) / n - float(share[s])) < 0.04,
				"The MCG's %s share follows 2026 (%.3f against %.3f)" % [s, float(counts[s]) / n, float(share[s])])
	# A ground with too few matches to mean anything uses the league's share.
	_check(Kickoff.shares("Bellerive Oval") == Kickoff.data()["default"] and Kickoff.shares("Nowhere") == Kickoff.data()["default"],
			"A ground with a match or two in 2026 uses the league's share")
	# Kardinia Park hosted no day match in 2026; a hot day there is still not a night game.
	var geelong := {}
	for k in range(400):
		geelong[Kickoff.slot("GMHBA Stadium", "hot", k)] = true
	_check(not geelong.has(Kickoff.NIGHT) and geelong.size() >= 1, "A hot day at a night ground is moved out of the night (%s)" % str(geelong.keys()))


func _test_slot_of_a_match() -> void:
	Kickoff.forced_slot = ""
	Kickoff.use_match({})
	_check(Kickoff.now("perfect") == Kickoff.NIGHT and Kickoff.now("hot") == Kickoff.NIGHT,
			"With no match set, a scene is a night game, as every scene was")
	var res := {"home": "FRE", "away": "MEL", "label": "Round 3"}
	Ground.use_match(res)
	var first: String = Kickoff.now("perfect")
	_check(Kickoff.has_match and Kickoff.venue == Ground.ground_of(res), "Setting the match's ground sets its time of day too (%s)" % Kickoff.venue)
	var warm_up := {"home": "FRE", "away": "MEL", "label": "Round 3", "weather": "perfect", "tag": ""}
	Kickoff.use_match(warm_up, Ground.ground_of(warm_up))
	_check(Kickoff.now("perfect") == first, "The warm-up and the match are under the same sky (%s)" % first)
	Kickoff.use_match({"home": "FRE", "away": "MEL", "label": "Grand Final", "venue": "MCG"}, "MCG")
	_check(Kickoff.now("perfect") == Kickoff.DAY and Kickoff.now("wet") == Kickoff.DAY, "The Grand Final is played by day")
	for s in Kickoff.SLOTS:
		Kickoff.forced_slot = s
		_check(Kickoff.now("perfect") == s, "A capture tool can ask for %s" % s)
	# A closed roof keeps its lights whatever the hour.
	Kickoff.forced_slot = Kickoff.DAY
	Ground.venue = "Marvel Stadium"
	_check(Ground.spec.get("roof") == "closed" and Ground.slot_now("perfect") == Kickoff.NIGHT,
			"Under a closed roof the ground is lit as at night whatever the hour")
	Ground.venue = "MCG"
	_check(Ground.slot_now("perfect") == Kickoff.DAY, "An open ground takes the hour")
	Ground.venue = ""
	Kickoff.forced_slot = ""
	Kickoff.use_match({})
	_check(Kickoff.lights(Kickoff.NIGHT) == 1.0 and Kickoff.lights(Kickoff.DAY) == 0.0
			and Kickoff.lights(Kickoff.TWILIGHT) > 0.0 and Kickoff.lights(Kickoff.TWILIGHT) < 1.0,
			"The lights are on at night, off by day and coming on at twilight")


## The night look is the one the director likes: its numbers are pinned as they were.
func _test_night_look_is_unchanged() -> void:
	var night: Dictionary = Grade.look("perfect")
	_check(night == {"contrast": 1.24, "saturation": 1.14, "lift": 0.0,
			"hi_tint": Vector3(1.10, 1.02, 0.86), "lo_tint": Vector3(0.88, 0.95, 1.10),
			"vignette": 0.36, "bloom": 0.28, "bloom_from": 0.55, "grain": 0.028}, "The night grade is as it was (%s)" % str(night))
	_check(Grade.look("perfect", Kickoff.NIGHT) == night and Grade.look("windy", Kickoff.NIGHT) == night, "Night is the look when no time of day is given")
	_check(float(Grade.look("hot")["bloom"]) == 0.34 and float(Grade.look("wet")["saturation"]) == 0.88, "Hot and wet nights are graded as they were")
	var base := [Color(0.16, 0.39, 0.17), Color(0.18, 0.43, 0.19)]
	_check(Wx.grass("perfect", base) == base and Wx.grass("windy", base, Kickoff.NIGHT) == base, "Night turf is the turf's own colours")
	_check((Wx.grass("hot", base)[0] as Color).is_equal_approx(base[0].lerp(Color(0.46, 0.46, 0.22), 0.42)), "A hot night's turf yellows as it did")
	_check(Wx.haze("perfect") == Color(0.85, 0.88, 1.0, 0.13) and Wx.haze("hot") == Color(1.0, 0.86, 0.6, 0.32), "The lights' haze at night is as it was")
	_check(Wx.sky("perfect", Kickoff.NIGHT).is_empty() and Wx.sky("perfect", Kickoff.DAY).size() == 3
			and Wx.sky("wet", Kickoff.TWILIGHT).size() == 3, "Night keeps its flat dark sky; day and twilight have their own")
	Kickoff.forced_slot = ""
	Kickoff.use_match({})
	_check(Wx.shadow_alpha("perfect") == 0.32 and Wx.shadow_alpha("hot") == 0.58 and Wx.shadow_alpha("wet") == 0.18
			and Wx.shadow_tight("hot") == 1.0, "Shadows under lights fall as they did")
	_check(Ground._lit(Color(0.2, 0.3, 0.4), Color.WHITE, 0.0) == Color(0.2, 0.3, 0.4), "At night no stand colour moves toward daylight")
	# The seats the crowd is painted on (whoever paints it ahead of a scene asks the ground).
	var was: String = Kickoff.shown
	Kickoff.shown = Kickoff.NIGHT
	var seats: Color = Ground.seat_colour()
	_check(seats == Color.html(str(Ground.spec.get("seat", "#121216"))), "Under lights the seats are the ground's own colour")
	Kickoff.shown = Kickoff.DAY
	_check(Ground.seat_colour() != seats and Ground.seat_colour() == Ground._seats_in(Kickoff.DAY),
			"By day the ground names the paler seats it draws, so a crowd painted ahead is the one shown")
	Kickoff.shown = was


## Hot must read as hot at a glance: set margins between a hot day and a mild one.
func _test_hot_differs_from_perfect() -> void:
	var hot: Dictionary = Grade.look("hot", Kickoff.DAY)
	var mild: Dictionary = Grade.look("perfect", Kickoff.DAY)
	_check(float(hot["exposure"]) - float(mild["exposure"]) >= 0.1, "A hot day is lit harder: exposure up by 0.1 or more (%.2f against %.2f)" % [float(hot["exposure"]), float(mild["exposure"])])
	_check(float(hot["contrast"]) - float(mild["contrast"]) >= 0.2, "A hot day's contrast is harder by 0.2 or more")
	_check(float(hot["shimmer"]) >= 0.8 and float(mild["shimmer"]) == 0.0, "Only the hot day shimmers at the horizon")
	_check((hot["hi_tint"] as Vector3).z < (mild["hi_tint"] as Vector3).z - 0.08, "A hot day's highlights are bleached warm")
	var base := [Color(0.16, 0.39, 0.17), Color(0.18, 0.43, 0.19)]
	var g_hot: Color = Wx.grass("hot", base, Kickoff.DAY)[0]
	var g_mild: Color = Wx.grass("perfect", base, Kickoff.DAY)[0]
	_check(g_hot.r / g_hot.g > g_mild.r / g_mild.g + 0.25, "Hot turf is yellowed, not green (red to green %.2f against %.2f)" % [g_hot.r / g_hot.g, g_mild.r / g_mild.g])
	_check(g_mild.g > base[0].g + 0.08, "A mild day's turf is brighter than under lights")
	Kickoff.use_match({})
	Kickoff.forced_slot = Kickoff.DAY
	_check(Wx.shadow_alpha("hot") - Wx.shadow_alpha("perfect") >= 0.25, "A hot day's shadow is a dark pool (%.2f against %.2f)" % [Wx.shadow_alpha("hot"), Wx.shadow_alpha("perfect")])
	_check(Wx.shadow_tight("hot") <= 0.85 and Wx.shadow_tight("perfect") == 1.0, "And a tight one, pulled in under the boots")
	_check(Wx.haze("hot", Kickoff.DAY).a >= Wx.haze("perfect", Kickoff.DAY).a + 0.2, "The far side sits in a heat haze")
	Kickoff.forced_slot = ""
	# Every weather and time of day has a full grade.
	var whole := true
	for s in Kickoff.SLOTS:
		for w in WEATHERS:
			var l: Dictionary = Grade.look(w, s)
			for k in ["contrast", "saturation", "lift", "hi_tint", "lo_tint", "vignette", "bloom", "bloom_from", "grain"]:
				if not l.has(k):
					whole = false
	_check(whole, "Every weather has a grade at every time of day")


func _test_ball() -> void:
	Kickoff.shown = Kickoff.DAY
	_check(not Ball.night(), "By day the red ball is used")
	Kickoff.shown = Kickoff.TWILIGHT
	_check(Ball.night(), "At twilight the yellow ball is used")
	Kickoff.shown = Kickoff.NIGHT
	_check(Ball.night(), "At night the yellow ball is used")
	# The kick's drift in the wind has one helper, VignetteExtras.drift; the replay turns it
	# to the side the wind blows (BroadcastVignette._drifted), so the ball goes where the
	# flags stream and still leaves the boot and lands where the match says.
	_check(not _names(Ball).has("drift"), "The ball's drift has one home (VignetteExtras.drift)")
	var extras = load("res://scripts/ui/match/VignetteExtras.gd")
	_check(is_zero_approx(float(extras.drift(0.0, 1.0))) and is_zero_approx(float(extras.drift(1.0, 1.0))),
			"A kick in the wind still leaves the boot and lands where the match says")
	_check(float(extras.drift(0.5, Wx.wind("perfect"))) == 0.0 and float(extras.drift(0.5, Wx.wind("hot"))) == 0.0,
			"No drift unless it is windy")
	var replay = load("res://scripts/ui/match/BroadcastVignette.gd").new()
	replay.weather = "windy"
	var from := Vector3(0.0, 30.0, 0.6)
	var to := Vector3(2.0, 79.0, 3.0)
	var line := Vector2(to.x - from.x, to.y - from.y).normalized()
	for end in [1, -1]:
		replay.set("_wind_end", end)
		var straight := from.lerp(to, 0.5)
		var bent: Vector3 = replay.call("_drifted", straight, from, to, 0.5)
		var moved := Vector2(bent.x - straight.x, bent.y - straight.y)
		_check(moved.length() > 1.5 and absf(moved.dot(line)) < 0.001 and moved.dot(Wx.wind_world(end)) > 0.0,
				"In flight it drifts across its line, the way the wind blows (%s, breeze to end %d)" % [str(moved), end])
	replay.free()


func _sim(seed_n: int) -> Object:
	var db = root.get_node("GameDB")
	var squad: Script = load("res://scripts/sim/Squad.gd")
	var match_sim: Script = load("res://scripts/sim/MatchSim.gd")
	return match_sim.new(squad.new("FRE", db.club_list("FRE"), true, "FRE"), squad.new("MEL", db.club_list("MEL"), false, "MEL"), seed_n)


## Looks never reach the match: the same seed plays the same match whatever sky and
## weather the scenes are drawing, and a windy match's breeze is only ever read.
func _test_same_match_under_every_sky() -> void:
	Kickoff.forced_slot = ""
	Grade.forced_weather = ""
	var first = _sim(8128)
	first.weather = "windy"
	var breeze: int = first.breeze_side
	var want: Dictionary = first.run()
	_check((want["events"] as Array).size() > 100, "A whole match is played to compare (%d events)" % (want["events"] as Array).size())
	var stage := Stage.new()
	stage.ground = Ground
	stage.cam = _cam()
	stage.size = Vector2(390, 844)
	root.add_child(stage)
	var same := 0
	var drawn := 0
	var combos := 0
	for s in Kickoff.SLOTS:
		for w in WEATHERS:
			combos += 1
			Kickoff.forced_slot = s
			Grade.forced_weather = w
			Kickoff.use_match({"home": "FRE", "away": "MEL", "label": "Round %d" % combos}, "Optus Stadium")
			var sim = _sim(8128)
			sim.weather = "windy"
			stage.weather = w
			stage.board = {"wind": 1 if sim.with_breeze(0) else -1}
			var before := stage.drawn
			stage.queue_redraw()
			await process_frame
			await process_frame
			if stage.drawn > before and Kickoff.shown == s:
				drawn += 1
			if sim.breeze_side != breeze:
				same = -100
			var got: Dictionary = sim.run()
			if got["events"] == want["events"] and got["score"] == want["score"]:
				same += 1
	_check(combos == 12 and drawn == combos, "The ground is drawn in every weather at every time of day (%d of %d)" % [drawn, combos])
	_check(same == combos, "The same seed plays the same match under every sky and weather (%d of %d)" % [same, combos])
	stage.queue_free()
	Kickoff.forced_slot = ""
	Grade.forced_weather = ""
	Kickoff.use_match({})


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)
