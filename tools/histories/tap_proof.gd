extends SceneTree
## Real taps through a new career, timed from the last tap to Choose your club
## (or Tasmania's draft), with histories or live.
##   godot --path . --script tools/histories/tap_proof.gd -- <canberra|tasmania> [--live]
## Windowed, because the taps go through the viewport. Writes to a temp save.

const Tap := preload("res://tests/tap.gd")


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	var router = root.get_node("Router")
	gs.save_path = "user://tap_proof_career.save"
	gs.settings_path = "user://tap_proof_settings.cfg"
	gs.delete_saved_career()
	gs.set_setting("seen_draft_intro", true)
	if OS.get_cmdline_user_args().has("--live"):
		gs.replay_seed = 1
	var canberra: bool = OS.get_cmdline_user_args()[0] == "canberra"
	root.size = Vector2i(390, 844)
	change_scene_to_file("res://scenes/Main.tscn")
	await _frames(20)
	_tap("NewCareer")
	await _frames(20)
	await _tap_wait("StartMode_real")
	await _tap_wait("Canberra_yes" if canberra else "Canberra_no")
	var t0 := Time.get_ticks_msec()
	await _tap_wait("StartCareer")
	if canberra:
		await _until(func(): return gs.choosing_club() and _found("Choose_MEL") != null)
		print("TAP canberra choose open ms ", Time.get_ticks_msec() - t0, " year ", gs.season_year)
		await _tap_wait("Choose_MEL")
		await _frames(10)
		print("TAP club ", gs.my_club, " user_club ", gs.draft.user_club, " saved ", gs.has_saved_career())
	else:
		await _until(func(): return _found("Choose_TAS") != null)
		await _frames(6)
		await _tap_wait("Choose_TAS")
		await _frames(8)
		t0 = Time.get_ticks_msec()
		await _tap_wait("WaitGo")
		await _until(func(): return gs.my_club == "TAS" and current_scene != null and current_scene.name != "Main")
		print("TAP tasmania draft open ms ", Time.get_ticks_msec() - t0, " year ", gs.season_year)
		print("TAP club ", gs.my_club, " user_club ", gs.draft.user_club, " saved ", gs.has_saved_career())
	gs.delete_saved_career()
	quit(0)


func _found(n: String) -> Control:
	return current_scene.find_child(n, true, false) as Control if current_scene != null else null


func _tap(n: String) -> void:
	var c := _found(n)
	if c == null:
		push_error("TAP missing " + n)
		quit(1)
		return
	c.emit_signal("pressed")


func _tap_wait(n: String) -> void:
	var c := _found(n)
	if c == null:
		print("TAP missing ", n)
		quit(1)
		return
	var p := c.get_parent()
	while p != null:
		if p is ScrollContainer:
			(p as ScrollContainer).ensure_control_visible(c)
		p = p.get_parent()
	await _frames(4)
	var why: String = await Tap.tap(c)
	print("TAP ", n, " ", "ok" if why == "" else why)
	await _frames(6)


func _until(cond: Callable) -> void:
	var t0 := Time.get_ticks_msec()
	while not cond.call() and Time.get_ticks_msec() - t0 < 400000:
		await process_frame


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame
