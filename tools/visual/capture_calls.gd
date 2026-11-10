extends SceneTree
## Row T2.4: every structural call on the oval, filmed against Balanced on the same
## events, at the size the real match screen draws the oval. One launch per screen size.
## Needs a real renderer (windowed, through C:/kt/gpu_slot.sh, off screen):
##   godot --path . --windowed --script tools/visual/capture_calls.gd -- --size 390x844 --out DIR
##
## 1. Starts a seeded season for Fremantle, opens the real match screen at --size and
##    reads where it puts the oval, whether it stands upright and whether it follows
##    the ball. Every frame below is that rect, so the framing is the game's own.
## 2. Plays a seeded Fremantle v Melbourne match (the sim never touched). For each call,
##    Fremantle's recorded calls are replaced with that call (as test_match_motion's
##    _with_call does), and a dry run logs, every 1/30 s, whether the moment the call
##    acts on is on (Fremantle has the ball in open play, a ball-up, a centre bounce,
##    Melbourne has it inside Fremantle's press zone...). The window opens on the first
##    event after 30 s of play where that moment holds for most of --secs.
## 3. Films the window twice from the same event: Fremantle on Balanced, then on the
##    call. Writes DIR/<call>_bal_f0000.png.. and DIR/<call>_call_f0000.png.., cropped to
##    the oval, and prints per call: the event window, the share of frames the moment
##    held, the mean distance between each Fremantle player on the call and the same
##    player on Balanced (metres, as drawn), and any disc drawn outside the oval's rect.
##
##   --seed N (default 42)  --home FRE --away MEL  --secs S (default 5)  --only KEY
##   --size WxH (default 390x844)  --out DIR

const CALLS := [
	["corridor", "Attack Corridor", "attacking", [], "has"],
	["controlled", "Controlled Tempo", "controlled", [], "has"],
	["contest_stop", "Win Contest (ball-up)", "contest", [], "ballup"],
	["contest_open", "Win Contest (open play)", "contest", [], "open"],
	["press", "Defensive Press", "defensive", [], "press"],
	["surge", "Throw numbers at it", "balanced", ["surge"], "has"],
	["hold", "Slow it down", "balanced", ["hold"], "has"],
	["flood", "Flood behind the ball", "balanced", ["flood"], "not"],
	["stack", "Stack the stoppage", "balanced", ["stack"], "centre"],
	["push", "Push numbers forward", "balanced", ["push"], "has"],
]
const DT := 1.0 / 60.0
const SAMPLE := 2          # a sample every 2 steps (1/30 s)
const HOLD_SHARE := 0.8    # the moment holds in at least this share of the window
const CENTRE_SHARE := 0.3  # a centre bounce is short: its set-up and the bounce, then the clearance
const SETTLE_S := 30.0     # skip the first 30 s of play (the opening bounce)
const MAX_EVENTS := 700


func _initialize() -> void:
	_run.call_deferred()


func _args() -> Dictionary:
	var out := {}
	var a := OS.get_cmdline_user_args()
	var i := 0
	while i < a.size():
		var k := str(a[i])
		if k.begins_with("--"):
			var v := ""
			if i + 1 < a.size() and not str(a[i + 1]).begins_with("--"):
				v = str(a[i + 1])
				i += 1
			out[k.substr(2)] = v
		i += 1
	return out


func _run() -> void:
	await process_frame
	var a := _args()
	var wh := str(a.get("size", "390x844")).split("x")
	var w := int(wh[0])
	var h := int(wh[1])
	var out := str(a.get("out", "user://calls"))
	DirAccess.make_dir_recursive_absolute(out)
	root.size = Vector2i(w, h)
	DisplayServer.window_set_size(Vector2i(w, h))
	for i in range(4):
		await process_frame

	# 1. Where the real match screen puts the oval.
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://capture_calls.save"
	gs.settings_path = "user://capture_calls.cfg"
	gs.replay_seed = 2027
	var db = root.get_node("GameDB")
	var home := str(a.get("home", "FRE"))
	var away := str(a.get("away", "MEL"))
	gs.reset()
	gs.start_season(home, db.club_list(home))
	if not gs.prepare_interactive_match():
		print("CAPTURE FAIL: no live match")
		quit(1)
		return
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	for i in range(12):
		await process_frame
	var real_pitch = m.get("_pitch")
	var rect: Rect2 = real_pitch.get_global_rect()
	var upright: bool = real_pitch.upright
	var cam: bool = real_pitch.camera_enabled
	var vis: Vector2 = root.get_visible_rect().size
	var px := Vector2(w, h) / vis
	var crop := Rect2i(Vector2i((rect.position * px).round()), Vector2i((rect.size * px).round()))
	print("CAPTURE screen %dx%d: oval at %s canvas units, %s pixels, upright %s, follows the ball %s" % [
			w, h, str(rect), str(crop), str(upright), str(cam)])
	m.queue_free()
	for i in range(4):
		await process_frame

	# 2. The match.
	var squad_script = load("res://scripts/sim/Squad.gd")
	var sim_script = load("res://scripts/sim/MatchSim.gd")
	var sim = sim_script.new(squad_script.new(home, db.club_list(home), true, home),
			squad_script.new(away, db.club_list(away), false, away), int(a.get("seed", "42")))
	var res: Dictionary = sim.run()
	res["home"] = home
	res["away"] = away
	res["events"] = (res["events"] as Array).slice(0, MAX_EVENTS)

	var pitch = load("res://scripts/ui/PitchView.gd").new()
	pitch.position = rect.position
	pitch.size = rect.size
	root.add_child(pitch)
	await process_frame
	pitch.camera_enabled = cam
	pitch.upright = upright
	var secs := float(a.get("secs", "5"))
	var only := str(a.get("only", ""))
	for c in CALLS:
		if only != "" and str(c[0]) != only:
			continue
		var r_call := _with_call(res, str(c[2]), c[3])
		var r_bal := _with_call(res, "balanced", [])
		var pick := _pick_window(pitch, r_call, str(c[4]), secs)
		if pick.is_empty():
			print("CALL %s: no window where the moment holds" % str(c[0]))
			continue
		var bal: Dictionary = await _film(pitch, r_bal, int(pick["idx"]), secs, "%s/%s_bal" % [out, str(c[0])], crop, str(c[4]))
		var cal: Dictionary = await _film(pitch, r_call, int(pick["idx"]), secs, "%s/%s_call" % [out, str(c[0])], crop, str(c[4]))
		var moved := _moved(bal["home"], cal["home"])
		print("CALL %s | %s | events %d..%d | moment held %.0f%% of the dry run window, %.0f%% filmed on the call | Fremantle on the call stands %.1f m from Balanced on average (median player %.1f m) | discs outside the oval: %d bal, %d call | frames %d" % [
				str(c[0]), str(c[1]), int(pick["idx"]), int(cal["last"]), 100.0 * float(pick["share"]),
				100.0 * float(cal["share"]), float(moved["mean"]), float(moved["median"]),
				int(bal["outside"]), int(cal["outside"]), int(cal["frames"])])
	quit(0)


## `res` with Fremantle (side 0) on `plan` and `bursts` all match (the sim untouched).
static func _with_call(res: Dictionary, plan: String, bursts: Array) -> Dictionary:
	var r2 := res.duplicate()
	var tl := []
	for e in res["timeline"]:
		var e2: Dictionary = (e as Dictionary).duplicate(true)
		if int(e2["side"]) == 0:
			e2["plan"] = plan
			e2["bursts"] = bursts
		tl.append(e2)
	r2["timeline"] = tl
	return r2


## Is the moment this call acts on happening now (for Fremantle, side 0)?
static func _moment(d, want: String) -> bool:
	if d.mode == "break" or d.tokens.is_empty():
		return false
	var stop: bool = d._stoppage_on()
	match want:
		"has":
			return d._poss == 0 and not stop and d.mode != "centre"
		"not":
			return d._poss == 1 and not stop and d.mode != "centre"
		"open":
			return not stop and d.mode != "centre"
		"ballup":
			return stop and d.mode == "stoppage"
		"centre":
			return d.mode == "centre"
		"press":
			var bx: float = (d.ball["pos"] as Vector2).x * d._dir(0)
			return d._poss == 1 and not stop and d._pressing(0, bx)
	return false


## Dry run on the call: the first event start after SETTLE_S where the moment holds
## for HOLD_SHARE of the next `secs`.
func _pick_window(pitch, r: Dictionary, want: String, secs: float) -> Dictionary:
	pitch.setup(r)
	pitch.set_speed(1.0)
	pitch.play()
	pitch.set_process(false)
	var on: Array = []      # per sample: moment on
	var idx: Array = []     # per sample: events emitted
	var steps := 0
	while pitch.playing and pitch.current_index() < MAX_EVENTS - 5 and steps < 60 * 60 * 30:
		pitch._process(DT)
		steps += 1
		if steps % SAMPLE == 0:
			on.append(_moment(pitch.director, want))
			idx.append(pitch.current_index())
	var n := int(round(secs * 30.0))
	var first := int(SETTLE_S * 30.0) if want != "centre" else 0
	for s in range(maxi(1, first), on.size() - n):
		if int(idx[s]) == int(idx[s - 1]) or not bool(on[s]):
			continue
		var held := 0
		for j in range(s, s + n):
			if bool(on[j]):
				held += 1
		var share := float(held) / float(n)
		if share >= (CENTRE_SHARE if want == "centre" else HOLD_SHARE) and (want != "centre" or int(idx[s]) > 3):
			return {"idx": int(idx[s]), "share": share}
	return {}


## Plays `r` to the moment event `from` is emitted, then films `secs` at 1x.
func _film(pitch, r: Dictionary, from: int, secs: float, stem: String, crop: Rect2i, want: String) -> Dictionary:
	pitch.setup(r)
	pitch.set_speed(1.0)
	pitch.play()
	pitch.set_process(false)
	var guard := 0
	while pitch.current_index() < from and guard < 600000:
		pitch._process(DT)
		guard += 1
	var steps := int(round(secs / DT))
	var homes: Array = []
	var outside := 0
	var held := 0
	var n := 0
	var box: Rect2 = Rect2(Vector2.ZERO, pitch.size).grow(0.5)
	for s in range(steps):
		pitch._process(DT)
		if s % SAMPLE != 0:
			continue
		pitch.queue_redraw()
		await process_frame
		await process_frame
		var img: Image = root.get_viewport().get_texture().get_image()
		img.get_region(crop).save_png("%s_f%04d.png" % [stem, n])
		var drawn: PackedVector2Array = pitch.disc_positions_drawn()
		var sc: float = pitch._scale()
		var frame_home := []
		for i in range(drawn.size()):
			if not box.has_point(drawn[i]):
				outside += 1
			if int(pitch.director.tokens[i]["side"]) == 0:
				frame_home.append(drawn[i] / maxf(0.0001, sc))
		homes.append(frame_home)
		if _moment(pitch.director, want):
			held += 1
		n += 1
	return {"home": homes, "outside": outside, "frames": n, "last": pitch.current_index(),
			"share": float(held) / float(maxi(1, n))}


## Mean and median distance between each Fremantle player in `a` and `b`, frame by frame.
static func _moved(a: Array, b: Array) -> Dictionary:
	var ds: Array = []
	for f in range(mini(a.size(), b.size())):
		var fa: Array = a[f]
		var fb: Array = b[f]
		for i in range(mini(fa.size(), fb.size())):
			ds.append((fa[i] as Vector2).distance_to(fb[i] as Vector2))
	if ds.is_empty():
		return {"mean": 0.0, "median": 0.0}
	var sum := 0.0
	for d in ds:
		sum += float(d)
	ds.sort()
	return {"mean": sum / ds.size(), "median": float(ds[ds.size() / 2])}
