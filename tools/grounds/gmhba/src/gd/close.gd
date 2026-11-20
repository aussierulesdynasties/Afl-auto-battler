extends SceneTree
# Loads gmhba.glb at runtime and saves 4 turntable stills (45/135/225/315 deg).
var glb:String; var out:String
func _initialize():
	var a=OS.get_cmdline_user_args(); glb=a[0]; out=a[1]
	var doc=GLTFDocument.new(); var st=GLTFState.new()
	var err=doc.append_from_file(glb,st)
	if err!=OK: print("load failed ",err); quit(1); return
	var model=doc.generate_scene(st); root.add_child(model)
	var sun=DirectionalLight3D.new(); root.add_child(sun)
	sun.look_at_from_position(Vector3.ZERO,Vector3(0.574,-0.700,0.819),Vector3.UP)   # same sun as the Blender render
	sun.light_energy=1.3; sun.shadow_enabled=true; sun.directional_shadow_max_distance=900
	var env=Environment.new(); env.background_mode=Environment.BG_COLOR; env.background_color=Color(0.62,0.66,0.72)
	env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color=Color(0.62,0.66,0.72); env.ambient_light_energy=0.6
	env.tonemap_mode=Environment.TONE_MAPPER_FILMIC
	var we=WorldEnvironment.new(); we.environment=env; root.add_child(we)
	var cam=Camera3D.new(); cam.fov=40; cam.far=3000; root.add_child(cam); cam.current=true
	var bb=AABB(); var first=true
	for m in model.find_children("*","MeshInstance3D",true,false):
		var b=m.global_transform*m.get_aabb()
		if first: bb=b; first=false
		else: bb=bb.merge(b)
	var c=bb.get_center(); c.y=0; print("aabb ",bb)
	cam.fov=50
	var shots=[["facade_closeup",Vector3(-104.4,3.0,121.1),Vector3(-88.82,10.5,105.0)],["facade_closeup_wide",Vector3(-122.0,4.0,139.0),Vector3(-88.82,12.0,105.0)],["join_ne_36",Vector3(138.5,22.0,-84.3),Vector3(81.8,10.0,-43.1)],["join_nw_100",Vector3(-43.4,22.0,-160.7),Vector3(-31.2,10.0,-91.8)],["join_sw_box_156",Vector3(-158.4,22.0,-41.6),Vector3(-94.4,10.0,-13.1)],["join_w_players_209",Vector3(-157.5,22.0,105.5),Vector3(-96.3,10.0,71.6)],["join_se_pocket_278",Vector3(12.9,22.0,192.3),Vector3(3.1,10.0,123.0)],["join_e_pocket_320",Vector3(108.2,22.0,124.0),Vector3(54.6,10.0,79.0)]]
	for sh in shots:
		cam.look_at_from_position(sh[1],sh[2],Vector3.UP)
		for i in 8: await process_frame
		root.get_viewport().get_texture().get_image().save_png("%s/%s.png"%[out,sh[0]]); print("saved ",sh[0])
	quit(0)
