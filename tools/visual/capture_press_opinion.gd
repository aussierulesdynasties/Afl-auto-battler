extends SceneTree
## A player's opinion of you (director 2026-11-08), for QC at phone size:
##   godot --path . --resolution 390x844 --windowed --script tools/visual/capture_press_opinion.gd -- --out DIR
## Writes DIR/opinion_press_gate.png (the Muckraker after a heavy loss, the
## answer calling a player out scrolled into view with both outcomes and their
## sizes), DIR/opinion_press_result.png (answered, he took it personally: his
## opinion of you moving), DIR/opinion_talks.png (the season over, contract
## talks with him at 45/100: the chance he won't re-sign) and
## DIR/opinion_sheet.png (his profile: "Opinion of you", the rule and his
## reasons). Seeded; never touches a real save.


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


## Waits for the question to show (the room hands over to it), up to ~6 s.
func _question_up() -> bool:
	for i in range(360):
		await process_frame
		var q: Control = root.find_child("MediaQuestion", true, false)
		if q != null and q.is_visible_in_tree():
			await _frames(20)
			return true
	return false


func _shot(path: String) -> void:
	root.get_viewport().get_texture().get_image().save_png(path)
	print("wrote ", path)


func _fail(why: String) -> void:
	push_error("capture_press_opinion: " + why)
	quit(1)


## A label's words, plain or rich.
func _text(c: Control) -> String:
	if c is RichTextLabel:
		return (c as RichTextLabel).get_parsed_text()
	return str(c.get("text"))


## Scrolls `c` into view in the scroll container holding it.
func _into_view(c: Control) -> void:
	var sc: Node = c.get_parent()
	while sc != null and not (sc is ScrollContainer):
		sc = sc.get_parent()
	if sc != null:
		(sc as ScrollContainer).ensure_control_visible(c)


## Nudges the scroll holding `c` down until no line of text is cut in half
## at its top edge (scrolling down only shows more below).
func _snap(c: Control) -> void:
	var sc: Node = c.get_parent()
	while sc != null and not (sc is ScrollContainer):
		sc = sc.get_parent()
	if sc == null:
		return
	var scroll := sc as ScrollContainer
	for i in range(3):
		var edge := scroll.get_global_rect().position.y
		var cut := 0.0
		for n in scroll.find_children("*", "Control", true, false):
			var k := n as Control
			if k.is_visible_in_tree() and (k is Label or k is RichTextLabel):
				var r := k.get_global_rect()
				if r.position.y < edge - 0.5 and r.end.y > edge + 0.5:
					cut = maxf(cut, r.end.y - edge)
		if cut <= 0.0:
			return
		scroll.scroll_vertical += int(ceil(cut)) + 4
		await _frames(3)


func _run() -> void:
	var out := "caps"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		if str(a[i]).begins_with("--out="):
			out = str(a[i]).substr(6)
		elif str(a[i]) == "--out" and i + 1 < a.size():
			out = str(a[i + 1])
	DirAccess.make_dir_recursive_absolute(out)
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	var MC = load("res://scripts/sim/MediaConference.gd")
	var club := "COL"
	state.autosave_enabled = false
	state.save_path = "user://capture_press_opinion.save"
	state.settings_path = "user://capture_press_opinion.cfg"
	seed(2031)
	state.reset()
	state.career_seed = 2031
	state.replay_seed = 2031
	state.set_setting("seen_weekly_loop_intro", true)
	state.start_season(club, db.club_list(club))
	state.set_vignettes_on(false)
	DisplayServer.window_set_size(Vector2i(390, 844))
	root.size = Vector2i(390, 844)
	await _frames(4)
	# The Muckraker after a heavy loss; the fourth answer calls a player out,
	# one whose deal ends this season.
	var named: Dictionary = state.my_list[3]
	named["contract_years"] = 1
	var id := str(named["id"])
	var key := Trust.player_key(id)
	state.relations.erase(key)
	state.media_conference = MC.pick({"club": club, "opponent_name": "Carlton", "round": 8,
			"year": int(state.season_year), "result": {"home": club, "away": "CAR", "score": [55, 101]},
			"named": {"heavy_loss": {"id": id, "name": str(db.player_display_name(named))}}}, {})
	state.media_conference["opp"] = "Carlton"
	# A career where he takes it personally, so the result shows his opinion move.
	var mkey := str(state.media_conference.get("key", ""))
	for sd in range(1, 300):
		if MC.roll(sd, state.season_year, int(state.media_conference.get("round", 0)), mkey, 3) > state.press_chance(3):
			state.career_seed = sd
			break
	router.stack = []
	router.go("press")
	if not await _question_up():
		_fail("the question did not show")
		return
	var ans: Button = root.find_child("MediaAnswer_3", true, false)
	var line: Control = root.find_child("MediaAnswerLine_3", true, false)
	if ans == null or line == null:
		_fail("no fourth answer")
		return
	_into_view(line)
	await _frames(20)
	await _snap(line)
	await _frames(10)
	print("gate: ", _text(line))
	_shot(out.path_join("opinion_press_gate.png"))
	ans.emit_signal("pressed")
	await _frames(30)
	var op: Control = root.find_child("MediaOutcomeOpinion", true, false)
	if op == null or not op.is_visible_in_tree():
		_fail("the result shows no opinion change")
		return
	print("result: ", _text(op))
	_shot(out.path_join("opinion_press_result.png"))
	state.media_conference = {}
	# The season played out; contract talks with him at 45/100.
	var season = state.season
	season.round_index = season.fixture.size()
	state.ensure_finals()
	while not season.is_season_over():
		state.advance()
	state.relations.erase(key)
	Trust.change(state.relations, key, -MC.CALLOUT_OPINION_DROP * Trust.PER_POINT, "You called him out in the press", state.season_year, "Round 8")
	Trust.change(state.relations, key, -8, "You promised him a game and left him out", state.season_year, "Round 14")
	named.erase("talks")
	router.stack = []
	router.go("offseason")
	# The router loads the screen in the background: wait for it, up to ~10 s.
	var scene: Node = null
	for i in range(600):
		await process_frame
		if current_scene != null and current_scene.has_method("_open_talks"):
			scene = current_scene
			break
	await _frames(20)
	if scene == null:
		_fail("no off-season screen")
		return
	scene.call("_open_talks", id)
	await _frames(20)
	var refuse: Control = root.find_child("TalksRefuse", true, false)
	if refuse == null or not refuse.is_visible_in_tree():
		_fail("the talks show no refusal chance")
		return
	print("talks: ", _text(refuse))
	_shot(out.path_join("opinion_talks.png"))
	scene.call("_close_talks")
	await _frames(10)
	# His profile: the number, then a finger on Why shows the rule and his reasons.
	var sheet: Control = load("res://scripts/ui/PlayerSheet.gd").open(current_scene, named)
	await _frames(20)
	var words: Control = sheet.find_child("TrustWords", true, false)
	var why: Button = sheet.find_child("TrustWhy", true, false)
	if words == null or why == null:
		_fail("the profile shows no opinion of you")
		return
	why.emit_signal("pressed")
	await _frames(10)
	var reasons: Control = sheet.find_child("TrustReasons", true, false)
	_into_view(reasons)
	await _frames(20)
	print("sheet: ", _text(words))
	_shot(out.path_join("opinion_sheet.png"))
	quit(0)
