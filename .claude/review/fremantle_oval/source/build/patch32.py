import shutil
p = 'build/build.py'
shutil.copy(p, 'build/build_v12pre32.py')
s = open(p, encoding='utf-8', newline='').read()
def rep(a, b):
    global s
    assert a in s, a[:80]; s = s.replace(a, b, 1)

# several photo-matched cameras in one run: -- photos out1.png fit/cam1.json dz1 out2.png fit/cam2.json dz2 ...
rep("elif MODE == 'glb':", """elif MODE == 'photos':
    import mathutils
    args_ = sys.argv[sys.argv.index('--') + 2:]
    for i_ in range(0, len(args_), 3):
        out_, js_, dz_ = args_[i_], args_[i_ + 1], float(args_[i_ + 2])
        PC = json.load(open(os.path.join(ROOT, js_)))
        p = list(PC['p']); p[2] += dz_; W_, H_ = PC['W'], PC['H']
        yaw, pit, rol = p[3:6]
        f_ = np.array([math.cos(yaw) * math.cos(pit), math.sin(yaw) * math.cos(pit), math.sin(pit)]); r_ = np.array([math.sin(yaw), -math.cos(yaw), 0.0]); u_ = np.cross(r_, f_)
        right = math.cos(rol) * r_ + math.sin(rol) * u_; up = -math.sin(rol) * r_ + math.cos(rol) * u_
        rot = mathutils.Matrix([[right[0], up[0], -f_[0]], [right[1], up[1], -f_[1]], [right[2], up[2], -f_[2]]])
        cam = bpy.data.cameras.new('pcam%d' % i_); cam.sensor_fit = 'HORIZONTAL'; cam.sensor_width = 36.0
        cam.lens = p[6] * 36.0 / W_; cam.clip_end = 5000
        co = bpy.data.objects.new('pcam%d' % i_, cam); scn.collection.objects.link(co)
        co.matrix_world = mathutils.Matrix.Translation(p[:3]) @ rot.to_4x4(); scn.camera = co
        scn.render.resolution_x, scn.render.resolution_y = W_, H_; scn.render.resolution_percentage = 100
        scn.render.filepath = os.path.join(ROOT, out_); bpy.ops.render.render(write_still=True)
elif MODE == 'glb':""")
open(p, 'w', encoding='utf-8', newline='').write(s); print('ok')
