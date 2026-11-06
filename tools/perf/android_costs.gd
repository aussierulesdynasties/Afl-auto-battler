extends SceneTree
## Android cost probe (2026-11-07): My List tab switch (ms, nodes), a mid-season
## save (ms), and the title screen's save checks. Median of 5 each. Its own save
## and settings files; never the real career.
##   godot --headless --path . --script tools/perf/android_costs.gd

func _initialize() -> void:
	call_deferred("_go")


func _med(a: Array) -> float:
	a.sort()
	return float(a[a.size() / 2]) / 1000.0


func _go() -> void:
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	gs.autosave_enabled = false
	gs.save_path = "user://perf_costs_%d.save" % OS.get_process_id()
	gs.settings_path = "user://perf_costs_%d.cfg" % OS.get_process_id()
	gs.reset()
	gs.career_seed = 4242
	gs.replay_seed = 4242
	gs.start_season("GEE", db.club_list("GEE"))
	gs.stories_on = false
	gs.open_preseason()
	gs.preseason_sim_to_round1()
	for i in range(12):
		gs.advance()
	# A mid-season save (round 12).
	var t := []
	for i in range(5):
		var a := Time.get_ticks_usec()
		gs.save_career()
		t.append(Time.get_ticks_usec() - a)
	print("PERF save_ms %.1f" % _med(t))
	# The title screen's questions of the save.
	t = []
	for i in range(5):
		var a := Time.get_ticks_usec()
		gs.has_saved_career()
		gs.saved_career_meta()
		gs.has_saved_career()
		t.append(Time.get_ticks_usec() - a)
	print("PERF title_checks_ms %.1f" % _med(t))
	# My List on a phone: tab switches after the first visit to each pane.
	root.size = Vector2i(390, 844)
	var scene: Control = (load("res://scenes/ListScene.tscn") as PackedScene).instantiate()
	root.add_child(scene)
	for i in range(4):
		await process_frame
	var press := func(text: String) -> int:
		var b: Button = null
		for n in scene.find_children("*", "Button", true, false):
			if (n as Button).text == text and (n as Button).is_visible_in_tree():
				b = n
		var a := Time.get_ticks_usec()
		b.emit_signal("pressed")
		return Time.get_ticks_usec() - a
	press.call("Full list")
	await process_frame
	press.call("Shape")
	await process_frame
	var ts := []
	var made := []
	var added := [0]
	node_added.connect(func(_n): added[0] += 1)
	for i in range(5):
		var n0: int = added[0]
		ts.append(press.call("Full list"))
		await process_frame
		await process_frame
		ts.append(press.call("Shape"))
		await process_frame
		await process_frame
		made.append(added[0] - n0)
	print("PERF tab_switch_ms %.1f nodes_added_per_round_trip %s" % [_med(ts), str(made)])
	CareerSave.delete(gs.save_path)
	DirAccess.remove_absolute(gs.settings_path)
	quit()
