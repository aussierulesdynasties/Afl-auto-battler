extends SceneTree
## Scratch probe (never commit): seed BD_SEED played at the tail check's step. When restart beat
## BD_K leaves its setup, prints every man's spot; then follows beat BD_T (the tackle) and prints
## the carrier's and tackler's spots each step, and the arrival. JSON lines for the board.

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
	var seed := int(OS.get_environment("BD_SEED")) if OS.get_environment("BD_SEED") != "" else 1
	var bk := int(OS.get_environment("BD_K"))
	var bt := int(OS.get_environment("BD_T"))
	var res: Dictionary = suite._result(seed)
	var evs: Array = res["events"]
	for i in range(bk, bt + 1):
		print("BD ev %s" % JSON.stringify({"i": i, "kind": str(evs[i].get("kind", "")), "side": int(evs[i].get("side", -1)),
				"num": int(evs[i].get("num", 0)), "name": str(evs[i].get("name", "")), "fp": float(evs[i].get("fp", 0.0)),
				"bounce": evs[i].get("bounce", []), "text": str(evs[i].get("text", ""))}))
	var MD = load("res://scripts/ui/match/MatchDirector.gd")
	var d = MD.new()
	d.setup(res, evs)
	print("BD goal_x %.2f" % MatchMotion.GOAL_X)
	print("BD ground %s" % JSON.stringify({"half_len": MatchMotion.HALF_LEN, "half_wid": MatchMotion.HALF_WID,
			"goal_x": MatchMotion.GOAL_X, "shape": MatchMotion.SHAPE.size()}))
	var dt := 1.0 / 60.0 * 4.0
	var guard := 0
	var dumped := false
	var actors := {}
	while not d.idle() and guard < 200000:
		guard += 1
		d.advance(dt)
		var k := int(d._beat.get("k", -1))
		if k < bk:
			continue
		if k > bt:
			break
		var ph := {}
		if d._pi < d._phases.size():
			ph = d._phases[d._pi]
		var pt := str(ph.get("t", "-"))
		if k == bk and not dumped and pt != "setup":
			dumped = true
			for t in d.tokens:
				print("BD spot %s" % JSON.stringify({"id": int(t["id"]), "side": int(t["side"]), "num": int(t["num"]),
						"slot": str(t["slot"]), "role": str(t["role"]), "name": str(t.get("surname", "")),
						"x": (t["pos"] as Vector2).x, "y": (t["pos"] as Vector2).y}))
			print("BD ball %s" % JSON.stringify({"x": (d.ball["pos"] as Vector2).x, "y": (d.ball["pos"] as Vector2).y}))
			var tk := int(d._actor_id(evs[bt]))
			var pv := int(d._actor_id(evs[d._prev_real(bt)]))
			actors = {"tackler": tk, "carrier": pv}
			print("BD actors %s" % JSON.stringify(actors))
		if dumped and k >= bk and actors.size() == 2:
			var tk2: int = actors["tackler"]
			var cv: int = actors["carrier"]
			if tk2 >= 0 and cv >= 0:
				print("BD step %s" % JSON.stringify({"t": d.time, "k": k, "ph": pt,
						"cx": (d.tokens[cv]["pos"] as Vector2).x, "cy": (d.tokens[cv]["pos"] as Vector2).y,
						"tx": (d.tokens[tk2]["pos"] as Vector2).x, "ty": (d.tokens[tk2]["pos"] as Vector2).y}))
	for a in d.arrivals:
		if int(a["idx"]) >= bk and int(a["idx"]) <= bt:
			print("BD arrival %s" % JSON.stringify({"idx": int(a["idx"]), "kind": str(a["kind"]),
					"x": (a["pos"] as Vector2).x, "y": (a["pos"] as Vector2).y, "want_x": float(a["want_x"])}))
	quit(0)
