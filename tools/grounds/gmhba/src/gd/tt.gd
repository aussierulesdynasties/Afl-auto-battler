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
	for deg in [45,135,225,315]:
		var r=deg_to_rad(deg)
		cam.look_at_from_position(c+Vector3(cos(r)*330,150,sin(r)*330),c+Vector3(0,4,0),Vector3.UP)
		for i in 8: await process_frame
		var img=root.get_viewport().get_texture().get_image()
		img.save_png("%s/turntable_%03d.png"%[out,deg]); print("saved ",deg)
	DirAccess.make_dir_recursive_absolute(out+"/tt")
	for k in 72:
		var r=deg_to_rad(k*5.0)
		cam.look_at_from_position(c+Vector3(cos(r)*330,150,sin(r)*330),c+Vector3(0,4,0),Vector3.UP)
		for i in 4: await process_frame
		root.get_viewport().get_texture().get_image().save_png("%s/tt/f%03d.png"%[out,k])
	print("frames done")
	quit(0)
