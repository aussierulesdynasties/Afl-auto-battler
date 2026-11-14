extends SceneTree
## Traits up to five (director, 2026-11-12), for the director's look. Real renderer,
## through C:/kt/gpu_slot.sh:
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_traits_five.gd
## Environment: CAP_W, CAP_H (default 390x844), CAP_OUT (prefix, default "traits_five").
## Melbourne, the 2026 lists. Saves <prefix>_sheet.png (the player sheet of the
## Melbourne man with the most good traits) and <prefix>_near.png (Max Gawn's
## Training page with a durability focus picked: the near-trait line).
## Illustrative only; it never touches a real save.

const OTHER := ["unicorn", "wet_weather", "fine_wine", "hothead"]


func _initialize() -> void:
	_run.call_deferred()


var traits
var kit
var sheet


func _good(p: Dictionary) -> int:
	var n := 0
	for t in traits.of(p):
		if not OTHER.has(str(t)) and not traits.is_bad(str(t)):
			n += 1
	return n


func _run() -> void:
	await process_frame
	traits = load("res://scripts/sim/Traits.gd")
	kit = load("res://scripts/ui/UiKit.gd")
	sheet = load("res://scripts/ui/PlayerSheet.gd")
	OS.low_processor_usage_mode = false
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	state.autosave_enabled = false
	state.save_path = "user://capture_traits_five.save"
	state.settings_path = "user://capture_traits_five.cfg"
	state.replay_seed = 2027
	db.reload()
	state.reset()
	state.start_season("MEL", db.club_list("MEL"))
	state.set_setting("seen_training_intro", true)
	var w := int(OS.get_environment("CAP_W")) if OS.get_environment("CAP_W") != "" else 390
	var h := int(OS.get_environment("CAP_H")) if OS.get_environment("CAP_H") != "" else 844
	var prefix := OS.get_environment("CAP_OUT") if OS.get_environment("CAP_OUT") != "" else "traits_five"
	DisplayServer.window_set_size(Vector2i(w, h))
	root.size = Vector2i(w, h)
	# Every Melbourne man's good traits, for the record.
	var best: Dictionary = {}
	for q in state.my_list:
		var n := _good(q)
		if n > 0:
			print("TRAITS %s %d %s" % [db.player_display_name(q), n, str(traits.of(q))])
		if best.is_empty() or n > _good(best):
			best = q
	var gawn: Dictionary = {}
	for q in state.my_list:
		if str(q.get("real_name", q.get("name", ""))).contains("Gawn"):
			gawn = q
	# 1. The player sheet.
	var host := ColorRect.new()
	host.color = kit.BG
	root.add_child(host)
	host.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	sheet.open(host, best)
	await _frames(10)
	await _save(prefix + "_sheet.png")
	print("SHEET %s %d good: %s" % [db.player_display_name(best), _good(best), str(traits.of(best))])
	host.queue_free()
	await _frames(2)
	# 2. Gawn's Training page, a durability focus picked.
	if gawn.is_empty():
		print("NO GAWN")
		quit()
		return
	print("GAWN durability %d traits %s near %s" % [int(gawn["attr"]["durability"]), str(traits.of(gawn)), str(traits.near(gawn))])
	router.go("training")
	await _frames(8)
	for i in range(120):
		if current_scene != null and current_scene.has_method("_open_player"):
			break
		await process_frame
	var scene = current_scene
	scene.call("_open_player", str(gawn["id"]))
	await _frames(6)
	if state.focus_options(gawn).has("durability"):
		scene.set("_focus_choice", "durability")
		scene.call("_build")
		await _frames(6)
	var line: Control = scene.find_child("StatFocusTrait", true, false)
	print("NEAR LINE: ", (line as Label).text if line is Label else "(none)")
	var sc: ScrollContainer = scene.get("_detail_scroll")
	# His page's head: the trait words under his name.
	if sc != null:
		sc.scroll_vertical = 0
	await _frames(4)
	await _save(prefix + "_chips.png")
	if line != null and sc != null:
		sc.scroll_vertical = maxi(0, int(line.global_position.y - sc.global_position.y) + sc.scroll_vertical - 260)
	await _frames(4)
	await _save(prefix + "_near.png")
	print("CAPTURE saved ", prefix, " at ", w, "x", h)
	quit()


func _save(path: String) -> void:
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(path)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame
