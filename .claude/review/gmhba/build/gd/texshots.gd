extends SceneTree
# Texture close-ups: for each material, a game-distance shot (fov 30, ~100 m) and a close shot (fov 50, 8 m),
# placed from the model's own faces with a line-of-sight test against every triangle.
var glb:String; var out:String
var tris=[]   # [a,b,c] world
func _initialize():
	var a=OS.get_cmdline_user_args(); glb=a[0]; out=a[1]
	var doc=GLTFDocument.new(); var st=GLTFState.new()
	if doc.append_from_file(glb,st)!=OK: quit(1); return
	var model=doc.generate_scene(st); root.add_child(model)
	var sun=DirectionalLight3D.new(); root.add_child(sun)
	sun.look_at_from_position(Vector3.ZERO,Vector3(0.574,-0.700,0.819),Vector3.UP)
	sun.light_energy=1.3; sun.shadow_enabled=true; sun.directional_shadow_max_distance=900
	var env=Environment.new(); env.background_mode=Environment.BG_COLOR; env.background_color=Color(0.62,0.66,0.72)
	env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color=Color(0.62,0.66,0.72); env.ambient_light_energy=0.6
	env.tonemap_mode=Environment.TONE_MAPPER_FILMIC
	var we=WorldEnvironment.new(); we.environment=env; root.add_child(we)
	var cam=Camera3D.new(); cam.far=3000; root.add_child(cam); cam.current=true
	var bym={}
	for m in model.find_children("*","MeshInstance3D",true,false):
		var xf=m.global_transform; var mesh=m.mesh
		for s in mesh.get_surface_count():
			var mat=mesh.surface_get_material(s); var nm=mat.resource_name if mat else "?"
			var ar=mesh.surface_get_arrays(s); var v=ar[Mesh.ARRAY_VERTEX]; var idx=ar[Mesh.ARRAY_INDEX]
			if not bym.has(nm): bym[nm]=[]
			var n=idx.size() if idx else v.size()
			for k in range(0,n,3):
				var p0=xf*v[idx[k] if idx else k]; var p1=xf*v[idx[k+1] if idx else k+1]; var p2=xf*v[idx[k+2] if idx else k+2]
				tris.append([p0,p1,p2]); bym[nm].append([p0,p1,p2])
	print("materials ",bym.keys())
	var PC=Vector3(-10.755,0,24.161)
	# name, material, game-shot mode: "n" = along the face normal, "p" = from the pitch at 18 m
	var jobs=[["concrete","wall","n"],["cladding","fascia","n"],["roof_top","roof","n"],["roof_dark","roofd","n"],["roof_under","under","u"],["seats","seats","p"],["steel_tower","tower","p"],["seats_row","seats","s"],["steel_navy","navy","f"],["deck","deck","f"],["paving","pave","n"],["soffit","soffit","f"],["recess","recess","n"],["teal","teal","n"],["glass","aglass","n"],["precast","cream","n"]]
	for j in jobs:
		if not bym.has(j[1]): print("no material ",j[1]); continue
		var L=bym[j[1]].duplicate(); L.sort_custom(func(x,y): return _area(x)>_area(y))
		var done=false
		for t in L.slice(0,200):
			var c=(t[0]+t[1]+t[2])/3.0; var nn=(t[1]-t[0]).cross(t[2]-t[0]).normalized()
			var gpos:Vector3
			if j[2]=="f" or j[2]=="s":
				# free camera beside the surface, no sightline from the pitch: "f" 4 m off the face;
				# "s" at seat height a few rows away, looking along the tier so the rows read
				if j[2]=="f":
					var fp=c+nn*4.0
					if abs(nn.y)>0.7:   # a slab: stand off to one side, 3 m above (or below) it, and look across it
						var hz=(PC-c); hz.y=0; fp=c-hz.normalized()*4.0+Vector3.UP*(3.0 if j[1]=="deck" else -2.5)
					if not _clear(fp,c): fp=c-nn*4.0; nn=-nn
					if fp.y<0.5 or not _clear(fp,c): continue
					cam.fov=50.0; cam.look_at_from_position(fp,c,Vector3.UP if abs((c-fp).normalized().y)<0.95 else Vector3.FORWARD)
				else:
					# a spectator's eye 1.3 m above the raked seats, two rows back, looking across the tier and down the rake
					var h=(PC-c); h.y=0; h=h.normalized(); var tg=h.cross(Vector3.UP); var up=nn if nn.y>0 else -nn
					var dr=(-h-up*((-h).dot(up))).normalized(); var sp=c+dr*1.5+tg*3.0+up*1.3; var tgt=c-dr*6.0-tg*6.0
					if not _clear(sp,c) or not _clear(sp,tgt): sp=c+dr*1.5-tg*3.0+up*1.3; tgt=c-dr*6.0+tg*6.0
					if not _clear(sp,c) or not _clear(sp,tgt): continue
					cam.fov=60.0; cam.look_at_from_position(sp,tgt,Vector3.UP)
				for i in 8: await process_frame
				root.get_viewport().get_texture().get_image().save_png("%s/tex_%s_close.png"%[out,j[0]])
				print("free shot ",j[0]," at ",c); done=true; break
			if j[2]=="u":
				var hu=(PC-c); hu.y=0; gpos=c+hu.normalized()*100.0; gpos.y=2.0
				if nn.y>0: nn=-nn
			elif j[2]=="p":
				var h=(PC-c); h.y=0; gpos=c+h.normalized()*100.0; gpos.y=18.0
				if (gpos-c).dot(nn)<0: nn=-nn
			else:
				gpos=c+nn*100.0; gpos.y=max(gpos.y,c.y)
			var cpos=c+nn*8.0
			if j[2]=="u":
				var hv=(PC-c); hv.y=0; cpos=c+hv.normalized()*6.0; cpos.y=c.y-4.0
			elif j[2]=="p":
				var hh=(PC-c); hh.y=0; cpos=c+hh.normalized()*10.0; cpos.y=c.y+4.0
			if (gpos-c).dot(nn)<=0.05 or cpos.y<0.5: continue
			if not _clear(gpos,c) or not _clear(cpos,c): continue
			for sh in [["game",gpos,30.0],["close",cpos,50.0]]:
				cam.fov=sh[2]; var up=Vector3.UP if abs((c-sh[1]).normalized().y)<0.95 else Vector3.FORWARD
				cam.look_at_from_position(sh[1],c,up)
				for i in 8: await process_frame
				root.get_viewport().get_texture().get_image().save_png("%s/tex_%s_%s.png"%[out,j[0],sh[0]])
			print("shot ",j[0]," at ",c," dist ",(gpos-c).length()); done=true; break
		if not done: print("NO CLEAR SHOT ",j[0])
	quit(0)
func _area(t): return (t[1]-t[0]).cross(t[2]-t[0]).length()
func _clear(o:Vector3,c:Vector3)->bool:
	var d=c-o; var L=d.length(); d/=L
	for t in tris:
		var e1=t[1]-t[0]; var e2=t[2]-t[0]; var p=d.cross(e2); var det=e1.dot(p)
		if abs(det)<1e-9: continue
		var inv=1.0/det; var s=o-t[0]; var u=s.dot(p)*inv
		if u<0 or u>1: continue
		var q=s.cross(e1); var v=d.dot(q)*inv
		if v<0 or u+v>1: continue
		var tt=e2.dot(q)*inv
		if tt>0.01 and tt<L-0.3: return false
	return true
