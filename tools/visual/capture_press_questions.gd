extends SceneTree
## Visual review of the press-conference questions added by the press-questions PR:
## each new occasion and each second version, on the press screen, for a seeded
## Fremantle save (seed 7737, real list players). The match facts each question
## quotes are written into the result the question reads (MediaConference.pick
## gets the same ctx GameState._prepare_media_conference builds).
## Needs a real renderer (windowed, through C:/kt/gpu_slot.sh, off screen via override.cfg):
##   godot --path . --script tools/visual/capture_press_questions.gd -- --out /tmp/pq --size 390x844
## Writes <out>_<n>_<qid>.png (top of the screen) and, when the answers run below
## the fold, <out>_<n>_<qid>_answers.png (scrolled to the end). Prints each
## question with its journalist. Never touches a real save.




func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot() -> Image:
	await _frames(8)
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	return img


## A result FRE (home) v `opp`, from goals and behinds per quarter for each side.
func _res(opp: String, quarters: Array, team := {}) -> Dictionary:
	var g := [0, 0]
	var b := [0, 0]
	var pts := []
	for q in quarters:
		var row := []
		for s in range(2):
			g[s] += int(q[s][0])
			b[s] += int(q[s][1])
			row.append(int(q[s][0]) * 6 + int(q[s][1]))
		pts.append(row)
	var r := {"home": "FRE", "away": opp, "goals": g, "behinds": b,
			"score": [g[0] * 6 + b[0], g[1] * 6 + b[1]], "quarters": pts}
	if not team.is_empty():
		r["team"] = team
	return r


## A ladder after `played` games with FRE at `my_pos` and `opp` at `opp_pos`,
## the rest in club order: wins and percentage fall with each place.
func _ladder(season, played: int, my_pos: int, opp: String, opp_pos: int) -> void:
	var codes: Array = season.ladder.keys()
	var n := codes.size()
	var order := []
	order.resize(n)
	order[my_pos - 1] = "FRE"
	order[opp_pos - 1] = opp
	var rest := codes.filter(func(c): return c != "FRE" and c != opp)
	for i in range(n):
		if order[i] == null:
			order[i] = rest.pop_front()
	for i in range(n):
		var w := roundi(float(played) * float(n - 1 - i) / float(n - 1))
		var pct := 135.0 - 4.0 * i
		var pa := 82 * played
		season.ladder[order[i]] = {"code": order[i], "p": played, "w": w, "l": played - w, "d": 0,
				"pf": roundi(pa * pct / 100.0), "pa": pa, "pts": 4 * w, "pct": pct}


func _run() -> void:
	var out := "/tmp/pq"
	var size := Vector2i(390, 844)
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--size":
			size = Vector2i(int(str(a[i + 1]).get_slice("x", 0)), int(str(a[i + 1]).get_slice("x", 1)))
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_pq.save"
	state.settings_path = "user://capture_pq_settings.cfg"
	state.career_seed = 7737
	state.replay_seed = 7737
	state.reset()
	state.start_season("FRE", db.club_list("FRE"))
	root.size = size
	DisplayServer.window_set_size(size)
	await _frames(4)
	var y: int = state.season_year
	var list: Array = state.my_list.duplicate()
	list.sort_custom(func(x, z): return float(x.get("age", 30.0)) < float(z.get("age", 30.0)))
	var kid: Dictionary = list[0]
	var vet: Dictionary = list[-1]
	var mid: Dictionary = list[list.size() / 2]
	var who := func(p: Dictionary) -> Dictionary:
		return {"id": str(p["id"]), "name": db.player_display_name(p)}
	var named := {"heavy_loss": who.call(mid), "big_win": who.call(vet), "young_side": who.call(kid)}

	# Each case: [file tag, ctx overrides, times the question was asked before].
	var cases := [
		["final_win", {"opp": "GEE", "round": 26, "final": {"label": "semi-final", "status": "alive"},
				"result": _res("GEE", [[[3, 2], [2, 3]], [[4, 1], [3, 2]], [[3, 3], [2, 2]], [[2, 2], [2, 1]]])}, 0],
		["final_loss", {"opp": "SYD", "round": 27, "final": {"label": "preliminary final", "status": "eliminated"},
				"result": _res("SYD", [[[2, 2], [3, 1]], [[2, 3], [4, 2]], [[3, 1], [3, 3]], [[2, 2], [3, 2]]])}, 0],
		["blown_lead", {"opp": "CAR", "round": 9,
				"result": _res("CAR", [[[5, 1], [1, 2]], [[3, 2], [2, 1]], [[1, 2], [5, 2]], [[1, 1], [5, 2]]])}, 0],
		["comeback", {"opp": "HAW", "round": 11,
				"result": _res("HAW", [[[1, 1], [4, 3]], [[4, 2], [2, 2]], [[5, 1], [2, 1]], [[4, 2], [2, 1]]])}, 0],
		["upset_loss", {"opp": "WCE", "round": 14, "my_pos": 3, "opp_pos": 16,
				"result": _res("WCE", [[[2, 2], [3, 2]], [[3, 1], [3, 3]], [[2, 2], [4, 1]], [[2, 3], [3, 2]]])}, 0],
		["upset_win", {"opp": "BRL", "round": 15, "my_pos": 15, "opp_pos": 2,
				"result": _res("BRL", [[[3, 2], [2, 2]], [[3, 1], [3, 2]], [[2, 3], [2, 1]], [[3, 1], [2, 2]]])}, 0],
		["losing_run", {"opp": "ADE", "round": 7, "losing_run": 3,
				"result": _res("ADE", [[[2, 2], [3, 2]], [[2, 1], [3, 1]], [[3, 2], [3, 2]], [[2, 1], [3, 3]]])}, 0],
		["winning_run", {"opp": "STK", "round": 8, "winning_run": 4,
				"result": _res("STK", [[[4, 2], [2, 1]], [[3, 2], [2, 3]], [[3, 1], [2, 1]], [[3, 2], [3, 2]]])}, 0],
		["milestone", {"opp": "MEL", "round": 10, "milestone": {"id": str(vet["id"]), "name": db.player_display_name(vet), "games": 150},
				"result": _res("MEL", [[[3, 2], [2, 2]], [[3, 1], [3, 2]], [[2, 3], [2, 1]], [[3, 1], [2, 2]]])}, 0],
		["debut", {"opp": "GCS", "round": 4, "debut": {"id": str(kid["id"]), "name": db.player_display_name(kid), "games": 1},
				"result": _res("GCS", [[[3, 2], [2, 2]], [[3, 1], [3, 2]], [[2, 3], [2, 1]], [[3, 1], [2, 2]]])}, 0],
		["wayward", {"opp": "RIC", "round": 12,
				"result": _res("RIC", [[[2, 4], [3, 1]], [[2, 3], [3, 2]], [[1, 4], [3, 1]], [[2, 4], [2, 1]]])}, 0],
		["heavy_loss_v2", {"opp": "GWS", "round": 6,
				"result": _res("GWS", [[[1, 2], [5, 2]], [[2, 1], [4, 3]], [[1, 2], [5, 1]], [[2, 1], [4, 2]]])}, 1],
		["big_win_v2", {"opp": "NTH", "round": 13,
				"result": _res("NTH", [[[5, 2], [1, 2]], [[5, 3], [2, 1]], [[4, 2], [1, 1]], [[5, 1], [2, 2]]])}, 1],
		["star_v2", {"opp": "ESS", "round": 16, "star": {"id": str(mid["id"]), "name": db.player_display_name(mid), "line": "kicked 7 goals"},
				"result": _res("ESS", [[[4, 2], [2, 1]], [[3, 2], [2, 3]], [[3, 1], [2, 1]], [[3, 2], [3, 2]]])}, 1],
		["injury_v2", {"opp": "PAD", "round": 17, "injuries": [{"id": str(mid["id"]), "name": db.player_display_name(mid)}],
				"result": _res("PAD", [[[2, 2], [3, 2]], [[2, 1], [3, 1]], [[3, 2], [3, 2]], [[2, 1], [3, 3]]])}, 1],
		["young_side_v2", {"opp": "WBD", "round": 18, "young": 7,
				"result": _res("WBD", [[[2, 2], [3, 2]], [[3, 1], [3, 1]], [[3, 2], [3, 2]], [[2, 1], [3, 3]]])}, 1],
	]
	var host := Control.new()
	host.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(host)
	var MC = load("res://scripts/sim/MediaConference.gd")
	var n := 0
	for c in cases:
		n += 1
		var tag := str(c[0])
		var over: Dictionary = c[1]
		var opp := str(over["opp"])
		var ctx := {"club": "FRE", "opponent_name": db.club_name(opp), "year": y, "named": named, "young": 0}
		for k in over:
			if k != "opp":
				ctx[k] = over[k]
		# The ladder as it stands after the game, so the positions the question
		# quotes and the Stats Geek's record line agree.
		var mp := int(over.get("my_pos", 8))
		var op := int(over.get("opp_pos", 11))
		_ladder(state.season, mini(int(over["round"]), 24), mp, opp, op)
		ctx["my_pos"] = state.my_position()
		ctx["opp_pos"] = state.club_position(opp)
		var key := tag.trim_suffix("_v2")
		var memory := {"asked": {key: int(c[2])}}
		var conf: Dictionary = MC.pick(ctx, memory)
		if conf.is_empty():
			print("FAIL ", tag, ": no question")
			continue
		conf["opp"] = db.club_name(opp)
		var j := str(conf.get("journalist", ""))
		conf["lead"] = MC.lead_in(j, state.press_standing(j))
		state.media_conference = conf
		print("Q %02d %s [%s] %s | %s" % [n, tag, str(conf.get("qid", "")), str(conf.get("by", "")), state.press_question_text()])
		for o in conf.get("options", []):
			print("    - ", str((o as Dictionary).get("label", "")))
		if str(conf.get("key", "")) != key:
			print("FAIL ", tag, ": picked ", str(conf.get("key", "")))
		var press = load("res://scripts/ui/PressScene.gd").embed(host)
		await _frames(6)
		var scene = root.find_child("MediaConferenceVignette", true, false)
		if scene != null:
			scene.call("finish_now")
		await _frames(30)
		var base := "%s_%02d_%s" % [out, n, tag]
		(await _shot()).save_png(base + ".png")
		print("CAPTURED ", base, ".png")
		var sc: ScrollContainer = null
		for s in press.find_children("*", "ScrollContainer", true, false):
			if (s as ScrollContainer).is_visible_in_tree():
				sc = s
				break
		if sc != null and sc.get_v_scroll_bar().max_value > sc.size.y + 1:
			sc.scroll_vertical = int(sc.get_v_scroll_bar().max_value)
			(await _shot()).save_png(base + "_answers.png")
			print("CAPTURED ", base, "_answers.png")
		press.queue_free()
		state.media_conference = {}
		await _frames(4)
	quit(0)
