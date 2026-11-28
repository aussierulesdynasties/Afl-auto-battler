extends SceneTree
## Scratch probe (never commit): seed 1 (AFL_SKIP_OVR_ROWS=1) played at the tail check's step,
## printing every step of beats 883-889: phase, ball, the 886 kicker and the 887 tackler.

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
	var res: Dictionary = suite._result(1)
	var evs: Array = res["events"]
	print("TRACE events %d" % evs.size())
	for i in range(880, 891):
		print("TRACE ev %d %s" % [i, str(evs[i])])
	var MD = load("res://scripts/ui/match/MatchDirector.gd")
	var d = MD.new()
	d.setup(res, evs)
	var kicker: int = d._actor_id(evs[886])
	var tackler: int = d._actor_id(evs[887])
	print("TRACE kicker token %d tackler token %d" % [kicker, tackler])
	var dt := 1.0 / 60.0 * 4.0
	var guard := 0
	var last_line := ""
	while not d.idle() and guard < 200000:
		guard += 1
		d.advance(dt)
		var k := int(d._beat.get("k", -1))
		if k < 883:
			continue
		if k > 889:
			break
		var ph := {}
		if d._pi < d._phases.size():
			ph = d._phases[d._pi]
		var pt := str(ph.get("t", "-"))
		var line := "TRACE t %.2f k %d pi %d %s | ball %s %s holder %d | kicker %s | tackler %s" % [
			d.time, k, d._pi, pt, str(d.ball["mode"]), str(d.ball["pos"]), int(d.ball.get("holder", -1)),
			str(d.tokens[kicker]["pos"]), str(d.tokens[tackler]["pos"])]
		if pt != last_line or guard % 3 == 0:
			print(line)
		last_line = pt
	for a in d.arrivals:
		if int(a["idx"]) >= 883 and int(a["idx"]) <= 890:
			print("TRACE arrival %s" % str(a))
	quit(0)
