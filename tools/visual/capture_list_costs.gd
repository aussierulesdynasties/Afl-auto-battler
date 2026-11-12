extends SceneTree
## Visual review tool for the list costs' Gain / Cost rows (row T1.R26 L4,
## director 2026-11-10): a retiree you can ask to go around again, contract
## talks with an offer under his ask, and the release confirmation for a player
## with seasons left. Windowed:
##   godot --windowed --path . --script tools/visual/capture_list_costs.gd -- --out <prefix> --size 390x844
## Writes <prefix>_retire.png, <prefix>_haggle.png (a small haggle), <prefix>_haggle_floor.png (his
## floor), <prefix>_insult.png, <prefix>_release.png.
## A fresh Melbourne career at the off-season. Never touches a real save.

var _w := 390
var _h := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	var out := "list_costs"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	var feel = load("res://scripts/ui/Feel.gd")
	var RT = load("res://scripts/sim/Retirement.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_list_costs.save"
	state.settings_path = "user://capture_list_costs.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	UK.apply_appearance("dark")
	root.size = Vector2i(_w, _h)
	# No hover tooltips from the idle mouse: the tool drives the screen by calls.
	root.gui_disable_input = true
	DisplayServer.window_set_size(Vector2i(_w, _h))
	feel.force_phone = _w < _h
	state.reset()
	state.career_seed = 2026
	state.replay_seed = 2026
	state.start_season("MEL", db.club_list("MEL"))
	state.tutorials = false
	state.season.round_index = state.season.fixture.size()
	state.open_offseason()
	var year: int = state.season_year + 1
	# A veteran who would retire but is fit to be asked again.
	var vets: Array = state.my_list.duplicate()
	vets.sort_custom(func(x, y): return float(x.get("age", 0)) > float(y.get("age", 0)))
	var retiree := ""
	for p in vets:
		if float(p.get("age", 0)) < 30.0:
			break
		var before = p.get("retiring", 0)
		p["retiring"] = year
		if RT.can_ask(p, state.my_list, year):
			retiree = str(p["id"])
			# A season in the side, so the 40% ask shows (not a certain no).
			state.season_tally[retiree] = {"games": 18}
			break
		p["retiring"] = before
	# Your own player out of contract, for the talks; one with seasons left, to release.
	var talk_id := ""
	var release_p := {}
	var by_pay: Array = state.my_list.duplicate()
	by_pay.sort_custom(func(x, y): return int(x.get("salary", 0)) > int(y.get("salary", 0)))
	for p in by_pay:
		var left := int(p.get("contract_years", 1)) - 1
		if talk_id == "" and left <= 0 and str(p["id"]) != retiree:
			talk_id = str(p["id"])
		if release_p.is_empty() and left >= 2 and str(p["id"]) != retiree:
			release_p = p
	print("LISTCOSTS retiree=%s talk=%s release=%s" % [retiree, talk_id, str(release_p.get("id", ""))])
	var bg := ColorRect.new()
	bg.color = UK.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(bg)
	var off = load("res://scenes/OffseasonScene.tscn").instantiate()
	root.add_child(off)
	off.set("_tab", "contracts")
	off.call("_build")
	await _frames(6)
	if retiree != "":
		var cards: Array = off.find_children("Retiring_*", "", true, false)
		await _shot(off, "Retiring_%s/AskCost" % retiree, str(cards[0].name) if not cards.is_empty() else "Retiring_" + retiree, "%s_retire.png" % out)
	if talk_id != "":
		off.call("_open_talks", talk_id)
		await _frames(4)
		# Talks open at his ask: offer his floor (he signs, stung), then an insult.
		var CT = load("res://scripts/sim/Contracts.gd")
		var tp: Dictionary = state.list_player(talk_id)
		var yrs := int(off.get("_offer_years"))
		var floor_price: int = CT.lowest(tp, yrs) - state.culture_resign_discount(state.my_club, tp, yrs)
		# A small haggle first ($5k under his ask: a part sting), then his
		# floor (the full one).
		var ask: int = CT.asking_salary(tp)
		off.set("_offer_salary", maxi(floor_price, ask - 5000))
		off.call("_show_talks")
		await _shot(off, "HaggleCost", "HaggleGain", "%s_haggle.png" % out)
		off.set("_offer_salary", floor_price)
		off.call("_show_talks")
		await _shot(off, "HaggleCost", "HaggleGain", "%s_haggle_floor.png" % out)
		off.set("_offer_salary", int(floor_price * 0.6 / CT.SALARY_STEP) * CT.SALARY_STEP)
		off.call("_show_talks")
		await _shot(off, "HaggleCost", "HaggleGain", "%s_insult.png" % out)
		off.call("_close_talks")
		off.call("_build")
		await _frames(4)
	if not release_p.is_empty():
		off.call("_confirm_release", release_p)
		await _frames(10)
		print("LISTCOSTS release gain=%s" % str(off.find_child("ReleaseGain", true, false) != null))
		await _save("%s_release.png" % out)
	quit(0)


## Scroll so `last` sits near the bottom with `first` in view, then save.
func _shot(off: Node, last: String, first: String, path: String) -> void:
	await _frames(8)
	var target: Control = null
	if last.contains("/"):
		var holder := off.find_child(last.get_slice("/", 0), true, false)
		target = holder.find_child(last.get_slice("/", 1), true, false) if holder != null else null
	else:
		target = off.find_child(last, true, false)
	var top: Control = off.find_child(first, true, false)
	print("LISTCOSTS %s found=%s" % [last, str(target != null)])
	var box: ScrollContainer = null
	var up: Node = target
	while up != null and box == null:
		up = up.get_parent()
		box = up as ScrollContainer
	if target != null and box != null:
		# `first` at the top if `last` still fits below it, else `last` at the bottom.
		var y0 := box.global_position.y - box.scroll_vertical
		var s := (top if top != null else target).global_position.y - y0 - 8
		var bottom := target.global_position.y + target.size.y - y0
		if bottom - s > box.size.y - 8:
			s = bottom - box.size.y + 8
		box.scroll_vertical = maxi(0, int(s))
	await _frames(8)
	await _save(path)


func _save(path: String) -> void:
	await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)
