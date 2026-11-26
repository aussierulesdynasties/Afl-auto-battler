extends SceneTree
## A group of fringe players (Factions) brings its demand to the hub as a card on
## its leader: a real tap on meeting it, then a member's profile. Needs a real renderer:
##   godot --path . --script tools/visual/capture_faction.gd -- --out /tmp/faction
## Writes <out>_card.png (the demand and what each answer does), <out>_result.png
## (after the tap) and <out>_profile.png (a member's profile, before the answer).

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
	var out := "/tmp/faction"
	var club := "FRE"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_faction.save"
	state.settings_path = "user://capture_faction_settings.cfg"
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
	var opinion = load("res://scripts/sim/Opinion.gd")
	var factions = load("res://scripts/sim/Factions.gd")
	# Four fit men out of the side, each left out and sore about it.
	var side: Dictionary = state.current_side()
	var named := {}
	for k in side:
		for id in side[k]:
			named[str(id)] = true
	var men := []
	for p in state.my_list:
		if named.has(str(p["id"])) or not load("res://scripts/sim/Ratings.gd").available(p):
			continue
		men.append(p)
		opinion.call("add", state.relations, opinion.call("player_key", str(p["id"])), "dropped_star",
				state.season_year, "Round 1", club)
		opinion.call("add_raw", state.relations, opinion.call("player_key", str(p["id"])), "left_out_again", -6.0, 0.0,
				"selection", "Left out again", state.season_year, "Round 1", club)
		if men.size() == 4:
			break
	var games := {}
	for p in state.my_list:
		games[str(p["id"])] = state.games_played(p)
	var w: int = state.story_week()
	factions.call("round_tick", state, club, state.my_list, true, games, w)
	var f: Dictionary = factions.call("of_player", state, club, str(men[0]["id"]))
	f["state"] = "demanding"
	f["pressure"] = 32
	var leader: Dictionary = state.list_player(str(f["leader"]))
	print("group ", f)
	var member: Dictionary = {}
	for p in men:
		if str(p["id"]) != str(f["leader"]):
			member = p
			break
	# A member's profile first, while the group stands.
	var hub := await _open("res://scenes/HubScene.tscn", "HubScene")
	var sheet: Control = load("res://scripts/ui/PlayerSheet.gd").open(root.get_tree().current_scene, member)
	await _wait(10)
	var line: Control = sheet.find_child("ProfileFaction", true, false)
	print("profile line: ", (line as Label).text if line != null else "missing")
	if line != null:
		var sc: ScrollContainer = null
		var n: Node = line
		while n != null and sc == null:
			if n is ScrollContainer:
				sc = n
			n = n.get_parent()
		if sc != null:
			await _wait(4)
			sc.scroll_vertical = int(line.get_global_rect().position.y - sc.get_global_rect().position.y - 420)
	await _shot(out + "_profile.png")
	sheet.queue_free()
	await _wait(4)
	state.media_conference = {}
	# Dealt the way the week deals it: the demand noted on its leader, then drawn.
	load("res://scripts/state/ClubStories.gd").note_event(state, "faction_demand", str(leader["id"]))
	var deck: Array = load("res://scripts/sim/StoryDeck.gd").all().filter(func(t): return str(t["id"]).begins_with("faction_"))
	state.week_events = load("res://scripts/sim/StoryEngine.gd").pick_week(deck,
			load("res://scripts/state/ClubStories.gd").context(state), state.story)
	print("detail: ", state.week_events[0]["options"][0]["detail"])
	var meet := await _open("res://scenes/HubScene.tscn", "Event_0")
	print("button: ", meet.text if meet is Button else "missing")
	await _shot(out + "_card.png")
	var c := _top("Event_0")
	await Tap.steady(c)
	var why := await Tap.tap(c)
	print("tap result: '", why, "'")
	await _wait(12)
	print("outcome: ", state.week_events[0].get("outcome", ""))
	print("groups after: ", factions.call("of_club", state, club).size(), " owed a game: ", leader.has("expects_game"))
	await _shot(out + "_result.png")
	quit(0)
