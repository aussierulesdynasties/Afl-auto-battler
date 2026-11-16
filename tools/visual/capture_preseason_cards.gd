extends SceneTree
## The bonding card stop (rule 69a) for the director's look. Needs a real renderer:
##   godot --path . --script tools/visual/capture_preseason_cards.gd -- --out /tmp/precards --club FRE [--size 1280x720]
## Writes <out>_<NN>_<card>.png for each of the nine bonding cards (01_camp ...
## 09_heated), and <out>_<NN>_<card>_low.png scrolled to the foot when the card
## runs past the screen. Each stop is the real pre-season screen after a Team
## bonding week, with the card forced so it is the one on show (three players
## marked Indigenous, so the cultural day can come).

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(path: String) -> void:
	await _frames(40)
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if W >= 760 and img.get_width() != W:
		img.resize(W, H, Image.INTERPOLATE_LANCZOS)
	img.save_png(path)
	print("wrote ", path)


func _run() -> void:
	var out := "/tmp/precards"
	var club := "FRE"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--club":
			club = str(a[i + 1])
		if str(a[i]) == "--size":
			var wh := str(a[i + 1]).split("x")
			W = int(wh[0])
			H = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_precards.save"
	state.settings_path = "user://capture_precards_settings.cfg"
	state.reset()
	state.career_seed = 4127
	state.replay_seed = 4127
	state.set_setting("seen_weekly_loop_intro", true)
	state.set_setting("seen_training_intro", true)
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	await _frames(10)
	var layout = root.get_node("ScreenLayout")
	var density: float = layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0)
	layout.ui_scale = 1.0 / maxf(1.0, density)
	layout._update_scale()
	await _frames(13)
	state.start_season(club, db.club_list(club))
	state.open_preseason()
	# Past the meetings and the plan, then a week of Team bonding.
	state.preseason_meetings_done()
	state.set_preseason_plan("develop")
	var guard := 0
	while state.preseason_stop() != "week" and guard < 10:
		guard += 1
		state.preseason_advance()
	state.set_preseason_action("bond")
	state.preseason_advance()
	for q in state.my_list.slice(0, 3):
		q["indigenous"] = true
	var shots := [["bond_away_camp", {}, "01_camp"], ["bond_talent_quest", {}, "02_talent"],
			["bond_community_week", {}, "03_community"], ["bond_beach_day", {}, "04_beach"],
			["bond_cultural_day", {}, "05_cultural"], ["bond_leadership_workshop", {}, "06_workshop"],
			["bond_families_day", {}, "07_families"], ["pre_leaders_vote", {}, "08_leaders"], ["pre_sim_heated", {}, "09_heated"]]
	# Then the club's own bonding cards (10_<id> ...).
	var n := 10
	# Loaded at run time: a --script tool compiles before the autoloads exist.
	for t in load("res://scripts/sim/StoryDeck.gd").all():
		if str(t.get("club", "")) == club and (t.get("phase", []) as Array).has("bonding"):
			shots.append([str(t["id"]), {}, "%02d_%s" % [n, t["id"]]])
			n += 1
	for shot in shots:
		var card: Dictionary = state.story_card(str(shot[0]), shot[1])
		print(shot[2], " card: ", card.get("title", "EMPTY"))
		state.week_events = [card]
		state.preseason["story_pending"] = true
		root.get_node("Router").go("hub")
		await _frames(12)
		# The screen wipe swaps the scene on a thread; wait for the hub to land.
		var waited := 0
		while (current_scene == null or current_scene.find_child("PreSeasonPage", true, false) == null) and waited < 600:
			await process_frame
			waited += 1
		print("scene ", current_scene.name, " stop ", state.preseason_stop())
		await _shot(out + "_" + str(shot[2]) + ".png")
		var page: Node = current_scene.find_child("PreSeasonPage", true, false)
		var sc := page.get_parent() as ScrollContainer if page != null else null
		if sc != null and sc.get_v_scroll_bar().max_value > sc.size.y + 4.0:
			sc.scroll_vertical = int(sc.get_v_scroll_bar().max_value)
			await _shot(out + "_" + str(shot[2]) + "_low.png")
	quit()
