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
	_close_intros()
	await _frames(20)
	_show("WeekJobs")
	await _frames(10)
	_save(out + "_1_hub.png")
	print("tap job: '%s'" % await Tap.tap(_find("WeekJob_team")))
	await _frames(20)
	_close_intros()
	await _frames(10)
	_show("ConfirmSide")
	await _frames(10)
	_save(out + "_2_team.png")
	print("tap confirm: '%s'" % await Tap.tap(_find("ConfirmSide")))
	await _frames(20)
	_show("ConfirmSide")
	await _frames(10)
	_save(out + "_3_confirmed.png")
	router.stack = []
	router.go("main")
	await _frames(8)
	router.go("hub")
	await _frames(20)
	_close_intros()
	_show("WeekJobs")
	await _frames(10)
	_save(out + "_4_hub_done.png")
	print("route now: %s" % router.current())
	quit()


func _find(n: String) -> Control:
	return current_scene.find_child(n, true, false) as Control


## The first-visit intro is answered, as a returning player has.
func _close_intros() -> void:
	for b in root.find_children("*", "Button", true, false):
		if (b as Button).text == "Got it" and (b as Button).is_visible_in_tree():
			(b as Button).emit_signal("pressed")


## Scroll so `n` is on screen, as a player reading down would.
func _show(n: String) -> void:
	var c := _find(n)
	if c == null:
		print("missing: " + n)
		return
	var p := c.get_parent()
	while p != null:
		if p is ScrollContainer:
			(p as ScrollContainer).ensure_control_visible(c)
			return
		p = p.get_parent()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _save(path: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(path)
