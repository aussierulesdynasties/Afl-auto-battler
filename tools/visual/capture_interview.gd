extends SceneTree
## Visual review tool for the coach's appointment interview (row 119):
##   godot --path . --script tools/visual/capture_interview.gd -- [--size 960x540]
## Writes <out>_<w>x<h>_{name,question,reveal}.png at 390x844 and 960x540, and
## drives it with real taps (tests/tap.gd): Face the press, an answer to each
## question, then Continue, which must leave for the hub. A windowed run's
## OS window can differ from root.size, so run the taps --headless too.

const Tap := preload("res://tests/tap.gd")


func _initialize() -> void:
	_run.call_deferred()


func _shot(path: String) -> void:
	for i in range(8):
		await process_frame
	if DisplayServer.get_name() == "headless":
		return
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(path)
	print("SHOT ", path)


func _find(n: Node, nm: String) -> Node:
	if n.name == nm:
		return n
	for c in n.get_children():
		var f := _find(c, nm)
		if f != null:
			return f
	return null


func _tap(scene: Node, nm: String) -> bool:
	var c := _find(scene, nm) as Control
	if c == null:
		print("FAIL no ", nm)
		return false
	if DisplayServer.get_name() != "headless":
		(c as BaseButton).pressed.emit()  # images only; the headless run proves the taps
		for i in range(4):
			await process_frame
		return true
	var err: String = await Tap.tap(c)
	if err != "":
		print("FAIL tap ", nm, ": ", err)
		return false
	for i in range(4):
		await process_frame
	return true


func _run() -> void:
	var out := ProjectSettings.globalize_path("res://captures/interview")
	# One size per run: Continue routes on to the hub, which outlives the loop.
	var sizes := [Vector2i(390, 844)]
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--size":
			var wh := str(a[i + 1]).split("x")
			sizes = [Vector2i(int(wh[0]), int(wh[1]))]
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture.save"
	state.settings_path = "user://capture_settings.cfg"
	var ok := true
	for sz in sizes:
		state.reset()
		state.set_setting("seen_weekly_loop_intro", true)
		state.start_season("HAW", db.club_list("HAW"))
		state.interview_due = true
		root.size = sz
		DisplayServer.window_set_size(sz)
		var tag := "%s_%dx%d" % [out, sz.x, sz.y]
		var scene = load("res://scenes/InterviewScene.tscn").instantiate()
		root.add_child(scene)
		await _shot(tag + "_name.png")
		var field := _find(scene, "CoachName") as LineEdit
		field.text = "Sam Kelly"
		field.text_changed.emit(field.text)
		ok = await _tap(scene, "InterviewStart") and ok
		await _shot(tag + "_question.png")
		for q in range(7):
			ok = await _tap(scene, "InterviewAnswer%d" % (q % 2)) and ok
		await _shot(tag + "_reveal.png")
		print("ARCH ", state.coach_arch, " NAME ", state.coach_name)
		ok = await _tap(scene, "InterviewDone") and ok
		for i in range(6):
			await process_frame
		print("AFTER CONTINUE interview_due=", state.interview_due)
		for c in root.get_children():
			if c is Control:
				c.queue_free()
		await process_frame
	print("TAPS ", "OK" if ok else "FAILED")
	quit(0 if ok else 1)
