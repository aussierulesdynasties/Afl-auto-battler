extends SceneTree
## Visual review tool for Create a player's preview (PlayerPreview), on a phone
## (390x844) or any size given as --size WxH (1280x720 for the PC).
## Needs a real renderer:
##   godot --path . --script tools/visual/capture_forge_player.gd -- --out /tmp/forge_player
## Writes <out>_sheet.png: a new prospect as he starts; a named midfielder with
## his own look and number; a tall ruckman; a small forward, bald; a key forward in
## one of the 3D-only cuts and his favourite club's guernsey; the form scrolled to the
## look with the preview still in view. Then <out>_styles.png: the preview panel alone
## in every hair style (Appearance.HAIR_STYLES), in order, each a different colouring.

var W := 390
var H := 844

## [first, last, role, height, number, skin, hair colour, hair style, favourite club]
const LOOKS := [
	["Jack", "Mercer", "MID", 186, 7, 1, 0, "swept_back", ""],
	["Tom", "Okafor", "RUCK", 204, 23, 4, 0, "dreadlocks", ""],
	["Billy", "Nash", "FWD", 176, 41, 0, 4, "bald", ""],
	["Sam", "Petrakis", "FWD", 192, 12, 2, 2, "quiff", "FRE"],
]


func _initialize() -> void:
	_run.call_deferred()


func _shot() -> Image:
	for i in range(8):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	return img


func _run() -> void:
	var out := "/tmp/forge_player"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--size":
			var wh := str(a[i + 1]).split("x")
			W = int(wh[0])
			H = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	state.autosave_enabled = false
	state.save_path = "user://capture.save"
	state.settings_path = "user://capture_settings.cfg"
	state.reset()
	state.set_forge_player({})
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	var shots := []
	var scene = load("res://scenes/ClubForgeScene.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	scene.find_child("ForgeCreatePlayer", true, false).emit_signal("pressed")
	shots.append(await _shot())
	for l in LOOKS:
		var s: Dictionary = scene._spec
		s["first"] = l[0]
		s["last"] = l[1]
		s["role"] = l[2]
		s["height_cm"] = l[3]
		s["number_pref"] = l[4]
		s["look"]["skin"] = l[5]
		s["look"]["hair"] = l[6]
		s["look"]["hair_style"] = l[7]
		s["fav_club"] = l[8]
		scene._build()
		shots.append(await _shot())
	var sc: ScrollContainer = scene._scroll
	sc.scroll_vertical = int(sc.get_v_scroll_bar().max_value * 0.8)
	shots.append(await _shot())
	var sheet := Image.create(W * shots.size(), H, false, Image.FORMAT_RGBA8)
	for i in range(shots.size()):
		sheet.blit_rect(shots[i], Rect2i(0, 0, W, H), Vector2i(i * W, 0))
	sheet.save_png(out + "_sheet.png")
	print("wrote ", out, "_sheet.png")
	# Every style on the preview panel itself, cut from the screen.
	sc.scroll_vertical = 0
	var panel: Control = scene.find_child("ForgePlayerPreview", true, false)
	var tiles := []
	var styles: Array = Appearance.HAIR_STYLES
	for i in range(styles.size()):
		var s: Dictionary = scene._spec
		s["look"]["hair_style"] = styles[i]
		s["look"]["skin"] = i % Appearance.SKIN.size()
		s["look"]["hair"] = (i * 2 + 1) % Appearance.HAIR.size()
		var img := await _shot()
		panel = scene.find_child("ForgePlayerPreview", true, false)
		# The screen image is at the window's pixel size; the panel's rect is in the viewport's.
		var k := img.get_width() / root.get_visible_rect().size.x
		var r := panel.get_global_rect()
		tiles.append(img.get_region(Rect2i(Vector2i(r.position * k), Vector2i(r.size * k))))
	var tw: int = tiles[0].get_width()
	var th: int = tiles[0].get_height()
	var per := 8
	var grid := Image.create(tw * per, th * ceili(tiles.size() / float(per)), false, Image.FORMAT_RGBA8)
	grid.fill(Color("#15171c"))
	for i in range(tiles.size()):
		grid.blit_rect(tiles[i], Rect2i(0, 0, tw, th), Vector2i((i % per) * tw, (i / per) * th))
	grid.save_png(out + "_styles.png")
	print("wrote ", out, "_styles.png")
	quit(0)
