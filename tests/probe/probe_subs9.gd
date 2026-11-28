extends SceneTree
## Scratch probe (never commit): seed SB seed, every log line naming one side's man up to event 340,
## the replay's starting tokens and bench for that side, and the token the replay maps him to.

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_career.save"
	gs.settings_path = "user://test_settings.cfg"
	var suite = load("res://tests/test_match_visual.gd").new()
	gs.replay_seed = 2027
	root.get_node("GameDB").reload()
	suite._result(42)
	var res: Dictionary = suite._result(int(OS.get_environment("TR_SEED")) if OS.get_environment("TR_SEED") != "" else 9)
	var evs: Array = res["events"]
	var num := int(OS.get_environment("SB_NUM")) if OS.get_environment("SB_NUM") != "" else 12
	var side := int(OS.get_environment("SB_SIDE")) if OS.get_environment("SB_SIDE") != "" else 1
	var upto := int(OS.get_environment("SB_UPTO")) if OS.get_environment("SB_UPTO") != "" else 340
	var subs := 0
	for i in range(mini(evs.size(), upto)):
		var ev: Dictionary = evs[i]
		if str(ev.get("kind", "")) == "sub":
			subs += 1
		if int(ev.get("side", -1)) == side and (int(ev.get("num", -1)) == num or int(ev.get("off_num", -1)) == num):
			print("SB ev %d %s %s" % [i, str(ev.get("kind", "")), str(ev.get("text", ""))])
	print("SB sub events before %d: %d" % [upto, subs])
	print("SB keys %s" % str(res.keys()))
	var MD = load("res://scripts/ui/match/MatchDirector.gd")
	var d = MD.new()
	d.setup(res, evs)
	var nums := []
	for t in d.tokens:
		if int(t["side"]) == side:
			nums.append([int(t["num"]), str(t["slot"]), str(t.get("name", ""))])
	print("SB start tokens side %d %s" % [side, str(nums)])
	print("SB bench side %d %s" % [side, str(d.bench[side])])
	quit(0)
