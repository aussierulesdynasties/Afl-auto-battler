extends SceneTree
## Row 12: a clanger names why it went astray over the player who erred ("Slippery
## ball", "Blown off line"). Plays a seeded match through the real PitchView with
## the clanger causes shown and saves one frame at the moment each cause shows
## (up to --max), with the words on the oval beside it in <out>_log.txt.
## Needs a real renderer:
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_clanger_why.gd -- \
##       --home FRE --away MEL --size 390x330 --seed 9100 --max 6 --out /tmp/clanger
## Never touches a real save.

var W := 390
var H := 600
var _out := "/tmp/clanger"
var _seen := {}
var _log: PackedStringArray = []


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
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://capture_clanger.save"
	gs.settings_path = "user://capture_clanger.cfg"
	var a := _args()
	var home := str(a.get("home", "FRE"))
	var away := str(a.get("away", "MEL"))
	var seed := int(str(a.get("seed", "9100")))
	var max_shots := int(str(a.get("max", "6")))
	_out = str(a.get("out", _out))
	var size_s := str(a.get("size", "390x330")).split("x")
	W = int(size_s[0])
	H = int(size_s[1])
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	var db = root.get_node("GameDB")
	db.reload()
	var SquadC = load("res://scripts/sim/Squad.gd")
	var sim = load("res://scripts/sim/MatchSim.gd").new(SquadC.new(home, db.club_list(home), true, home),
			SquadC.new(away, db.club_list(away), false, away), seed)
	var res: Dictionary = sim.run()
	var pv = load("res://scripts/ui/PitchView.gd").new()
	# The project stretches canvas items: fill what is actually visible. The
	# phone's view (upright, whole oval, no camera) as the match screen shows it.
	pv.position = Vector2.ZERO
	pv.size = root.get_visible_rect().size
	pv.camera_enabled = false
	pv.upright = true
	root.add_child(pv)
	pv.setup(res)
	var hit := [{}]
	pv.event_played.connect(func(ev):
		var why := str(ev.get("why", ""))
		if str(ev.get("kind", "")) == "clanger" and why != "" and not _seen.has(why):
			hit[0] = ev)
	pv.set_speed(2.0)
	pv.play()
	var shots := 0
	var guard := 0
	while shots < max_shots and guard < 200000 and not pv.director.idle():
		guard += 1
		await process_frame
		if (hit[0] as Dictionary).is_empty():
			continue
		var ev: Dictionary = hit[0]
		hit[0] = {}
		_seen[str(ev["why"])] = true
		pv.playing = false
		await process_frame
		await process_frame
		var img := root.get_viewport().get_texture().get_image()
		var path := "%s_%02d_%s.png" % [_out, shots, str(ev["why"])]
		img.save_png(path)
		_log.append("%s | q%s %s | on the oval: '%s' | feed text: %s" % [path, str(ev["q"]),
				str(ev["name"]), pv.caption_text(), str(ev["text"])])
		shots += 1
		var lf := FileAccess.open(_out + "_log.txt", FileAccess.WRITE)
		lf.store_string("\n".join(_log) + "\n")
		lf.close()
		pv.playing = true
	var f := FileAccess.open(_out + "_log.txt", FileAccess.WRITE)
	f.store_string("\n".join(_log) + "\n")
	f.close()
	print("\n".join(_log))
	quit(0)
