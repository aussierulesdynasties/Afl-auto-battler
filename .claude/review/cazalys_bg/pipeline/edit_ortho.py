f='render.py'; s=open(f,newline='').read()
nl='\r\n' if '\r\n' in s else '\n'
a="    else:"+nl+"        aim(v[\"cam\"], v[\"look\"]"
assert a in s
s=s.replace(a,"    elif \"ortho\" in v:   # straight-down orthographic: {\"ortho\": width_m, \"centre\": [x, y]} for satellite overlays"+nl+
"        cam.type = 'ORTHO'; cam.ortho_scale = v['ortho']; cam.shift_x = cam.shift_y = 0"+nl+
"        cx, cy = v.get('centre', (0, 0)); co.location = (cx, cy, 3000); co.rotation_euler = (0, 0, 0)"+nl+
"        sc.render.filepath = os.path.join(job[\"out\"], v[\"name\"] + \".png\")"+nl+
"        bpy.ops.render.render(write_still=True); cam.type = 'PERSP'"+nl+a,1)
open(f,'w',newline='').write(s); print('ok')
