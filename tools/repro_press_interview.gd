extends SceneTree
## Repro (row 141): does each start mode reach the press interview? Drives the
## real screens through Router: New career -> draft -> pre-season -> hub, and
## logs interview_due and the screen at each step.
##   godot --headless --path . --script tools/repro_press_interview.gd

var state
var router


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _log(mode: String, step: String) -> void:
	print("REPRO %-26s %-34s due=%s club=%s coach='%s' arch=%s screen=%s preseason=%s" % [
			mode, step, state.interview_due, state.my_club, state.coach_name,
			not (state.coach_arch as Dictionary).is_empty(), router.current(), state.preseason_active()])


func _wait_route(want: String) -> void:
	for i in range(3000):
		if router.current() == want and not root.get_node("ScreenTransition").busy:
			break
		await process_frame
	await _frames(4)


func _run() -> void:
	state = root.get_node("GameState")
	router = root.get_node("Router")
	state.autosave_enabled = false
	state.save_path = "user://repro_interview.save"
	state.settings_path = "user://repro_interview.cfg"
	await _frames(2)
	for st in [["League redraft", "redraft", "none", false],
			["Real 2026 lists", "real", "none", false],
			["Real lists + Canberra", "real", "none", true],
			["Rebuild", "real", "rebuild", false]]:
		var mode := str(st[0])
		state.reset()
		state.replay_seed = 0 if bool(st[3]) else 4410
		state.tutorials = false
		router.stack = []
		router.go("main")
		await _wait_route("main")
		var menu = current_scene
		menu._on_new_career()
		menu.set("_pick_start", str(st[1]))
		menu.set("_pick_challenge", str(st[2]))
		menu.set("_pick_canberra", bool(st[3]))
		menu.set("_pick_tutorials", false)
		_log(mode, "setup")
		menu._start_new_career()
		_log(mode, "after start (Main sets it)")
		await _wait_route("draft")
		var ds = current_scene
		_log(mode, "draft opened")
		if state.my_club == "":
			var code := "CANB" if bool(st[3]) else ("FRE" if ds._draft.clubs.has("FRE") else str(ds._draft.clubs[0]))
			ds._on_club_chosen(code)
			await _frames(4)
		_log(mode, "club chosen")
		# Finish the draft as its own buttons do: every remaining pick made.
		var d = state.draft
		var guard := 0
		while not d.is_finished() and guard < 200:
			guard += 1
			var board: Array = d.board("", "", "", "overall", true).filter(func(p): return d.can_pick_player(p))
			if board.is_empty():
				break
			ds._on_pick(board[0])
			await process_frame
		print("REPRO %s draft is_finished=%s after %d picks" % [mode, d.is_finished(), guard])
		ds._on_finish()
		await _frames(6)
		await _frames(30)
		_log(mode, "draft finished")
		if router.current() == "preseason":
			state.preseason_sim_to_round1()
			router.replace("hub")
			await _frames(30)
			_log(mode, "pre-season simmed")
		# Save and reload, as a player closing the game would.
		state.autosave_enabled = true
		state.autosave()
		state.autosave_enabled = false
		state.reset()
		state.load_career()
		_log(mode, "after reload")
	quit(0)
