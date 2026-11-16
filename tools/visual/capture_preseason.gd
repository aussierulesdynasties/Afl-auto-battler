extends SceneTree
## The pre-season (rule 69a), for the director's look. Needs a real renderer:
##   godot --path . --script tools/visual/capture_preseason.gd -- --out /tmp/pre --club FRE [--size 1280x720] [--seed 4127] [--art off]
## Writes <out>_meetings.png (the player meetings), <out>_meeting.png (one
## player's meeting open), <out>_plan.png and <out>_plan_low.png (the fitness
## plans), <out>_plan_set.png (Peak picked), <out>_week.png (week 1, no action
## picked), <out>_sim.png (Sim to Round 1's warning), <out>_week_bond.png (Team
## bonding picked), <out>_card.png and <out>_card_answered.png (the bonding
## card), <out>_week_drill.png (drilling picked), <out>_week_locked.png (week 3:
## the running owed shuts the rest), <out>_trial.png and <out>_trial_low.png (the
## time trial), <out>_practice_setup / _practice_invited / _practice_invited_low
## (the pre-season match stop), <out>_match_break / _match_play /
## _match_fulltime (the coached match), <out>_practice_report /
## _practice_report_low, <out>_round1.png (the hub at Round 1) and
## <out>_draft_card.png (a prospect seen that day).

var W := 390
var H := 844
var _seed := 4127


func _initialize() -> void:
	_run.call_deferred()


func _shot(path: String) -> void:
	for i in range(8):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if W >= 760 and img.get_width() != W:
		img.resize(W, H, Image.INTERPOLATE_LANCZOS)
	img.save_png(path)
	print("wrote ", path)


func _run() -> void:
	var out := "/tmp/pre"
	var club := "FRE"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--club":
			club = str(a[i + 1])
		if str(a[i]) == "--art" and str(a[i + 1]) == "off":
			# The stops without their pictures, as they were (the before shot).
			load("res://scripts/ui/UiArt.gd").set("dir", "res://assets/ui/none")
		if str(a[i]) == "--seed":
			_seed = int(a[i + 1])
		if str(a[i]) == "--size":
			var wh := str(a[i + 1]).split("x")
			W = int(wh[0])
			H = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_preseason.save"
	state.settings_path = "user://capture_preseason_settings.cfg"
	state.reset()
	state.career_seed = _seed
	state.replay_seed = _seed
	state.set_setting("seen_weekly_loop_intro", true)
	state.set_setting("seen_training_intro", true)
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	# The canvas a player's screen gives the game, whatever this machine's display density.
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	for i in range(10):
		await process_frame
	var layout = root.get_node("ScreenLayout")
	var density: float = layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0)
	layout.ui_scale = 1.0 / maxf(1.0, density)
	layout._update_scale()
	for i in range(10):
		await process_frame
	print("canvas ", root.get_visible_rect().size)
	for i in range(3):
		await process_frame
	state.start_season(club, db.club_list(club))
	state.open_preseason()
	for m in state.season.fixture[0]:
		if str(m["home"]) == club or str(m["away"]) == club:
			print("round 1: ", m["home"], " v ", m["away"])
	root.get_node("Router").go("hub")
	await _settle("PreSeason")
	print("scene ", current_scene.name, " stop ", state.preseason_stop())
	await _shot(out + "_meetings.png")
	var tap: Node = current_scene.find_child("MeetTap_*", true, false)
	if tap != null:
		await _press(str(tap.name))
		await _into_view(current_scene.find_child("Meeting_*", true, false))
		await _shot(out + "_meeting.png")
	await _press("PreSeasonGo")
	print("stop ", state.preseason_stop())
	await _shot(out + "_plan.png")
	await _scroll(true)
	await _shot(out + "_plan_low.png")
	await _scroll(false)
	await _press("Plan_peak")
	await _shot(out + "_plan_set.png")
	await _press("PreSeasonGo")
	print("stop ", state.preseason_stop(), " running owed ", state.preseason_run_left())
	await _shot(out + "_week.png")
	await _press("PreSeasonSim")
	await _frames(6)
	await _shot(out + "_sim.png")
	var modal: Node = current_scene.get_node_or_null("PreSeasonSimConfirm")
	if modal != null:
		modal.queue_free()
		await _frames(4)
	await _press("ActionTap_bond")
	await _into_view(current_scene.find_child("Action_bond", true, false))
	await _shot(out + "_week_bond.png")
	await _press("PreSeasonGo")
	print("stop ", state.preseason_stop(), " card ", state.week_events[0].get("tid", "") if not state.week_events.is_empty() else "")
	await _shot(out + "_card.png")
	if state.preseason_stop() == "story":
		state.resolve_card(0, 1)
		current_scene.call("_build")
		await _frames(6)
		await _shot(out + "_card_answered.png")
		await _press("PreSeasonGo")
	await _press("ActionTap_drill")
	await _into_view(current_scene.find_child("DrillPicker", true, false))
	await _shot(out + "_week_drill.png")
	await _press("PreSeasonGo")
	print("week ", state.preseason_week(), " open ", state.preseason_actions())
	await _shot(out + "_week_locked.png")
	await _press("ActionTap_run")
	await _press("PreSeasonGo")
	await _frames(8)
	print("scene ", current_scene.name, " stop ", state.preseason_stop())
	await _shot(out + "_trial.png")
	await _scroll(true)
	await _shot(out + "_trial_low.png")
	# Weeks 4 to 7: the running Peak still owes, week by week.
	await _press("PreSeasonGo")
	var weeks := 0
	while state.preseason_stop() == "week" and weeks < 6:
		weeks += 1
		var open: Array = state.preseason_actions()
		await _press("ActionTap_" + str(open[0]))
		await _press("PreSeasonGo")
		await _frames(6)
	# The pre-season match: the opponent and the trial, the match itself, then
	# the report.
	# A pre-season event can come up on the way: press on past it (nothing changes).
	var hops := 0
	while state.preseason_stop() == "story" and hops < 4:
		hops += 1
		await _press("PreSeasonGo")
		await _frames(10)
	print("scene ", current_scene.name, " stop ", state.preseason_stop(), " opponent ", state.practice_opponent())
	await _shot(out + "_practice_setup.png")
	await _press("PracticeFill")
	await _shot(out + "_practice_invited.png")
	await _scroll(true)
	await _shot(out + "_practice_invited_low.png")
	await _scroll(false)
	await _press("PreSeasonGo")
	await _frames(30)
	print("scene ", current_scene.name, " ", state.pending_match)
	await _shot(out + "_match_break.png")
	await _press("StartQuarter")
	for i in range(240):
		await process_frame
	await _shot(out + "_match_play.png")
	current_scene.call("_on_skip")
	await _frames(40)
	await _shot(out + "_match_fulltime.png")
	await _press("FullTimeContinue")
	await _frames(14)
	# The screen wipe swaps the scene on a thread; wait for the pre-season page, then the wipe.
	var waited := 0
	while (current_scene == null or current_scene.find_child("PreSeasonPage", true, false) == null) and waited < 600:
		await process_frame
		waited += 1
	await _frames(60)
	print("scene ", current_scene.name, " stop ", state.preseason_stop(), " played ", state.practice_played())
	await _shot(out + "_practice_report.png")
	await _scroll(true)
	await _shot(out + "_practice_report_low.png")
	await _scroll(false)
	await _press("PreSeasonGo")
	await _frames(12)
	print("scene ", current_scene.name, " week ", state.preseason_week(), " line ", state.fitness_status_line())
	var line: Node = current_scene.find_child("SeasonPlanLine", true, false)
	var p: Node = line.get_parent() if line != null else null
	while p != null:
		if p is ScrollContainer:
			(p as ScrollContainer).ensure_control_visible(line as Control)
			break
		p = p.get_parent()
	await _shot(out + "_round1.png")
	# The draft card of a prospect seen in the pre-season match, at the
	# National Draft that follows (the season itself is not played here).
	var seen_id := ""
	for prospect in state.draftee_pool:
		if seen_id == "" and (prospect.get("seen", {}) as Dictionary).has(club):
			seen_id = str(prospect["id"])
	state.season.round_index = state.season.fixture.size()
	if seen_id != "" and state.begin_intake_draft():
		root.get_node("Router").go("draft")
		await _settle("Draft")
		current_scene.call("_open_player", seen_id)
		await _frames(6)
		var seen_lbl: Node = current_scene.find_child("SeenPreSeason", true, false)
		print("draft card ", seen_id, " line ", (seen_lbl as Label).text if seen_lbl != null else "MISSING")
		if seen_lbl != null:
			var lp: Node = seen_lbl.get_parent()
			while lp != null and not (lp is ScrollContainer):
				lp = lp.get_parent()
			if lp != null:
				(lp as ScrollContainer).ensure_control_visible(seen_lbl as Control)
		await _shot(out + "_draft_card.png")
	quit(0)


## The router loads a screen over a few frames: wait until it is the current scene.
func _settle(scene: String) -> void:
	var guard := 0
	while (current_scene == null or not current_scene.scene_file_path.contains(scene)) and guard < 600:
		await process_frame
		guard += 1
	await _frames(10)


## Scroll the page until `c` is on screen.
func _into_view(c: Node) -> void:
	var p: Node = c.get_parent() if c != null else null
	while p != null and not (p is ScrollContainer):
		p = p.get_parent()
	if p != null:
		(p as ScrollContainer).ensure_control_visible(c as Control)
	await _frames(4)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


## The page to its foot, or back to the top.
func _scroll(to_foot: bool) -> void:
	await _frames(3)
	var page: Node = current_scene.find_child("PreSeasonPage", true, false)
	var sc := page.get_parent() as ScrollContainer if page != null else null
	if sc != null:
		sc.scroll_vertical = int(sc.get_v_scroll_bar().max_value) if to_foot else 0
	await _frames(3)


func _press(node_name: String) -> void:
	await _frames(3)
	var b: Node = current_scene.find_child(node_name, true, false)
	if b is Button:
		(b as Button).emit_signal("pressed")
	else:
		print("MISSING ", node_name)
	await _frames(3)
