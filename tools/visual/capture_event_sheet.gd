extends SceneTree
## A new club card opening over the hub, and the hub after Later with the card
## first, for the director's look. Needs a real renderer:
##   godot --path . --script tools/visual/capture_event_sheet.gd -- --out /tmp/event_sheet [--club FRE]
## Writes <out>_sheet.png (the card over the hub), <out>_later.png (the hub
## after Later, the card first) and <out>_answered.png (answered in the sheet).

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _shot(path: String) -> void:
	for i in range(40):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(path)
	print("wrote ", path)


## Wait until the routed screen is up and has had time to settle.
func _hub(prev: Node = null) -> Node:
	for i in range(600):
		await process_frame
		var sc := current_scene
		if sc != null and sc != prev and is_instance_valid(sc) and sc.is_node_ready():
			break
	for i in range(30):
		await process_frame
	print("scene ", current_scene)
	return current_scene


func _run() -> void:
	var out := "/tmp/event_sheet"
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
	state.save_path = "user://capture_event_sheet.save"
	state.settings_path = "user://capture_event_sheet_settings.cfg"
	state.show_real_names = false
	state.reset()
	state.set_setting("seen_weekly_loop_intro", true)
	DisplayServer.window_set_size(Vector2i(W, H))
	root.size = Vector2i(W, H)
	for i in range(3):
		await process_frame
	state.replay_seed = 3
	state.career_seed = 3
	state.start_season(club, db.club_list(club))
	state.advance()
	state.media_conference = {}
	var young: Dictionary = state.my_list[0]
	for p in state.my_list:
		if int(p.get("age", 30)) <= 20:
			young = p
			break
	var router = root.get_node("Router")
	state.week_events = [state.story_card("training_kid_pushing", young)]
	router.go("hub")
	var hub: Node = await _hub()
	await _shot(out + "_sheet.png")
	var sheet: Node = hub.find_child("EventSheet", true, false) if hub != null else null
	var later: Button = sheet.find_child("EventLater", true, false) if sheet != null else null
	if later != null:
		later.emit_signal("pressed")
	await _shot(out + "_later.png")
	state.week_events = [state.story_card("training_kid_pushing", young)]
	var old := hub
	router.go("hub")
	hub = await _hub(old)
	sheet = hub.find_child("EventSheet", true, false) if hub != null else null
	var answer: Button = sheet.find_child("Event_0", true, false) if sheet != null else null
	if answer != null:
		answer.emit_signal("pressed")
	await _shot(out + "_answered.png")
	quit(0)
