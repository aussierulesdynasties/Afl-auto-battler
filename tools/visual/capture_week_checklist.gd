extends SceneTree
## The week's checklist and its big call in a normal career (TODO row 51), for
## the director's look. Needs a real renderer:
##   godot --path . --script tools/visual/capture_week_checklist.gd -- --out /tmp/wk [--size 390x844] [--club FRE]
## A fresh career with no captain named, so the big call is "Name a captain".
## Every step is a real tap (tests/tap.gd). Writes:
##   <out>_1_hub.png       the Hub, scrolled to the week's list
##   <out>_2_team.png      Team after a tap on "Look over the side", Confirm side in view
##   <out>_3_confirmed.png Team after a tap on Confirm side
##   <out>_4_hub_done.png  back on the Hub, the job ticked
## Never touches a real save.

const Tap := preload("res://tests/tap.gd")

var _w := 390
var _h := 844
var club := "FRE"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "week_checklist"
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
	state.save_path = "user://capture_week_checklist.save"
	state.settings_path = "user://capture_week_checklist.cfg"
	state.reset()
	state.start_season(club, db.club_list(club))
	state.tutorials = false
	var rec: Dictionary = state.captaincy.get(club, {})
	rec["slots"] = []
	rec["seeded"] = true
	state.captaincy[club] = rec
	root.size = Vector2i(_w, _h)
	router.stack = []
	router.go("main")
	await _frames(8)
	router.go("hub")
	await _frames(20)
	await _close_intros()
	await _frames(20)
	await Tap.steady(_find("WeekJobs"))
	_save(out + "_0_hub_top.png")
	await _show("WeekJobs")
	await _frames(10)
	_save(out + "_1_hub.png")
	await _tap("WeekJob_team")
	await _frames(20)
	await _frames(20)
	await _close_intros()
	await _frames(10)
	await _show("ConfirmSide")
	await _frames(10)
	_save(out + "_2_team.png")
	await _tap("ConfirmSide")
	await _frames(20)
	await _frames(20)
	await _show("ConfirmSide")
	await _frames(10)
	_save(out + "_3_confirmed.png")
	router.stack = []
	router.go("main")
	await _frames(8)
	router.go("hub")
	await _frames(20)
	await _close_intros()
	await _show("WeekJobs")
	await _frames(10)
	_save(out + "_4_hub_done.png")
	print("route now: %s" % router.current())
	quit()


## A real tap (tests/tap.gd). The suites prove taps headless at phone size;
## this window has no focus, so a miss here falls back to the button's own
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


## The first-visit intro is answered, as a returning player has, and any week
## event that pops up is put off with "Later" so the list underneath shows.
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


## Scroll so `n` is on screen, as a player reading down would.
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


## Frames, then however long the screen wipe (ScreenTransition) still runs:
## a windowed run plays it at real speed, so a fixed frame count can land
## under the cover.
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
