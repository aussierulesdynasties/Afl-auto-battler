extends SceneTree
## The Hub's fitness plan ask at a revision point (director, 2026-11-12:
## "something needs to offer you a fitness plan change when it becomes available
## too easy to miss"), for the director's look. Needs a real renderer:
##   godot --path . --script tools/visual/capture_fitness_ask.gd -- --out /tmp/fit [--size 390x844] [--club FRE]
## --size is the window in pixels; a phone size lays out at one unit a pixel,
## a desktop size (1920x1080) at the desktop's own density (960x540 units).
## Round 14, a revision point. Every step is a real tap (tests/tap.gd). Writes:
##   <out>_1_hub.png       the Hub, scrolled to the week's list, the ask open
##   <out>_2_sheet.png     the fitness plan sheet after a tap on the ask
##   <out>_3_hub_done.png  back on the Hub after Close, the ask ticked
## Never touches a real save.

const Tap := preload("res://tests/tap.gd")

var _w := 390
var _h := 844
var club := "FRE"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "fitness_ask"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--club":
				club = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	state.autosave_enabled = false
	state.save_path = "user://capture_fitness_ask.save"
	state.settings_path = "user://capture_fitness_ask.cfg"
	state.reset()
	state.start_season(club, db.club_list(club))
	state.tutorials = false
	state.week_events = []
	state.season.round_index = load("res://scripts/sim/Conditioning.gd").ROUND_14
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	var sl = root.get_node("ScreenLayout")
	if _w < 768:
		# A phone: one unit a pixel, whatever the desktop's scaling.
		sl.ui_scale = 96.0 / maxf(96.0, float(DisplayServer.screen_get_dpi()))
	else:
		# A desktop: half its pixels in units (1920x1080 lays out at 960x540),
		# whatever this machine's own scaling would give.
		await process_frame
		sl.ui_scale *= float(root.content_scale_size.x) / (_w * 0.5)
	sl.call("_update_scale")
	router.stack = []
	router.go("main")
	await _frames(8)
	router.go("hub")
	await _frames(20)
	await _close_intros()
	await _frames(20)
	print("canvas units: %s" % str(root.content_scale_size))
	await _show("WeekJob_fitness")
	await _frames(10)
	_save(out + "_1_hub.png")
	await _tap("WeekJob_fitness")
	await _frames(20)
	_save(out + "_2_sheet.png")
	await _tap("SeasonPlanClose")
	await _frames(20)
	await _show("WeekJob_fitness")
	await _frames(10)
	_save(out + "_3_hub_done.png")
	quit()


## A real tap (tests/tap.gd). A miss here falls back to the button's own
## press and says so, to keep the frames coming.
func _tap(n: String) -> void:
	var c := _find(n)
	await Tap.steady(c)
	var why: String = await Tap.tap(c)
	print("tap %s: %s" % [n, "ok" if why == "" else why])
	if why != "" and c is BaseButton and is_instance_valid(c):
		(c as BaseButton).emit_signal("pressed")


func _find(n: String) -> Control:
	return root.find_child(n, true, false) as Control


func _close_intros() -> void:
	for i in range(4):
		var hit := false
		for b in root.find_children("*", "Button", true, false):
			var t := (b as Button).text
			if (t == "Got it" or t == "Later") and (b as Button).is_visible_in_tree():
				(b as Button).emit_signal("pressed")
				hit = true
		if not hit:
			return
		await _frames(8)


func _show(n: String) -> void:
	var c := _find(n)
	if c == null:
		print("missing: " + n)
		return
	await Tap.steady(c)
	var p := c.get_parent()
	while p != null:
		if p is ScrollContainer:
			(p as ScrollContainer).ensure_control_visible(c)
			break
		p = p.get_parent()
	await Tap.steady(c)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame
	var wipe := root.get_node_or_null("ScreenTransition")
	var guard := 0
	while wipe != null and bool(wipe.get("busy")) and guard < 600:
		await process_frame
		guard += 1
	for i in range(6):
		await process_frame


func _save(path: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(path)
