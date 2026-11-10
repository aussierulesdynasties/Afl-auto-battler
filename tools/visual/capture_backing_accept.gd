extends SceneTree
## Backing a young player from the hub card with a side you named: a real tap on
## "Back him", then Selection shows him in the side. Needs a real renderer:
##   godot --path . --script tools/visual/capture_backing_accept.gd -- --out /tmp/backing
## Writes <out>_card.png (the ask, with who makes way), <out>_result.png (after
## the tap) and <out>_selection.png (Selection, his card on the ground).

const Tap := preload("res://tests/tap.gd")
var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _wait(n := 8) -> void:
	for i in range(n):
		await process_frame


func _shot(path: String) -> void:
	await _wait()
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(path)
	print("wrote ", path)


## The visible control of that name drawn last (a popup's copy over the hub's).
func _top(name: String) -> Control:
	var found: Control = null
	for c in root.find_children(name, "", true, false):
		if c is Control and (c as Control).is_visible_in_tree():
			found = c
	return found


## Shows a screen the way a phone would, without the Router's threaded load
## (a --script run cannot parse scripts on the loader thread), then waits for
## `want` to be on screen.
func _open(path: String, want: String) -> Control:
	var old := root.get_tree().current_scene
	if old != null:
		old.queue_free()
	var scene: Node = load(path).instantiate()
	root.add_child(scene)
	root.get_tree().current_scene = scene
	for i in range(300):
		await process_frame
		var c := _top(want)
		if c != null and i > 10:
			return c
	return null


func _run() -> void:
	var out := "/tmp/backing"
	var club := "FRE"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--club":
			club = str(a[i + 1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_backing.save"
	state.settings_path = "user://capture_backing_settings.cfg"
	state.show_real_names = false
	state.reset()
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	DisplayServer.window_set_size(Vector2i(W, H))
	root.size = Vector2i(W, H)
	await _wait(3)
	state.replay_seed = 5512
	state.career_seed = 5512
	state.start_season(club, db.club_list(club))
	state.tutorials = false
	state.week_events = []
	state.advance()
	# The kid: a fit young midfielder auto-pick leaves out, with no senior games yet.
	var kid := {}
	var side: Dictionary = state.current_side()
	var named := {}
	for k in side:
		for id in side[k]:
			named[str(id)] = true
	for p in state.my_list:
		if str(p["role"]) != "MID" or named.has(str(p["id"])) or not load("res://scripts/sim/Ratings.gd").available(p):
			continue
		if kid.is_empty() or float(p.get("age", 30)) < float(kid.get("age", 30)):
			kid = p
	kid["career"] = {"games": 0, "goals": 0, "stints": [], "through": state.season_year - 1, "unknown": []}
	kid.erase("backed")
	kid.erase("back_asked")
	state.set_selection(side)   # the side you named, without him
	state.media_conference = {}
	state.week_events = [state.story_card("training_kid_pushing", kid)]
	print("kid ", kid["id"], " ", db.player_display_name(kid), " in side before: ", state.in_current_side(kid))
	print("detail: ", state.week_events[0]["options"][0]["detail"])
	var back := await _open("res://scenes/HubScene.tscn", "Event_0")
	print("button: ", back.text if back is Button else "missing")
	await _shot(out + "_card.png")
	# The hub's card opens as a sheet: the finger presses the sheet's button,
	# the one drawn on top (the hub's own copy sits under the sheet).
	var c := _top("Event_0")
	await Tap.steady(c)
	var where := str(c.get_path())
	print("tap at ", Tap.pixel_point(c, c.size * 0.5), " in a ", root.size, " window: ", where)
	var why := await Tap.tap(c)
	print("tap result: '", why, "'")
	await _wait(12)
	print("outcome: ", state.week_events[0].get("outcome", ""))
	await _shot(out + "_result.png")
	print("in side after: ", state.in_current_side(kid), " named: ", str(state.my_selection()).contains(str(kid["id"])))
	# Selection: his card on the ground (the field fits the screen at 390 x 844).
	var shown := await _open("res://scenes/SelectionScene.tscn", "ConfirmSide")
	print("selection open: ", shown != null)
	await _shot(out + "_selection.png")
	quit(0)
