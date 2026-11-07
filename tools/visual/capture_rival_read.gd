extends SceneTree
## Review capture for the rival coach read (director, 2026-11-08; RivalRead),
## dark, 390x844 by default:
##   godot --path . --script tools/visual/capture_rival_read.gd -- --out /tmp/rr [--club MEL] [--size 390x844]
## Needs a real renderer and a window (keep it off screen with an override.cfg).
## Writes <out>_1_report.png (the Assistant's report, opened by a real tap on the
## match preview: how they play and who matters, their tagger and loose man),
## <out>_2_coach.png (the same report at "Their coach"), <out>_3_break.png (a
## break as the skip lands on it) and <out>_4_break_facts.png (the break at the
## quarter's facts: "They played ..., their answer to your ..." and their mood).
## The report: a fresh career played on until the week's opponent has a
## specialist tagger and a loose man, two rounds in. The break: career seeds
## played in the match screen on one plan (real taps on Start and the skip
## button) until a break's line carries both their answer to your plan and
## their mood. Nothing touches a save.

const Tap := preload("res://tests/tap.gd")
## Your plan each quarter, one pattern a seed in turn.
const MY_PLANS := ["attacking", "defensive", "controlled"]
## Loaded at run time: a class name here would compile the sim before the autoloads exist.
var RR: GDScript

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n := 10) -> void:
	for i in range(n):
		await process_frame


func _save(path: String) -> void:
	await _frames()
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)


## Scroll `target`'s scroll box so it sits near the top.
func _scroll_to(target: Control, above := 24) -> void:
	var n: Node = target.get_parent()
	while n != null:
		if n is ScrollContainer:
			var box := n as ScrollContainer
			box.scroll_vertical = maxi(0, int(target.global_position.y - box.global_position.y) - above + box.scroll_vertical)
			break
		n = n.get_parent()
	await _frames(4)


func _label(under: Node, text: String) -> Control:
	for l in under.find_children("*", "Label", true, false):
		if str((l as Label).text) == text:
			return l
	return null


func _start(state, db, club: String, seed: int) -> void:
	state.autosave_enabled = false
	state.save_path = "user://capture_rival_read.save"
	state.settings_path = "user://capture_rival_read.cfg"
	state.reset()
	state.career_seed = seed
	state.replay_seed = seed
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	state.start_season(club, db.club_list(club))


## Who matters, from the week's report: [has a tagger line, has a loose man line].
func _who(state, code: String) -> Array:
	var tagger := false
	var loose := false
	for part in state.opponent_report(code):
		if str(part[0]) != "Who matters":
			continue
		for t in part[1]:
			tagger = tagger or str(t).contains(" is a tagger: ")
			loose = loose or str(t).contains(" can roam behind the ball")
	return [tagger, loose]


func _set_plan(sim, side: int, plan: String) -> void:
	var t: Dictionary = (sim.tactics[side] as Dictionary).duplicate()
	t["gameplan"] = plan
	sim.set_tactics(side, t)


func _run() -> void:
	var out := "/tmp/rr"
	var club := "MEL"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--club":
				club = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				W = int(wh[0])
				H = int(wh[1])
	await process_frame
	RR = load("res://scripts/sim/RivalRead.gd")
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	var sl = root.get_node("ScreenLayout")
	sl.ui_scale = 1.0 / maxf(0.01, sl.desktop_density(Vector2(W, H), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0))
	sl._update_scale()

	# The report: a week whose opponent has a tagger and a season behind it.
	_start(state, db, club, 2027)
	var found := false
	for r in range(14):
		var code := str(state.my_next_opponent().get("code", ""))
		if code != "" and r >= 2:
			var who := _who(state, code)
			if bool(who[0]) and bool(who[1]):
				print("report: round ", r + 1, " v ", code)
				found = true
				break
		state.advance()
	if not found:
		push_error("no week with a tagger and a loose man")
		quit(1)
		return
	var ui: Control = load("res://scenes/MatchPreviewScene.tscn").instantiate()
	root.add_child(ui)
	await _frames()
	var btn: Button = ui.find_child("AssistantReport", true, false)
	var why := "no report button" if btn == null else str(await Tap.tap(btn))
	if why != "":
		push_error("the tap missed the report: " + why)
		quit(1)
		return
	await _frames()
	var sheet: Node = ui.find_child("AssistantReportSheet", true, false)
	if sheet == null:
		push_error("no report sheet")
		quit(1)
		return
	for line in state.opponent_report(str(state.my_next_opponent().get("code", ""))):
		print("  ", line[0], ": ", line[1])
	await _save(out + "_1_report.png")
	var coach := _label(sheet, "Their coach")
	if coach != null:
		await _scroll_to(coach)
	await _save(out + "_2_coach.png")
	ui.queue_free()
	await _frames(4)

	# The break: their answer to your plan, and their mood, on one line.
	# Candidates from a quick off-screen pass, then each played in the match
	# itself (real taps on Start and the skip button) until a break reads both.
	var cands := []
	for seed in range(1, 241):
		_start(state, db, club, seed)
		if not state.prepare_interactive_match():
			continue
		var sim = state.pending_sim
		var me := int(sim.moment_side)
		var plan := str(MY_PLANS[seed % MY_PLANS.size()])
		for q in range(1, 4):
			_set_plan(sim, me, plan)
			sim.run_quarter()
			if _wanted(RR.break_line(sim, me)):
				cands.append(seed)
				break
		if cands.size() >= 12:
			break
	print("break candidates: ", cands)
	for seed in cands:
		if await _play_to_read(state, db, club, int(seed), out):
			quit(0)
			return
	push_error("no break with their answer and their mood")
	quit(1)


func _wanted(line: String) -> bool:
	var mood := false
	for m in RR.MOODS.values():
		mood = mood or line.ends_with(str(m))
	return line.contains(", their answer to your ") and mood


## A real tap; an off-screen window can be scaled by the desktop, so a tap
## that misses there falls back to pressing (as capture_skip_to_break).
func _press(b: Control) -> void:
	var why: String = await Tap.tap(b)
	if why != "" and b is Button:
		print("tap missed (", why, "), pressing instead")
		(b as Button).pressed.emit()
		await process_frame


func _answer_moment(m: Node, state) -> void:
	var sim = state.pending_sim
	var mo = m.get("_moment_overlay")
	if mo != null and is_instance_valid(mo) and sim != null and not sim.pending_moment.is_empty():
		m.call("_on_moment_choice", int(sim.pending_moment.get("default", 0)))


## Play `seed` in the match screen on one plan, skipping to each break; shoot
## the first break whose read carries their answer and their mood.
func _play_to_read(state, db, club: String, seed: int, out: String) -> bool:
	_start(state, db, club, seed)
	state.set_vignettes_on(false)
	if not state.prepare_interactive_match():
		return false
	var sim = state.pending_sim
	var me := int(sim.moment_side)
	_set_plan(sim, me, str(MY_PLANS[seed % MY_PLANS.size()]))
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	await _frames()
	for q in range(1, 4):
		var start: Control = m.find_child("StartQuarter", true, false)
		if start == null:
			break
		await _press(start)
		for i in range(60):
			_answer_moment(m, state)
			await process_frame
		var sb: Button = m.find_child("SkipToBreak", true, false)
		if sb == null or not sb.is_visible_in_tree():
			break
		_answer_moment(m, state)
		await process_frame
		await _press(sb)
		await _frames(30)
		var line: String = RR.break_line(state.pending_sim, me)
		if _wanted(line):
			print("break: seed ", seed, " after Q", q, ": ", line)
			await _save(out + "_3_break.png")
			var facts: Control = m.find_child("QuarterFacts", true, false)
			if facts != null:
				await _scroll_to(facts, 120)
				await _save(out + "_4_break_facts.png")
			m.queue_free()
			await _frames(4)
			return true
	print("seed ", seed, ": no such break in the match screen")
	m.queue_free()
	await _frames(4)
	return false
