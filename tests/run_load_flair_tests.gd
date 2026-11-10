extends SceneTree
## godot --headless --path . --script tests/run_load_flair_tests.gd
## The load screens (row 121): the logo and the set shot go up on every wait with
## a line and on no plain wipe; the ball really flies and turns, and every kick
## crosses the goal line in the goals or the behinds; Reduced motion leaves it on
## the ground; the beats through the rollover change nothing in the results; the
## boot splash is ours; a finger still reaches the screen after the cover.
## Classes are reached through load() and autoload nodes.

var _state: Node
var _router: Node
var _db: Node
var _wipe: Node
var _season: GDScript
var _checks := 0
var _failures: Array[String] = []

const SUITE_SEED := 2027
const Tap := preload("res://tests/tap.gd")


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_router = root.get_node("Router")
	_db = root.get_node("GameDB")
	_wipe = root.get_node("ScreenTransition")
	_season = load("res://scripts/sim/Season.gd")
	_state.autosave_enabled = false
	_state.event_sheets = false
	_state.save_path = "user://test_load_flair.save"
	_state.settings_path = "user://test_load_flair.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	_state.set_confirm_sim_round(false)
	await _t("_test_flair_only_with_a_line")
	await _t("_test_cover_shown_before_work")
	await _t("_test_stack_fits", [Vector2i(390, 844)])
	await _t("_test_stack_fits", [Vector2i(320, 568)])
	await _t("_test_stack_fits", [Vector2i(1280, 720)])
	_t("_test_every_kick_is_a_set_shot")
	_t("_test_ball_flies_and_turns")
	_t("_test_reduced_motion_rests")
	_t("_test_web_ball_rests")
	_t("_test_no_frames_by_hand_headless")
	_t("_test_boot_splash_is_ours")
	_t("_test_lines")
	await _t("_test_beats_change_nothing")
	await _t("_test_tap_after_cover")
	await _t("_test_browser_loads_under_the_line")
	print(Ran.line("Load flair", self))
	if not _failures.is_empty():
		for f in _failures:
			print("FAIL: ", f)
		quit(1)
		return
	quit(0)


func _flair() -> Control:
	return _wipe.call("flair")


func _fresh() -> void:
	_state.reset()
	_state.replay_seed = SUITE_SEED
	_state.start_season("FRE", _db.club_list("FRE"))
	_state.tutorials = false


func _test_flair_only_with_a_line() -> void:
	_wipe.set("test_cover", true)
	var seen := {"line": false, "plain": false, "logo_ok": false, "hook": false}
	await _wipe.call("run", "Playing Round 7...", func():
		await process_frame
		seen["line"] = _flair().visible
		var logo: TextureRect = _flair().get_node("LoadLogo")
		var art := logo.texture as AtlasTexture
		seen["logo_ok"] = art != null and art.atlas != null \
				and art.atlas.resource_path.ends_with("aussie_rules_dynasties_logo_placeholder.png")
		seen["hook"] = (_season.get("wait_hook") as Callable).is_valid())
	_check(seen["line"], "a wait with a line has the flair on it")
	_check(seen["logo_ok"], "the logo on it is the game's wordmark, not a fallback")
	_check(seen["hook"], "while it is up, blocking work can keep the ball moving")
	await _down()
	_check(not _flair().visible, "the flair leaves with the cover")
	_check(not (_season.get("wait_hook") as Callable).is_valid(), "and blocking work stops drawing")
	var done := [false]
	_wipe.call("cover", func():
		await process_frame
		seen["plain"] = _flair().visible
		done[0] = true)
	while not done[0]:
		await process_frame
	await _down()
	_check(not seen["plain"], "a plain wipe between screens stays plain: no flair")
	_wipe.set("test_cover", false)


## The set shot reaches the screen before the work starts (director,
## 2026-11-10: "a grey screen for a few seconds then for a split second the
## anim"): the frame that drew it has returned before the work runs, so a
## browser has shown it; and a screen building itself under the cover gives the
## ball a chance to move with every node it adds.
func _test_cover_shown_before_work() -> void:
	_wipe.set("test_cover", true)
	var seen := {}
	await _wipe.call("run", "Loading your list...", func():
		seen["frame"] = Engine.get_process_frames()
		seen["line_frame"] = int(_wipe.get("line_frame"))
		seen["shot"] = _flair().visible and bool(_wipe.call("line_visible"))
		seen["hooked"] = root.get_tree().node_added.is_connected(Callable(_wipe, "_on_node_added"))
		var beats: int = int(_wipe.get("node_beats"))
		var box := VBoxContainer.new()
		for i in range(5):
			box.add_child(Label.new())
		root.add_child(box)
		seen["beats"] = int(_wipe.get("node_beats")) - beats
		box.queue_free())
	await _down()
	_check(seen.get("shot", false), "the work starts with the line and the set shot up")
	_check(int(seen.get("frame", -1)) > int(seen.get("line_frame", 0)),
			"and after the frame that drew them returned (line in frame %s, work in %s)" % [
			seen.get("line_frame"), seen.get("frame")])
	_check(seen.get("hooked", false), "while the line is up, a screen adding nodes keeps the ball moving")
	_check(int(seen.get("beats", 0)) == 6, "one chance per node added (%s)" % seen.get("beats"))
	_check(not root.get_tree().node_added.is_connected(Callable(_wipe, "_on_node_added")),
			"and the hook comes off with the cover")
	_wipe.set("test_cover", false)


func _down() -> void:
	var t0 := Time.get_ticks_msec()
	while bool(_wipe.get("busy")) and Time.get_ticks_msec() - t0 < 20000:
		await process_frame


## Logo, shot and line on screen, in that order, overlapping nothing.
func _test_stack_fits(view: Vector2i) -> void:
	root.size = view
	await process_frame
	_wipe.set("test_cover", true)
	var at := {}
	await _wipe.call("run", "Playing the qualifying and elimination finals...", func():
		await process_frame
		var logo: Control = _flair().get_node("LoadLogo")
		var stage: Control = _flair().get_node("LoadStage")
		var line: Label = _wipe.get_node("CoverLine")
		at["logo"] = logo.get_global_rect()
		at["stage"] = stage.get_global_rect()
		at["line_top"] = line.get_global_rect().position.y
		at["line_h"] = line.get_minimum_size().y)
	await _down()
	_wipe.set("test_cover", false)
	var who := "%dx%d" % [view.x, view.y]
	var logo: Rect2 = at["logo"]
	var stage: Rect2 = at["stage"]
	var window := Rect2(Vector2.ZERO, Vector2(view))
	_check(window.encloses(logo), "%s: the logo is on screen (%s)" % [who, logo])
	_check(window.encloses(stage), "%s: the shot is on screen (%s)" % [who, stage])
	_check(logo.end.y <= stage.position.y, "%s: the logo sits clear above the shot" % who)
	_check(stage.end.y <= float(at["line_top"]), "%s: the line sits clear below the shot" % who)
	_check(float(at["line_top"]) + float(at["line_h"]) <= float(view.y), "%s: the longest line fits, wrapped" % who)
	_check(stage.size.x >= 120.0, "%s: the shot is big enough to read" % who)


func _test_every_kick_is_a_set_shot() -> void:
	var flair := _flair()
	flair.call("open", "FRE", false)
	var from: Array = flair.get("KICK_FROM")
	var to: Array = flair.get("KICK_TO")
	_check(from.size() == to.size() and to.size() == 6, "six kicks in the loop")
	var goals := 0
	for k in range(to.size()):
		var w: float = absf(float(to[k]))
		_check(w < 3.0, "kick %d crosses the goal line inside the behind posts" % k)
		if w < 1.0:
			goals += 1
		else:
			_check(w > 1.15, "kick %d is clear of the goal post" % k)
	_check(goals == 5, "five goals and one behind (%d)" % goals)
	flair.set("hand_clock_ms", -1)
	flair.call("close")


func _test_ball_flies_and_turns() -> void:
	var flair := _flair()
	flair.call("open", "FRE", false)
	flair.set("_still", false)
	var steps := []
	for ms in [100, 400, 700, 1000, 1300]:
		flair.set("hand_clock_ms", ms)
		flair.call("tick")
		var f: Dictionary = flair.call("flight", float(ms) / 1500.0, 0)
		steps.append({"at": flair.get("ball_at"), "turn": flair.get("ball_turn"), "half": f["half_len"], "gap":
				(f["shadow_at"] as Vector2).y - (f["at"] as Vector2).y})
	_check(steps.size() == 5, "five moments of one kick")
	for i in range(1, steps.size()):
		_check(steps[i]["at"] != steps[i - 1]["at"], "the ball moves between moments %d and %d" % [i - 1, i])
		_check(float(steps[i]["turn"]) > float(steps[i - 1]["turn"]), "it keeps turning (%d)" % i)
		_check(float(steps[i]["half"]) < float(steps[i - 1]["half"]), "it shrinks going away (%d)" % i)
	for i in range(steps.size()):
		_check(float(steps[i]["gap"]) > 0.0, "it is above its own shadow, in the air (%d)" % i)
	var turns: float = float(flair.get("TURNS"))
	_check(turns >= 2.0, "end over end, at least twice a kick (%s)" % turns)
	# After the flight, before the next kick: no ball left hanging.
	flair.set("hand_clock_ms", 1600)
	var moved_to: Vector2 = flair.get("ball_at")
	flair.call("tick")
	_check(flair.get("ball_at") == moved_to, "between kicks the ball is not moved")
	flair.set("hand_clock_ms", -1)
	flair.call("close")


func _test_reduced_motion_rests() -> void:
	var flair := _flair()
	flair.call("open", "FRE", true)
	var a: Vector2 = flair.get("ball_at")
	flair.call("tick")
	_check(flair.get("ball_at") == a, "Reduced motion: the ball does not move")
	var stage: Control = flair.get_node("LoadStage")
	_check(a.y > stage.size.y * 0.8, "and it sits on the ground, not in the air (%s of %s)" % [a.y, stage.size.y])
	flair.call("close")


## A browser shows stills for a blocking wait (a skip draws one a week): the
## ball rests on the turf there, so no still has it hanging in the air.
func _test_web_ball_rests() -> void:
	var flair := _flair()
	var stage: Control = flair.get_node("LoadStage")
	flair.set("web_still", true)
	flair.call("open", "FRE", false)
	var a: Vector2 = flair.get("ball_at")
	flair.call("tick")
	_check(flair.get("ball_at") == a and a.y > stage.size.y * 0.8,
			"in a browser the ball sits still on the ground (%s of %s)" % [a.y, stage.size.y])
	flair.set("web_still", false)
	flair.call("close")
	flair.set("hand_clock_ms", 500)
	flair.call("open", "FRE", false)
	_check((flair.get("ball_at") as Vector2).y < stage.size.y * 0.8, "elsewhere it is kicked (%s)" % flair.get("ball_at"))
	flair.set("hand_clock_ms", -1)
	flair.call("close")


func _test_no_frames_by_hand_headless() -> void:
	var before: int = int(_wipe.get("pumped_frames"))
	_wipe.call("keep_moving")
	_check(int(_wipe.get("pumped_frames")) == before, "no cover up: no frame is drawn by hand")


func _test_boot_splash_is_ours() -> void:
	var path := str(ProjectSettings.get_setting("application/boot_splash/image", ""))
	_check(path.ends_with("boot_splash.png") and FileAccess.file_exists(path), "the boot splash is our image (%s)" % path)
	var ui: GDScript = load("res://scripts/ui/UiKit.gd")
	ui.call("apply_appearance", "dark")
	var cover: Color = ui.get("PANEL_ALT")
	var bg: Color = ProjectSettings.get_setting("application/boot_splash/bg_color", Color.BLACK)
	_check(absf(bg.r - cover.r) < 0.01 and absf(bg.g - cover.g) < 0.01 and absf(bg.b - cover.b) < 0.01,
			"on the loading cover's colour (%s, %s)" % [bg, cover])


func _test_lines() -> void:
	var lines: Dictionary = _router.get("LINES")
	_check(lines.has("draft"), "draft night has its own line on the cover")


## The whole of a rollover with something on the hook is the same league as
## without it, and the hook was called through it.
func _test_beats_change_nothing() -> void:
	# The first career in a process comes out different from every one after it,
	# hook or no hook (measured: none A, none B, hook B, none B), so it is played
	# and thrown away and the comparison is between two later ones.
	_rollover()
	var without: String = _rollover()
	var calls := [0]
	var hook := func(): calls[0] += 1
	_season.set("wait_hook", hook)
	var with_hook: String = _rollover()
	_season.set("wait_hook", Callable())
	_check(calls[0] >= 10, "the rollover beats through its steps (%d)" % calls[0])
	_check(without != "" and without == with_hook, "the same league either way (%s / %s)" % [without, with_hook])


func _rollover() -> String:
	_fresh()
	seed(SUITE_SEED)
	while not _state.season.is_season_over():
		_state.advance()
	_state.start_next_season()
	var bits := PackedStringArray()
	for code in _state.league_lists:
		var sum := 0
		for p in _state.league_lists[code]:
			sum += int(p["overall"]) + hash(str(p["id"])) % 1000
		bits.append("%s:%d:%d" % [code, (_state.league_lists[code] as Array).size(), sum])
	bits.sort()
	return str(hash(",".join(bits)))


## The flair takes no touch, and a finger reaches the screen after the cover.
func _test_tap_after_cover() -> void:
	root.size = Vector2i(390, 844)
	await process_frame
	_fresh()
	_router.stack = []
	_router.go("hub")
	await process_frame
	await process_frame
	var flair := _flair()
	_check(flair.mouse_filter == Control.MOUSE_FILTER_IGNORE, "the flair lets touches through")
	for c in flair.get_children():
		_check((c as Control).mouse_filter == Control.MOUSE_FILTER_IGNORE, "%s lets touches through" % c.name)
	_wipe.set("test_cover", true)
	await _wipe.call("run", "Loading your list...", func(): await process_frame)
	await _down()
	_wipe.set("test_cover", false)
	var sim: Control = current_scene.find_child("SimRound", true, false)
	_check(sim != null, "the hub shows Sim the week")
	if sim == null:
		return
	var why: String = await Tap.tap(sim)
	_check(why == "", "a finger's tap reaches Sim the week after the cover (%s)" % why)


## A browser build has no threads, so loading the next screen blocks: it must
## not start while the dots sweep in (they would freeze half way), only once
## the cover and a line are on screen.
func _test_browser_loads_under_the_line() -> void:
	var path := "res://scenes/StatsHubScene.tscn"
	_router.set("test_main_thread_load", true)
	_wipe.set("test_cover", true)
	_router.go("stats")
	var during_sweep := ResourceLoader.load_threaded_get_status(path)
	var phase_then := int(_wipe.get("_phase"))
	var seen := {"line": false}
	var t0 := Time.get_ticks_msec()
	while ResourceLoader.load_threaded_get_status(path) == ResourceLoader.THREAD_LOAD_INVALID_RESOURCE 			and Time.get_ticks_msec() - t0 < 10000:
		seen["line"] = bool(_wipe.call("line_visible"))
		seen["drawn"] = int(_wipe.get("drawn_count"))
		await process_frame
	await _down()
	_router.set("test_main_thread_load", false)
	_wipe.set("test_cover", false)
	_check(phase_then == 1 and during_sweep == ResourceLoader.THREAD_LOAD_INVALID_RESOURCE,
			"no load while the dots sweep in (phase %d, status %d)" % [phase_then, during_sweep])
	_check(seen.get("line", false), "the line is up before the load starts")
	_check(current_scene != null and current_scene.scene_file_path == path,
			"and the screen still opens (%s)" % (current_scene.scene_file_path if current_scene else "none"))
