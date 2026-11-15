extends SceneTree
## Copy voice pass 8 (contracts and trades, director 2026-11-10: option B) captures, phone portrait
## 390x844, a fresh Fremantle career fast-forwarded to the off-season; never touches a real save.
## One launch writes every state whose copy the pass changed, so the same script gives the before
## (on the base) and the after. Needs a real renderer:
##   godot --path . --script tools/visual/capture_copy_voice_contracts.gd -- --out <prefix> [--only a,b]
## Writes <prefix>_<state>.png for: offseason_intro, contracts, whole_list, talks, talks_intro,
## release, agents, fa_talks, trade, trade_intro, trade_offers, budget, staff, staff_intro,
## draft_trade, draft_trade_intro.

const CLUB := "FRE"
var _out := "copy_voice_contracts"
var _only: PackedStringArray = []
var _state: Node
var _db: Node
var _router: Node
var _keys: Array = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			_out = str(a[i + 1])
		elif str(a[i]) == "--only":
			_only = str(a[i + 1]).split(",")
	await process_frame
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_router = root.get_node("Router")
	_state.autosave_enabled = false
	_state.save_path = "user://capture_copy_voice_contracts.save"
	_state.settings_path = "user://capture_copy_voice_contracts.cfg"
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	root.size = Vector2i(390, 844)
	DisplayServer.window_set_size(Vector2i(390, 844))
	_keys = load("res://scripts/ui/FirstVisitIntro.gd").TEXT.keys()

	if _want("offseason_intro"):
		_fresh(["offseason"])
		await _go("offseason", "Offseason")
		await _shot("offseason_intro")

	if _want("contracts") or _want("whole_list") or _want("talks") or _want("release") or _want("talks_intro"):
		_fresh([])
		var ui: Node = await _go("offseason", "Offseason")
		await _scroll_to(ui, "OutOfContractHead")
		await _shot("contracts")
		await _scroll_to(ui, "Retiring_*")
		await _shot("whole_list")
		var who := _expiring_id(ui)
		print("talks with: ", who)
		if who != "":
			ui.call("_open_talks", who)
			await _frames(12)
			await _shot("talks")
			ui.call("_close_talks")
			await _frames(4)
			_state.tutorials = true
			_state.set_setting("seen_contracts_intro", false)
			ui.call("_open_talks", who)
			await _frames(12)
			await _shot("talks_intro")
			_state.tutorials = false
			for o in ui.find_children("ContractsIntro*", "Control", true, false):
				o.queue_free()
			ui.call("_close_talks")
			await _frames(4)
		ui.call("_confirm_release", _state.my_list[_state.my_list.size() - 1])
		await _frames(10)
		await _shot("release")
		ui.call("_close_release")

	if _want("agents") or _want("fa_talks"):
		_fresh([])
		var ui2: Node = await _go("offseason", "Offseason")
		ui2.set("_tab", "agents")
		ui2.call("_build")
		await _frames(10)
		await _shot("agents")
		if not _state.free_agents.is_empty():
			var fa: Dictionary = _state.free_agents[0]
			ui2.call("_open_talks", str(fa["id"]), true)
			await _frames(6)
			var want: Dictionary = load("res://scripts/sim/Contracts.gd").wants(fa)
			ui2.call("_make_offer", int(want["salary"]), int(want["years"]))
			await _frames(12)
			await _shot("fa_talks")

	if _want("trade") or _want("trade_intro") or _want("trade_offers"):
		_fresh([])
		var ui3: Node = await _go("offseason", "Offseason")
		ui3.set("_tab", "trade")
		var rival := str(ui3.get("_trade_club"))
		var theirs: Array = _state.season.lists[rival]
		ui3.set("_mine", [str(_state.my_list[_state.my_list.size() - 2]["id"])])
		ui3.set("_theirs", [str(theirs[3]["id"])])
		ui3.call("_build")
		await _frames(12)
		await _shot("trade_offers")
		await _scroll_to(ui3, "TradeClub")
		await _shot("trade")
		_state.tutorials = true
		_state.set_setting("seen_trade_intro", false)
		ui3.call("_build")
		load("res://scripts/ui/FirstVisitIntro.gd").show_if_due(ui3, "trade")
		await _frames(12)
		await _shot("trade_intro")
		_state.tutorials = false

	if _want("budget"):
		_fresh([])
		var ui4: Node = await _go("offseason", "Offseason")
		ui4.set("_tab", "budget")
		ui4.call("_build")
		await _frames(10)
		await _shot("budget")

	if _want("staff"):
		_fresh([])
		await _go("staff", "Staff")
		await _shot("staff")
	if _want("staff_intro"):
		_fresh(["staff"])
		await _go("staff", "Staff")
		await _shot("staff_intro")

	if _want("draft_trade") or _want("draft_trade_intro"):
		_fresh(["draft_trade"])
		_state.set_setting("seen_draft_intro", true)
		if _state.begin_intake_draft():
			var draft = _state.draft
			var ui5: Control = load("res://scenes/DraftScene.tscn").instantiate()
			root.add_child(ui5)
			await _frames(6)
			var done: Button = ui5.find_child("MeetingDone", true, false)
			if done != null:
				done.emit_signal("pressed")
			var guard := 0
			while not draft.is_user_turn() and not draft.is_finished() and guard < 200:
				guard += 1
				draft.auto_until_user_turn()
			ui5.call("_refresh")
			ui5.call("_finish_night")
			await _frames(20)
			ui5.call("_on_trade_picks")
			await _frames(20)
			await _shot("draft_trade_intro")
			for o in ui5.find_children("*IntroOk", "Button", true, false):
				(o as Button).emit_signal("pressed")
			await _frames(10)
			await _shot("draft_trade")
		else:
			print("no draft")

	quit()


func _want(state: String) -> bool:
	return _only.is_empty() or _only.has(state)


## A fresh career at the off-season; every intro seen except the ones named.
func _fresh(unseen: Array) -> void:
	_state.reset()
	_state.career_seed = 4402
	_state.replay_seed = 4402
	_state.start_season(CLUB, _db.club_list(CLUB))
	_state.week_events = []
	for key in _keys:
		_state.set_setting("seen_%s_intro" % key, not unseen.has(key))
	_state.set_setting("seen_training_intro", true)
	_state.tutorials = not unseen.is_empty()
	_state.season.round_index = _state.season.fixture.size()
	_state.open_offseason()


func _expiring_id(ui: Node) -> String:
	for n in ui.find_children("Contract_*", "Control", true, false):
		return str(n.name).trim_prefix("Contract_")
	return ""


## Opens a screen fresh through the router and waits for it to settle.
func _go(route: String, scene: String) -> Node:
	_router.stack = []
	_router.go("main")
	var guard := 0
	while not _on("Main") and guard < 600:
		await process_frame
		guard += 1
	_router.go(route)
	guard = 0
	while not _on(scene) and guard < 600:
		await process_frame
		guard += 1
	await _frames(40)
	return current_scene


## Scrolls the page so the named part sits near the top.
func _scroll_to(ui: Node, node_name: String) -> void:
	await _frames(8)
	var found: Array = ui.find_children(node_name, "Control", true, false)
	if found.is_empty():
		print("missing ", node_name)
		return
	var target: Control = found[0]
	var sc: Node = target.get_parent()
	while sc != null and not (sc is ScrollContainer):
		sc = sc.get_parent()
	if sc != null:
		(sc as ScrollContainer).scroll_vertical = int(target.global_position.y - (sc as Control).global_position.y
				+ (sc as ScrollContainer).scroll_vertical - 8.0)
	await _frames(8)


func _on(scene: String) -> bool:
	return current_scene != null and current_scene.scene_file_path.contains(scene)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(name: String) -> void:
	await _frames(3)
	var img := root.get_viewport().get_texture().get_image()
	img.save_png("%s_%s.png" % [_out, name])
	print("wrote %s_%s.png" % [_out, name])
