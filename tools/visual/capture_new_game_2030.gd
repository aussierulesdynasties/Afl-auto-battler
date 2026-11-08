extends SceneTree
## New career (director, 2026-11-08): who is in the league from the start.
## Needs a real renderer:
##   godot --path . --resolution 390x844 --windowed --script tools/visual/capture_new_game_2030.gd -- --out <dir>
## Writes, into <dir>:
##   1_setup_redraft_yes.png   League redraft, Canberra joins? Yes, your Forge club brought
##   2_setup_real_note.png     Real 2026 lists: the Your club row gone, its note in its place
##   3_choose_redraft.png      Choose your club in a 21-club League redraft (Tasmania, Canberra)
##   4_choose_2030.png         Choose your club at the 2029 National Draft after 2027-2029 play out,
##                             scrolled to Tasmania and Canberra (the list top starts with Collingwood)

var W := 390
var H := 844
var out := "C:/Users/DANTE/Documents/GitHub/afl-wt/caps/new-game-2030"
var state
var db

const FORGE := {"name": "Port Melbourne", "short": "Borough", "code": "PMB",
		"location": "port-melbourne", "primary": "#1B3A8C", "secondary": "#C8102E",
		"accent": "#FFFFFF", "design": "hoops", "kit": "p/s/a"}


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		if str(a[i]) == "--out" and i + 1 < a.size():
			out = str(a[i + 1])
	DirAccess.make_dir_recursive_absolute(out)
	await process_frame
	state = root.get_node("GameState")
	db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture.save"
	state.settings_path = "user://capture_settings.cfg"
	state.reset()
	state.set_forge_club(FORGE)
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))

	# 1 and 2: the New career form.
	var main: Control = load("res://scenes/Main.tscn").instantiate()
	root.add_child(main)
	await _frames(10)
	main.call("_on_new_career")
	await _frames(6)
	_press(main, "StartMode_redraft")
	_press(main, "Canberra_yes")
	_press(main, "ForgedClub_in")
	await _frames(4)
	_show(main, "ForgedClub")
	await _shot("1_setup_redraft_yes")
	_press(main, "StartMode_real")
	await _frames(4)
	_show(main, "ForgedClubOnly")
	await _shot("2_setup_real_note")
	main.queue_free()
	await _frames(2)

	# 3: Choose your club, a League redraft with Canberra and your club.
	state.reset()
	state.set_canberra(true)
	state.create_club(FORGE)
	state.begin_draft()
	state.set_setting("seen_draft_intro", true)
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _frames(12)
	_show(ui, "Choose_TAS")
	await _shot("3_choose_redraft")
	ui.queue_free()
	await _frames(2)

	# 4: Real 2026 lists with Canberra: 2027 to 2029 play out, then the choice.
	state.reset()
	state.set_forge_club({})
	state.set_canberra(true)
	var t0 := Time.get_ticks_msec()
	state.begin_sim_ahead()
	var steps := 0
	while steps < 400:
		steps += 1
		if state.sim_ahead_step() == "":
			break
	print("sim-ahead: %d steps, %d ms, choosing=%s year=%d" % [steps, Time.get_ticks_msec() - t0,
			str(state.choosing_club()), state.season_year])
	state.set_setting("seen_draft_intro", true)
	ui = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _frames(12)
	_show(ui, "Choose_CANB")
	await _shot("4_choose_2030")
	quit(0)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _press(scene: Node, name: String) -> void:
	var b := scene.find_child(name, true, false) as BaseButton
	if b == null:
		print("missing ", name)
		return
	b.emit_signal("pressed")


## Scrolls the node into view in every scroll container above it.
func _show(scene: Node, name: String) -> void:
	var n := scene.find_child(name, true, false) as Control
	if n == null:
		print("missing ", name)
		return
	var p := n.get_parent()
	while p != null:
		if p is ScrollContainer:
			(p as ScrollContainer).ensure_control_visible(n)
		p = p.get_parent()


func _shot(name: String) -> void:
	await _frames(6)
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(out + "/" + name + ".png")
	print("wrote ", out + "/" + name + ".png")
