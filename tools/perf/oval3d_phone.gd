extends Node
## Phone cost of the 3D oval, ground by ground (docs/PHONE_3D_BUDGET.md): the main scene of a
## separate measuring APK (export preset "Android 3D probe", feature perf_probe), never of the game.
## For every ground the match view plays in, at each graphics level (Oval3DQuality), a seeded
## Fremantle v St Kilda match plays at 4x under the broadcast camera (Oval3DBroadcast) with the
## crowd on its seats: WARM s to settle, then MEASURE s measured. Each row is written to
## user://oval3d_phone.txt as it lands (a long run can be stopped and still read); at the end the
## table stays on screen (screenshot it). On a PC or in the cloud (a software GPU there: only the
## counts, memory and the ratios of the times carry over to a phone):
##   godot --path . --rendering-method mobile tools/perf/Oval3DPhone.tscn -- [grounds=mcg,marvel]
##       [levels=high,low] [size=1012x1242] [measure=5] [slot=night] [out=rows.json] [shots=DIR] [aa=msaa2] [quit]
##       [looks=NAME:px,py,pz,tx,ty,tz[,fov];NAME2:...]
## shots=DIR saves each ground and level's last measured frame as DIR/<ground>_<level>.png.
## slot= day (default), twilight or night: the time of day measured (a night game adds the towers).
## looks= also saves, after the measuring, a still from each fixed camera (match metres, from p
## looking at t, fov 60 unless given) as DIR/<ground>_<level>_<NAME>.png: a façade or roof
## detail the broadcast camera never frames, at the level's own render settings and aa=.
## Columns: frame = wall time a frame (mean, then the worst 5%); proc = the whole frame's process
## time; cpu / gpu = the renderer's own measured time; draws and ktris = what the frame drew;
## mem = the game's memory and the video memory in use, MB; load = s to build the scene.

const WARM := 2.0
var MEASURE := 5.0
const SPEED := 4.0
## The oval's share of the match screen on a 1080 x 2400 phone (PitchView._fit_3d; measured in
## tools/visual/capture_look3d.gd).
const VIEW := Vector2i(1012, 1242)
var _view: SubViewport

var label: Label
var rows: Array = []
var data: Array = []           # each row as numbers, for out=
var head := ""
const COLS := "ground        lvl   frame  p95  proc   cpu   gpu draws ktris  mem  vmem load"


func _ready() -> void:
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	OS.low_processor_usage_mode = false
	label = Label.new()
	label.add_theme_font_size_override("font_size", 13)
	label.add_theme_color_override("font_color", Color.WHITE)
	label.add_theme_color_override("font_outline_color", Color.BLACK)
	label.add_theme_constant_override("outline_size", 6)
	label.position = Vector2(8, 8)
	var layer := CanvasLayer.new()
	layer.layer = 100
	layer.add_child(label)
	add_child(layer)
	_run.call_deferred()


func _arg(name: String, fallback: String) -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with(name + "="):
			return a.substr(name.length() + 1)
	return fallback


func _run() -> void:
	var gdb = get_node("/root/GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	label.text = "Playing the match..."
	await get_tree().process_frame
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	res["home"] = "FRE"
	res["away"] = "STK"
	var grounds: Array = ["(stand)"]
	for k in GroundModels.GROUNDS:
		grounds.append(k)
	var want := _arg("grounds", "all")
	if want != "all":
		grounds = grounds.filter(func(k): return k == "(stand)" and "(stand)" in want.split(",") \
				or GroundModels.GROUNDS.get(k, "") in want.split(","))
	var levels := _arg("levels", "high,medium,low").split(",")
	MEASURE = float(_arg("measure", str(MEASURE)))
	# The oval is drawn into its own picture the size of its share of the match screen, as
	# PitchView draws it (1012 x 1242 on a 1080 x 2400 phone), whatever the window is.
	var sz := _arg("size", "%dx%d" % [VIEW.x, VIEW.y])
	var vp := SubViewport.new()
	vp.size = Vector2i(int(sz.split("x")[0]), int(sz.split("x")[1]))
	vp.own_world_3d = true
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(vp)
	var show := TextureRect.new()
	show.texture = vp.get_texture()
	show.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	show.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	show.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(show)
	move_child(show, 0)
	_view = vp
	RenderingServer.viewport_set_measure_render_time(vp.get_viewport_rid(), true)
	head = "%s | %s | 3D %dx%d\n" % [OS.get_model_name(), RenderingServer.get_video_adapter_name(), vp.size.x, vp.size.y]
	var f := FileAccess.open("user://oval3d_phone.txt", FileAccess.WRITE)
	if f:
		f.store_line(head + COLS)
	for g in grounds:
		for level in levels:
			label.text = "%s%s\n%s\nLoading %s, %s..." % [head, COLS, "\n".join(rows), g, level]
			await get_tree().process_frame
			var t0 := Time.get_ticks_usec()
			var director = load("res://scripts/ui/match/MatchDirector.gd").new()
			director.setup(res, res["events"])
			var oval := Oval3D.new()
			oval.quality = level
			oval.ground = "" if g == "(stand)" else g
			Oval3DQuality.apply_viewport(level, vp)
			vp.add_child(oval)
			oval.build(director, "FRE", "STK")
			oval.turf.apply("", _arg("slot", VignetteKickoff.DAY))
			var tv := Oval3DBroadcast.new(oval)
			var load_s := (Time.get_ticks_usec() - t0) / 1e6
			await _play(WARM, null, director, oval, tv)
			var acc := {"frames": [], "proc": 0.0, "cpu": 0.0, "gpu": 0.0, "draws": 0.0, "tris": 0.0, "n": 0,
					"draws_max": 0.0, "tris_max": 0.0}
			await _play(MEASURE, acc, director, oval, tv)
			var shots := _arg("shots", "")
			if shots != "":
				# The picture as measured, for checking each level's look (the table hidden).
				label.visible = false
				await RenderingServer.frame_post_draw
				var slug_s: String = "stand" if g == "(stand)" else GroundModels.GROUNDS[g]
				vp.get_texture().get_image().save_png("%s/%s_%s.png" % [shots, slug_s, level])
				for spec in _arg("looks", "").split(";", false):
					var parts := spec.split(":")
					var v := parts[1].split_floats(",")
					var cam: Camera3D = oval.camera
					cam.far = maxf(cam.far, 3000.0)
					cam.global_position = Vector3(v[0], v[1], v[2])
					cam.look_at(Vector3(v[3], v[4], v[5]), Vector3.UP)
					cam.fov = v[6] if v.size() > 6 else 60.0
					for i in 8:
						await get_tree().process_frame
					await RenderingServer.frame_post_draw
					vp.get_texture().get_image().save_png("%s/%s_%s_%s.png" % [shots, slug_s, level, parts[0]])
				label.visible = true
			var fr: Array = acc["frames"]
			fr.sort()
			var n := maxi(1, int(acc["n"]))
			var avg := 0.0
			for x in fr:
				avg += x
			avg /= maxf(1.0, fr.size())
			var slug: String = "(stand)" if g == "(stand)" else GroundModels.GROUNDS[g]
			var ms := OS.get_static_memory_usage() / 1048576.0
			var vm := Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0
			data.append({"ground": slug, "level": level, "frame": avg,
					"p95": fr[int(fr.size() * 0.95)] if fr.size() > 0 else 0.0, "proc": acc["proc"] / n,
					"cpu": acc["cpu"] / n, "gpu": acc["gpu"] / n, "draws": acc["draws"] / n,
					"tris": acc["tris"] / n, "draws_max": acc["draws_max"], "tris_max": acc["tris_max"],
					"mem_mb": ms, "vmem_mb": vm, "load_s": load_s,
					"tex_mb": Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0,
					"buf_mb": Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED) / 1048576.0,
					"supporters": oval.crowd.supporters if oval.crowd != null else 0})
			var row := "%-13s %-5s %5.1f %5.1f %5.2f %5.1f %5.1f %5d %5d %4d %5d %4.1f" % [slug, level.substr(0, 3),
					avg, fr[int(fr.size() * 0.95)] if fr.size() > 0 else 0.0,
					acc["proc"] / n, acc["cpu"] / n, acc["gpu"] / n, int(acc["draws"] / n), int(acc["tris"] / n / 1000.0),
					int(ms), int(vm), load_s]
			rows.append(row)
			print(row)
			if f:
				f.store_line(row)
				f.flush()
			oval.queue_free()
			for i in range(4):
				await get_tree().process_frame
	label.text = head + COLS + "\n" + "\n".join(rows) + "\nDone: screenshot this (also in user://oval3d_phone.txt)."
	var out := _arg("out", "")
	if out != "":
		var jf := FileAccess.open(out, FileAccess.WRITE)
		if jf:
			jf.store_string(JSON.stringify({"head": head.strip_edges(), "rows": data}, " "))
	if "quit" in OS.get_cmdline_user_args():
		get_tree().quit()


## aa=none|msaa2|msaa4|fxaa|msaa2+fxaa overrides the level's edge smoothing, to cost each one.
func _aa(vp: Viewport) -> void:
	var aa := _arg("aa", "")
	if aa == "":
		return
	vp.msaa_3d = Viewport.MSAA_4X if "msaa4" in aa else (Viewport.MSAA_2X if "msaa2" in aa else Viewport.MSAA_DISABLED)
	vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA if "fxaa" in aa else Viewport.SCREEN_SPACE_AA_DISABLED


func _play(secs: float, acc, director, oval: Oval3D, tv: Oval3DBroadcast) -> void:
	var t := 0.0
	var vp := _view.get_viewport_rid()
	while t < secs:
		await get_tree().process_frame
		var wall := minf(get_process_delta_time(), 0.1)
		t += wall
		director.advance(wall * SPEED)
		oval.sync(wall * SPEED)
		tv.frame(wall * SPEED, wall)
		if acc != null:
			acc["proc"] += Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0
			acc["frames"].append(wall * 1000.0)
			acc["cpu"] += RenderingServer.viewport_get_measured_render_time_cpu(vp)
			acc["gpu"] += RenderingServer.viewport_get_measured_render_time_gpu(vp)
			var dr := Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
			var tr := Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
			acc["draws"] += dr
			acc["tris"] += tr
			acc["draws_max"] = maxf(acc["draws_max"], dr)
			acc["tris_max"] = maxf(acc["tris_max"], tr)
			acc["n"] += 1
