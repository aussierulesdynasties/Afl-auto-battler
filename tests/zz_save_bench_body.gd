extends RefCounted
## Scratch (bug bash, never commit): current vs candidate save encoder: same bytes? how fast?

const REPS := 5


func _check(st: Node, label: String) -> void:
	var NEW = load("res://tests/zz_enc_new.gd")
	var state: Dictionary = st.call("_save_state")
	var meta: Dictionary = st.call("_save_meta")
	var t_old := 0.0
	var t_new := 0.0
	var same := true
	var size := 0
	for rep in range(REPS):
		var t0 := Time.get_ticks_usec()
		var e1 = CareerSave.new()
		var b1 = e1._encode(state)
		e1._untag()
		t_old += (Time.get_ticks_usec() - t0) / 1000.0
		t0 = Time.get_ticks_usec()
		var e2 = NEW.new()
		var b2 = e2._encode(state)
		e2._untag()
		t_new += (Time.get_ticks_usec() - t0) / 1000.0
		var x1 := var_to_bytes({"version": CareerSave.VERSION, "meta": meta, "players": e1._players, "state": b1})
		var x2 := var_to_bytes({"version": CareerSave.VERSION, "meta": meta, "players": e2._players, "state": b2})
		size = x1.size()
		same = same and x1 == x2
	# Nothing left tagged on the live players.
	var tagged := 0
	for code in st.get("season").lists:
		for p in st.get("season").lists[code]:
			if (p as Dictionary).has(CareerSave.WRITE_TAG):
				tagged += 1
	print("CMP %s: %d bytes, identical %s, old %.1f ms, new %.1f ms, tags left %d" % [label, size, same, t_old / REPS, t_new / REPS, tagged])


func _advance_rounds(st: Node, n: int) -> void:
	var played := 0
	for i in range(400):
		var before: int = st.get("season").round_index
		var y0: int = st.get("season_year")
		st.advance()
		if st.get("season").round_index > before or int(st.get("season_year")) != y0:
			played += 1
		if played >= n:
			return


func run(tree: SceneTree) -> void:
	var root := tree.root
	var st: Node = root.get_node("GameState")
	var db: Node = root.get_node("GameDB")
	for code in ["COL", "FRE"]:
		st.replay_seed = 2026 if code == "COL" else 7
		st.reset()
		st.start_season(code, db.club_list(code))
		_check(st, "%s start" % code)
		_advance_rounds(st, 3)
		_check(st, "%s round %d" % [code, st.get("season").round_index])
		_advance_rounds(st, 12)
		_check(st, "%s round %d" % [code, st.get("season").round_index])
	print("done")
