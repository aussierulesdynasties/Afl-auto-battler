extends SceneTree
## godot --headless --path . --script tests/run_orbit_tests.gd
## The aerial orbit round a ground (scripts/ui/match/Oval3DOrbit.gd, director 2026-11-27): measured on a
## made-up ground (a stadium of known size, a tower beside the camera's path and one between the path and
## the stadium), the circle is sized from the stadium, holds one height, climbs smoothly over the tower
## by its path and never passes through anything. Then Marvel Stadium as the match builds it, when its
## model is on this machine.
## Seeded by design: nothing random runs; the made-up ground and Marvel are fixed geometry.

const STADIUM_R := 120.0     # the made-up stadium's outer radius
const STADIUM_H := 40.0
const NEAR_TOWER := Vector3(395.0, 0.0, 0.0)   # on the camera's path due east (its radius: 3.2 x 120 = 384)

var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_t("_test_made_up_ground")
	await _t("_test_marvel")
	print(Ran.line("Orbit", self))
	quit(0 if _failures.is_empty() else 1)


func _box(parent: Node3D, at: Vector3, size: Vector3) -> void:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	# An ArrayMesh, as a model's meshes are (a primitive mesh is read as the picture's film or the ball).
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, bm.get_mesh_arrays())
	mi.mesh = am
	mi.position = at + Vector3(0.0, size.y * 0.5, 0.0)
	parent.add_child(mi)


func _made_up() -> Node3D:
	var world := Node3D.new()
	root.add_child(world)
	var ground := Node3D.new()
	ground.name = "Ground"
	world.add_child(ground)
	var stadium := Node3D.new()
	stadium.name = "madeup"
	ground.add_child(stadium)
	# Rings of stands from the fence (80 x 65) out to STADIUM_R.
	for r in [85.0, 95.0, 105.0, 115.0]:
		for k in 80:
			var a := TAU * k / 80.0
			_box(stadium, Vector3(cos(a) * r, 0.0, -sin(a) * r), Vector3(10.0, STADIUM_H, 10.0))
	var town := Node3D.new()
	town.name = "Buildings"
	ground.add_child(town)
	_box(town, NEAR_TOWER, Vector3(30.0, 260.0, 30.0))          # by the camera's path
	_box(town, Vector3(0.0, 0.0, 250.0), Vector3(30.0, 140.0, 30.0))   # between the path and the stadium
	return world


func _test_made_up_ground() -> void:
	var world := _made_up()
	var o := Oval3DOrbit.plan(world, Vector2(80.0, 65.0), "madeup")
	_check(absf(o.r_out - STADIUM_R) <= 2.0 * Oval3DOrbit.CELL,
			"The stadium's outer radius is measured off its own model, not the towers (%.0f, want %.0f)" % [
			o.r_out, STADIUM_R])
	_check(absf(o.top - STADIUM_H) < 1.0, "Its top is its own (%.1f m)" % o.top)
	_check(is_equal_approx(o.radius, Oval3DOrbit.ORBIT_K * o.r_out), "The circle is sized from the stadium")
	# Never through anything: at every degree the camera is over everything within CLEAR_R of it.
	var worst := INF
	var steepest := 0.0
	for i in Oval3DOrbit.SAMPLES:
		var eye := o.at(float(i) / Oval3DOrbit.SAMPLES * Oval3DOrbit.LAP_S).origin
		worst = minf(worst, eye.y - o.highest_near(eye.x, eye.z, Oval3DOrbit.CLEAR_R))
		var nxt := o.heights[(i + 1) % Oval3DOrbit.SAMPLES]
		steepest = maxf(steepest, absf(nxt - o.heights[i]))
	_check(worst >= Oval3DOrbit.CLEARANCE - 0.5,
			"The camera passes at least %.0f m over everything by its path (closest %.1f m)" % [Oval3DOrbit.CLEARANCE, worst])
	# The climb over the tower by the path is eased: no more than a few metres a degree (a lap is 72 s).
	_check(steepest < 8.0, "The height changes smoothly round the circle (at most %.1f m a degree)" % steepest)
	var east := o.at(0.0).origin.y
	var west := o.at(Oval3DOrbit.LAP_S * 0.5).origin.y
	_check(east > 260.0 + Oval3DOrbit.CLEARANCE - 0.5 and west < east,
			"It climbs over the tower by its path (%.0f m there) and holds its own height elsewhere (%.0f m)" % [east, west])
	# Always looking at the stadium, from outside it.
	var xf := o.at(10.0)
	var to_aim := (o.aim - xf.origin).normalized()
	_check((xf.basis * Vector3.FORWARD).dot(to_aim) > 0.999, "The camera looks at the stadium's middle")
	_check(o.fov > 20.0 and o.fov < 80.0, "The lens is a sensible one (%.1f degrees across)" % o.fov)
	world.queue_free()


## Marvel Stadium as a match builds it: the orbit clears everything round Docklands.
func _test_marvel() -> void:
	if GroundModels.files("marvel").is_empty():
		print("SKIP: Marvel's model is not on this machine (tools/ground_assets.sh fetch)")
		_check(true, "skipped")
		return
	var world := Node3D.new()
	root.add_child(world)
	var gr := GroundModels.instantiate("marvel")
	world.add_child(gr)
	await process_frame
	var o := Oval3DOrbit.plan(world, GroundModels.match_fence(), "marvel")
	_check(o.r_out > 100.0 and o.r_out < 160.0, "Marvel's outer radius is the stadium's (%.0f m)" % o.r_out)
	var worst := INF
	for i in Oval3DOrbit.SAMPLES:
		var eye := o.at(float(i) / Oval3DOrbit.SAMPLES * Oval3DOrbit.LAP_S).origin
		worst = minf(worst, eye.y - o.highest_near(eye.x, eye.z, Oval3DOrbit.CLEAR_R))
	_check(worst >= Oval3DOrbit.CLEARANCE - 0.5, "Over Docklands the camera clears every tower by its path (%.1f m)" % worst)
	world.queue_free()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)
