extends RefCounted


func run(names: Array) -> void:
	var t = load("res://tests/test_match_visual.gd").new()
	GameState.replay_seed = t.SUITE_SEED
	GameDB.reload()
	var res: Dictionary = t._result(42)
	for n in names:
		await t.call(str(n), res)
	print("PROBE checks=%d failures=%s" % [t.checks, str(t.failures)])
