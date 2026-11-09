extends SceneTree
## Review sheet for the premiership-year tattoos (VignetteInk, TODO row 73): figures with no
## flag, one, two and three premiership years, through the game's own draw
## (StoppageVignette.draw_frame and figure.gdshader), in three skin tones, from the front,
## ready, side-on running and from behind - close up and at phone size.
##   godot --path . --script tools/visual/capture_ink.gd -- --out /tmp/ink
##   ... -- --out /tmp/ink --gif jog,side_l    (one close-up PNG per frame of that move)
## Writes <out>.png (or <out>_<i>.png). Needs a real renderer and a window.

## [skin, hair]: light skin / brown, mid skin / black, deep skin / black.
const LOOKS := [[1, 2], [3, 0], [5, 0]]
const POSES := [["idle", "front", 0], ["ready", "front", 1], ["jog", "side_l", 2], ["jog", "back_r", 4]]
const CLOSE := 2.25
const PHONE := 0.32
const CELL := 210.0
const ROW := 470.0
const LEFT := 110.0


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "/tmp/ink"
	var gif := ""
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		elif str(a[i]) == "--gif":
			gif = str(a[i + 1])
	await process_frame
	var SV: GDScript = load("res://scripts/ui/match/StoppageVignette.gd")
	var kit := {"design": "plain", "base": Color(0.06, 0.11, 0.33), "pattern": Color(0.85, 0.1, 0.15),
			"pattern2": Color(0.85, 0.1, 0.15), "shorts": Color(0.06, 0.11, 0.33)}
	var w := int(LEFT + CELL * POSES.size() * LOOKS.size() + 20) if gif == "" else 3 * 260
	var h := int(ROW * 4 + 20) if gif == "" else 520
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.content_scale_factor = 1.0
	root.size = Vector2i(w, h)
	DisplayServer.window_set_size(Vector2i(w, h))
	var bg := ColorRect.new()
	bg.color = Color(0.29, 0.44, 0.25)
	bg.size = Vector2(w, h)
	root.add_child(bg)
	var c := Control.new()
	c.size = Vector2(w, h)
	c.material = SV.figure_material([kit])
	var frame := [0]
	SV.log_frames = true
	c.draw.connect(func():
		if gif != "":
			var parts := gif.split(",")
			var info := VignetteFigures.strip("average", parts[0], parts[1])
			for j in LOOKS.size():
				var col: Color = SV.look_colour(0, {"skin": LOOKS[j][0], "hair": LOOKS[j][1]})
				SV.draw_frame(c, Vector2(130 + j * 260, 490), info, frame[0], CLOSE, col, false,
						Color(0, 0, 0, 0), Transform2D.IDENTITY, "short_crop", 1, 3)
			return
		var font := ThemeDB.fallback_font
		for r in range(4):
			var y := 10.0 + r * ROW
			c.draw_string(font, Vector2(8, y + 24), ["no flag", "1 flag", "2 flags", "3 flags"][r],
					HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)
			var x := LEFT
			for look in LOOKS:
				for pose in POSES:
					var info := VignetteFigures.strip("average", pose[0], pose[1])
					var col: Color = SV.look_colour(0, {"skin": look[0], "hair": look[1]})
					SV.draw_frame(c, Vector2(x + CELL * 0.5, y + 440.0), info, int(pose[2]), CLOSE, col, false,
							Color(0, 0, 0, 0), Transform2D.IDENTITY, "short_crop", 1, r)
					# Phone size, as a match draws him, top left of the cell.
					SV.draw_frame(c, Vector2(x + 30.0, y + 80.0), info, int(pose[2]), PHONE, col, false,
							Color(0, 0, 0, 0), Transform2D.IDENTITY, "short_crop", 1, r)
					x += CELL
	)
	root.add_child(c)
	if gif == "":
		for i in range(4):
			c.queue_redraw()
			await process_frame
		root.get_viewport().get_texture().get_image().save_png(out + ".png")
		print("wrote ", out + ".png", " ink draws ", SV.ink_log.size())
	else:
		var parts := gif.split(",")
		var n := int(VignetteFigures.strip("average", parts[0], parts[1])["frames"])
		for f in range(n):
			frame[0] = f
			for i in range(3):
				c.queue_redraw()
				await process_frame
			root.get_viewport().get_texture().get_image().save_png("%s_%02d.png" % [out, f])
		print("wrote ", n, " frames, ink draws ", SV.ink_log.size())
	var tex := {}
	for e in SV.ink_log:
		tex[(e["texture"] as Texture2D).resource_path] = true
	print("ink textures ", tex.keys())
	quit()
