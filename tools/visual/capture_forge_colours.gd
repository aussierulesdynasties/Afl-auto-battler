extends SceneTree
## Visual review tool for the Club Forge's wider palette (director 2026-11-11),
## on a phone (390x844), dark theme. Needs a real renderer:
##   godot --path . --script tools/visual/capture_forge_colours.gd -- --out /tmp/forge_colours
## Writes <out>_1_palette.png (the colour picker with every colour, painting
## with a new one), <out>_2_guernsey.png (a guernsey made in new colours:
## bottle green with old gold hoops and cream trim, on the phone's paint
## canvas), <out>_3_saved.png (the Forge with that club saved) and
## <out>_sheet.png (the three side by side).

const W := 390
const H := 844


func _initialize() -> void:
	_run.call_deferred()


func _shot() -> Image:
	for i in range(8):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	return img


## Scroll the form so `node` sits `top` px below the top of the scroll.
func _show(scene: Node, node: Control, top: float) -> void:
	await process_frame
	await process_frame
	var sc: ScrollContainer = scene._scroll
	var y := node.get_global_rect().position.y - sc.get_global_rect().position.y + sc.scroll_vertical
	sc.scroll_vertical = int(maxf(0.0, y - top))


func _run() -> void:
	var out := "/tmp/forge_colours"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
	await process_frame
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	var state = root.get_node("GameState")
	state.autosave_enabled = false
	state.save_path = "user://capture.save"
	state.settings_path = "user://capture_settings.cfg"
	state.reset()
	state.set_forge_player({})
	state.set_forge_club({})
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	var scene = load("res://scenes/ClubForgeScene.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	scene.find_child("ForgeCreateClub", true, false).emit_signal("pressed")
	await process_frame
	scene._pick_place("port-melbourne")
	scene._club["short"] = "Borough"
	scene._club["code"] = "PMB"
	scene._club["design"] = "hoops"
	scene._club["primary"] = "#0C4A2F"
	scene._club["secondary"] = "#B8913A"
	scene._club["accent"] = "#EDE3C8"
	scene._kit_touched = true
	scene._build()
	scene._brush = "#1FB8C9"
	scene._rebuild_paint()
	var shots := []
	await _show(scene, scene.find_child("ForgePalette", true, false), 90.0)
	shots.append(await _shot())
	await _show(scene, scene.find_child("ForgePaint", true, false), 120.0)
	shots.append(await _shot())
	scene._on_save_club()
	shots.append(await _shot())
	var names := ["1_palette", "2_guernsey", "3_saved"]
	var sheet := Image.create(W * shots.size(), H, false, Image.FORMAT_RGBA8)
	for i in range(shots.size()):
		(shots[i] as Image).save_png("%s_%s.png" % [out, names[i]])
		sheet.blit_rect(shots[i], Rect2i(0, 0, W, H), Vector2i(i * W, 0))
	sheet.save_png(out + "_sheet.png")
	state.set_forge_club({})
	print("wrote ", out + "_sheet.png")
	quit(0)
