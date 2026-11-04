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


## Training grid (row 24, critic round 2026-11-04): two cards across at phone
## width in rows of equal height, every card inside the screen, the same four
## slots on every card, sentence-case words a thumb can read, tabs and back a
## thumb tall, the club's colour on each card, an opaque header, an outlined
## group bar, and a real tap on a card opens that player. Off, the list is the
## full-width rows.
func _test_training_grid() -> void:
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var features = load("res://scripts/core/Features.gd")
	for on in [false, true]:
		features.set_on("training_grid", on)
		gs.reset()
		gs.set_setting("seen_training_intro", true)
		gs.start_season("FRE", db.club_list("FRE"))
		if on:
			# A long surname, to prove it is never cut.
			gs.my_list[0]["generic_name"] = "Alexander Papaioannou-Featherstone"
			gs.my_list[1]["injury_weeks"] = 3
		root.size = Vector2i(390, 844)
		var scene: Control = load("res://scenes/TrainingScene.tscn").instantiate()
		root.add_child(scene)
		await _settle()
		var grids := scene.find_children("TrainingGrid", "", true, false)
		if not on:
			_check(grids.is_empty(), "Grid off: Training keeps its full-width rows")
			scene.queue_free()
			await _settle()
			continue
		var rows := scene.find_children("GridRow", "HBoxContainer", true, false)
		var two_across := not rows.is_empty()
		var equal_heights := true
		for r in rows:
			var kids: Array = (r as Control).get_children()
			if kids.size() > 2 or kids.is_empty():
				two_across = false
			for k in kids:
				if absf((k as Control).size.y - (kids[0] as Control).size.y) > 0.5:
					equal_heights = false
		_check(two_across, "Grid on: players sit in rows of two cards, none left with a hole beside it")
		_check(equal_heights, "Grid on: the cards in a row are the same height")
		var cards := scene.find_children("Trainee_*", "Button", true, false)
		_check(cards.size() == gs.my_list.size(), "Grid on: every listed player has a card (%d of %d)" % [cards.size(), gs.my_list.size()])
		var inside := true
		var whole_words := true
		var one_line := true
		var small := ""
		var shouting := ""
		var club_bar := true
		var slots := true
		var heights := {}
		for c in cards:
			var card: Control = (c as Button).get_parent()
			var r := card.get_global_rect()
			heights[int(roundf(r.size.y))] = true
			if r.position.x < -0.5 or r.end.x > 390.5 or r.size.x < 140.0 or r.size.y < 100.0:
				inside = false
			if card.find_child("ClubBar", true, false) == null:
				club_bar = false
			for slot in ["Position", "Rating", "Name", "Status", "Trait"]:
				if card.find_child(slot, true, false) == null:
					slots = false
			var nm: Label = card.find_child("Name", true, false)
			for l in card.find_children("*", "Label", true, false):
				var lab := l as Label
				if lab.text == "":
					continue
				if not card.get_global_rect().grow(0.5).encloses(lab.get_global_rect()):
					whole_words = false
				var fs := lab.get_theme_font_size("font_size")
				if fs < 13 and small == "":
					small = "%s at %d" % [lab.text, fs]
				if lab.text != lab.text.to_lower() and lab.text == lab.text.to_upper() and lab.text.length() > 3 and shouting == "":
					shouting = lab.text
				if lab != nm and lab.get_line_count() > 1:
					one_line = false
			# The name is whole: no ellipsis, no word cut, at most two lines.
			if nm != null and (nm.text.ends_with("...") or nm.text.ends_with("…") or nm.get_line_count() > 2):
				whole_words = false
			var pos: Label = card.find_child("Position", true, false)
			if pos != null and pos.text.contains("/"):
				one_line = false
		_check(inside, "Grid on: every card is inside the screen, at least 140 wide and 100 tall")
		_check(heights.size() == 1, "Grid on: every card is the same height (%s)" % str(heights.keys()))
		_check(slots and club_bar, "Grid on: every card has the club's colour and the same slots: position, rating, name, status, trait")
		_check(whole_words, "Grid on: no card's words spill out of it or are cut short")
		_check(one_line, "Grid on: position, status and trait each stay on one line, and a position is never a slash list")
		_check(small == "", "Grid on: every word on a card is 13 or larger (%s)" % small)
		_check(shouting == "", "Grid on: no all-capitals labels on a card (%s)" % shouting)
		# The long name is whole on its card.
		var long_card := scene.find_child("Card_" + str(gs.my_list[0]["id"]), true, false)
		var long_name: Label = long_card.find_child("Name", true, false) if long_card != null else null
		_check(long_name != null and long_name.text.ends_with("Papaioannou-Featherstone") and long_name.get_line_count() <= 2,
				"Grid on: a long surname is shown whole (%s)" % (long_name.text if long_name != null else "no card"))
		var hurt := scene.find_child("Card_" + str(gs.my_list[1]["id"]), true, false)
		var hurt_status: Label = hurt.find_child("Status", true, false) if hurt != null else null
		_check(hurt_status != null and hurt_status.text == "Injured 3 wks", "Grid on: an injury reads in sentence case (%s)" % (hurt_status.text if hurt_status != null else "no card"))
		# Tabs in sentence case, a thumb tall; back and Stat guide too.
		var tabs := scene.find_child("RoleTabs", true, false)
		var tab_ok := tabs != null and tabs.get_child_count() == 5
		var tab_names := []
		if tabs != null:
			for t in tabs.get_children():
				var tb := t as Button
				tab_names.append(tb.text)
				if tb.size.y < 47.5 or tb.text != tb.text.capitalize():
					tab_ok = false
		_check(tab_ok, "Grid on: the role tabs are sentence case and 48 tall (%s)" % str(tab_names))
		var back := scene.find_child("TopBarBack", true, false) as Control
		_check(back != null and back.size.y >= 47.5 and back.size.x >= 47.5, "Grid on: Back is a thumb target (%s)" % str(back.size if back != null else "missing"))
		# The words behind the title are opaque, whatever the club.
		var header := scene.find_child("TrainingHeader", true, false) as PanelContainer
		var sb := header.get_theme_stylebox("panel") as StyleBoxFlat if header != null else null
		_check(sb != null and sb.bg_color.a >= 0.99, "Grid on: the title and Stat guide sit on an opaque backing")
		# The hint, in words a thumb or a mouse can follow.
		var hint := scene.find_child("GroupHint", true, false) as Label
		_check(hint != null and hint.text.contains("Touch and hold") and not hint.text.contains("Click"), "Grid on: the group hint says 'Touch and hold' on a phone (%s)" % (hint.text if hint != null else "missing"))
		# At least three rows of cards on screen at once.
		var scroll := scene.get("_list_scroll") as ScrollContainer
		var one_row := 0.0
		if not rows.is_empty():
			one_row = (rows[0] as Control).size.y
		_check(scroll != null and one_row > 0.0 and scroll.size.y >= 3.0 * one_row + 12.0,
				"Grid on: three rows of cards show without scrolling (%d tall for rows of %d)" % [int(scroll.size.y) if scroll != null else 0, int(one_row)])
		# The group bar: one outlined row, no extra sentence.
		var first: Button = cards[0]
		var first_id: String = first.name.trim_prefix("Trainee_")
		var second_id: String = str(cards[1].name).trim_prefix("Trainee_")
		var why: String = await Tap.tap(first)
		await _settle()
		_check(why == "" and bool(scene.get("_showing_detail")) and str(scene.get("_selected")) == first_id,
				"Grid on: a real tap on a card opens that player (%s)" % why)
		scene.set("_showing_detail", false)
		scene.set("_bulk_selected", {first_id: true, second_id: true})
		scene.call("_build")
		await _settle()
		var bar := scene.find_child("BulkRow", true, false)
		var plan_buttons := scene.find_children("GroupPlan_*", "Button", true, false)
		var outlined := not plan_buttons.is_empty()
		for pb in plan_buttons:
			var psb := (pb as Button).get_theme_stylebox("normal") as StyleBoxFlat
			if psb == null or psb.border_width_left < 1 or psb.bg_color.a > 0.01 or (pb as Button).size.y < 44.0:
				outlined = false
		_check(bar != null and outlined, "Grid on: the group bar's plans are outlined buttons a thumb tall (%d)" % plan_buttons.size())
		var sentence := false
		for l in scene.find_children("*", "Label", true, false):
			if (l as Label).text.contains("Apply one development focus"):
				sentence = true
		_check(not sentence, "Grid on: the group bar has no sentence explaining itself")
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
