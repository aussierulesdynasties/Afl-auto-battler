class_name OptionsSheet
extends RefCounted
## Settings, from the main menu and from the hub's top bar: display and flow
## preferences apply at once; career actions keep destructive changes behind
## an explicit confirmation.

const APPEARANCE_OPTIONS := [["dark", "Dark"], ["light", "Light"]]
const NAME_OPTIONS := [["generated", "Generated"], ["real", "Real"]]
const NAMES_INFO := "Real shows each player's AFL name; generated names are invented. Ratings and results are the same either way."
const SPEED_OPTIONS := [["1", "1x"], ["2", "2x"], ["4", "4x"], ["8", "8x"]]


## Opens the sheet over `host`. `in_career` adds Main menu and Delete this
## career. Returns the overlay (free it to close).
static func open(host: Control, in_career: bool, quit := false) -> Control:
	var box := UiKit.modal_box(host, 440.0, 0.0)
	var overlay: Control = box["overlay"]
	overlay.name = "Settings"
	UiKit.close_on_outside_tap(box)
	var v: VBoxContainer = box["body"]
	v.add_theme_constant_override("separation", 6)
	v.add_child(UiKit.heading("Settings", UiKit.H1))

	_row(v, "Appearance", "SettingsAppearance", APPEARANCE_OPTIONS,
			GameState.appearance(), "Changes the interface only; club colours and the football ground stay as they are.",
			func(k):
				if GameState.set_appearance(k):
					overlay.queue_free()
					host.get_tree().call_deferred("reload_current_scene"))
	_row(v, "Player names", "SettingsNames", NAME_OPTIONS,
			"real" if GameState.show_real_names else "generated", NAMES_INFO,
			func(k): GameState.set_show_real_names(k == "real"))
	_row(v, "Mute sounds", "SettingsMuteSounds", [["off", "Off"], ["on", "On"]],
			"on" if GameState.sounds_muted() else "off",
			"Mutes all music and sound effects.",
			func(k): GameState.set_sounds_muted(k == "on"))
	# No row for a control that does nothing: it returns with the director's tracks.
	if not MusicManager.TRACK_PATHS.is_empty():
		_row(v, "Music", "SettingsMusic", AudioLevels.LEVELS, GameState.music_level(),
				"The music between matches.", func(k): GameState.set_music_level(k))
	_row(v, "Crowd", "SettingsCrowd", AudioLevels.LEVELS, GameState.crowd_level(),
			"The crowd at a match you watch. The match tells you the same either way.",
			func(k): GameState.set_crowd_level(k))
	_row(v, "Button sounds", "SettingsButtonSounds", AudioLevels.LEVELS, GameState.button_sounds(),
			"A boot through the ball when you press a button, a stud tap on a choice, the siren at the end of a match or a draft, and the crowd when a result lands.",
			func(k): GameState.set_button_sounds(k))
	if Feel.phone():
		_row(v, "Vibration", "SettingsVibration", [["on", "On"], ["off", "Off"]],
				"on" if GameState.haptics_on() else "off",
				"A light buzz when you press a button, and a firmer one when a result lands.",
				func(k): GameState.set_haptics_on(k == "on"))
	_row(v, "Ask before simming the week for me", "SettingsSimConfirm", [["on", "On"], ["off", "Off"]],
			"on" if GameState.confirm_sim_round() else "off",
			"Sim the week plays out your own match without you. With this on, it asks first.",
			func(k): GameState.set_confirm_sim_round(k == "on"))
	_row(v, "Match speed", "SettingsSpeed", SPEED_OPTIONS,
			str(int(GameState.match_speed())), "How fast a match you watch starts. You can change it during the game.",
			func(k): GameState.set_match_speed(float(k)))
	if ScreenLayout.is_desktop():
		var sizes := []
		for row in ScreenLayout.SCREEN_SIZES:
			sizes.append([row[0], row[1]])
		_row(v, "Screen size", "SettingsScreenSize", sizes, GameState.screen_size(),
				"Everything bigger, for a big screen across the room. TV suits a television from the couch.",
				func(k): GameState.set_screen_size(k))
		_row(v, "Display", "SettingsFullscreen", [["on", "Fullscreen"], ["off", "Window"]],
				"on" if GameState.fullscreen() else "off",
				"Fullscreen fills the screen with no border; Window opens maximised. Alt+Enter switches.",
				func(k): GameState.set_fullscreen(k == "on"))
	_row(v, "Tutorials", "SettingsTutorials", [["on", "On"], ["off", "Off"]],
			"on" if GameState.tutorials_on() else "off",
			"A short note the first time you open each screen. Off stops them opening by themselves; notes you've already read don't come back.",
			func(k): GameState.set_tutorials_on(k == "on"))
	_row(v, "Battery saver", "SettingsBatterySaver", [["off", "Off"], ["on", "On"]],
			"on" if GameState.battery_saver() else "off",
			"Draws 30 frames a second instead of 60. Uses less battery; matches and scenes play the same, a little less smoothly.",
			func(k): GameState.set_battery_saver(k == "on"))
	_row(v, "Screen shake", "SettingsScreenShake", [["on", "On"], ["off", "Off"]],
			"on" if GameState.screen_shake_on() else "off",
			"A small, short shake of the oval when a goal is scored. Off keeps the screen still.",
			func(k): GameState.set_screen_shake_on(k == "on"))
	_row(v, "Reduced motion", "SettingsReducedMotion", [["off", "Off"], ["on", "On"]],
			"on" if GameState.reduced_motion() else "off",
			"On keeps the screen still: no fades, counting numbers, pulses, moving backgrounds or shake. Everything shows the same.",
			func(k): GameState.set_reduced_motion(k == "on"))
	_row(v, "Vignettes", "SettingsVignettes", [["on", "On"], ["off", "Off"]],
			"on" if GameState.vignettes_on() else "off",
			"The match-day scenes: the banner, the centre ball-up, replays, the press conference and the awards. Off skips the scenes; every call and result stays the same.",
			func(k): GameState.set_vignettes_on(k == "on"))
	_row(v, "Match view", "SettingsMatchFigures", [["tokens", "Tokens"], ["figures", "Figures (prototype)"]],
			"figures" if GameState.match_figures_on() else "tokens",
			"Figures draws the six players nearest the ball as small footballers on the oval. A prototype for judging on a phone; the match plays the same either way.",
			func(k): GameState.set_match_figures_on(k == "figures"))
	_row(v, "Centre ball-up scene every match", "SettingsBounceScene", [["off", "Off"], ["on", "On"]],
			"on" if GameState.bounce_scene_every_match() else "off",
			"For playtesting: the centre ball-up call comes at the first centre ball-up of every last quarter you coach, whatever the score.",
			func(k): GameState.set_bounce_scene_every_match(k == "on"))

	_saves(v, overlay, host)

	if in_career:
		v.add_child(UiKit.spacer(UiKit.GAP))
		v.add_child(UiKit.rule())
		var menu := UiKit.btn("Main menu", UiKit.NAME)
		menu.name = "OptionsMainMenu"
		menu.custom_minimum_size = Vector2(0, 44)
		menu.pressed.connect(func():
			overlay.queue_free()
			Router.to_main_menu())
		v.add_child(menu)
		var fresh := UiKit.btn("New career", UiKit.NAME)
		fresh.name = "OptionsNewCareer"
		fresh.custom_minimum_size = Vector2(0, 44)
		fresh.tooltip_text = "Your current save is kept until you confirm the new career."
		fresh.pressed.connect(func():
			overlay.queue_free()
			Router.to_new_career_setup())
		v.add_child(fresh)
		var confirm := UiKit.vbox(6)
		confirm.name = "DeleteConfirm"
		confirm.visible = false
		var del := UiKit.danger_btn("Delete this career", UiKit.NAME)
		del.name = "OptionsDelete"
		del.custom_minimum_size = Vector2(0, 44)
		del.pressed.connect(func():
			del.visible = false
			confirm.visible = true)
		v.add_child(del)
		var warn := UiKit.lbl("This deletes your saved career for good. It cannot be undone.",
				UiKit.BODY, UiKit.BAD)
		warn.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		confirm.add_child(warn)
		var row := UiKit.hbox(8)
		var keep := UiKit.btn("Keep it", UiKit.NAME)
		keep.name = "OptionsDeleteCancel"
		keep.custom_minimum_size = Vector2(0, 44)
		keep.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		keep.pressed.connect(func():
			confirm.visible = false
			del.visible = true)
		row.add_child(keep)
		var go := UiKit.btn("Delete career", UiKit.NAME, true)
		go.name = "OptionsDeleteConfirm"
		go.custom_minimum_size = Vector2(0, 44)
		go.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		go.pressed.connect(func():
			overlay.queue_free()
			GameState.delete_saved_career()
			GameState.reset()
			Router.to_main_menu(false))
		row.add_child(go)
		confirm.add_child(row)
		v.add_child(confirm)

	if in_career:
		# Read-only: the two dials are chosen at New career and kept with the career.
		v.add_child(UiKit.spacer(UiKit.GAP))
		var dials := UiKit.detail(GameState.career_dials_line())
		dials.name = "OptionsCareerDials"
		v.add_child(dials)

	v.add_child(UiKit.spacer(UiKit.GAP))
	var ver := UiKit.lbl("Version %s" % BuildInfo.label(),
			UiKit.SMALL, UiKit.MUTED)
	ver.name = "OptionsVersion"
	v.add_child(ver)

	var done := UiKit.btn("Done", UiKit.NAME, true)
	done.name = "SettingsDone"
	done.custom_minimum_size = Vector2(0, 44)
	done.pressed.connect(func(): overlay.queue_free())
	box["footer"].add_child(done)
	if quit and not OS.has_feature("web"):
		var q := UiKit.btn("Quit game", UiKit.NAME)
		q.name = "QuitGame"
		q.pressed.connect(func(): host.get_tree().quit())
		box["footer"].add_child(q)
	return overlay


## A labelled row of choices, the current one outlined, with its one-line
## explanation under it.
static func _row(v: VBoxContainer, title: String, node_name: String, options: Array,
		current: String, note: String, on_pick: Callable) -> void:
	v.add_child(UiKit.spacer(4))
	v.add_child(UiKit.lbl(title, UiKit.BODY, UiKit.TEXT, true))
	v.add_child(UiKit.choice_grid(node_name, options, current, options.size(), on_pick))
	var l := UiKit.lbl(note, UiKit.SMALL, UiKit.MUTED)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(l)


## Backups and earlier saves (row 57): write the career to a file the coach
## keeps, load one back, or go back to one of the last few saves. Loading or
## restoring keeps the career it replaces as an earlier save, so each can be
## undone from the same list.
const SAVES_INFO := "Back up writes your career to a file you keep, to move it to another device or keep it safe. Loading a backup or an earlier save keeps the career it replaces in the list below, so you can go back."


static func _saves(v: VBoxContainer, overlay: Control, host: Control) -> void:
	var box := UiKit.vbox(6)
	box.name = "SettingsSaves"
	v.add_child(UiKit.spacer(UiKit.GAP))
	v.add_child(UiKit.rule())
	box.add_child(UiKit.lbl("Your career saves", UiKit.NAME, UiKit.TEXT, true))
	var info := UiKit.detail(SAVES_INFO)
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(info)
	var status := UiKit.lbl("", UiKit.BODY, UiKit.TEXT)
	status.name = "SavesStatus"
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	status.visible = false
	var say := func(text: String, bad: bool):
		status.text = text
		status.add_theme_color_override("font_color", UiKit.BAD if bad else UiKit.TEXT)
		status.visible = text != ""
	# Mid-match the career cannot change under the match.
	var locked := not GameState.pending_match.is_empty()
	var row := UiKit.hbox(8)
	var backup_btn := UiKit.btn("Back up career", UiKit.NAME)
	backup_btn.name = "SavesExport"
	backup_btn.custom_minimum_size = Vector2(0, 44)
	backup_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	backup_btn.disabled = locked or not (GameState.has_career() or GameState.has_saved_career())
	backup_btn.pressed.connect(func():
		var bytes := GameState.export_career()
		if bytes.is_empty():
			say.call("There is no saved career to back up yet.", true)
			return
		SaveFiles.save_to_device(host, bytes, GameState.export_file_name(), func(ok: bool):
			say.call("Backed up." if ok else "The backup could not be written there.", not ok)))
	row.add_child(backup_btn)
	var import_btn := UiKit.btn("Load a backup", UiKit.NAME)
	import_btn.name = "SavesImport"
	import_btn.custom_minimum_size = Vector2(0, 44)
	import_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	import_btn.disabled = locked
	import_btn.pressed.connect(func():
		SaveFiles.pick_from_device(host, func(bytes: PackedByteArray):
			var why := GameState.import_career(bytes)
			if why != "":
				say.call(why, true)
				return
			_open_saved(overlay, say)))
	row.add_child(import_btn)
	box.add_child(row)
	var earlier := GameState.saved_career_history()
	if not earlier.is_empty():
		box.add_child(UiKit.lbl("Earlier saves", UiKit.BODY, UiKit.TEXT, true))
		for meta in earlier:
			var line := UiKit.hbox(8)
			line.name = "EarlierSave%d" % int(meta["slot"])
			var what := UiKit.lbl(_save_line(meta), UiKit.BODY, UiKit.TEXT)
			what.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			what.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			line.add_child(what)
			var go := UiKit.btn("Restore", UiKit.NAME)
			go.name = "Restore"
			go.custom_minimum_size = Vector2(110, 44)
			go.disabled = locked
			var slot := int(meta["slot"])
			go.pressed.connect(func():
				if not GameState.restore_saved_career(slot):
					say.call("That save could not be read. Your career is unchanged.", true)
					return
				_open_saved(overlay, say))
			line.add_child(go)
			box.add_child(line)
	box.add_child(status)
	v.add_child(box)


## "Fremantle · 2027 · Round 6 · saved 5 Nov 14:02"
static func _save_line(meta: Dictionary) -> String:
	var bits: PackedStringArray = []
	for k in ["club_name", "year", "stage"]:
		if str(meta.get(k, "")) != "":
			bits.append(str(meta[k]))
	var at := str(meta.get("saved_at", ""))
	if at.length() >= 16:
		bits.append("saved " + at.substr(0, 10) + " " + at.substr(11, 5))
	return "  ·  ".join(bits)


## The save on disk is now the one chosen: open it where it stands.
static func _open_saved(overlay: Control, say: Callable) -> void:
	if not GameState.load_career():
		say.call(GameState.SAVE_UNREADABLE, true)
		return
	if is_instance_valid(overlay):
		overlay.queue_free()
	Router.go("hub" if GameState.season != null else "draft")
