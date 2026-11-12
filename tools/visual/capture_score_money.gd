extends SceneTree
## Row 6.29 (STYLE-02): the scoreboard and money in the real screens, at the
## score and money forms that are hardest to fit. The match header is set to
## fixed scorelines (12.8 (80) v 6.9 (45), then 28.18 (186) v 19.11 (125)), and
## the off-season Contracts tab and a contract talk show the payroll and salary
## lines. Fremantle v Melbourne. Never touches a real save. Needs a renderer:
##   godot --windowed --path . --script tools/visual/capture_score_money.gd -- --out <prefix> [--size 390x844]
## Writes <prefix>_<n>_<what>.png.

const SCORES := [[[12, 6], [8, 9]], [[28, 19], [18, 11]], [[10, 1], [10, 1]]]

var _w := 390
var _h := 844
var _out := "score_money"
var _n := 0


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out":
				_out = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_score_money.save"
	state.settings_path = "user://capture_score_money.cfg"
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	state.reset()
	state.replay_seed = 2027
	state.start_season("FRE", db.club_list("FRE"))
	state.set_match_way("watch")
	state.prepare_interactive_match()
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	await _frames(20)
	for s in SCORES:
		m.set("_shown_goals", [s[0][0], s[0][1]])
		m.set("_shown_behinds", [s[1][0], s[1][1]])
		m.call("_paint_scoreboard")
		await _shot("match_%d.%d_v_%d.%d" % [s[0][0], s[1][0], s[0][1], s[1][1]])
	m.queue_free()
	await _frames(4)
	state.season.round_index = state.season.fixture.size()
	state.open_offseason()
	var o: Control = load("res://scenes/OffseasonScene.tscn").instantiate()
	root.add_child(o)
	await _frames(6)
	await _shot("offseason_contracts")
	var talk := o.find_child("Negotiate", true, false) as Button
	if talk != null:
		talk.emit_signal("pressed")
		await _frames(6)
		for i in 6:
			var up := o.find_child("SalaryUp", true, false) as Button
			if up == null:
				break
			up.emit_signal("pressed")
			await _frames(2)
		await _shot("contract_talk")
	quit()


func _shot(name: String) -> void:
	await _frames(8)
	RenderingServer.force_draw(false)
	var img := root.get_viewport().get_texture().get_image()
	_n += 1
	var path := "%s_%d_%s.png" % [_out, _n, name]
	img.save_png(path)
	print("wrote ", path)


func _frames(n: int) -> void:
	for i in n:
		await process_frame
