extends SceneTree
## The almanac's story of the season with its arc sentence (row 145, SeasonTale), for the
## director's look. Fremantle, seeded.
## Needs a real renderer (windowed, through C:/kt/gpu_slot.sh, off screen via override.cfg):
##   godot --windowed --path . --script tools/visual/capture_season_arc.gd -- --out DIR [--size 390x844]
## Writes DIR/<W>x<H>_<page>.png:
##   played: the season as the seed played it, its page written at the season's close;
##   surge, flag, lost_first: that same page with a staged run of results (the ladder line
##   and the win-loss record follow the staged results; the names stay the played season's).
## Prints each story and whether its last line is inside the card. Never touches a real save.

const SEED := 2031
var W := 390
var H := 844
var out := "/tmp/season_arc"
## Loaded in _run: both name autoloads, which do not exist when this script compiles.
var Alm
var Tale


func _initialize() -> void:
	_run.call_deferred()


func _arg(name: String, fallback: String) -> String:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == name:
			return str(a[i + 1])
	return fallback


## Season.results' shape from one letter a round ("-" is our bye).
func _rounds(form: String, rng: RandomNumberGenerator) -> Array:
	var rounds := []
	for i in form.length():
		var rnd := []
		if form[i] != "-":
			var low := 40 + rng.randi() % 60
			var high := low + (0 if form[i] == "D" else 1 + rng.randi() % 50)
			var mine := high if form[i] == "W" else low
			var theirs := low if form[i] == "W" else high
			rnd.append({"home": "FRE", "away": "STK", "score": [mine, theirs]})
		rounds.append(rnd)
	return rounds


## The played page with a staged run of results in place of its own.
func _staged(played: Dictionary, year: int, form: String, finals: String, flag: bool, ladder: int) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	rng.seed = SEED + year
	var e := played.duplicate(true)
	var tag := "GF" if flag else ("" if finals == "" else "EF1")
	e.merge({"year": year, "ladder": ladder, "w": form.count("W"), "l": form.count("L"), "d": form.count("D"),
			"flag": flag, "finals_tag": tag, "finals_text": str(Alm.finals_text(tag, flag, false)),
			"premier": "FRE" if flag else str(played.get("premier", "")), "legends": []}, true)
	e[Alm.ARC_KEY] = Tale.tell(Tale.record(_rounds(form, rng), _rounds(finals, rng), "FRE"), flag)
	e[Alm.PARTS_KEY] = Alm.story_parts(e, {})
	e[Alm.STORY_KEY] = Alm.compose(e[Alm.PARTS_KEY])
	return e


func _shot(scene: Control, year: int, name: String) -> void:
	for i in range(4):
		await process_frame
	var card: Control = scene.find_child("AlmanacSeason_%d" % year, true, false)
	if card == null:
		print("CAPTURE missing the %d page" % year)
		return
	for sc in scene.find_children("*", "ScrollContainer", true, false):
		var box := sc as ScrollContainer
		if box.is_ancestor_of(card):
			box.scroll_vertical += int(card.get_global_rect().position.y - box.get_global_rect().position.y - 12.0)
	for i in range(14):
		await process_frame
	var story: Label = card.find_child("StoryOfTheSeason", true, false)
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	var path := "%s/%dx%d_%s.png" % [out, W, H, name]
	img.save_png(path)
	var inside := story != null and card.get_global_rect().encloses(story.get_global_rect()) \
			and story.get_global_rect().end.x <= float(W) and story.get_visible_line_count() == story.get_line_count()
	print("CAPTURED %s | %d lines, inside the card: %s | %s" % [path,
			story.get_line_count() if story != null else 0, str(inside), story.text if story != null else "(no story)"])


func _run() -> void:
	out = _arg("--out", out)
	var size := _arg("--size", "390x844")
	W = int(size.get_slice("x", 0))
	H = int(size.get_slice("x", 1))
	await process_frame
	Alm = load("res://scripts/sim/Almanac.gd")
	Tale = load("res://scripts/sim/SeasonTale.gd")
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture.save"
	state.settings_path = "user://capture_settings.cfg"
	state.reset()
	state.career_seed = SEED
	state.replay_seed = SEED
	state.start_season("FRE", db.club_list("FRE"))
	state.tutorials = false
	var guard := 0
	while not state.season.is_season_over() and guard < 40:
		state.advance()
		guard += 1
	if state.almanac.is_empty():
		print("CAPTURE the season wrote no page")
		quit(1)
		return
	var played: Dictionary = state.almanac[-1]
	var y := int(played["year"])
	print("PLAYED %d arc: %s" % [y, str(played.get(str(Alm.ARC_KEY), {}))])
	state.almanac.append(_staged(played, y + 1, "LLWLLLWLLWLW-WWLWWWLWWLW", "", false, 10))
	state.almanac.append(_staged(played, y + 2, "WLWWLWWWLWWW-WLWWWWWWWWW", "WWW", true, 1))
	state.almanac.append(_staged(played, y + 3, "LLLLLLLLWLLL-LLWLLLLDLLL", "", false, 18))
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	var alm: Control = load("res://scenes/AlmanacScene.tscn").instantiate()
	root.add_child(alm)
	await _shot(alm, y, "played")
	await _shot(alm, y + 1, "surge")
	await _shot(alm, y + 2, "flag")
	await _shot(alm, y + 3, "lost_first")
	quit(0)
