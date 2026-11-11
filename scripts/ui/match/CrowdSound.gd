class_name CrowdSound
extends Node
## FL-004: the crowd at a match you watch (assets/audio/crowd, generated, original).
## A low murmur under everything, a roar for a goal, a lift for a behind and the
## siren at the end of every quarter - each said once, when the pitch shows it,
## never when the match is skipped through, and never two at once (a roar isn't
## cut off by a behind). Presentation only: muted, the match tells you exactly
## the same, and nothing here is read by the match.
##
## Row 6.51, the crowd knows the score:
## - goals in a row by one side lift the murmur and each roar (RUN_STEP_DB a
##   goal, to RUN_CAP goals); the other side's next goal drops it back;
## - the home side's goals and behinds are louder than the visitors' (AWAY_DB);
## - the siren goes at the end of each of the four quarters, and once more at
##   the end of extra time;
## - every sound is logged in `heard` with the gap in milliseconds between the
##   pitch showing the event and the sound starting.

const BED_DB := -14.0
const ROAR_DB := -6.0
const LIFT_DB := -9.0
const SIREN_DB := -6.0
## The visitors' supporters are the smaller crowd: their sounds sit this far under.
const AWAY_DB := -4.0
## Each goal in a row after the first lifts the roar by this much, to RUN_CAP goals.
const RUN_STEP_DB := 1.5
const RUN_CAP := 4
## The murmur between goals rises with the run too, by this much a goal.
const BED_STEP_DB := 1.0
const HOME := 0
const DIR := "res://assets/audio/crowd/"
const FILES := ["crowd_goal.wav", "crowd_behind.wav", "crowd_siren.wav"]

## Every sound started, in order: {kind, side, q, run, db, file, gap_ms}.
## gap_ms is -1.0 when the caller gave no time for the event being shown.
var heard: Array = []

var _bed: AudioStreamPlayer
var _cue: AudioStreamPlayer
var _streams := {}          # file -> AudioStream, loaded once so a cue never waits on the disk
var _sirens := {}           # quarter -> true, each quarter's siren goes once
var _extra_time := false    # play went past the fourth quarter
var _full_time_done := false
var _run_side := -1         # who kicked the last goal, and how many in a row
var _run_len := 0


func _ready() -> void:
	_bed = _player(BED_DB)
	_cue = _player(0.0)
	for file in FILES:
		var s := load(DIR + file) as AudioStream
		if s != null:
			_streams[file] = s
	var bed := load(DIR + "crowd_bed.wav") as AudioStreamWAV
	if bed != null:
		bed = bed.duplicate() as AudioStreamWAV
		bed.loop_mode = AudioStreamWAV.LOOP_FORWARD
		bed.loop_begin = 0
		bed.loop_end = int(bed.get_length() * bed.mix_rate)
		_bed.stream = bed
		_bed.play()


func _player(db: float) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.bus = AudioLevels.bus(AudioLevels.CROWD)
	p.volume_db = db
	add_child(p)
	return p


## How loud a goal's roar is: the home side's is louder, and each goal in a row
## by the same side lifts it.
static func roar_db(side: int, run: int) -> float:
	return ROAR_DB + (0.0 if side == HOME else AWAY_DB) + RUN_STEP_DB * float(clampi(run, 1, RUN_CAP) - 1)


## How loud the murmur is while one side has kicked `run` goals in a row.
static func bed_db(side: int, run: int) -> float:
	var step := BED_STEP_DB if side == HOME else BED_STEP_DB * 0.5
	return BED_DB + step * float(clampi(run, 1, RUN_CAP) - 1)


## A football event as the pitch shows it: "goal", "behind" or "quarter" (the
## end of quarter `q`). `side` is 0 for the home side. `shown_usec` is
## Time.get_ticks_usec() when the pitch showed it. A goal that was skipped past
## (`audible` false) still counts toward the run, without a sound.
func event(kind: String, side: int = HOME, shown_usec: int = -1, audible: bool = true, q: int = 0) -> void:
	if kind == "goal":
		if side == _run_side:
			_run_len += 1
		else:
			_run_side = side
			_run_len = 1
		if _bed != null:
			_bed.volume_db = bed_db(side, _run_len)
		if audible:
			_play("goal", "crowd_goal.wav", roar_db(side, _run_len), true, side, q, shown_usec)
	elif kind == "behind":
		if audible:
			_play("behind", "crowd_behind.wav", LIFT_DB + (0.0 if side == HOME else AWAY_DB), false, side, q, shown_usec)
	elif kind == "quarter":
		if q > 4:
			_extra_time = true
		elif q >= 1 and audible and not _sirens.has(q):
			_sirens[q] = true
			_play("siren", "crowd_siren.wav", SIREN_DB, true, -1, q, shown_usec)


## Full time: the siren, once. The fourth quarter's siren is the full-time
## siren when it has just gone; a match skipped to its end, or one that went to
## extra time, gets its siren here.
func full_time(shown_usec: int = -1) -> void:
	if _full_time_done:
		return
	_full_time_done = true
	if _sirens.has(4) and not _extra_time:
		return
	_play("siren", "crowd_siren.wav", SIREN_DB, true, -1, 5 if _extra_time else 4, shown_usec)


## What's playing now (tests): the cue's file, or "".
func cue() -> String:
	return _cue.stream.resource_path.get_file() if _cue.playing and _cue.stream != null else ""


## Goals in a row by the side that kicked the last one (tests).
func run_length() -> int:
	return _run_len


func _play(kind: String, file: String, db: float, over: bool, side: int, q: int, shown_usec: int) -> void:
	if _cue.playing and not over:
		return     # let the roar finish
	var s: AudioStream = _streams.get(file)
	if s == null:
		return
	_cue.stream = s
	_cue.volume_db = db
	_cue.play()
	var gap := -1.0
	if shown_usec >= 0:
		gap = float(Time.get_ticks_usec() - shown_usec) / 1000.0
	heard.append({"kind": kind, "side": side, "q": q, "run": _run_len if kind == "goal" else 0,
			"db": db, "file": file, "gap_ms": gap})
