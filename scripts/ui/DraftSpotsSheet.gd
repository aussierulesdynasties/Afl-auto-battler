class_name DraftSpotsSheet
extends RefCounted
## Before the National Draft starts (director report, 2026-11-07: "I had 4
## picks in the draft but it only let me use two. Maybe my list was full, but
## I had no idea"). When the draft button is pressed and some of your picks
## have no senior list spot (GameState.draft_list_spots), this sheet states
## the rule and the consequence before anything happens: how full your senior
## list will be when the draft opens, which picks pass, and that delisting is
## only possible before the draft starts (out-of-contract players, on the
## Contracts tab; any player can be traded). Two answers, no advice: go to
## Trades & Contracts or start the draft.
##
## Must make room (director, 2026-11-12): a club takes at least three players,
## or every pick it holds when fewer. While your list is short of that
## (GameState.draft_room_short) the sheet is a gate: it says how many to delist,
## the draft cannot start, and its two routes are Delist (the Contracts tab) and
## Trade (the Trade tab). Once the rule is met, the picks left over pass as before.

const NAME := "DraftSpots"
## The off-season tab the gate's route opens ("" for the screen's own default).
## OffseasonScene reads it once on opening and clears it.
static var route_tab := ""


## True when the coach should see the sheet first: a pick of his would pass,
## or could pass if a player testing the market or holding his offer signs.
static func needed() -> bool:
	var g = GameState
	if g.draft != null and g.draft.intake_mode:
		return false   # resuming: the draft screen says it
	if g.season == null or not (g.season.is_season_over() or g.season.is_regular_done()):
		return false
	# An older save can reach the draft button before its off-season opened,
	# and this year's picks only count once it is open. Pressing the button
	# opens it anyway (begin_intake_draft's first step), so open it here.
	g.open_offseason()
	var s: Dictionary = g.draft_list_spots()
	var picks: Array = s["picks"]
	if g.draft_room_short() > 0:
		return true
	return not (s["passing"] as Array).is_empty() \
			or (int(s["maybe"]) > 0 and picks.size() > int(s["open"]) - int(s["maybe"]))


## Open the sheet over `host`. `on_start` begins the draft.
static func open(host: Control, on_start: Callable) -> Control:
	var old := host.get_node_or_null(NAME)
	if old != null and is_instance_valid(old) and not old.is_queued_for_deletion():
		return old
	var s: Dictionary = GameState.draft_list_spots()
	var box := UiKit.modal_box(host, 520.0, 0.0)
	var overlay: Control = box["overlay"]
	overlay.name = NAME
	var v: VBoxContainer = box["body"]
	v.add_child(UiKit.heading("Before the draft", UiKit.TITLE))
	for line in lines(s):
		var l := UiKit.lbl(str(line[0]), 15 if bool(line[1]) else 14,
				UiKit.BAD if str(line[2]) == "bad" else (UiKit.TEXT if bool(line[1]) else UiKit.MUTED), bool(line[1]))
		l.name = str(line[3])
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(l)
	var footer: VBoxContainer = box["footer"]
	var gate: String = GameState.draft_room_line()
	if gate != "":
		# The gate: no start until the list meets the rule; two routes to meet it.
		var said := UiKit.lbl(gate, 15, UiKit.BAD, true)
		said.name = "DraftRoomGate"
		said.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(said)
		v.move_child(said, 1)
		var row := UiKit.hbox(8)
		footer.add_child(row)
		for r in [["DraftRoomDelist", "Delist", "contracts"], ["DraftRoomTrade", "Trade", "trade"]]:
			var b := UiKit.btn(str(r[1]), UiKit.NAME, str(r[2]) == "contracts")
			b.name = str(r[0])
			b.custom_minimum_size = Vector2(0, 48)
			b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			var tab := str(r[2])
			b.pressed.connect(func() -> void:
				overlay.queue_free()
				route_tab = tab
				Router.go("offseason"))
			row.add_child(b)
		return overlay
	var delist := UiKit.btn("Trades & Contracts", UiKit.NAME)
	delist.name = "DraftSpotsDelist"
	delist.custom_minimum_size = Vector2(0, 48)
	delist.pressed.connect(func() -> void:
		overlay.queue_free()
		Router.go("offseason"))
	footer.add_child(delist)
	var start := UiKit.btn("Start the draft", UiKit.NAME, true)
	start.name = "DraftSpotsStart"
	start.custom_minimum_size = Vector2(0, 48)
	start.pressed.connect(func() -> void:
		overlay.queue_free()
		on_start.call())
	footer.add_child(start)
	return overlay


## The sheet's lines: [text, bold, tone, node name]. Facts and the rule only.
static func lines(s: Dictionary) -> Array:
	var out := []
	var picks: Array = s["picks"]
	var passing: Array = s["passing"]
	# Small counts in words, as the gate's line says them; list sizes stay digits.
	if bool(s.get("by_44", false)):
		# The 44, not the senior list, sets the spots: the count shown is that one.
		out.append(["Your senior and Category A rookie lists together will hold %d of %d when the draft opens: %s spot%s for %s pick%s." % [
				int(s["list"]), int(s["list_cap"]), GameState._count_word(int(s["open"])), "" if int(s["open"]) == 1 else "s",
				GameState._count_word(picks.size()), "" if picks.size() == 1 else "s"], true, "", "DraftSpotsCount"])
	else:
		out.append(["Your senior list will hold %d of %d when the draft opens: %s spot%s for %s pick%s." % [
				int(s["held"]), int(s["cap"]), GameState._count_word(int(s["open"])), "" if int(s["open"]) == 1 else "s",
				GameState._count_word(picks.size()), "" if picks.size() == 1 else "s"], true, "", "DraftSpotsCount"])
	if not passing.is_empty():
		out.append(["%s %s will pass." % ["Pick" if passing.size() == 1 else "Picks", Draft.picks_words(passing)],
				true, "bad", "DraftSpotsPassing"])
	if int(s["resign"]) > 0:
		out.append(["That counts %s undecided player%s who re-sign%s when the draft opens." % [
				GameState._count_word(int(s["resign"])), "" if int(s["resign"]) == 1 else "s", "s" if int(s["resign"]) == 1 else ""],
				false, "", "DraftSpotsResign"])
	if int(s["ties"]) > 0:
		out.append(["It counts %s father-son or academy player%s who join%s your list first." % [
				GameState._count_word(int(s["ties"])), "" if int(s["ties"]) == 1 else "s", "s" if int(s["ties"]) == 1 else ""],
				false, "", "DraftSpotsTies"])
	if int(s["maybe"]) > 0:
		out.append(["%s player%s testing the market or holding your offer could still sign; each who does takes a spot." % [
				GameState._count_word(int(s["maybe"]), true), "" if int(s["maybe"]) == 1 else "s"], false, "", "DraftSpotsMaybe"])
	if int(s["retiring"]) > 0:
		out.append(["Retiring players hold their spot until the draft is over.", false, "", "DraftSpotsRetiring"])
	out.append(["A club with a full senior list passes its picks, and so does a club with %d on its senior and Category A rookie lists together. Out-of-contract players can be delisted before the draft starts, and any player traded away; contracted players cannot be delisted. Rookies do not take a senior spot." % int(s.get("list_cap", Contracts.max_list())),
			false, "", "DraftSpotsRule"])
	return out


static func close_open(host: Control) -> bool:
	var s := host.get_node_or_null(NAME)
	if s == null or not is_instance_valid(s) or s.is_queued_for_deletion():
		return false
	s.queue_free()
	return true
