extends SceneTree
## Visual review tool for the expansion veterans' history (T3.F defect, PR 1126):
## the player profile of players on Tasmania's state-league foundation list,
## opened over the hub of a Fremantle career. Needs a real renderer and a window
## (keep it off screen with an override.cfg). Never touches a real save.
##   godot --path . --script tools/visual/capture_veteran_provenance.gd -- --out <prefix> [--size 390x844] [--seed 7]
## Writes <prefix>_<n>_<who>.png: a veteran from a VFL club, a veteran from a
## TSL club, and a teenager still from the Talent League.

var _w := 390
var _h := 844
var _seed := 7
var _out := "veteran_provenance"


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out":
				_out = str(a[i + 1])
			"--seed":
				_seed = int(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	state.autosave_enabled = false
	state.save_path = "user://capture_veteran_provenance.save"
	state.settings_path = "user://capture_veteran_provenance.cfg"
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	state.set_setting("seen_weekly_loop_intro", true)
	state.set_setting("tutorials", false)
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	state.set_vignettes_on(false)
	state.reset()
	state.career_seed = _seed
	state.replay_seed = _seed
	state.start_season("FRE", db.club_list("FRE"))
	var build = load("res://scripts/state/ExpansionBuild.gd")
	build.ensure_foundation(state, "TAS")
	var list: Array = build.list_of(state, "TAS")
	var profile = load("res://scripts/sim/PlayerProfile.gd")
	for p in list:
		print("%s age %.1f | %s | %s" % [db.player_display_name(p), float(p["age"]),
				profile.pedigree(p), profile.production(p)["title"]])
	var picks := [
		["vfl_veteran", func(p): return float(p["age"]) >= 20.0 and str(p.get("draft_league", "")) == "VFL"],
		["tsl_veteran", func(p): return float(p["age"]) >= 25.0 and str(p.get("draft_league", "")) == "TSL"],
		["talent_league_teen", func(p): return float(p["age"]) < 20.0 and str(p.get("draft_league", "")) == "Talent League"],
	]
	router.go("hub")
	var guard := 0
	# The screen transition swaps the scene under a cover: wait for the hub,
	# then for the cover to clear.
	while guard < 600 and (root.get_tree().current_scene == null
			or not str(root.get_tree().current_scene.scene_file_path).to_lower().contains("hub")):
		guard += 1
		await process_frame
	await _frames(90)
	var n := 0
	for pick in picks:
		var who: Dictionary = {}
		for p in list:
			if (pick[1] as Callable).call(p):
				who = p
				break
		if who.is_empty():
			print("none for ", pick[0])
			continue
		n += 1
		var host: Control = root.get_tree().current_scene
		var sheet: Control = load("res://scripts/ui/PlayerSheet.gd").open(host, who)
		await _frames(8)
		# Bring his record (the "<league> season" line) into view.
		var title := str(profile.production(who)["title"])
		var target: Control = null
		for c in sheet.find_children("*", "Label", true, false):
			if (c as Label).text == title:
				target = c
				break
		if target != null:
			var sc: Node = target.get_parent()
			while sc != null and not (sc is ScrollContainer):
				sc = sc.get_parent()
			if sc != null:
				(sc as ScrollContainer).ensure_control_visible(target)
		print("shot %d %s: %s, %.1f, '%s' found=%s" % [n, pick[0], db.player_display_name(who),
				float(who["age"]), title, target != null])
		await _frames(8)
		var img := root.get_viewport().get_texture().get_image()
		var path := "%s_%d_%s.png" % [_out, n, pick[0]]
		img.save_png(path)
		print("wrote ", path)
		sheet.queue_free()
		await _frames(4)
	quit()
