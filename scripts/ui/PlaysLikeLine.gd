class_name PlaysLikeLine
## The one line "Plays like: <real AFL player>" under a draft prospect
## (director, 2026-11-12; the rule is scripts/sim/PlaysLike.gd). Its own line,
## never part of his name: the earlier ruling that a display name carries no
## "plays like" stands (GameDB.player_display_name).


## The line for `p`, named "PlaysLike_<id>"; null when there is nobody to
## compare him with. It wraps rather than cuts on a phone.
static func make(p: Dictionary, fs := UiKit.SECONDARY, colour := UiKit.TEXT) -> Label:
	var text := PlaysLike.line(p)
	if text == "":
		return null
	var l := UiKit.lbl(text, fs, colour)
	l.name = "PlaysLike_" + str(p.get("id", ""))
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


## `above` with the line under it, for a row that was one label and a button.
static func under(above: Control, p: Dictionary, fs := UiKit.SECONDARY) -> Control:
	var l := make(p, fs)
	if l == null:
		return above
	var v := UiKit.vbox(2)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_child(above)
	v.add_child(l)
	return v
