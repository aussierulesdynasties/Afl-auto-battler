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
##       [levels=high,low] [size=1080x1240] [measure=5] [out=rows.json] [shots=DIR] [quit]
## shots=DIR saves each ground and level's last measured frame as DIR/<ground>_<level>.png.
## Columns: frame = wall time a frame (mean, then the worst 5%); proc = the whole frame's process
## time; cpu / gpu = the renderer's own measured time; draws and ktris = what the frame drew;
## mem = the game's memory and the video memory in use, MB; load = s to build the scene.

const WARM := 2.0
var MEASURE := 5.0
const SPEED := 4.0

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
	var sz := _arg("size", "")
	if sz != "":
		get_tree().root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
		DisplayServer.window_set_size(Vector2i(int(sz.split("x")[0]), int(sz.split("x")[1])))
		await get_tree().process_frame
	var vp := get_viewport()
	RenderingServer.viewport_set_measure_render_time(vp.get_viewport_rid(), true)
	var win := DisplayServer.window_get_size()
	head = "%s | %s | 3D %dx%d\n" % [OS.get_model_name(), RenderingServer.get_video_adapter_name(), win.x, win.y]
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
			add_child(oval)
			oval.build(director, "FRE", "STK")
			oval.turf.apply("", VignetteKickoff.DAY)
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


func _play(secs: float, acc, director, oval: Oval3D, tv: Oval3DBroadcast) -> void:
	var t := 0.0
	var vp := get_viewport().get_viewport_rid()
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
