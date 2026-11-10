extends SceneTree
## The development talk (row T5.r93) on a phone: the card as it opens over the
## hub, a real finger on "Promise him a run there if it takes", what happened,
## then the follow-through (the verdict's news line and the promised games'
## result card). Seeded; never touches a real save.
##   godot --path . --script tools/visual/capture_dev_talk.gd -- --out PREFIX [--club FRE] [--seed 2031]
## Writes <prefix>_card.png, <prefix>_answered.png, <prefix>_news.png and
## <prefix>_result.png, and prints TAP lines (empty reason = the button got it).

const Tap := preload("res://tests/tap.gd")
const W := 390
const H := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


## The screen the Router changed to (the change lands a frame or more later).
var _last: Node = null


func _scene() -> Node:
	for i in range(1200):
		if current_scene != null and current_scene != _last and str(current_scene.scene_file_path).contains("Hub"):
			_last = current_scene
			for k in range(10):
				await process_frame
			return current_scene
		await process_frame
	push_error("capture_dev_talk: no new hub (%s)" % (current_scene.scene_file_path if current_scene != null else "none"))
	return current_scene if current_scene != null else root


func _snap(path: String) -> void:
	await _frames(8)
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(path)
	print("wrote ", path)


## A player in the side who can learn a position, put on that project at week 2.
func _learner(gs) -> Dictionary:
	var side: Dictionary = gs.current_side()
	var first := {}
	for q in gs.my_list:
		var line: String = gs._line_of(side, str(q["id"]))
		if line in ["", "BENCH"] or int(q.get("injury_weeks", 0)) > 0:
			continue
		var jobs: Array = gs.learnable_jobs(q)
		if jobs.is_empty():
			continue
		gs.set_player_plan(str(q["id"]), gs.LEARN_PREFIX + str(jobs[0]))
		if gs.project_job(q) == "":
			continue
		(q["project"] as Dictionary)["weeks"] = 2
		if first.is_empty():
			first = q
		if str(gs.take_odds(q)).begins_with("about"):
			return q
		gs.set_player_plan(str(q["id"]), "")
		q.erase("project")
	return first


func _run() -> void:
	var out := "dev_talk"
	var club := "FRE"
	var seed_ := 2031
	var cli := OS.get_cmdline_user_args()
	for i in range(cli.size() - 1):
		match str(cli[i]):
			"--out": out = str(cli[i + 1])
			"--club": club = str(cli[i + 1])
			"--seed": seed_ = int(cli[i + 1])
	await process_frame
	var gs = root.get_node("GameState")
	var router = root.get_node("Router")
	gs.autosave_enabled = false
	gs.save_path = "user://capture_dev_talk.save"
	gs.settings_path = "user://capture_dev_talk.cfg"
	gs.show_real_names = false
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	root.size = Vector2i(W, H)
	await _frames(10)
	var layout = root.get_node("ScreenLayout")
	layout.ui_scale = 1.0 / maxf(1.0, layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0))
	layout._update_scale()
	gs.reset()
	gs.career_seed = seed_
	gs.replay_seed = seed_
	for k in ["seen_training_intro", "seen_season_stats_intro", "seen_weekly_loop_intro"]:
		gs.set_setting(k, true)
	gs.start_season(club, root.get_node("GameDB").club_list(club))
	for i in range(3):
		gs.advance()
	var p := _learner(gs)
	if p.is_empty():
		push_error("capture_dev_talk: nobody in the side can learn a position")
		quit(1)
		return
	var id := str(p["id"])
	print("PLAYER ", gs.list_player(id).get("name"), " job ", gs.project_job(p), " odds ", gs.take_odds(p))
	# The card opens over the hub on its own.
	gs.media_conference = {}
	gs.week_events = [gs.story_card("training_dev_talk", p)]
	router.go("hub")
	await _frames(30)
	var sheet: Control = (await _scene()).find_child("EventSheet", true, false)
	print("SHEET ", sheet != null)
	await _snap(out + "_card.png")
	var promise: Button = sheet.find_child("Event_0", true, false) if sheet != null else null
	var why: String = (await Tap.tap(promise)) if promise != null else "missing"
	await _frames(20)
	var dt: Dictionary = p.get("dev_talk", {})
	print("TAP promise '", why, "' said ", dt.get("said", "-"), " state ", dt.get("state", "-"))
	await _snap(out + "_answered.png")
	var done: Button = sheet.find_child("EventDone", true, false) if is_instance_valid(sheet) else null
	why = (await Tap.tap(done)) if done != null else "missing"
	print("TAP done '", why, "'")
	await _frames(10)
	# It takes: the verdict's news line, on the hub.
	var own := int(p["overall"])
	p["overall"] = gs.rating_as(p, gs.project_role(p))
	gs._finish_project(p, true, "Round %d" % (gs.season.round_index + 1))
	p["overall"] = own
	print("NEWS ", gs.news[0]["text"])
	gs.week_events = []
	router.go("hub")
	await _scene()
	await _snap(out + "_news.png")
	# His three games there, then the result card.
	gs._dev_promise_week()
	print("TRIAL ", gs.role_trial)
	for i in range(3):
		gs.advance()
	print("KEPT ", dt.get("state", "-"), " result ", gs.trial_result)
	gs.media_conference = {}
	router.go("hub")
	await _frames(40)
	var hub := await _scene()
	var card: Control = hub.find_child("WeekEvent", true, false)
	if card == null:
		card = hub.find_child("SheetEvent", true, false)
	print("RESULT card ", card != null, " events ", gs.week_events.map(func(e): return e.get("tid", "")))
	await _snap(out + "_result.png")
	quit(0)
