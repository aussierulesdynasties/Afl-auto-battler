extends SceneTree
## The hub before a match after a real tap on a response card under an
## opposition fact: the card shows chosen and the hub stays (no match starts).
## Starts a seeded season, plays `--rounds` rounds, opens the hub, taps the
## first enabled option card with a finger at its place on screen and saves the frame scrolled to it.
## Needs a real renderer (windowed, through C:/kt/gpu_slot.sh, off screen via override.cfg):
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_hub_fact_choice.gd -- \
##       --club GCS --rounds 1 --size 390x844 --seed 2027 --out /tmp/hub_fact_choice
## Writes <out>.png and prints the chosen card and whether a match started. Never touches a real save.



func _initialize() -> void:
	_run.call_deferred()


func _args() -> Dictionary:
	var out := {}
	var a := OS.get_cmdline_user_args()
	var i := 0
	while i < a.size():
		var k := str(a[i])
		if k.begins_with("--"):
			var v := ""
			if i + 1 < a.size() and not str(a[i + 1]).begins_with("--"):
				v = str(a[i + 1])
				i += 1
			out[k.substr(2)] = v
		i += 1
	return out


func _run() -> void:
	await process_frame
	var a := _args()
	var out := str(a.get("out", "/tmp/hub_fact_choice"))
	var club := str(a.get("club", "GCS"))
	var wh := str(a.get("size", "390x844")).split("x")
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	state.autosave_enabled = false
	state.save_path = "user://capture_hub_fact.save"
	state.settings_path = "user://capture_hub_fact.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	state.set_setting("seen_weekly_loop_intro", true)
	state.reset()
	state.career_seed = int(str(a.get("seed", "2027")))
	state.replay_seed = state.career_seed
	state.start_season(club, db.club_list(club))
	state.tutorials = false
	for i in range(int(str(a.get("rounds", "1")))):
		state.advance()
	DisplayServer.window_set_size(Vector2i(int(wh[0]), int(wh[1])))
	root.size = Vector2i(int(wh[0]), int(wh[1]))
	# Last week's press conference is skipped (its own flow; this frame is about the cards).
	state.skip_media_conference()
	router.stack = []
	router.go("hub")
	await _frames(30)
	var hub: Node = current_scene
	var card: Button = null
	for c in hub.find_children("FactOption_*", "Button", true, false):
		if not (c as Button).disabled:
			card = c
			break
	if card == null:
		print("CAPTURE: no enabled option card on the hub")
		quit(1)
		return
	# The card scrolled to where the fact sits above it, as a player reading down would.
	_scroll_to(hub, card)
	await _frames(10)
	var why: String = await _finger(card)
	await _frames(20)
	var started: bool = current_scene == null or current_scene.name != hub.name or state.pending_sim != null
	var play: Button = hub.find_child("PlayMatch", true, false)
	print("CAPTURE: tapped %s (%s) why='%s' chosen=%s match_started=%s intent=%s play='%s'" % [card.name,
			(card.get_parent().find_child("OptionName", true, false) as Label).text, why, card.get_meta("chosen", false), started,
			state.call_intent, play.text if play != null else "none"])
	_scroll_to(hub, card)
	await _frames(10)
	root.get_viewport().get_texture().get_image().save_png(out + ".png")
	print("CAPTURE: saved %s.png" % out)
	quit()


## A finger on c's centre: a touch at its place in window pixels (the canvas is
## stretched to the window here, which tests/tap.gd's headless runs never are).
func _finger(c: Button) -> String:
	var at: Vector2 = root.get_final_transform() * c.get_global_transform_with_canvas() * (c.size * 0.5)
	var hit := [false]
	var on_press := func(): hit[0] = true
	c.pressed.connect(on_press)
	for down in [true, false]:
		var touch := InputEventScreenTouch.new()
		touch.index = 0
		touch.position = at
		touch.pressed = down
		Input.parse_input_event(touch)
		Input.flush_buffered_events()
		await _frames(2)
	if is_instance_valid(c):
		c.pressed.disconnect(on_press)
	if hit[0]:
		return ""
	var top := root.gui_get_hovered_control()
	return "the tap at %s went to %s" % [at, top.name if top != null else "nothing"]


func _scroll_to(hub: Node, c: Control) -> void:
	for sc in hub.find_children("*", "ScrollContainer", true, false):
		var s := sc as ScrollContainer
		if s.is_ancestor_of(c):
			s.scroll_vertical = int(c.global_position.y - s.global_position.y + s.scroll_vertical - 160.0)
			break


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame
