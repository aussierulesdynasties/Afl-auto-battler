extends SceneTree
## Contact sheet per figure strip for the player looks (register row 6): every frame of the
## strip (columns) in every hair style (rows, Appearance.HAIR_STYLES), each row wearing face
## (row mod 5), styles wrapped into a grid, through the game's own draw (StoppageVignette.draw_frame, figure.gdshader).
##   godot --path . --script tools/visual/capture_strip_looks.gd -- \
##       --out tools/output/looks --strips average/ready/front,ruck/tap/back
## Writes <out>/<body>_<anim>_<facing>.png. Needs a real renderer and a window.

const K := 1.5
const LEFT := 110.0
const LOOKS := [[1, 2], [4, 0], [0, 4], [2, 1], [3, 3]]


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "/tmp/looks"
	var strips: PackedStringArray = []
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		elif str(a[i]) == "--strips":
			strips = str(a[i + 1]).split(",")
	DirAccess.make_dir_recursive_absolute(out)
	await process_frame
	var SV: GDScript = load("res://scripts/ui/match/StoppageVignette.gd")
	var styles: Array = Appearance.HAIR_STYLES
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.content_scale_factor = 1.0
	for key in strips:
		var p := key.split("/")
		var info := VignetteFigures.strip(p[0], p[1], p[2])
		if info.is_empty():
			print("no strip ", key)
			continue
		var fw := float(info["size"][0]) * K
		var fh := float(info["size"][1]) * K
		var n := int(info["frames"])
		var bw := LEFT + fw * n + 10.0
		var cols := maxi(1, int(2400.0 / bw))
		var rows := int(ceil(float(styles.size()) / cols))
		var w := int(bw * cols)
		var h := int(40 + fh * rows)
		root.size = Vector2i(w, h)
		DisplayServer.window_set_size(Vector2i(w, h))
		var bg := ColorRect.new()
		bg.color = Color(0.29, 0.44, 0.25)
		bg.size = Vector2(w, h)
		root.add_child(bg)
		var c := Control.new()
		c.size = Vector2(w, h)
		var kit := {"design": "plain", "base": Color(0.1, 0.1, 0.12), "pattern": Color(1, 1, 1),
				"pattern2": Color(1, 1, 1), "shorts": Color(1, 1, 1)}
		c.material = SV.figure_material([kit])
		c.draw.connect(func():
			var font := ThemeDB.fallback_font
			c.draw_string(font, Vector2(8, 26), key, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
			for r in styles.size():
				var y := 40.0 + int(r / cols) * fh
				var x0 := (r % cols) * bw
				c.draw_string(font, Vector2(x0 + 8, y + 24), styles[r], HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color.WHITE)
				c.draw_string(font, Vector2(x0 + 8, y + 42), "face %d" % (r % VignetteLooks.FACES.size()),
						HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color.WHITE)
				var look: Array = LOOKS[r % LOOKS.size()]
				var col: Color = SV.look_colour(0, {"skin": look[0], "hair": look[1]})
				for f in n:
					var feet := Vector2(x0 + LEFT + f * fw + float(info["pivot"][0]) * K, y + float(info["pivot"][1]) * K)
					SV.draw_frame(c, feet, info, f, K, col, false, Color(0, 0, 0, 0), Transform2D.IDENTITY,
							styles[r], r % VignetteLooks.FACES.size())
		)
		root.add_child(c)
		for i in range(4):
			c.queue_redraw()
			await process_frame
		var img := root.get_viewport().get_texture().get_image()
		var fn := "%s/%s.png" % [out, key.replace("/", "_")]
		img.save_png(fn)
		print("wrote ", fn)
		c.queue_free()
		bg.queue_free()
		await process_frame
	quit()
