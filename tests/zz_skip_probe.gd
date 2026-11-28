extends SceneTree
## Scratch (bug bash, never commit): split "Skip to full time" into its parts.
## A: rest of our match (_simulate_remaining), then the pitch drain + full time (skip_to_end).
## B: rest of our match, then GameState.finish_interactive_match alone, then autosave alone.

func _initialize() -> void:
	_run.call_deferred()


func _ms(t0: int) -> float:
	return (Time.get_ticks_usec() - t0) / 1000.0


func _setup(st: Node, db: Node, seed_v: int) -> Control:
	st.replay_seed = seed_v
	st.reset()
	st.start_season("COL", db.club_list("COL"))
	root.size = Vector2i(1280, 720)
	st.prepare_interactive_match()
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	for i in range(10):
		await process_frame
	# Let the round's other matches finish (a browser has pumped them all by the first break).
	await create_timer(3.0).timeout
	return m


func _run() -> void:
	await process_frame
	var st: Node = root.get_node("GameState")
	var db: Node = root.get_node("GameDB")
	for rep in range(3):
		var seed_v := 2026 + rep
		var m: Control = await _setup(st, db, seed_v)
		m.set("_skipping", true)
		m.call("_close_coach")
		var t0 := Time.get_ticks_usec()
		m.call("_simulate_remaining")
		var a_sim := _ms(t0)
		t0 = Time.get_ticks_usec()
		(m.get("_pitch") as Node).call("skip_to_end")
		var a_rest := _ms(t0)
		print("A seed %d: rest of match %.0f ms, drain + finish + full time %.0f ms" % [seed_v, a_sim, a_rest])
		m.queue_free()
		await process_frame

		m = await _setup(st, db, seed_v)
		m.set("_skipping", true)
		m.call("_close_coach")
		t0 = Time.get_ticks_usec()
		m.call("_simulate_remaining")
		var b_sim := _ms(t0)
		var res: Dictionary = m.get("_res")
		m.call("_stamp_match_meta")
		var b_fin := await _finish_split(st, res)
		t0 = Time.get_ticks_usec()
		st.call("autosave")
		var b_save := _ms(t0)
		print("B seed %d: rest of match %.0f ms, finish_interactive_match %.0f ms (autosave alone again %.0f ms)" % [seed_v, b_sim, b_fin, b_save])
		m.queue_free()
		await process_frame
	var prof: Dictionary = st.call("prof_dump")
	var keys := prof.keys()
	keys.sort_custom(func(a, b): return float(prof[a]) > float(prof[b]))
	for k in keys.slice(0, 25):
		print("PROF %7.1f ms a round  %s" % [float(prof[k]) / 6.0, k])
	print("done")
	quit(0)


## finish_interactive_match's regular-season body, step by step (same order).
func _finish_split(st: Node, res: Dictionary) -> float:
	var T := {}
	var t_all := Time.get_ticks_usec()
	var season = st.get("season")
	var pm: Dictionary = st.get("pending_match")
	res["round"] = int(pm.get("round", season.round_index + 1))
	res["label"] = str(pm.get("label", "Match"))
	var t0 := Time.get_ticks_usec()
	var others: Array = st.call("_collect_others")
	T["collect_others"] = _ms(t0)
	t0 = Time.get_ticks_usec()
	var pr: Array = st.get("pending_round_results")
	for r in others:
		r["round"] = res["round"]
		r["label"] = res["label"]
		pr.append(r)
		season.record_regular(r)
	season.record_regular(res)
	var played := pr.duplicate()
	played.append(res)
	season.results.append(played)
	season.round_index += 1
	season.recalc_ladder()
	st.call("ensure_finals")
	T["record+ladder"] = _ms(t0)
	st.set("last_results", played)
	st.set("last_match", res)
	st.set("last_phase", "regular")
	st.set("last_label", str(res["label"]))
	var log: Array = st.get("season_log")
	for r in played:
		log.append(r)
	for step in ["_grant_match_xp", "_train_rivals", "_record_rivalries", "_after_round"]:
		t0 = Time.get_ticks_usec()
		if step == "_grant_match_xp":
			st.call(step, res)
		else:
			st.call(step, played)
		T[step] = _ms(t0)
	t0 = Time.get_ticks_usec()
	st.call("_clear_pending")
	T["clear_pending"] = _ms(t0)
	t0 = Time.get_ticks_usec()
	st.call("autosave")
	T["autosave"] = _ms(t0)
	var line := ""
	for k in T:
		line += " %s %.0f" % [k, T[k]]
	print("   split:" + line)
	return _ms(t_all)
