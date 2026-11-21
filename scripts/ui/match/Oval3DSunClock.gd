class_name Oval3DSunClock
extends RefCounted
## The real sun over a match (plan 2a.4: one setting drives the sky, light and turf). Sky3D's
## astronomy (addons/sky_3d, TimeOfDay, MIT) gives the sun's height for the ground's place, the
## match's date and the time on the ground's clock; the match clock moves that time on, so a
## twilight game starts in low sun and finishes under the lights, as real ones do.
## Looks only: nothing here is saved and nothing here reaches the match sim. The skies stay our
## own approved ones (rule 2.84); Sky3D only says where the sun is.

## Local kick-off hours for each slot, as the AFL fixtures them (the slots themselves:
## tools/visual/build_kickoff_shares.py, day before 16:00, twilight to 17:59, night after).
const KICKOFF := {"day": 13.75, "twilight": 16.583, "night": 19.5}
## Real minutes from the bounce to the start of each quarter (30-minute quarters, a six-minute
## break at quarter and three-quarter time, twenty at half time), and a quarter's real length.
const QUARTER_STARTS := [0.0, 36.0, 86.0, 122.0]
const QUARTER_REAL := 30.0
## The season's calendar: the Opening Round on the first weekend of March, a round a week, and
## the finals through September.
const SEASON_YEAR := 2026
const OPENING := [3, 7]
const FINALS := [9, 12]

static var _places := {}

var lat := 0.0          # degrees, south negative
var lon := 0.0          # degrees, east positive
var utc := 10.0         # hours, daylight saving included
var month := 6
var day := 1
var kickoff := 13.75    # local hours


## The sun clock for a match: its ground, its round's label ("Round 7", "Grand Final") and its
## slot (VignetteKickoff day, twilight or night).
static func for_match(ground: String, round_label: String, slot: String) -> Oval3DSunClock:
	var c := Oval3DSunClock.new()
	var p := place(ground)
	c.lat = float(p.get("lat", -37.82))
	c.lon = float(p.get("lon", 144.98))
	var md := date_of(round_label)
	c.month = md[0]
	c.day = md[1]
	c.utc = float(p.get("utc", 10.0)) + (1.0 if daylight_saving(str(p.get("dst", "none")), c.month, c.day) else 0.0)
	c.kickoff = float(KICKOFF.get(slot, KICKOFF["night"]))
	return c


## A ground's place (data/ground_places.json), or the default's.
static func place(ground: String) -> Dictionary:
	if _places.is_empty():
		var f := FileAccess.open("res://data/ground_places.json", FileAccess.READ)
		var parsed = JSON.parse_string(f.get_as_text()) if f != null else null
		_places = parsed if parsed is Dictionary else {"default": {}, "grounds": {}}
	return (_places.get("grounds", {}) as Dictionary).get(ground, _places.get("default", {}))


## [month, day] a round is played on: "Opening Round" the first weekend of March, "Round n" n
## weeks after it, a final in September; anything else mid-season.
static func date_of(round_label: String) -> Array:
	var n := -1
	if round_label.begins_with("Opening Round"):
		n = 0
	elif round_label.begins_with("Round "):
		n = int(round_label.substr(6).to_int())
	elif round_label.contains("Final"):
		return FINALS.duplicate()
	if n < 0:
		return [6, 15]
	var d := Time.get_unix_time_from_datetime_dict({"year": SEASON_YEAR, "month": OPENING[0], "day": OPENING[1]})
	var t := Time.get_datetime_dict_from_unix_time(int(d) + n * 7 * 86400)
	return [int(t["month"]), int(t["day"])]


## Daylight saving on a day of the season: Australia's (to the first Sunday of April) and New
## Zealand's (the same end; it starts again on the last Sunday of September).
static func daylight_saving(rule: String, m: int, d: int) -> bool:
	if rule == "none" or rule == "":
		return false
	if m < 4 or (m == 4 and d < 6):
		return true
	return rule == "nz" and m == 9 and d >= 27


## Local hours on the ground's clock at match minute `minute` of quarter `quarter` (1 to 4,
## minute counted from the start of the match as the scoreboard does, 30 to a quarter).
func hour_at(quarter: int, minute: float) -> float:
	var q := clampi(quarter, 1, 4)
	var within := clampf(minute - (q - 1) * QUARTER_REAL, 0.0, QUARTER_REAL * 1.5)
	return kickoff + (float(QUARTER_STARTS[q - 1]) + within) / 60.0


## The sun's height above the horizon at a local hour, in degrees (negative below it), from
## Sky3D's TimeOfDay in its realistic mode.
func sun_altitude(hour: float) -> float:
	return sun_at(hour).x


## The sun at a local hour: x its height in degrees, y its compass bearing in degrees (0 north,
## 90 east).
func sun_at(hour: float) -> Vector2:
	var tod := TimeOfDay.new()
	tod.celestials_calculations = TimeOfDay.CelestialMode.REALISTIC
	tod.latitude = deg_to_rad(lat)
	tod.longitude = deg_to_rad(lon)
	tod.utc = utc
	tod.year = SEASON_YEAR
	tod.month = month
	tod.day = day
	tod.current_time = fposmod(hour, 24.0)
	tod._compute_realistic_sun_coords()
	var c: Vector2 = tod._sun_coords
	tod.free()
	# Sky3D keeps the zenith angle in y and the azimuth from the north, westward negative, in x.
	return Vector2(90.0 - rad_to_deg(c.y), fposmod(rad_to_deg(c.x), 360.0))
