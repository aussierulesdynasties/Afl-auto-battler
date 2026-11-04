extends SceneTree
## godot --headless --path . --script tests/run_training_tests.gd
## Run a headless editor import first on a fresh clone to register global classes.

const Tap := preload("res://tests/tap.gd")

var _checks := 0
var _failures: Array = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_isolate_saves()
	# A suite that fails to compile must fail the run, not hang it.
	var script = load("res://tests/test_training.gd")
	if script == null or not script.can_instantiate():
		push_error("Could not load res://tests/test_training.gd")
		quit(1)
		return
	var suite = script.new()
	suite.run()
	_checks = suite.checks
	_failures.append_array(suite.failures)
	await _t("_test_training_hero")
	await _t("_test_training_grid")
	print(Ran.line("Training", self, [suite]))
	quit(0 if _failures.is_empty() else 1)


## The training gear on the Training screen (director, 2026-10-14): the real
## picture in the club's wash beside the week's news, never red, no word cut
## short, and a player still opens on a real tap. Without the file the news
## has the panel to itself.
func _test_training_hero() -> void:
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var art = load("res://scripts/ui/UiArt.gd")
	var culture = load("res://scripts/ui/CultureSheet.gd")
	for club in ["FRE", "MEL"]:
		for sz in [Vector2i(390, 844), Vector2i(1280, 720)]:
			var tag := "%s %dx%d" % [club, sz.x, sz.y]
			gs.reset()
			gs.set_setting("seen_training_intro", true)
			gs.start_season(club, db.club_list(club))
			root.size = sz
			var scene: Control = load("res://scenes/TrainingScene.tscn").instantiate()
			root.add_child(scene)
			await _settle()
			var trade: Label = scene.find_child("TrainingTradeOff", true, false)
			_check(trade != null and trade.is_visible_in_tree() and trade.text.contains("costs more as a stat climbs"),
					"%s: Training says in a line what a plan costs and what it buys (P-63)" % tag)
			var hero: TextureRect = scene.find_child("TrainingHero", true, false)
			var tex: Texture2D = hero.texture if hero != null else null
			_check(tex != null and tex.resource_path == "res://assets/ui/models/training_gear.png"
					and float(tex.get_height()) >= 2.0 * hero.size.y and hero.size.y >= 72.0,
					"%s: Training shows the training gear's own picture, sharp at this size (%s)" % [tag, tex.resource_path if tex != null else "missing"])
			if hero == null:
				scene.queue_free()
				await _settle()
				continue
			# Its own colours: orange cones at the foot on the left, never a club's wash.
			var gear := tex.get_image()
			var cone := gear.get_pixel(int(gear.get_width() * 0.2), int(gear.get_height() * 0.8))
			var bag := gear.get_pixel(int(gear.get_width() * 0.68), int(gear.get_height() * 0.45))
			_check(hero.modulate == Color.WHITE and cone.a > 0.9 and cone.h > 0.02 and cone.h < 0.12 and cone.s > 0.6
					and bag.a > 0.9 and bag.h > 0.58 and bag.h < 0.72 and bag.s > 0.6,
					"%s: the gear is in its own colours, orange cones and a blue bag, in no club's wash (%s, %s)" % [tag, cone.to_html(false), bag.to_html(false)])
			var panel: Control = hero.get_parent().get_parent()
			var whole := panel.get_global_rect().grow(0.5).encloses(hero.get_global_rect()) and hero.mouse_filter == Control.MOUSE_FILTER_IGNORE
			var words := 0
			for l in panel.find_children("*", "Label", true, false):
				var lab := l as Label
				if not lab.is_visible_in_tree() or lab.text == "":
					continue
				words += 1
				if lab.size.y + 1.0 < lab.get_combined_minimum_size().y or lab.get_global_rect().intersects(hero.get_global_rect()) 						or not panel.get_global_rect().grow(0.5).encloses(lab.get_global_rect()):
					whole = false
			var first_word: Control = null
			for l in panel.find_children("*", "Label", true, false):
				if (l as Label).is_visible_in_tree() and (l as Label).text != "":
					first_word = l
					break
			var beside := first_word != null and (hero.get_global_rect().end.x <= first_word.global_position.x if sz.x >= 760
					else hero.size.x <= 60.0 and hero.global_position.x >= first_word.get_global_rect().end.x - 1.0)
			_check(whole and words > 0 and beside,
					"%s: the gear stands inside the news panel beside the words (leading them on a PC; no wider than 60 on a phone), takes no tap, and no word is cut short or covered" % tag)
			var row: Button = null
			for b in scene.find_children("Trainee_*", "Button", true, false):
				row = b
				break
			_check(row != null and row.size.y >= 44.0, "%s: a player's row is still a thumb tall (%d)" % [tag, int(row.size.y) if row != null else 0])
			if sz.x < 600 and club == "FRE":
				var why: String = await Tap.tap(row)
				await _settle()
				_check(why == "" and bool(scene.get("_showing_detail")), "%s: a real tap still opens a player (%s)" % [tag, why])
			scene.queue_free()
			await _settle()
	art.dir = "res://assets/ui/no_such_folder"
	root.size = Vector2i(390, 844)
	var plain: Control = load("res://scenes/TrainingScene.tscn").instantiate()
	root.add_child(plain)
	await _settle()
	_check(plain.find_child("TrainingHero", true, false) == null and not plain.find_children("Trainee_*", "Button", true, false).is_empty(),
			"Without the picture Training opens as it did, the list under the news")
	plain.queue_free()
	await _settle()
	art.dir = "res://assets/ui/models"


## Training grid (row 24): two cards across at phone width, every card inside
## the screen, name and development line share a left edge, traits shown, a
## real tap on a card opens that player. Off, the list is the full-width rows.
func _test_training_grid() -> void:
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var features = load("res://scripts/core/Features.gd")
	for on in [false, true]:
		features.set_on("training_grid", on)
		gs.reset()
		gs.set_setting("seen_training_intro", true)
		gs.start_season("FRE", db.club_list("FRE"))
		root.size = Vector2i(390, 844)
		var scene: Control = load("res://scenes/TrainingScene.tscn").instantiate()
		root.add_child(scene)
		await _settle()
		var grids := scene.find_children("TrainingGrid", "GridContainer", true, false)
		if not on:
			_check(grids.is_empty(), "Grid off: Training keeps its full-width rows")
			scene.queue_free()
			await _settle()
			continue
		_check(not grids.is_empty() and (grids[0] as GridContainer).columns == 2, "Grid on: players sit two cards across")
		var cards := scene.find_children("Trainee_*", "Button", true, false)
		_check(cards.size() == gs.my_list.size(), "Grid on: every listed player has a card (%d of %d)" % [cards.size(), gs.my_list.size()])
		var screen := Rect2(Vector2.ZERO, Vector2(390, 844))
		var inside := true
		var aligned := true
		var whole_words := true
		for c in cards:
			var b := c as Button
			var card: Control = b.get_parent()
			var r := card.get_global_rect()
			if r.position.x < -0.5 or r.end.x > 390.5 or r.size.x < 140.0 or r.size.y < 64.0:
				inside = false
			var nm: Label = card.find_child("Name", true, false)
			for l in card.find_children("*", "Label", true, false):
				var lab := l as Label
				if lab.text != "" and lab != nm and lab.size.y + 1.0 < lab.get_combined_minimum_size().y and lab.text_overrun_behavior == TextServer.OVERRUN_NO_TRIMMING:
					whole_words = false
				if lab.text != "" and not card.get_global_rect().grow(0.5).encloses(lab.get_global_rect()):
					# a card that can't hold its words is a fail; rows below the fold are laid out too
					whole_words = false
			var under: Label = null
			for l in card.find_children("*", "Label", true, false):
				if l != nm and (l as Label).text != "" and (l as Label).get_parent() == nm.get_parent() and l.get_index() == nm.get_index() + 1:
					under = l
			if nm == null or under == null or absf(nm.global_position.x - under.global_position.x) > 0.5:
				aligned = false
		_check(inside, "Grid on: every card is inside the screen, at least 140 wide and 64 tall")
		_check(aligned, "Grid on: each card's name and development line share one left edge")
		_check(whole_words, "Grid on: no card's words spill out of it")
		var with_traits := 0
		for c in cards:
			var tr := c.get_parent().find_child("Traits", true, false)
			if tr != null and tr.get_child_count() > 0:
				with_traits += 1
		var expect := 0
		for p in gs.my_list:
			if not Traits.of(p).is_empty():
				expect += 1
		_check(with_traits == expect and expect > 0, "Grid on: a card shows his traits (%d of %d with traits)" % [with_traits, expect])
		var first: Button = cards[0]
		var first_id: String = first.name.trim_prefix("Trainee_")
		var why: String = await Tap.tap(first)
		await _settle()
		_check(why == "" and bool(scene.get("_showing_detail")) and str(scene.get("_selected")) == first_id,
				"Grid on: a real tap on a card opens that player (%s)" % why)
		scene.queue_free()
		await _settle()
	features.clear("training_grid")


func _settle() -> void:
	for i in range(6):
		await process_frame


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


## Never touch a real career save or settings file from a test run.

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)
func _isolate_saves() -> void:
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_career.save"
	gs.settings_path = "user://test_settings.cfg"
	# Return visits: the first-visit intros (FirstVisitIntro.gd) have their own suite.
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		gs.set_setting("seen_%s_intro" % key, true)
	gs.show_real_names = false
