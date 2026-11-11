extends SceneTree
## godot --headless --path . --script tests/run_onboarding_walk_tests.gd
## Row T3.R56: onboarding walked on genuinely fresh saves (director: "Walk
## through genuinely fresh saves with full onboarding enabled, not a mature
## save with tutorial flags already set"). Every walk starts from a settings
## file that doesn't exist yet and a new career, opens the real screens in the
## order a coach meets them, and records which tip each one showed. The
## "WALK|" lines are the record in docs/research/ONBOARDING_WALKTHROUGH.md.
const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")

const SUITE_SEED := 2031
const CLUB := "FRE"
const SETTINGS := "user://test_onboarding_walk_settings.cfg"
const SAVE := "user://test_onboarding_walk.save"
## The first-week screens, in the order the hub's buttons lead to them.
const WEEK := [["selection", "res://scenes/SelectionScene.tscn"], ["coaching", "res://scenes/CoachingScene.tscn"],
		["training", "res://scenes/TrainingScene.tscn"], ["list", "res://scenes/ListScene.tscn"],
		["staff", "res://scenes/StaffScene.tscn"], ["season_stats", "res://scenes/StatsHubScene.tscn"]]

var _state: Node
var _router: Node
var _db: Node
var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_router = root.get_node("Router")
	_db = root.get_node("GameDB")
	_state.autosave_enabled = false
	_state.save_path = SAVE
	_state.settings_path = SETTINGS
	_state.show_real_names = false
	root.size = Vector2i(390, 844)
	await _t("_test_walk_initial_draft_and_week")
	await _t("_test_walk_first_postseason")
	await _t("_test_walk_early_elimination")
	await _t("_test_walk_reload")
	await _t("_test_walk_skip")
	await _t("_test_walk_off")
	await _t("_test_walk_replay")
	print(Ran.line("Onboarding walk", self))
	quit(0 if _failures.is_empty() else 1)


## A device that has never run the game, then New career with the menu's
## Tutorials choice, as Main._start_new_career does.
func _fresh_device(tips := true) -> void:
	_state.delete_saved_career()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SETTINGS))
	_check(_state.new_career_tutorials(), "A fresh device defaults Tutorials to On")
	_state.set_new_career_tutorials(tips)
	_state.replay_seed = SUITE_SEED
	_state.reset()
	_check(_state.tutorials_on() == tips, "The new career takes the menu's Tutorials choice")


func _walk(mode: String, what: String) -> void:
	print("WALK|%s|%s" % [mode, what])


## The tips over `host` right now: FirstVisitIntro sheets and the older
## hand-built ones (weekly loop, training, season stats), by node name.
func _tips(host: Node) -> Array:
	var out := []
	for n in host.get_children():
		if n.is_queued_for_deletion():
			continue
		var nm := str(n.name)
		if nm.ends_with("Intro") or n.is_in_group("first_visit_intro"):
			out.append(nm)
	return out


## The heading of a tip sheet, for the record.
func _tip_title(host: Node, tip: String) -> String:
	var n: Node = host.find_child(tip, false, false)
	if n == null:
		return tip
	var labels := n.find_children("*", "Label", true, false)
	return str((labels[0] as Label).text) if not labels.is_empty() else tip


## Close every tip over host the way a finger does: its Got it, else Back.
func _close_tips(host: Node) -> void:
	for i in range(4):
		var ok: Button = null
		for pattern in ["*IntroOk", "FinishOnboarding"]:
			for b in host.find_children(pattern, "Button", true, false):
				if not b.is_queued_for_deletion() and b.is_visible_in_tree():
					ok = b
					break
			if ok != null:
				break
		if ok == null:
			if not _tips(host).is_empty() and host.has_method("handle_back"):
				host.handle_back()
				await _settle()
			return
		var what := str(ok.name)
		var why: String = await Tap.tap(ok)
		_check(why == "", "%s takes a finger's tap (%s)" % [what, why])
		await _settle()


## Open a screen, record what tip it showed, close it, leave.
func _visit(mode: String, label: String, path: String) -> Array:
	var s: Control = load(path).instantiate()
	root.add_child(s)
	await _settle()
	var tips := _tips(s)
	var titles := tips.map(func(t): return _tip_title(s, t))
	_walk(mode, "%s: %s" % [label, ", ".join(titles) if not titles.is_empty() else "no tip"])
	await _close_tips(s)
	_check(_tips(s).is_empty(), "%s: the tip closes (%s)" % [label, mode])
	s.queue_free()
	await _settle()
	return tips


## The League redraft to a full list, picking the best player each turn. With
## `interview` (a new career), taking the club opens the press interview before
## the board (director, 2026-11-11: "its meant to go before the draft").
func _initial_draft(mode: String, interview := false) -> void:
	_state.begin_draft()
	_state.interview_due = interview
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _settle()
	var tips := _tips(ui)
	_walk(mode, "Initial draft, Choose your club: %s" % (", ".join(tips.map(func(t): return _tip_title(ui, t))) if not tips.is_empty() else "no tip"))
	await _close_tips(ui)
	ui.call("_on_club_chosen", CLUB)
	await _settle()
	if interview:
		var iv := current_scene
		_check(_router.current() == "interview" and iv != null and str(iv.scene_file_path).ends_with("InterviewScene.tscn"),
				"Taking the club opens the press interview before the board (at %s)" % _router.current())
		if iv != null:
			var it := _tips(iv)
			_walk(mode, "Appointment interview: %s" % (", ".join(it.map(func(t): return _tip_title(iv, t))) if not it.is_empty() else "no tip"))
			await _close_tips(iv)
			_check(_tips(iv).is_empty(), "Appointment interview: the tip closes (%s)" % mode)
			if mode != "off":
				await _interview_press_room(iv)
		# The answers are career_ui's to prove; here the walk goes on to the board.
		_state.interview_due = false
		if iv != null:
			iv.queue_free()
		ui.queue_free()
		await _settle()
		ui = load("res://scenes/DraftScene.tscn").instantiate()
		root.add_child(ui)
		await _settle()
	tips = _tips(ui)
	_walk(mode, "Initial draft, the board after choosing %s: %s" % [CLUB, ", ".join(tips.map(func(t): return _tip_title(ui, t))) if not tips.is_empty() else "no tip"])
	if mode != "off":
		_check(tips.has("LeagueDraftIntro"), "The League redraft's own tip opens on the board")
	await _close_tips(ui)
	var d = _state.draft
	var guard := 0
	while not d.is_finished() and guard < 80:
		guard += 1
		var want := ""
		var status: Dictionary = d.position_status()
		for role in ["RUCK", "DEF", "MID", "FWD"]:
			if int((status[role] as Dictionary)["short"]) > 0:
				want = role
				break
		var board: Array = d.board(want, "", "", "overall", true)
		board = board.filter(func(p): return d.can_pick_player(p))
		if board.is_empty():
			break
		ui.call("_on_pick", board[0])
	_check(d.is_finished() and d.is_valid(), "The initial draft finishes with a valid list (%s)" % mode)
	_walk(mode, "Initial draft: %d players taken, then Start season" % d.list().size())
	_state.start_season(CLUB, d.list())
	_state.open_preseason(false)
	ui.queue_free()
	await _settle()


## Director, 2026-11-12: "the onboarding press interview has a LOT of empty space
## taking up like 80% of the screen. theres no press scene". The interview opens
## in the same press room as every press conference, drawn from the figure sheet
## (not a fallback), the coach's name and the first answer take a finger's tap
## past it, and the question page leaves no empty block under the answers.
func _interview_press_room(iv: Control) -> void:
	var SV = load("res://scripts/ui/match/StoppageVignette.gd")
	var VF = load("res://scripts/ui/match/VignetteFigures.gd")
	var stage: Control = iv.find_child("InterviewStage", true, false)
	_check(stage != null and stage.is_visible_in_tree(), "Appointment interview: the press room is on the screen")
	if stage == null:
		return
	var room: Control = stage.find_child("MediaConferenceVignette", false, false)
	_check(room != null and room.get_script() == load("res://scripts/ui/MediaConferenceVignette.gd"),
			"Appointment interview: the room is the press conference's own scene")
	if room == null:
		return
	var mat := room.material as ShaderMaterial
	_check(mat != null and mat.shader == SV.FIGURE_SHADER and mat.get_shader_parameter("mask_tex") == SV.FIGURE_MASK
			and mat.get_shader_parameter("sheet_size") == VF.SHEET_SIZE,
			"Appointment interview: the coach is drawn with the figure shader and its mask")
	var sheet: Texture2D = SV.FIGURE_SHADE
	_check(sheet != null and sheet.resource_path == "res://assets/vignette/figures_shade.png"
			and Vector2i(sheet.get_size()) == Vector2i(VF.SHEET_SIZE),
			"Appointment interview: the figure sheet loaded at its own size (%s, %s)" % [
				sheet.resource_path if sheet != null else "none", sheet.get_size() if sheet != null else Vector2.ZERO])
	_check(VF.strip("coach", "coach_seated", "front") is Dictionary and not (VF.strip("coach", "coach_seated", "front") as Dictionary).is_empty(),
			"Appointment interview: the sheet holds the seated coach the room draws")
	_check(room.size.x >= 300.0 and room.size.y >= 180.0, "Appointment interview: the room fills its stage (%s)" % room.size)
	# Director's check, 2026-11-12 (blurry coach): the sheet is never blown up past
	# its own pixels, even at the camera's closest; more screen means more room.
	_check(room.call("figure_scale") <= 1.001,
			"Appointment interview: the coach is drawn at or under the sheet's own size (%.2f screen units per sheet pixel)" % room.call("figure_scale"))
	var named_size := stage.size
	var named_box: Rect2 = room.call("scene_box")
	var name_go: Control = iv.find_child("InterviewStart", true, false)
	var name_field: Control = iv.find_child("CoachName", true, false)
	if name_go != null and name_field != null:
		var under := name_go.get_global_rect().position.y - name_field.get_global_rect().end.y
		_check(under < 40.0, "Appointment interview: Face the press sits right under the name field (%d px)" % under)
	var field: LineEdit = iv.find_child("CoachName", true, false)
	if field != null:
		field.text = "Pat Reid"
		field.text_changed.emit(field.text)
		await _settle()
		var why: String = await Tap.tap(iv.find_child("InterviewStart", true, false))
		_check(why == "", "Appointment interview: Face the press takes a finger's tap (%s)" % why)
		await _settle()
	var answer: Control = iv.find_child("InterviewAnswer0", true, false)
	_check(answer != null, "Appointment interview: the first question is up")
	if answer == null:
		return
	await _settle()
	# The room takes the height the question leaves: the last answer sits near the
	# foot of the screen, not above an empty block.
	var last: Control = iv.find_child("InterviewAnswer3", true, false)
	var gap := float(root.size.y) - last.get_global_rect().end.y
	_check(stage.size.y > 180.0 and gap < 140.0,
			"Appointment interview: no empty block under the answers (room %d px high, %d px under the last answer)" % [stage.size.y, gap])
	_check(stage.find_child("MediaConferenceVignette", false, false) == room,
			"Appointment interview: the same room stays through the questions")
	_check(stage.size == named_size and (room.call("scene_box") as Rect2).size == named_box.size,
			"Appointment interview: the room keeps its size from page to page (%s then %s)" % [named_size, stage.size])
	var why2: String = await Tap.tap(answer)
	_check(why2 == "", "Appointment interview: an answer takes a finger's tap past the room (%s)" % why2)
	await _settle()
	var second := iv.find_children("*", "Label", true, false).filter(func(l): return str((l as Label).text).begins_with("Question 2 of"))
	_check(not second.is_empty(), "Appointment interview: the next question follows the answer")


func _hub(mode: String, label: String) -> Control:
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _settle()
	var tips := _tips(hub)
	_walk(mode, "%s: %s" % [label, ", ".join(tips.map(func(t): return _tip_title(hub, t))) if not tips.is_empty() else "no tip"])
	return hub


func _gone(n: Node) -> void:
	n.queue_free()
	await _settle()


## Initial draft, the pre-season and the first week's screens.
func _test_walk_initial_draft_and_week() -> void:
	_fresh_device(true)
	# Main._start_new_career: a new career opens with the interview, once the
	# club is taken and before the first pick.
	await _initial_draft("initial draft", true)
	# The draft's Start season goes to the hub, then to the pre-season screen
	# until Round 1.
	var pre := await _visit("weekly loop", "Pre-season", "res://scenes/PreSeasonScene.tscn")
	_check(not pre.is_empty(), "The pre-season shows its tip")
	# Into Round 1, as the pre-season's last stop does.
	_state.preseason["done"] = true
	var hub := await _hub("weekly loop", "Hub, first visit (Round 1)")
	_check(_tips(hub).has("WeeklyLoopIntro"), "The first hub shows its weekly-loop tip")
	await _close_tips(hub)
	await _gone(hub)
	for v in WEEK:
		var tips := await _visit("weekly loop", str(v[0]).capitalize(), str(v[1]))
		_check(not tips.is_empty(), "%s shows its tip on a fresh save" % v[0])
	hub = await _hub("weekly loop", "Hub, second visit")
	_check(_tips(hub).is_empty(), "The hub's tip doesn't come back")
	await _gone(hub)
	for v in WEEK:
		var again := await _visit("weekly loop", "%s again" % str(v[0]).capitalize(), str(v[1]))
		_check(again.is_empty(), "%s: no tip the second time" % v[0])


## A fresh career played to the end of its first finals series (top of the ladder).
func _season_to_finals(rank: int) -> void:
	var sea = _state.season
	var codes: Array = sea.ladder.keys()
	codes.sort()
	codes.erase(CLUB)
	codes.insert(rank - 1, CLUB)
	for i in range(codes.size()):
		var row: Dictionary = sea.ladder[codes[i]]
		row["w"] = 20 - i
		row["l"] = 3 + i
		row["d"] = 0
		row["p"] = 23
		row["pf"] = 2400 - i * 20
		row["pa"] = 2000
	sea.round_index = sea.fixture.size()
	sea.recalc_ladder()
	_state.ensure_finals()
	_state.week_events = []


## A fresh device and career at Round 1, its first hub visit made (the
## weekly-loop tip read), as any coach meets it before the finals.
func _new_season_career(mode: String, first_hub := true) -> void:
	_fresh_device(true)
	_state.start_season(CLUB, _db.club_list(CLUB))
	_walk(mode, "Fresh device, new career at %s, Tutorials on" % CLUB)
	if not first_hub:
		return
	var hub := await _hub(mode, "Hub, Round 1")
	await _close_tips(hub)
	await _gone(hub)


## The first postseason: finals played from the hub, then each stop in order.
func _test_walk_first_postseason() -> void:
	var mode := "first postseason"
	await _new_season_career(mode)
	_season_to_finals(1)
	var guard := 0
	while not _state.season.is_season_over() and guard < 8:
		guard += 1
		_state.advance()
	_state.season.finals["done"] = true
	if _state.media_conference_pending():
		_walk(mode, "The press conference after the Grand Final comes first (skipped here)")
		_state.skip_media_conference()
	var hub := await _hub(mode, "Hub, the Grand Final over")
	_check(_tips(hub).has("PostseasonIntro"), "The finals over, the postseason tip opens")
	await _close_tips(hub)
	_walk(mode, "After Got it, the week's asks follow: %s" % ("yes" if hub.find_child("WeekActions", true, false) != null else "no"))
	await _gone(hub)
	var review: Control = load("res://scenes/SeasonReviewScene.tscn").instantiate()
	root.add_child(review)
	await _settle()
	var night := review.find_child("AwardsSkip", true, false) as Button
	if night == null:
		night = review.find_child("AwardsNext", true, false) as Button
	_walk(mode, "Season review, first screen: %s" % ("awards night" if night != null else
			", ".join(_tips(review).map(func(t): return _tip_title(review, t)))))
	var guard_night := 0
	while night != null and guard_night < 12:
		guard_night += 1
		await Tap.tap(night)
		await _settle()
		night = review.find_child("AwardsSkip", true, false) as Button
		if night == null:
			night = review.find_child("AwardsNext", true, false) as Button
	var after_night := _tips(review)
	_walk(mode, "Season review, after awards night: %s" % (", ".join(after_night.map(func(t): return _tip_title(review, t))) if not after_night.is_empty() else "no tip"))
	_check(after_night.has("SeasonReviewIntro"), "The Season review tip follows awards night")
	await _close_tips(review)
	await _gone(review)
	_state.open_offseason()
	var p: Dictionary = _state.my_list[0]
	p["contract_years"] = 1
	for k in ["resigned", "talks", "retiring"]:
		p.erase(k)
	var s: Control = load("res://scenes/OffseasonScene.tscn").instantiate()
	root.add_child(s)
	await _settle()
	_walk(mode, "Trades & Contracts: %s" % ", ".join(_tips(s).map(func(t): return _tip_title(s, t))))
	await _close_tips(s)
	var talk: Button = s.find_child("Negotiate", true, false)
	if talk != null:
		await Tap.tap(talk)
		await _settle()
	_walk(mode, "Talk contract (own player): %s" % ", ".join(_tips(s).map(func(t): return _tip_title(s, t))))
	_check(_tips(s).has("ContractsIntro"), "Talks open the contract tip")
	await _close_tips(s)
	var cancel: Button = s.find_child("CancelTalks", true, false)
	if cancel != null:
		_check((await Tap.tap(cancel)) == "", "Cancel closes the talks")
		await _settle()
	var tab: Button = s.find_child("Tab_trade", true, false)
	var tapped := "no Trade tab"
	if tab != null:
		tapped = await Tap.tap(tab)
		await _settle()
	_check(tapped == "", "The Trade tab takes a tap (%s)" % tapped)
	_walk(mode, "Trade tab: %s" % ", ".join(_tips(s).map(func(t): return _tip_title(s, t))))
	_check(_tips(s).has("TradeIntro"), "The Trade tab opens the trade tip")
	await _close_tips(s)
	await _gone(s)
	if not _state.begin_intake_draft():
		_check(false, "The National Draft opens")
		return
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _settle()
	var first := _tips(ui)
	_walk(mode, "National Draft, first screen: %s%s" % [", ".join(first.map(func(t): return _tip_title(ui, t))) if not first.is_empty() else "no tip",
			" (the recruiting panel meets first)" if ui.find_child("MeetingDone", true, false) != null else ""])
	var meet: Button = ui.find_child("MeetingDone", true, false)
	if meet != null:
		await Tap.tap(meet)
		await _settle()
	_walk(mode, "National Draft, after the panel: %s" % (", ".join(_tips(ui).map(func(t): return _tip_title(ui, t))) if not _tips(ui).is_empty() else "no tip"))
	await _close_tips(ui)
	var d = _state.draft
	guard = 0
	while not d.is_user_turn() and not d.is_finished() and guard < 200:
		guard += 1
		d.auto_until_user_turn()
	ui.call("_refresh")
	await _settle()
	var trade: Button = ui.find_child("TradePicks", true, false)
	if trade != null:
		await Tap.tap(trade)
		await _settle()
	_walk(mode, "Trade picks on draft night: %s" % (", ".join(_tips(ui).map(func(t): return _tip_title(ui, t))) if not _tips(ui).is_empty() else "no tip"))
	_check(_tips(ui).has("DraftTradeIntro"), "Trade picks opens the pick-trading tip")
	await _close_tips(ui)
	await _gone(ui)
	_state.draft = null


## Knocked out in the first week of the finals: the league plays on from the
## hub, and the postseason tip waits for the Grand Final's results.
func _test_walk_early_elimination() -> void:
	var mode := "early elimination"
	await _new_season_career(mode)
	_season_to_finals(8)
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _settle()
	await _close_tips(hub)   # the weekly-loop tip of a fresh device
	var weeks := 0
	var early := false
	while not _state.season.is_season_over() and weeks < 8:
		weeks += 1
		hub.call("_sim_week")
		await _settle()
		if _tips(hub).has("PostseasonIntro"):
			early = true
		var go: Button = hub.find_child("ResultsContinue", true, false)
		if not _state.season.is_season_over() and go != null:
			go.pressed.emit()
			await _settle()
	_walk(mode, "Finals played on from the hub for %d weeks; tip before the Grand Final's results: %s" % [weeks, "yes" if early else "no"])
	_check(not early, "No postseason tip while the finals are still on")
	var last: Button = hub.find_child("ResultsContinue", true, false)
	if last != null:
		await Tap.tap(last)
		await _settle()
	_walk(mode, "Grand Final results closed: %s" % ", ".join(_tips(hub).map(func(t): return _tip_title(hub, t))))
	if not _tips(hub).has("PostseasonIntro"):
		# Say what holds it back, so the record is honest about the order.
		_walk(mode, "Held back by: season over %s, press conference %s, season wrap %s" % [
				_state.season.is_season_over(), _state.media_conference_pending(), _state.needs_season_wrap()])
		await _gone(hub)
		if _state.media_conference_pending():
			_walk(mode, "The press conference after the Grand Final comes first (skipped here)")
			_state.skip_media_conference()
		hub = await _hub(mode, "Hub after the press conference")
	_check(_tips(hub).has("PostseasonIntro"), "The postseason tip opens once the finals are over")
	await _gone(hub)


## Save half-way through the tips, quit, load: seen stays seen, unseen still due.
func _test_walk_reload() -> void:
	var mode := "reload"
	await _new_season_career(mode)
	await _visit(mode, "Selection", "res://scenes/SelectionScene.tscn")
	_check(_state.save_career(), "The career saves")
	_state.reset()
	_check(_state.load_career(), "The career loads")
	_walk(mode, "Saved and loaded; Tutorials still %s" % ("on" if _state.tutorials_on() else "off"))
	var hub := await _hub(mode, "Hub after reload")
	_check(_tips(hub).is_empty(), "The weekly-loop tip doesn't come back after a reload")
	await _gone(hub)
	var sel := await _visit(mode, "Selection after reload", "res://scenes/SelectionScene.tscn")
	_check(sel.is_empty(), "Selection's tip doesn't come back after a reload")
	var coach := await _visit(mode, "Coaching after reload (never opened before)", "res://scenes/CoachingScene.tscn")
	_check(not coach.is_empty(), "A tip not yet seen still comes after a reload")
	_check(_state.intro_due("postseason"), "The postseason tip is still due after a reload")


## Skip on the first hub's tip: the week's asks still come, and every other
## screen still has its tip. Skipping help never skips a football decision.
func _test_walk_skip() -> void:
	var mode := "skip"
	await _new_season_career(mode, false)
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _settle()
	var skip: Button = hub.find_child("SkipOnboarding", true, false)
	_check(skip != null, "The first hub's tip has Skip")
	if skip != null:
		_check((await Tap.tap(skip)) == "", "Skip takes a finger's tap")
		await _settle()
	_walk(mode, "Skip on the hub's tip: closed %s, week's buttons there %s" % [
			"yes" if _tips(hub).is_empty() else "no", "yes" if hub.find_child("WeekActions", true, false) != null else "no"])
	_check(hub.find_child("WeekActions", true, false) != null, "After Skip the week's buttons are there")
	await _gone(hub)
	var sel := await _visit(mode, "Selection after Skip", "res://scenes/SelectionScene.tscn")
	_walk(mode, "Skip covers the hub's tip only; other screens keep theirs: %s" % ("yes" if not sel.is_empty() else "no"))


## Tutorials off at New career: no tip anywhere; turned on in Settings later,
## the unseen ones come.
func _test_walk_off() -> void:
	var mode := "off"
	_fresh_device(false)
	await _initial_draft(mode)
	var hub := await _hub(mode, "Hub, first visit")
	_check(_tips(hub).is_empty(), "Tips off: no hub tip")
	await _gone(hub)
	for v in WEEK:
		var tips := await _visit(mode, str(v[0]).capitalize(), str(v[1]))
		_check(tips.is_empty(), "Tips off: no %s tip" % v[0])
	_state.set_tutorials_on(true)
	_walk(mode, "Settings > Tutorials On, mid-career")
	var sel := await _visit(mode, "Selection after turning tips on", "res://scenes/SelectionScene.tscn")
	_check(not sel.is_empty(), "Tips turned on: the unseen tips come")


## Replay: is there any way to see a tip again? Turning Tutorials off and on
## doesn't reset what was seen, and no control re-opens a seen tip.
func _test_walk_replay() -> void:
	var mode := "replay"
	await _new_season_career(mode)
	await _visit(mode, "Selection", "res://scenes/SelectionScene.tscn")
	_state.set_tutorials_on(false)
	_state.set_tutorials_on(true)
	var again := await _visit(mode, "Selection after Tutorials off then on", "res://scenes/SelectionScene.tscn")
	_walk(mode, "Seen tips come back after off/on: %s" % ("yes" if not again.is_empty() else "no"))
	# Settings' tips row is On/Off only: no control re-opens a tip already seen.
	var src := FileAccess.get_file_as_string("res://scripts/ui/OptionsSheet.gd")
	var rows := src.count("_row(v, ")
	_walk(mode, "Settings rows: %d; tips controls: Tutorials On/Off%s" % [rows,
			"" if src.find("seen_") == -1 else ", plus a reset of seen tips"])
	_check(src.find("seen_") == -1, "Replay still unbuilt: when a reset lands, update docs/research/ONBOARDING_WALKTHROUGH_2026-11-10.md")


func _settle() -> void:
	for i in range(4):
		await process_frame


func _check(ok: bool, what: String) -> void:
	_checks += 1
	if not ok:
		_failures.append(what)
		push_error(what)


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)
