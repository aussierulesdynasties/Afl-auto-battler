class_name ProblemReport
extends RefCounted
## "Report a problem" (T3.R43): a plain-text note the player pastes into a
## message to the developer. It holds the build, the career seed, where the
## career is, the screen and the last twenty lines of the match feed. It is
## only copied to the clipboard; nothing is ever sent from the game.

const FEED_LINES := 20

## The feed lines of the match watched most recently, oldest first (at most
## FEED_LINES), and which match they came from. Kept for the session only.
static var _feed: Array = []
static var _feed_title := ""


## A match screen opened: its feed starts empty.
static func start_feed(title: String) -> void:
	_feed = []
	_feed_title = title


## One line as the match feed shows it.
static func note_feed(text: String) -> void:
	var t := text.strip_edges()
	if t == "":
		return
	_feed.append(t)
	while _feed.size() > FEED_LINES:
		_feed.pop_front()


static func feed() -> Array:
	return _feed.duplicate()


## The note as it is copied. `screen` is the screen the player was on.
static func text(screen: String) -> String:
	var out: PackedStringArray = []
	out.append("Aussie Rules Dynasties: problem report")
	out.append("What happened: ")
	out.append("")
	out.append("Build: %s" % BuildInfo.label())
	out.append("Seed: %s" % (str(GameState.career_seed) if GameState.has_career() else "no career"))
	out.append("Round: %s" % _where())
	out.append("Screen: %s" % (screen if screen != "" else "main menu"))
	if _feed.is_empty():
		out.append("Match feed: no match watched this session")
	else:
		out.append("Match feed (last %d lines, %s):" % [_feed.size(), _feed_title])
		for l in _feed:
			out.append(str(l))
	return "\n".join(out) + "\n"


## Copies the note to the clipboard and returns it.
static func copy(screen: String) -> String:
	var t := text(screen)
	DisplayServer.clipboard_set(t)
	return t


static func _where() -> String:
	if not GameState.has_career():
		return "no career"
	var meta: Dictionary = GameState._save_meta()
	return "%d, %s" % [int(meta.get("year", GameState.season_year)), str(meta.get("stage", ""))]
