extends SceneTree
## Review capture for the rival coach read (director, 2026-11-08; RivalRead),
## dark, 390x844 by default:
##   godot --path . --script tools/visual/capture_rival_read.gd -- --out /tmp/rr [--club MEL] [--size 390x844] [--check SEED]
## (--check prints that seed's half-time read beside its scoreboard first.)
## Needs a real renderer and a window (keep it off screen with an override.cfg).
## Writes <out>_1_report.png (the Assistant's report, opened by a real tap on the
## match preview: how they play, who matters with their tagger and loose man,
## and "Their coach"), <out>_2_coach.png (a later week's report on a rival
## whose coach reads differently, with their match against you),
## <out>_3_break.png (a break as the skip lands on it: "They played ..., their
## answer to your ..." and their mood) and <out>_4_break_facts.png (a later
## break of the same match, reached by a real tap on Start quarter and the skip:
## their line again and the legs line with why theirs are going).
## The report: a fresh career played on to the first opponent with a specialist
## tagger and a loose man, then to a later one with a match against you whose
## coach goes by another rule. A report fits on one phone screen (a whole season
## of them measured 492-728 px, inside the sheet), so "Their coach" is in full
## view without a scroll; a shot is refused if any of it is not. The
## break: career seeds played in the match screen on one plan (real taps on
## Start and the skip button) until one break's line carries both their answer
## to your plan and their mood, and a later break gives their legs a reason.
## Each pair of shots is refused if the second frame did not move.
## Nothing touches a save.

const Tap := preload("res://tests/tap.gd")
## Your plan each quarter, one pattern a seed in turn.
const MY_PLANS := ["attacking", "defensive", "controlled"]
## Loaded at run time: a class name here would compile the sim before the autoloads exist.
var RR: GDScript
var MN: GDScript

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n := 10) -> void:
	for i in range(n):
		await process_frame


func _save(path: String) -> Image:
	await _frames()
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)
	return img


## The scroll box `target` sits in, or null.
func _scroll_of(target: Control) -> ScrollContainer:
	var n: Node = target.get_parent()
	while n != null:
		if n is ScrollContainer:
			return n as ScrollContainer
		n = n.get_parent()
	return null


## Scroll `target`'s scroll box so it sits near the top.
func _scroll_to(target: Control, above := 24) -> void:
	var box := _scroll_of(target)
	if box != null:
		box.scroll_vertical = maxi(0, int(target.global_position.y - box.global_position.y) - above + box.scroll_vertical)
	await _frames(4)


## True when two shots are the same picture (a scroll or tap that did nothing).
func _same(a: Image, b: Image) -> bool:
	return a.get_size() == b.get_size() and a.get_data() == b.get_data()


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


## From the week's report: whether it has a tagger line, a loose man line and
## their match against you, and its coach's first line (his scoreboard rule).
func _who(state, code: String) -> Dictionary:
	var who := {"tagger": false, "loose": false, "vs": false, "coach": ""}
	for part in state.opponent_report(code):
		for t in part[1]:
			who["tagger"] = bool(who["tagger"]) or str(t).contains(" is a tagger: ")
			who["loose"] = bool(who["loose"]) or str(t).contains(" can roam behind the ball")
			who["vs"] = bool(who["vs"]) or str(t).begins_with("Against you ")
		if str(part[0]) == "Their coach" and not (part[1] as Array).is_empty():
			who["coach"] = str(part[1][0])
	return who


func _set_plan(sim, side: int, plan: String) -> void:
	var t: Dictionary = (sim.tactics[side] as Dictionary).duplicate()
	t["gameplan"] = plan
	sim.set_tactics(side, t)


func _run() -> void:
	var out := "/tmp/rr"
	var club := "MEL"
	var check := 0
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--check":
				check = int(a[i + 1])
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
	MN = load("res://scripts/ui/match/MatchNotes.gd")
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	var sl = root.get_node("ScreenLayout")
	sl.ui_scale = 1.0 / maxf(0.01, sl.desktop_density(Vector2(W, H), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0))
	sl._update_scale()

	# --check N: print seed N's half-time read beside its scoreboard first.
	if check > 0:
		_start(state, db, club, check)
		if state.prepare_interactive_match():
			var cs = state.pending_sim
			var cme := int(cs.moment_side)
			for q in range(1, 3):
				_set_plan(cs, cme, str(MY_PLANS[check % MY_PLANS.size()]))
				cs.run_quarter()
			print("seed ", check, " at half time: ", RR.break_line(cs, cme))
			_print_scores(cs, cme)

	# The report: the first opponent with a tagger and a loose man, then a later
	# one with a match against you whose coach goes by another scoreboard rule.
	_start(state, db, club, 2027)
	var first: Image = null
	var first_coach := ""
	var second: Image = null
	for r in range(23):
		var code := str(state.my_next_opponent().get("code", ""))
		if code != "" and r >= 1:
			var who := _who(state, code)
			var path := ""
			if first == null and bool(who["tagger"]) and bool(who["loose"]):
				path = out + "_1_report.png"
			elif first != null and bool(who["vs"]) and str(who["coach"]) != first_coach:
				path = out + "_2_coach.png"
			if path != "":
				print("report: round ", r + 1, " v ", code, " ", who)
				var img: Image = await _shoot_report(state, code, path)
				if img == null:
					quit(1)
					return
				if first == null:
					first = img
					first_coach = str(who["coach"])
				else:
					second = img
					break
		state.advance()
	if second == null:
		push_error("no season with a tagger and loose man's report and a later rival coach of another kind")
		quit(1)
		return
	if _same(first, second):
		push_error("the two reports are the same picture")
		quit(1)
		return

	# The break: their answer to your plan and their mood on one break, and a
	# reason for their legs on a later one. Candidates from a quick off-screen
	# pass, then each played in the match itself (real taps on Start and the
	# skip button) until both breaks read so.
	var cands := []
	for seed in range(1, 601):
		_start(state, db, club, seed)
		if not state.prepare_interactive_match():
			continue
		var sim = state.pending_sim
		var me := int(sim.moment_side)
		var plan := str(MY_PLANS[seed % MY_PLANS.size()])
		var want_q := 0
		for q in range(1, 4):
			_set_plan(sim, me, plan)
			sim.run_quarter()
			if want_q == 0:
				if _wanted(RR.break_line(sim, me)):
					want_q = q
			elif _legs_reasoned(sim, me):
				cands.append(seed)
				break
		if cands.size() >= 8:
			break
	print("break candidates: ", cands)
	for seed in cands:
		if await _play_to_read(state, db, club, int(seed), out):
			quit(0)
			return
	push_error("no match with their answer and mood at one break and their legs' reason at a later one")
	quit(1)


## Open the week's report with a real tap and shoot it with "Their coach" in
## full view (scrolled to it if the report runs past the screen); null on a
## failure.
func _shoot_report(state, code: String, path: String) -> Image:
	var ui: Control = load("res://scenes/MatchPreviewScene.tscn").instantiate()
	root.add_child(ui)
	await _frames()
	var btn: Button = ui.find_child("AssistantReport", true, false)
	var why := "no report button" if btn == null else str(await Tap.tap(btn))
	if why != "":
		push_error("the tap missed the report: " + why)
		return null
	await _frames()
	var sheet: Node = ui.find_child("AssistantReportSheet", true, false)
	var coach: Control = _label(sheet, "Their coach") if sheet != null else null
	var box: ScrollContainer = _scroll_of(coach) if coach != null else null
	if box == null:
		push_error("no report sheet with a \"Their coach\" part in a scroll box")
		return null
	for line in state.opponent_report(code):
		print("  ", line[0], ": ", line[1])
	if not _coach_in_view(box, coach):
		await _scroll_to(coach)
		print("  scrolled ", box.scroll_vertical, " px to \"Their coach\"")
	var body: Control = box.get_child(0)
	print("  report ", int(body.size.y), " px, sheet view ", int(box.size.y), " px")
	if not _coach_in_view(box, coach):
		push_error("\"Their coach\" is not all in view")
		return null
	var img := await _save(path)
	ui.queue_free()
	await _frames(4)
	return img


## "Their coach" and every line after it (it is the report's last part) sit
## inside the scroll box's view.
func _coach_in_view(box: ScrollContainer, coach: Control) -> bool:
	var view := box.get_global_rect()
	var past := false
	for c in box.get_child(0).get_children():
		if c == coach:
			past = true
		if past and c is Control and (c as Control).visible:
			var r := (c as Control).get_global_rect()
			if r.position.y < view.position.y - 0.5 or r.end.y > view.end.y + 0.5:
				return false
	return past


func _wanted(line: String) -> bool:
	var mood := false
	for m in RR.MOODS.values():
		mood = mood or line.ends_with(str(m))
	return line.contains(", their answer to your ") and mood


## A side's midfield and ruck energy on the ground (MatchScene._group_energy).
func _group_energy(sim, side: int) -> float:
	var total := 0.0
	var n := 0
	for r in sim.legs(side):
		if bool(r["on"]) and (str(r["role"]) == "MID" or str(r["role"]) == "RUCK"):
			total += float(r["energy"])
			n += 1
	return total / float(maxi(1, n))


## The break's legs line as the sheet builds it (MatchScene._legs_view).
func _legs_text(sim, me: int) -> String:
	var reason: String = RR.legs_reason(RR.calls_of(sim, 1 - me), RR.calls_of(sim, me))
	return MN.legs_line(_group_energy(sim, me), _group_energy(sim, 1 - me), reason)


## The legs line names why theirs are going ("...; theirs is tiring: they've ...").
func _legs_reasoned(sim, me: int) -> bool:
	return _legs_text(sim, me).contains(": they've ")


## The scoreboard at this break, each quarter's points and the side `me` is,
## so the mood can be checked against it.
func _print_scores(sim, me: int) -> void:
	var opp := 1 - me
	print("  you: ", sim.squads[me].code, " (side ", me, "), they: ", sim.squads[opp].code)
	print("  score: you ", sim.goals(me), ".", sim.behinds(me), " (", sim.score(me), ")  they ",
			sim.goals(opp), ".", sim.behinds(opp), " (", sim.score(opp), ")")
	for q in range(sim.q_goals.size()):
		var pts := func(s: int) -> int: return int(sim.q_goals[q][s]) * 6 + int(sim.q_behinds[q][s])
		print("  Q", q + 1, ": you ", pts.call(me), "  they ", pts.call(opp))
	print("  their mood (ai_mood): \"", sim.ai_mood(opp), "\"")


## The text of the break sheet's legs line, as drawn.
func _legs_on_screen(m: Node) -> String:
	var v: Node = m.find_child("LegsView", true, false)
	if v == null:
		return ""
	for l in v.find_children("*", "Label", true, false):
		return str((l as Label).text)
	return ""


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
## the first break whose read carries their answer and their mood, then play
## on (a real tap on Start quarter, then the skip) and shoot the first later
## break whose legs line gives their legs a reason.
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
	var first: Image = null
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
		var legs := _legs_on_screen(m)
		if first == null and _wanted(line):
			print("break: seed ", seed, " after Q", q, ": ", line)
			print("  legs: ", legs)
			_print_scores(state.pending_sim, me)
			first = await _save(out + "_3_break.png")
		elif first != null and legs.contains(": they've "):
			print("break: seed ", seed, " after Q", q, ": ", line)
			print("  legs: ", legs)
			_print_scores(state.pending_sim, me)
			var later := await _save(out + "_4_break_facts.png")
			m.queue_free()
			await _frames(4)
			if _same(first, later):
				push_error("the later break is the same picture as the first")
				return false
			return true
	print("seed ", seed, ": no such pair of breaks in the match screen")
	m.queue_free()
	await _frames(4)
	return false
