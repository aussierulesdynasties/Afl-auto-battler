extends SceneTree
## Ambitions and the Council's new teeth, as a phone shows them: a player's
## profile with his ambition for the season, a week's card two council members
## clash over, and a card that seats a restless line coach. Needs a real renderer:
##   godot --path . --script tools/visual/capture_ambition.gd -- --out /tmp/ambition
## Writes <out>_profile.png, <out>_clash.png and <out>_restless.png.

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


func _scroll_to(node: Control, above := 300) -> void:
	var sc: ScrollContainer = null
	var n: Node = node
	while n != null and sc == null:
		if n is ScrollContainer:
			sc = n
		n = n.get_parent()
	if sc != null:
		await _wait(4)
		sc.scroll_vertical = int(node.get_global_rect().position.y - sc.get_global_rect().position.y - above)


func _run() -> void:
	var out := "/tmp/ambition"
	var club := "FRE"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_ambition.save"
	state.settings_path = "user://capture_ambition_settings.cfg"
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
	for i in 6:
		state.week_events = []
		state.advance()
	var amb = load("res://scripts/sim/Ambitions.gd")
	# A player of yours chasing something this season, part of the way there.
	var who: Dictionary = {}
	for k in ["milestone_push", "bigger_role", "senior_spot", "win_now"]:
		for p in state.my_list:
			var am: Dictionary = amb.call("of", p, state.season_year)
			if str(am.get("k", "")) == k and str(am.get("state", "")) == "active":
				who = p
				break
		if not who.is_empty():
			break
	print("ambition: ", who.get("ambition", {}), " ", db.player_display_name(who))
	var hub := await _open("res://scenes/HubScene.tscn", "HubScene")
	var sheet: Control = load("res://scripts/ui/PlayerSheet.gd").open(root.get_tree().current_scene, who)
	await _wait(10)
	var line: Control = sheet.find_child("ProfileAmbition", true, false)
	print("profile ambition: ", (line.find_child("AmbitionWant", true, false) as Label).text if line != null else "missing",
			" / ", (line.find_child("AmbitionStatus", true, false) as Label).text if line != null else "")
	if line != null:
		await _scroll_to(line, 360)
	await _shot(out + "_profile.png")
	sheet.queue_free()
	await _wait(4)
	state.media_conference = {}
	# Two of the council with opposite views: the senior assistant holds the
	# line on standards, the development coach wants the kids through.
	var staff: Dictionary = state.club_staff(club)
	for job in staff:
		staff[job]["agenda"] = "fitness"
	staff["SA"]["agenda"] = "standards"
	staff["DEV"]["agenda"] = "youth"
	for job in ["LM", "HP"]:
		state.council["office"][club][job]["agenda"] = "fitness"
	var council = load("res://scripts/sim/Council.gd")
	var engine = load("res://scripts/sim/StoryEngine.gd")
	var cs = load("res://scripts/state/ClubStories.gd")
	var clash_card: Dictionary = {}
	for t in load("res://scripts/sim/StoryDeck.gd").all():
		if str((t.get("subject", {}) as Dictionary).get("kind", "club")) != "club" or str(t.get("club", "")) != "":
			continue
		var card: Dictionary = state.story_card(str(t["id"]))
		if card.is_empty() or (card.get("options", []) as Array).size() < 2:
			continue
		council.call("pitch_cards", state, [card])
		if not (card.get("clash", {}) as Dictionary).is_empty():
			clash_card = card
			break
	print("clash card: ", clash_card.get("tid", "none"), " ", council.call("pitch_lines", clash_card))
	if not clash_card.is_empty():
		state.week_events = [clash_card]
		var c0 := await _open("res://scenes/HubScene.tscn", "Event_0")
		var pitch := _top("EventPitch_0")
		if pitch != null:
			await _scroll_to(pitch, 420)
		await _shot(out + "_clash.png")
	# The midfield coach gone restless: the leak card seats him.
	var mid: Dictionary = {}
	for m in council.call("members", state, club):
		if str(m["job"]) == "MID":
			mid = m
	var op = load("res://scripts/sim/Opinion.gd")
	state.relations.erase(str(mid["key"]))
	op.call("add_raw", state.relations, str(mid["key"]), "test", -40.0, 0.0, "council", "Overlooked", state.season_year, "Round 1")
	print("restless: ", council.call("restless", state, club).get("name", "none"), " loyalty ", council.call("loyalty", state, mid))
	state.week_events = [state.story_card("staff_restless_leak")]
	print("restless card: ", state.week_events.size())
	var c1 := await _open("res://scenes/HubScene.tscn", "Event_0")
	await _shot(out + "_restless.png")
	quit(0)
