class_name PatchNotes
extends RefCounted
## What changed in each version, in football words, shown once on the main
## menu the first time a new version opens (row T7.R84). The quiet version
## line at the foot of the menu opens the same sheet again.
##
## Whoever bumps config/version in project.godot adds that version here in
## the same change (tests/run_save_release_tests.gd fails the build without
## it). Each line names the football change the coach will meet, never a
## working name or a number from the tracker, and nothing that was removed
## (director, 2026-10-13: "please ensure you dont write misleading patch
## notes"; 2026-10-18: "dont mention the removals in the devlog").

const NOTES := {
	"1.0.14": [
		"Every call on match day shows what you gain, what it costs and the odds.",
		"League news covers every match of the round.",
		"A Tribunal verdict shows whether your challenge won, the ban before and after, and what it cost you.",
		"Each player's sheet tells the story of his career.",
	],
}

## The settings key holding the last version whose notes were shown.
const SEEN_KEY := "patch_notes_seen"


static func version() -> String:
	return str(ProjectSettings.get_setting("application/config/version", ""))


## The lines for `v`, or none when that version has no notes.
static func lines(v := "") -> Array:
	return NOTES.get(v if v != "" else version(), [])


## Should the sheet open now? `seen` is the version last shown ("" on a
## device that has never recorded one). A first run records the version and
## shows nothing: there is no earlier version to have changed from.
static func due(seen: String, v := "") -> bool:
	if v == "":
		v = version()
	return seen != "" and seen != v and not lines(v).is_empty()
