class_name TopUpSheet
extends RefCounted
## Essendon's 2016 top-up players, when you coach them (director, 2026-11-13:
## "You pick them"; the Supplements saga, TODO row 142). With players banned
## for the season, you sign up to one for each, ten at most, from the players
## no club has signed. Shown over the pre-season screen or the hub. Back closes
## the sheet and leaves the spots open; playing the next round without
## finishing passes the spots left (YearEvents.settle_top_up). A rival
## Essendon signs its own (YearEvents.top_up).

const NAME := "TopUpSheet"
const SHOWN := 8


## Open the sheet over `host` if your top-up picks wait on you. `on_done` runs
## once the sheet closes for good (all signed, or Done).
static func open(host: Control, on_done: Callable) -> Control:
	if not YearEvents.top_up_waiting(GameState):
		return null
	var old := host.get_node_or_null(NAME)
	if old != null and is_instance_valid(old) and not old.is_queued_for_deletion():
		return old
	var t := YearEvents.top_up_pending(GameState)
	var year := GameState.season_year
	var most := int(t["most"])
	var signed: Array = t.get("signed", [])
	var box := UiKit.modal_box(host, 560.0, 0.0)
	var overlay: Control = box["overlay"]
	overlay.name = NAME
	var v: VBoxContainer = box["body"]
	v.add_child(UiKit.heading("Top-up players", UiKit.TITLE))
	var count := UiKit.lbl("Signed %d of %d" % [signed.size(), most], UiKit.NAME, UiKit.TEXT, true)
	count.name = "TopUpCount"
	v.add_child(count)
	var note := UiKit.lbl(("With your banned players out for %d, you may sign up to %d top-up players from those no club has signed. " +
			"Each plays %d only, on the senior minimum of %s, and is out of contract at the end of the season. " +
			"Playing round 1 before you finish leaves the spots you have not filled empty.") % [
			year, most, year, Contracts.money(RookieList.senior_wage(year))], 15, UiKit.TEXT)
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(note)
	for p in MidseasonDraft.pool(GameState).slice(0, SHOWN):
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 12)
		var txt := UiKit.lbl("%s  %d\n%s, %d, %s" % [GameDB.player_display_name(p), int(p.get("overall", 0)),
				DraftNight.position_words(p), int(p.get("age", 0)), MidseasonDraft.from_word(GameState, p)], 14, UiKit.TEXT)
		txt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		txt.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		row.add_child(PlaysLikeLine.under(txt, p))
		var sign := UiKit.btn("Sign", UiKit.NAME)
		sign.name = "TopUpSign_%s" % str(p["id"])
		sign.custom_minimum_size = Vector2(88, 48)
		sign.pressed.connect(_sign.bind(host, overlay, str(p["id"]), on_done))
		row.add_child(sign)
		v.add_child(row)
	var done := UiKit.btn("Done: leave %d spot%s empty" % [int(t["left"]), "" if int(t["left"]) == 1 else "s"], UiKit.NAME, true)
	done.name = "TopUpDone"
	done.custom_minimum_size = Vector2(0, 48)
	done.pressed.connect(_done.bind(overlay, on_done))
	(box["footer"] as VBoxContainer).add_child(done)
	return overlay


## Back: close the sheet, the spots stay open.
static func close_open(host: Control) -> bool:
	var s := host.get_node_or_null(NAME)
	if s == null or not is_instance_valid(s) or s.is_queued_for_deletion():
		return false
	s.queue_free()
	return true


static func _close(overlay: Control) -> void:
	if is_instance_valid(overlay):
		overlay.name = NAME + "Closed"
		overlay.queue_free()


static func _sign(host: Control, overlay: Control, player_id: String, on_done: Callable) -> void:
	YearEvents.sign_top_up(GameState, player_id)
	GameState.autosave()
	_close(overlay)
	# Spots left: the sheet opens again with the next best.
	if YearEvents.top_up_waiting(GameState) and is_instance_valid(host):
		open(host, on_done)
	else:
		if not YearEvents.top_up_pending(GameState).is_empty():
			YearEvents.finish_top_up(GameState)   # nobody left to sign
			GameState.autosave()
		if on_done.is_valid():
			on_done.call()


static func _done(overlay: Control, on_done: Callable) -> void:
	YearEvents.finish_top_up(GameState)
	GameState.autosave()
	_close(overlay)
	if on_done.is_valid():
		on_done.call()
