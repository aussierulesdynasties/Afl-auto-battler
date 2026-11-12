class_name VignetteGrade
extends RefCounted
## The broadcast grade over a match vignette.
## attach() adds two children to the vignette: a full-rect ColorRect running
## assets/vignette/grade.gdshader over everything the vignette drew (one screen pass),
## then an overlay Control the caller draws its names and bars on, so text stays ungraded.
## Per weather (VignetteWeather / MatchSim.weather), under lights:
##   perfect / windy / unknown  warm highlights, cool shadows;
##   hot   warmer and punchier;
##   wet   cooler and flatter: lifted blacks, less saturation, almost no bloom.
## Per time of day (VignetteKickoff): night is that look; day and twilight have their own
## (look); a hot day gets harsh light and a heat shimmer on the horizon.
## Settings > Reduced motion holds the grain and the shimmer still.

const SHADER := preload("res://assets/vignette/grade.gdshader")

## Capture tools only: draw this weather instead of the match's ("" = the match's).
static var forced_weather := ""


static func weather_of(w: String) -> String:
	return forced_weather if forced_weather != "" else w


## Adds the grade and the overlay to host; returns the overlay, whose draw signal
## calls ui_draw.
static func attach(host: Control, weather: String, ui_draw: Callable) -> Control:
	var mat := ShaderMaterial.new()
	mat.shader = SHADER
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
	_set_look(grade, weather, VignetteGround.slot_now(weather))
	var ui := Control.new()
	ui.name = "GradeUI"
	ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	host.add_child(ui)
	ui.draw.connect(ui_draw)
	host.draw.connect(ui.queue_redraw)
	return ui


## Keeps a scene's grade in step with the ground it has just drawn (VignetteGround.draw_ground
## calls this every frame): the look for the weather and time of day shown, and where the
## far edge of the turf is on the picture, for the heat shimmer. A scene with no grade: nothing happens.
## horizon_y: the horizon's y on the scene, in its own pixels.
static func sync(ci: CanvasItem, weather: String, slot: String, horizon_y: float) -> void:
	var grade := ci.get_node_or_null("Grade") as ColorRect
	if grade == null or not (grade.material is ShaderMaterial):
		return
	_set_look(grade, weather, slot)
	horizon(ci, horizon_y)


## Where the horizon is on a graded scene, y in the scene's own pixels. A scene that draws
## its ground through a moving camera calls this after the ground, with where it landed.
static func horizon(ci: CanvasItem, horizon_y: float) -> void:
	var grade := ci.get_node_or_null("Grade") as ColorRect
	if grade == null or not (grade.material is ShaderMaterial) or grade.size.y <= 0.0:
		return
	var at := clampf(horizon_y / grade.size.y, 0.0, 1.0)
	if not is_equal_approx(float(grade.get_meta("horizon", -1.0)), at):
		grade.set_meta("horizon", at)
		(grade.material as ShaderMaterial).set_shader_parameter("horizon", at)


static func _set_look(grade: ColorRect, weather: String, slot: String) -> void:
	var key := weather + "|" + slot
	if str(grade.get_meta("look", "")) == key:
		return
	grade.set_meta("look", key)
	var mat := grade.material as ShaderMaterial
	var uniforms := look(weather, slot)
	for k in uniforms:
		mat.set_shader_parameter(k, uniforms[k])
	mat.set_shader_parameter("exposure", float(uniforms.get("exposure", 1.0)))
	mat.set_shader_parameter("shimmer", float(uniforms.get("shimmer", 0.0)))


## The grade's uniforms for a weather and a time of day (VignetteKickoff). Night is the
## look every scene had before there were day games, unchanged.
static func look(weather: String, slot := VignetteKickoff.NIGHT) -> Dictionary:
	match slot:
		VignetteKickoff.DAY:
			return _day(weather)
		VignetteKickoff.TWILIGHT:
			return _twilight(weather)
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


## By day: clean and even, little bloom (a bright sky would flood the picture) and a
## lighter edge. Hot: harsh light (the exposure lifted, hard contrast, bleached warm
## highlights, glare) and the heat shimmer. Wet: flat and grey.
static func _day(weather: String) -> Dictionary:
	match weather:
		VignetteWeather.WET:
			return {"exposure": 0.96, "contrast": 1.04, "saturation": 0.78, "lift": 0.06,
					"hi_tint": Vector3(0.97, 1.0, 1.04), "lo_tint": Vector3(0.9, 0.96, 1.08),
					"vignette": 0.3, "bloom": 0.04, "bloom_from": 0.8, "grain": 0.03, "shimmer": 0.0}
		VignetteWeather.HOT:
			return {"exposure": 1.12, "contrast": 1.36, "saturation": 1.02, "lift": 0.0,
					"hi_tint": Vector3(1.08, 1.03, 0.86), "lo_tint": Vector3(0.98, 0.95, 0.92),
					"vignette": 0.14, "bloom": 0.1, "bloom_from": 0.8, "grain": 0.022, "shimmer": 1.0}
		_:
			return {"exposure": 1.0, "contrast": 1.14, "saturation": 1.12, "lift": 0.0,
					"hi_tint": Vector3(1.04, 1.01, 0.96), "lo_tint": Vector3(0.94, 0.97, 1.06),
					"vignette": 0.2, "bloom": 0.1, "bloom_from": 0.8, "grain": 0.022, "shimmer": 0.0}


## At twilight: the last warm light low in the sky, the shadows gone blue, the lights
## starting to bloom.
static func _twilight(weather: String) -> Dictionary:
	match weather:
		VignetteWeather.WET:
			return {"exposure": 1.0, "contrast": 1.08, "saturation": 0.84, "lift": 0.05,
					"hi_tint": Vector3(0.99, 0.99, 1.04), "lo_tint": Vector3(0.88, 0.94, 1.12),
					"vignette": 0.36, "bloom": 0.1, "bloom_from": 0.66, "grain": 0.033, "shimmer": 0.0}
		VignetteWeather.HOT:
			return {"exposure": 1.05, "contrast": 1.3, "saturation": 1.12, "lift": 0.0,
					"hi_tint": Vector3(1.18, 1.0, 0.8), "lo_tint": Vector3(0.94, 0.9, 1.04),
					"vignette": 0.3, "bloom": 0.3, "bloom_from": 0.58, "grain": 0.026, "shimmer": 0.45}
		_:
			return {"exposure": 1.0, "contrast": 1.2, "saturation": 1.14, "lift": 0.0,
					"hi_tint": Vector3(1.12, 0.99, 0.86), "lo_tint": Vector3(0.86, 0.91, 1.14),
					"vignette": 0.34, "bloom": 0.22, "bloom_from": 0.6, "grain": 0.026, "shimmer": 0.0}
