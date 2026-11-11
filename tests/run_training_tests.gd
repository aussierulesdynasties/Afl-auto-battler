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
	await _t("_test_stat_focus_tap")
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
			var hero: TextureRect = scene.find_child("TrainingHero", true, false)
			if sz.x < 600:
				# The phone list is compact: the news in a line or two, no picture
				# and no standing explanation, so the cards get the screen.
				_check(trade == null and hero == null,
						"%s: the phone list leaves the picture and the plan line to the intro" % tag)
				scene.queue_free()
				await _settle()
				continue
			_check(trade != null and trade.is_visible_in_tree() and trade.text.contains("what he is developing as decides the stats it buys"),
					"%s: Training says in a line what a plan costs and what it buys (P-63)" % tag)
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
## group bar, and a real tap on a card opens that player.
func _test_training_grid() -> void:
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var ui_kit = load("res://scripts/ui/UiKit.gd")
	gs.reset()
	gs.set_setting("seen_training_intro", true)
	gs.start_season("FRE", db.club_list("FRE"))
	# A long surname, to prove it is never cut.
	gs.my_list[0]["generic_name"] = "Alexander Papaioannou-Featherstone"
	gs.my_list[1]["injury_weeks"] = 3
	root.size = Vector2i(390, 844)
	var scene: Control = load("res://scenes/TrainingScene.tscn").instantiate()
	root.add_child(scene)
	await _settle()
	var grids := scene.find_children("TrainingGrid", "", true, false)
	var rows := []
	for g in grids:
		rows.append_array(g.get_children())
	var two_across := not rows.is_empty()
	var equal_heights := true
	for r in rows:
		var kids: Array = (r as Control).get_children()
		if kids.size() > 2 or kids.is_empty():
			two_across = false
		for k in kids:
			if absf((k as Control).size.y - (kids[0] as Control).size.y) > 0.5:
				equal_heights = false
	_check(two_across, "Grid: players sit in rows of two cells")
	_check(equal_heights, "Grid: the cards in a row are the same height")
	var cards := scene.find_children("Trainee_*", "Button", true, false)
	_check(cards.size() == gs.my_list.size(), "Grid: every listed player has a card (%d of %d)" % [cards.size(), gs.my_list.size()])
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
		if r.position.x < -0.5 or r.end.x > 390.5 or r.size.x < 140.0 or r.size.y < 90.0:
			inside = false
		if card.find_child("ClubBar", true, false) == null:
			club_bar = false
		for slot in ["Position", "Rating", "Name", "Status"]:
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
	# One width for every card (an odd one out keeps a half-width card), a
	# symmetric gutter, and statuses level across a row.
	var widths := {}
	var left_edge := 9999.0
	var right_edge := 0.0
	var level := true
	var level_note := ""
	for r in rows:
		var ys := []
		for k in (r as Control).get_children():
			if k.name == "GridHole":
				continue
			widths[int(roundf((k as Control).size.x))] = true
			left_edge = minf(left_edge, (k as Control).get_global_rect().position.x)
			right_edge = maxf(right_edge, (k as Control).get_global_rect().end.x)
			var stl: Label = k.find_child("Status", true, false)
			if stl != null:
				ys.append(stl.get_global_rect().position.y)
		for y in ys:
			if absf(y - ys[0]) > 1.0:
				level = false
				level_note = "%s vs %s" % [str(y), str(ys[0])]
	# The name and the trait under it sit centred in the room between the top
	# line and his top three, on the same left edge as the status (the old full-width
	# row's name stack sat off centre: CLAUDE.md's confirmed defect).
	var centred := true
	var centred_note := ""
	for c in cards:
		var card3: Control = (c as Button).get_parent()
		var mid: Control = card3.find_child("CardMiddle", true, false)
		var top_line: Control = (card3.find_child("Position", true, false) as Control).get_parent()
		var st3: Label = card3.find_child("Status", true, false)
		var nm3: Label = card3.find_child("Name", true, false)
		if mid == null or st3 == null or nm3 == null:
			centred = false
			centred_note = "%s: no name stack" % card3.name
			continue
		var stack_top := 99999.0
		var stack_end := -99999.0
		for k in mid.get_children():
			stack_top = minf(stack_top, (k as Control).get_global_rect().position.y)
			stack_end = maxf(stack_end, (k as Control).get_global_rect().end.y)
		var room_top := top_line.get_global_rect().end.y
		# His top three sit between the trait and the status (row 150).
		var three3: Control = card3.find_child("TopThree", true, false)
		if three3 == null:
			centred = false
			centred_note = "%s: no top three" % card3.name
			continue
		var room_end := three3.get_global_rect().position.y
		var off := (stack_top + stack_end) * 0.5 - (room_top + room_end) * 0.5
		var left_off := nm3.get_global_rect().position.x - st3.get_global_rect().position.x
		if absf(off) > 1.5 or stack_top < room_top - 0.5 or stack_end > room_end + 0.5 or absf(left_off) > 0.5:
			centred = false
			centred_note = "%s: %.1f off centre, %.1f off the left edge" % [card3.name, off, left_off]
	_check(centred, "Grid: each name and trait sit centred between the top line and the top three, on one left edge (%s)" % centred_note)
	# The names of a row sit at one height, trait under him or not (CLAUDE.md's
	# confirmed name/second-line defect: a traitless card's name sat lower).
	var names_level := true
	var names_note := ""
	for r in rows:
		var nys := []
		for k in (r as Control).get_children():
			var nm4: Label = k.find_child("Name", true, false)
			if nm4 != null:
				nys.append(nm4.get_global_rect().position.y)
		for y in nys:
			if absf(y - nys[0]) > 1.0:
				names_level = false
				names_note = "%s vs %s" % [str(y), str(nys[0])]
	_check(names_level, "Grid: the names sit level across each row, trait or not (%s)" % names_note)
	var lone_rows := 0
	for r in rows:
		if (r as Control).find_child("GridHole", false, false) != null:
			lone_rows += 1
	_check(widths.size() == 1, "Grid: every card is one width, a lone last card too (%s, %d lone)" % [str(widths.keys()), lone_rows])
	_check(absf(left_edge - (390.0 - right_edge)) <= 1.0, "Grid: the cards sit centred, the same margin each side (%.1f left, %.1f right)" % [left_edge, 390.0 - right_edge])
	_check(level, "Grid: the status lines sit level across each row (%s)" % level_note)
	_check(inside, "Grid: every card is inside the screen, at least 140 wide and 90 tall")
	_check(heights.size() == 1, "Grid: every card is the same height (%s)" % str(heights.keys()))
	_check(slots and club_bar, "Grid: every card has the club's colour and the same slots: position, rating, name, status (and a trait when he has one)")
	_check(whole_words, "Grid: no card's words spill out of it or are cut short")
	_check(one_line, "Grid: position, status and trait each stay on one line, and a position is never a slash list")
	_check(small == "", "Grid: every word on a card is 13 or larger (%s)" % small)
	var grey_status := false
	var tint_ok := false
	for c in cards:
		var card2: Control = (c as Button).get_parent()
		var st2: Label = card2.find_child("Status", true, false)
		if st2 != null and st2.get_theme_color("font_color").is_equal_approx(ui_kit.MUTED):
			grey_status = true
		var surface := (card2 as PanelContainer).get_theme_stylebox("panel") as StyleBoxFlat
		if surface != null and not surface.bg_color.is_equal_approx(ui_kit.PANEL_ALT):
			tint_ok = true
	_check(not grey_status, "Grid: no development line is in the dim grey")
	_check(tint_ok, "Grid: the club's colour tints the card as well as its edge")
	_check(shouting == "", "Grid: no all-capitals labels on a card (%s)" % shouting)
	# The long name is whole on its card.
	var long_card := scene.find_child("Card_" + str(gs.my_list[0]["id"]), true, false)
	var long_name: Label = long_card.find_child("Name", true, false) if long_card != null else null
	_check(long_name != null and long_name.text.ends_with("Papaioannou-Featherstone") and long_name.get_line_count() <= 2,
			"Grid: a long surname is shown whole (%s)" % (long_name.text if long_name != null else "no card"))
	var hurt := scene.find_child("Card_" + str(gs.my_list[1]["id"]), true, false)
	var hurt_status: Label = hurt.find_child("Status", true, false) if hurt != null else null
	_check(hurt_status != null and hurt_status.text == "Injured 3 wks", "Grid: an injury reads in sentence case (%s)" % (hurt_status.text if hurt_status != null else "no card"))
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
	_check(tab_ok, "Grid: the role tabs are sentence case and 48 tall (%s)" % str(tab_names))
	var back := scene.find_child("TopBarBack", true, false) as Control
	_check(back != null and back.size.y >= 47.5 and back.size.x >= 47.5, "Grid: Back is a thumb target (%s)" % str(back.size if back != null else "missing"))
	# The words behind the title are opaque, whatever the club.
	var header := scene.find_child("TrainingHeader", true, false) as PanelContainer
	var sb := header.get_theme_stylebox("panel") as StyleBoxFlat if header != null else null
	_check(sb != null and sb.bg_color.a >= 0.99, "Grid: the title and Stat guide sit on an opaque backing")
	# The hint, in words a thumb or a mouse can follow.
	var hint := scene.find_child("GroupHint", true, false) as Label
	_check(hint != null and hint.text.contains("Touch and hold") and not hint.text.contains("Click"), "Grid: the group hint says 'Touch and hold' on a phone (%s)" % (hint.text if hint != null else "missing"))
	# One scroll, the page's: no list scrolling inside a page, and at least
	# three rows of cards in view at the top.
	var scroll := scene.get("_list_scroll") as ScrollContainer
	var scrolls := scene.find_children("*", "ScrollContainer", true, false)
	_check(scrolls.size() == 1 and scroll != null, "Grid: the page is the only scroll (%d scrolling areas)" % scrolls.size())
	var seen_rows := 0
	var row_tops := []
	for r in rows:
		row_tops.append(int((r as Control).get_global_rect().position.y))
	for r in rows:
		if (r as Control).get_global_rect().position.y + 40.0 <= 844.0:
			seen_rows += 1
	# The squad here is small, so also prove a third row would fit: three row
	# pitches below the first row's top still end inside the screen.
	var pitch := 0.0
	if rows.size() >= 2:
		pitch = float(row_tops[1] - row_tops[0])
	var third_fits: bool = rows.size() >= 2 and float(row_tops[0]) + 3.0 * pitch <= 844.0
	_check(seen_rows >= mini(3, rows.size()) and third_fits, "Grid: three rows of cards fit in view before any scrolling (%d in view; tops %s)" % [seen_rows, str(row_tops)])
	var before_y := {}
	for c in cards:
		before_y[c.name] = (c as Control).get_global_rect().position.y
	# The group bar: one outlined row, no extra sentence.
	var first: Button = cards[0]
	var first_id: String = first.name.trim_prefix("Trainee_")
	var second_id: String = str(cards[1].name).trim_prefix("Trainee_")
	var why: String = await Tap.tap(first)
	await _settle()
	_check(why == "" and bool(scene.get("_showing_detail")) and str(scene.get("_selected")) == first_id,
			"Grid: a real tap on a card opens that player (%s)" % why)
	scene.set("_showing_detail", false)
	scene.set("_bulk_selected", {first_id: true, second_id: true})
	scene.call("_build")
	await _settle()
	var bar := scene.find_child("BulkRow", true, false)
	var shifted := ""
	for c in scene.find_children("Trainee_*", "Button", true, false):
		if before_y.has(c.name) and absf((c as Control).get_global_rect().position.y - float(before_y[c.name])) > 0.5 and (c as Control).get_global_rect().position.y < 600.0:
			shifted = "%s moved" % c.name
			break
	_check(shifted == "", "Grid: picking a group moves no card (%s)" % shifted)
	_check(scene.find_children("Ticked", "", true, false).size() == 2, "Grid: each picked player carries a tick")
	var plan_buttons := scene.find_children("GroupPlan_*", "Button", true, false)
	var outlined := not plan_buttons.is_empty()
	for pb in plan_buttons:
		var psb := (pb as Button).get_theme_stylebox("normal") as StyleBoxFlat
		if psb == null or psb.border_width_left < 1 or psb.bg_color.a > 0.01 or (pb as Button).size.y < 47.5:
			outlined = false
	_check(bar != null and outlined, "Grid: the group bar's plans are outlined buttons 48 tall (%d)" % plan_buttons.size())
	var clear_btn := scene.find_child("ClearBulk", true, false) as Button
	_check(clear_btn != null and clear_btn.size.y >= 47.5, "Grid: Clear is 48 tall")
	var worded := true
	for pb in plan_buttons:
		var key: String = str(pb.name).trim_prefix("GroupPlan_")
		if key != "position" and not (pb as Button).text.begins_with("Train as "):
			worded = false
	_check(worded, "Grid: a role plan in the group bar reads 'Train as ...'")
	var sentence := false
	for l in scene.find_children("*", "Label", true, false):
		if (l as Label).text.contains("Apply one development focus"):
			sentence = true
	_check(not sentence, "Grid: the group bar has no sentence explaining itself")
	scene.queue_free()
	await _settle()


## Stat focus (row 97): on a phone, a real tap picks a stat, a second real tap
## locks it in, every target is a thumb tall and inside the screen, and once
## locked the picker is gone until next season.
func _test_stat_focus_tap() -> void:
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	gs.reset()
	gs.replay_seed = 2027
	gs.set_setting("seen_training_intro", true)
	gs.start_season("FRE", db.club_list("FRE"))
	var p: Dictionary = {}
	for q in gs.my_list:
		if gs.project_job(q) == "" and gs.focus_options(q).size() >= 2:
			p = q
			break
	_check(not p.is_empty(), "Stat focus tap: a player with stats to focus on")
	if p.is_empty():
		return
	var id := str(p["id"])
	root.size = Vector2i(390, 844)
	var scene: Control = load("res://scenes/TrainingScene.tscn").instantiate()
	root.add_child(scene)
	await _settle()
	scene.call("_open_player", id)
	await _settle()
	var opts: Array = gs.focus_options(p)
	var key := str(opts[opts.size() - 1])
	var picks: Array = scene.find_children("StatFocusPick_*", "Button", true, false)
	var thumb := picks.size() == opts.size()
	for b in picks:
		var r: Rect2 = (b as Control).get_global_rect()
		if r.size.y < 44.0 or r.position.x < 0.0 or r.end.x > 390.0:
			thumb = false
	_check(thumb, "Stat focus tap: one button per stat he can use (%d of %d), each a thumb tall and on screen" % [picks.size(), opts.size()])
	_check(scene.find_child("StatFocusLock", true, false) == null, "Stat focus tap: nothing to lock in before a stat is picked")
	var pick: Button = scene.find_child("StatFocusPick_" + key, true, false)
	var why: String = await Tap.tap(pick) if pick != null else "no button"
	await _settle()
	_check(why == "" and str(scene.get("_focus_choice")) == key and not gs.focus_locked(gs.list_player(id)),
			"Stat focus tap: a real tap picks %s without locking it (%s)" % [key, why])
	var lock: Button = scene.find_child("StatFocusLock", true, false)
	_check(lock != null and lock.size.y >= 44.0 and lock.text.to_lower().contains(gs.train_stat_label(key).to_lower()),
			"Stat focus tap: a thumb-tall Lock in button names the stat (%s)" % [lock.text if lock != null else "missing"])
	why = await Tap.tap(lock) if lock != null else "no button"
	await _settle()
	var after: Dictionary = gs.list_player(id)
	_check(why == "" and gs.focus_locked(after) and gs.stat_focus(after) == key,
			"Stat focus tap: a real tap on Lock in sets his focus for the season (%s)" % why)
	var locked: Label = scene.find_child("StatFocusLocked", true, false)
	_check(locked != null and locked.is_visible_in_tree() and locked.text.contains(str(int(gs.season_year) + 1))
			and scene.find_children("StatFocusPick_*", "Button", true, false).is_empty(),
			"Stat focus tap: once locked the picker is gone and the page says when it opens again")
	scene.queue_free()
	await _settle()

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
