extends SceneTree
## Stalls in a live match (TODO row T2.42): the real match screen plays seeded
## matches you coach, start to full time, at the window size given, and every
## frame is logged. Report only; it changes nothing in the game.
##   godot --path . --script tools/visual/trace_stall_live.gd -- [--matches 2 --seed 7 --size 390x844 --speed 4]
## Speed 4 is the game's default (GameState.match_speed). The coach's side is driven like a player who takes every default: Start at
## each break, the first choice at each call once it is on screen.
## Prints:
##   DEAD   the oval not playing and nothing on screen asking for a tap (no
##          break, call, close-up or full time) for 0.5 s or more: a freeze
##   STILL  the oval playing but the ball still and almost nobody moving
##   HITCH  one frame that took 100 ms or more of real time, with what it did
## and a SUMMARY line per match.

const BALL_STILL := 0.4
const RUN := 1.2
const FEW := 3
const DEAD_AFTER := 0.5
const STILL_AFTER := 1.0
const HITCH_MS := 100.0

var _gs
var _m: Control


func _initialize() -> void:
	_run.call_deferred()


func _arg(name: String, fallback: String) -> String:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == name:
			return str(a[i + 1])
	return fallback


func _run() -> void:
	var matches := int(_arg("--matches", "2"))
	var seed0 := int(_arg("--seed", "7"))
	var size_s := _arg("--size", "390x844").split("x")
	var speed := float(_arg("--speed", "4"))
	root.size = Vector2i(int(size_s[0]), int(size_s[1]))
	await process_frame
	_gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	_gs.autosave_enabled = false
	var clubs: Array = db.active_clubs(2027)
	var totals := {"dead": 0, "still": 0, "hitch": 0}
	for mi in range(matches):
		var club := str(clubs[(mi * 5 + 2) % clubs.size()])
		_gs.reset()
		_gs.replay_seed = seed0 + mi
		_gs.start_season(club, db.club_list(club))
		if not _gs.prepare_interactive_match():
			print("SKIP match %d: no live match for %s" % [mi, club])
			continue
		_m = load("res://scenes/MatchScene.tscn").instantiate()
		root.add_child(_m)
		await process_frame
		var r := await _play_one(mi, speed)
		for k in r:
			totals[k] = int(totals[k]) + int(r[k])
		_m.queue_free()
		await process_frame
		await process_frame
	print("TOTAL %d matches at %s: %s" % [matches, "x".join(size_s), str(totals)])
	quit()


func _find(n: String) -> Node:
	return _m.find_child(n, true, false) if _m != null else null


## What on screen is waiting for the coach, "" when nothing is.
func _asking() -> String:
	if _find("CoachBox") != null:
		return "break"
	var mc := _find("MomentCard")
	if mc != null:
		return "call"
	if _find("BroadcastVignetteOverlay") != null:
		return "closeup"
	if bool(_m.get("_fulltime_shown")):
		return "fulltime"
	if bool(_m.get("_skipping")):
		return "skipping"
	return ""


func _first_choice() -> Button:
	var mc := _find("MomentCard")
	if mc == null:
		return null
	for b in mc.find_children("*", "Button", true, false):
		var bt := b as Button
		if bt.is_visible_in_tree() and not bt.disabled and (str(bt.name).begins_with("Moment_") or bt.pressed.get_connections().size() > 0):
			return bt
	return null


func _play_one(mi: int, speed: float) -> Dictionary:
	var pitch = _m.get("_pitch")
	pitch.set_speed(speed)
	var out := {"dead": 0, "still": 0, "hitch": 0}
	var dead_s := 0.0
	var still_s := 0.0
	var still_info := ""
	var asked_s := 0.0
	var last_ask := ""
	var prev_ball := Vector2.INF
	var prev := {}
	var t_prev := Time.get_ticks_usec()
	var wall := 0.0
	var frames := 0
	var emitted_prev := 0
	while wall < 3600.0:
		await process_frame
		var now := Time.get_ticks_usec()
		var ms := float(now - t_prev) / 1000.0
		t_prev = now
		var dt := ms / 1000.0
		wall += dt
		frames += 1
		if not is_instance_valid(_m):
			break
		pitch = _m.get("_pitch")
		var d = pitch.director if pitch != null else null
		var emitted: int = d.emitted if d != null else 0
		var ask := _asking()
		if ask == "fulltime":
			break
		if ms >= HITCH_MS and frames > 2:
			out["hitch"] += 1
			var kinds := []
			if d != null:
				for i in range(emitted_prev, mini(emitted, d.events.size())):
					kinds.append(str((d.events[i] as Dictionary).get("kind", "")))
			print("HITCH match %d at %.1fs: %.0f ms  ask=%s->%s  events %s" % [mi, wall, ms, last_ask, ask, str(kinds)])
		emitted_prev = emitted
		# Drive the coach like a player taking the defaults.
		if ask != last_ask:
			asked_s = 0.0
		else:
			asked_s += dt
		last_ask = ask
		if ask == "break" and asked_s > 0.3:
			var s := _find("StartQuarter") as Button
			if s != null:
				s.pressed.emit()
		elif ask == "call" and asked_s > 0.4:
			var b := _first_choice()
			if b != null:
				b.pressed.emit()
		# A freeze: the oval stopped and nothing asks for a tap.
		var playing: bool = pitch != null and bool(pitch.playing)
		if not playing and ask == "":
			dead_s += dt
		else:
			if dead_s >= DEAD_AFTER:
				out["dead"] += 1
				print("DEAD match %d at %.1fs: %.2f s with the oval stopped and nothing to tap (event %d of %d)" % [
						mi, wall, dead_s, emitted, d.events.size() if d != null else 0])
			dead_s = 0.0
		if dead_s >= 20.0:
			out["dead"] += 1
			var beat: Dictionary = d.get("_beat") if d != null else {}
			print("DEAD match %d at %.1fs: stuck for good (idle=%s, event %d of %d, beat %s, moment=%s, broadcast pending=%s busy=%s waiting=%s)" % [
					mi, wall, str(d.idle()) if d != null else "-", emitted, d.events.size() if d != null else 0,
					str(beat.get("kind", "-")), str(not _gs.pending_sim.pending_moment.is_empty()) if _gs.pending_sim != null else "-",
					str(_m.get("_broadcast_pending")), str(_m.get("_broadcast_busy")), str(_m.get("_broadcast_finish_waiting"))])
			break
		# A still picture while the oval plays.
		if playing and d != null and dt > 0.0:
			var bp: Vector2 = d.ball["pos"]
			var bv := 0.0 if prev_ball == Vector2.INF else bp.distance_to(prev_ball) / dt
			prev_ball = bp
			var moving := 0
			for t in d.tokens:
				var id := int(t["id"])
				var tp: Vector2 = t["pos"]
				if prev.has(id) and tp.distance_to(prev[id]) / dt > RUN * speed:
					moving += 1
				prev[id] = tp
			if bv < BALL_STILL * speed and moving < FEW and str(d.mode) != "break":
				if still_s == 0.0:
					var ph: Array = d.get("_phases")
					var pi: int = d.get("_pi")
					var p: Dictionary = ph[pi] if pi < ph.size() else {}
					still_info = "phase %s, beat %s, ball %s" % [str(p.get("t", "-")), str((d.get("_beat") as Dictionary).get("kind", "-")), str(d.ball["mode"])]
				still_s += dt
			else:
				if still_s >= STILL_AFTER:
					out["still"] += 1
					print("STILL match %d at %.1fs: %.2f s (%s)" % [mi, wall, still_s, still_info])
				still_s = 0.0
		else:
			prev_ball = Vector2.INF
			prev = {}
	print("SUMMARY match %d: %.0f s, %d frames, %s, finished=%s" % [mi, wall, frames, str(out), str(_asking() == "fulltime")])
	return out
