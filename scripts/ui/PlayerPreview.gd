class_name PlayerPreview
extends SubViewportContainer
## Create a player: the prospect as you build him, on the 3D footballer the oval draws
## (Oval3D: the same body, kit shader, skin, hair colour and hair styles), standing in his
## idle, front on and from behind with his number. Reads the form's spec every frame, so a
## change to his look, height, number or club shows at once. Presentation only
## (director, ruling 2.76: "we will remove him and put a proper 3d player").
##
## He wears the guernsey of the club he followed growing up (FL-005), as a kid in the
## backyard would; until one is picked, a plain prospect's training guernsey. Looks the
## 3D footballer doesn't draw yet (facial hair, headband, bandaging, tattoos) aren't faked.

## A draft hopeful's plain light training guernsey and dark shorts: no club's colours,
## and light enough to stand out on the dark page.
const PROSPECT_KIT := {"design": "plain", "base": Color("#d6d2c8"), "pattern": Color("#2b2d33"),
		"pattern2": Color("#2b2d33"), "shorts": Color("#2b2d33")}
## Room for the tallest prospect (metres from the turf to the top of the frame).
const FRAME_M := 2.18
## The two figures' places across the frame (metres) and how far each is turned from
## square: front on (a touch to his right, so the hair's side shows), and from behind.
const SPOTS := [Vector3(-0.42, 0.0, 0.0), Vector3(0.42, 0.0, 0.0)]
const TURN_DEG := [-18.0, 162.0]

var spec := {}
var oval: Oval3D
var figures: Array = []      # Oval3D._player dictionaries: [front, back]
var _view: SubViewport
var _camera: Camera3D
var _model_h := 1.85         # the footballer's own height in the GLB, measured on build
var _kit_key := "-"
var _look_key := ""
var _shown := {}             # what is on him now: {"club", "skin", "hair", "hair_style", "number", "height_cm"}


func _ready() -> void:
	stretch = true
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_view = SubViewport.new()
	_view.name = "PreviewView"
	_view.own_world_3d = true
	_view.transparent_bg = true
	_view.msaa_3d = Viewport.MSAA_4X
	_view.render_target_update_mode = SubViewport.UPDATE_WHEN_VISIBLE
	add_child(_view)
	oval = Oval3D.new()
	oval.name = "PreviewFigures"
	_view.add_child(oval)
	_stage()
	# A build that left the footballer out (export_presets.cfg once excluded every .glb) must
	# say so, not crash the phone on a null model: the form stays usable without him.
	var scene: PackedScene = load(Oval3D.PLAYER_GLB) as PackedScene if ResourceLoader.exists(Oval3D.PLAYER_GLB) else null
	if scene == null:
		push_error("PlayerPreview: the 3D footballer %s is not in this build" % Oval3D.PLAYER_GLB)
		return
	for i in range(SPOTS.size()):
		var p := oval._player(scene, oval._kit(PROSPECT_KIT), [Color(0, 0, 0, 0)])
		(p["ring"] as Node3D).visible = false   # no club ring: he's no-one's yet
		var node: Node3D = p["node"]
		node.position = SPOTS[i]
		node.rotation_degrees.y = TURN_DEG[i]
		var ap: AnimationPlayer = p["anim"]
		ap.play("idle")
		# Out of step with each other, as two men standing are.
		ap.seek(fmod(0.9 * i, maxf(0.01, ap.current_animation_length)), true)
		figures.append(p)
	_model_h = _measure(figures[0]["node"])
	_apply()
	set_process(true)


## Light, a soft shade under each man, and the camera, square on at chest height.
func _stage() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.62, 0.66, 0.72)
	env.ambient_light_energy = 0.55
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var we := WorldEnvironment.new()
	we.environment = env
	oval.add_child(we)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-38.0, -30.0, 0.0)
	key.light_energy = 1.2
	oval.add_child(key)
	# A cool rim from behind so the hair's outline reads against the dark page.
	var rim := DirectionalLight3D.new()
	rim.rotation_degrees = Vector3(-20.0, 160.0, 0.0)
	rim.light_energy = 0.55
	rim.light_color = Color(0.75, 0.82, 1.0)
	oval.add_child(rim)
	for s in SPOTS:
		var shade := MeshInstance3D.new()
		var disc := CylinderMesh.new()
		disc.top_radius = 0.34
		disc.bottom_radius = 0.34
		disc.height = 0.002
		shade.mesh = disc
		shade.position = s + Vector3(0.0, 0.001, 0.0)
		shade.scale = Vector3(1.0, 1.0, 0.55)
		var m := StandardMaterial3D.new()
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.albedo_color = Color(0, 0, 0, 0.3)
		shade.material_override = m
		shade.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		oval.add_child(shade)
	_camera = Camera3D.new()
	_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	oval.add_child(_camera)


## The top of his head in the GLB, in metres: every body mesh's highest point.
static func _measure(node: Node3D) -> float:
	var top := 0.0
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		var bb := (mi as MeshInstance3D).get_aabb()
		top = maxf(top, bb.position.y + bb.size.y)
	return top if top > 1.0 else 1.85


func _process(delta: float) -> void:
	_apply()
	for p in figures:
		(p["anim"] as AnimationPlayer).advance(delta)
	# Framed for the tallest prospect, whatever the panel's shape: the whole frame's height
	# is FRAME_M, the two men centred across it.
	var aspect := size.x / maxf(1.0, size.y)
	_camera.size = maxf(FRAME_M, 1.9 / maxf(0.01, aspect))
	_camera.position = Vector3(0.0, _camera.size * 0.5 - 0.04, 6.0)


## Put the spec's look, club, number and height on both men, when they change.
func _apply() -> void:
	if spec.is_empty() or figures.is_empty():
		return
	var club := str(spec.get("fav_club", ""))
	if club != _kit_key:
		_kit_key = club
		var kit := oval._kit(GameDB.club_guernsey(club) if club != "" else PROSPECT_KIT)
		for p in figures:
			for mi in (p["node"] as Node3D).find_children("*", "MeshInstance3D", true, false):
				var m := mi as MeshInstance3D
				if not m.has_meta("kit"):
					continue
				for s in range(m.mesh.get_surface_count()):
					var own := m.mesh.surface_get_material(s)
					if own == null or own.resource_name != Oval3D.BOOT_MATERIAL:
						m.set_surface_override_material(s, kit)
		_shown["club"] = club
	var look: Dictionary = spec.get("look", {})
	var l := {"skin": int(look.get("skin", 1)), "hair": int(look.get("hair", 1)),
			"hair_style": str(look.get("hair_style", VignetteFigures.HAIR_BASE))}
	var number := int(spec.get("number_pref", 0))
	var cm := int(spec.get("height_cm", 184))
	var key := "%s|%d|%d" % [JSON.stringify(l), number, cm]
	if key == _look_key:
		return
	_look_key = key
	for i in range(figures.size()):
		var p: Dictionary = figures[i]
		oval.look(p, l)
		oval._number(p, number if number > 0 else -1)
		(p["node"] as Node3D).scale = Vector3.ONE * (cm / 100.0) / _model_h
	_shown["skin"] = l["skin"]
	_shown["hair"] = l["hair"]
	_shown["hair_style"] = str(figures[0].get("hair_style", ""))
	_shown["number"] = number
	_shown["height_cm"] = cm


## What the preview is showing now (tests): club, skin, hair, hair_style, number, height_cm.
func shown() -> Dictionary:
	return _shown.duplicate()
