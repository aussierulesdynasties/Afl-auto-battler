class_name AudioLevels
extends RefCounted
## Sound is two settings (row 98, T7.O16): Mute, and one Volume for
## everything - music, the crowd and button sounds together - set on Master.
## Music, crowd and button sounds still play on their own buses under Master
## so code can find them, but the player no longer sets them one by one.

const MUSIC := "Music"
const CROWD := "Crowd"
const INTERFACE := "Interface"   # button sounds and stings (Feel)
const DEFAULT_VOLUME := 100      # percent
## The old per-sound levels (FL-004), read only to carry an old settings
## file over: "quiet" was -10 dB, about 32% of full.
const OLD_KEYS := ["music_level", "crowd_level", "button_sounds"]
const OLD_QUIET_DB := -10.0


## The bus, made under Master if it isn't there yet.
static func bus(name: String) -> String:
	if AudioServer.get_bus_index(name) < 0:
		AudioServer.add_bus()
		var i := AudioServer.bus_count - 1
		AudioServer.set_bus_name(i, name)
		AudioServer.set_bus_send(i, "Master")
	return name


## A volume as a whole percent from 0 to 100.
static func valid(pct) -> int:
	if not (pct is int or pct is float):
		return DEFAULT_VOLUME
	return clampi(int(round(float(pct))), 0, 100)


## Master at `pct` percent of full (0 is silent), and every sound's own bus
## at full, so the one Volume is the only level.
static func apply_volume(pct: int) -> void:
	for name in [MUSIC, CROWD, INTERFACE]:
		var b := AudioServer.get_bus_index(bus(name))
		AudioServer.set_bus_mute(b, false)
		AudioServer.set_bus_volume_db(b, 0.0)
	var master := AudioServer.get_bus_index("Master")
	if master < 0:
		return
	var v := valid(pct)
	AudioServer.set_bus_volume_db(master, -80.0 if v == 0 else linear_to_db(v / 100.0))


## An old settings file's three levels as the new pair. Volume is the
## loudest of the three (normal 100%, quiet 30%), so nothing the player still
## heard gets quieter; when all three were off the player wanted silence, so
## Mute comes on and Volume stays at full for when he turns it off again.
## The old file held only the levels the player had changed: a missing crowd
## or button-sounds level was still playing at normal, so it counts as 100.
## A missing music level is left out, because no music ever played.
## Returns {} when there is nothing old to carry over.
static func from_old(levels: Dictionary) -> Dictionary:
	var any := false
	for k in OLD_KEYS:
		any = any or levels.has(k)
	if not any:
		return {}
	var loudest := -1
	for k in OLD_KEYS:
		if not levels.has(k) and k == "music_level":
			continue
		var lv := str(levels.get(k, "normal"))
		var pct := 0 if lv == "off" else (quiet_percent() if lv == "quiet" else 100)
		loudest = maxi(loudest, pct)
	if loudest == 0:
		return {"volume": DEFAULT_VOLUME, "mute": true}
	return {"volume": loudest, "mute": false}


## -10 dB as a percent, to the nearest 5 the slider steps in (30).
static func quiet_percent() -> int:
	return int(round(db_to_linear(OLD_QUIET_DB) * 100.0 / 5.0)) * 5
