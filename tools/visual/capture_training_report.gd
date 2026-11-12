extends SceneTree
## Visual review tool for the monthly training report. Needs a real renderer:
##   godot --path . --script tools/visual/capture_training_report.gd -- --club FRE --w 390 --h 844 --out /tmp/tr
## Writes <out>_popup.png (the new report over the hub), <out>_sheet_end.png
## (its foot: retraining), <out>_hub.png (the hub once it is closed),
## <out>_training.png (the line on Training) and <out>_training_sheet.png (the
## report opened from it) and <out>_learn.png (its first Learn button: his
## Training page at the new-position choices).

var W := 390
var H := 844
var uiscale := 0.0


func _initialize() -> void:
	_run.call_deferred()


func _shot() -> Image:
	for i in range(8):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	return img


## Until the screen has swapped in under the cover and the cover has gone.
func _arrive(scene: String) -> void:
	for i in range(600):
		await process_frame
		if current_scene != null and current_scene.scene_file_path.ends_with(scene + ".tscn"):
			break
	for i in range(90):
		await process_frame


func _run() -> void:
	var out := "/tmp/tr"
	var club := "FRE"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out": out = str(a[i + 1])
			"--club": club = str(a[i + 1])
			"--w": W = int(a[i + 1])
			"--h": H = int(a[i + 1])
			"--uiscale": uiscale = float(a[i + 1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	state.autosave_enabled = false
	state.save_path = "user://capture.save"
	state.settings_path = "user://capture_settings.cfg"
	state.reset()
	state.set_setting("seen_training_intro", true)
	state.replay_seed = 2027
	state.tutorials = false
	state.event_sheets = false
	state.start_season(club, db.club_list(club))
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	if uiscale > 0.0:
		var sl = root.get_node("ScreenLayout")
		sl.ui_scale = uiscale
		sl._update_scale()
	await process_frame
	print("logical ", root.content_scale_size, " window ", root.size)
	var made := 0
	for p in state.my_list:
		if made < 3 and int(p.get("potential", 0)) < 95:
			p["potential"] = 95
			made += 1
	for i in range(4):
		state.advance()
	state.skip_media_conference()
	router.stack = ["main"]
	router.go("hub")
	await _arrive("HubScene")
	var hub := current_scene
	var sheet = hub.find_child("TrainingReportSheet", true, false)
	if sheet == null:
		print("no popup")
		quit(1)
		return
	for i in range(30):
		await process_frame
	(await _shot()).save_png(out + "_popup.png")
	if OS.get_environment("TRDEBUG") != "":
		for c in sheet.find_children("*", "Control", true, false):
			var m: Vector2 = c.get_combined_minimum_size()
			if m.x > 500:
				print("WIDE ", c.get_class(), " ", c.name, " ", m)
	var scrolls = sheet.find_children("*", "ScrollContainer", true, false)
	if not scrolls.is_empty():
		var sc: ScrollContainer = scrolls[0]
		sc.scroll_vertical = int(sc.get_v_scroll_bar().max_value)
	(await _shot()).save_png(out + "_sheet_end.png")
	sheet.queue_free()
	(await _shot()).save_png(out + "_hub.png")
	router.go("training")
	await _arrive("TrainingScene")
	(await _shot()).save_png(out + "_training.png")
	var link = current_scene.find_child("TrainingReportLink", true, false)
	if link == null:
		print("no link")
		quit(1)
		return
	link.emit_signal("pressed")
	for i in range(30):
		await process_frame
	(await _shot()).save_png(out + "_training_sheet.png")
	# The report's first Learn button: his Training page at the new-position choices.
	var sheet2 = current_scene.find_child("TrainingReportSheet", true, false)
	var learn: Button = null
	if sheet2 != null:
		for b in sheet2.find_children("LearnGo_*", "Button", true, false):
			learn = b
			break
	if learn == null:
		print("no Learn button")
		quit(1)
		return
	learn.emit_signal("pressed")
	for i in range(30):
		await process_frame
	(await _shot()).save_png(out + "_learn.png")
	print("wrote ", out)
	quit(0)
