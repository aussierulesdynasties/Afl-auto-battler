class_name VignetteGrade
extends RefCounted
## The broadcast grade over a match vignette (Features "vignette_grade", off by default).
## attach() adds two children to the vignette: a full-rect ColorRect running
## assets/vignette/grade.gdshader over everything the vignette drew (one screen pass),
## then an overlay Control the caller draws its names and bars on, so text stays ungraded.
## Per weather (VignetteWeather / MatchSim.weather):
##   perfect / windy / unknown  golden afternoon: warm highlights, cool shadows;
##   hot   warmer and punchier;
##   wet   cooler and flatter: lifted blacks, less saturation, almost no bloom.
## Settings > Reduced motion holds the grain still.

const SWITCH := "vignette_grade"
const SHADER := preload("res://assets/vignette/grade.gdshader")

## Capture tools only: draw this weather instead of the match's ("" = the match's).
static var forced_weather := ""


static func on() -> bool:
	return Features.on(SWITCH)


static func weather_of(w: String) -> String:
	return forced_weather if forced_weather != "" else w


## Adds the grade and the overlay to host; returns the overlay, whose draw signal
## calls ui_draw. Null when the switch is off (draw the UI on the host as before).
static func attach(host: Control, weather: String, ui_draw: Callable) -> Control:
	if not on():
		return null
	var mat := ShaderMaterial.new()
	mat.shader = SHADER
	for k in look(weather):
		mat.set_shader_parameter(k, look(weather)[k])
	var reduced := false
	var gs = host.get_node_or_null("/root/GameState")
	if gs != null and gs.has_method("reduced_motion"):
		reduced = bool(gs.reduced_motion())
	mat.set_shader_parameter("grain_speed", 0.0 if reduced else 1.0)
	var grade := ColorRect.new()
	grade.name = "Grade"
	grade.material = mat
	grade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	grade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	host.add_child(grade)
	var ui := Control.new()
	ui.name = "GradeUI"
	ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	host.add_child(ui)
	ui.draw.connect(ui_draw)
	host.draw.connect(ui.queue_redraw)
	return ui


## The grade's uniforms for a weather.
static func look(weather: String) -> Dictionary:
	match weather:
		VignetteWeather.WET:
			return {"contrast": 1.10, "saturation": 0.88, "lift": 0.05,
					"hi_tint": Vector3(0.97, 1.0, 1.06), "lo_tint": Vector3(0.88, 0.96, 1.12),
					"vignette": 0.38, "bloom": 0.10, "bloom_from": 0.65, "grain": 0.035}
		VignetteWeather.HOT:
			return {"contrast": 1.28, "saturation": 1.16, "lift": 0.0,
					"hi_tint": Vector3(1.14, 1.03, 0.82), "lo_tint": Vector3(0.92, 0.95, 1.08),
					"vignette": 0.36, "bloom": 0.34, "bloom_from": 0.52, "grain": 0.028}
		_:
			return {"contrast": 1.24, "saturation": 1.14, "lift": 0.0,
					"hi_tint": Vector3(1.10, 1.02, 0.86), "lo_tint": Vector3(0.88, 0.95, 1.10),
					"vignette": 0.36, "bloom": 0.28, "bloom_from": 0.55, "grain": 0.028}
