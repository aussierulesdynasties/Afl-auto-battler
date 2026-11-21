p='scene.py';L=open(p,newline='').read().split('\n');out=[]
for l in L:
    e='\r' if l.endswith('\r') else ''
    if 'rotation_euler[2] -= MROT' in l: l="for o in _bg: o.matrix_world = Matrix.Rotation(-MROT, 4, 'Z') @ o.matrix_world"+e
    elif l.startswith('for o in _bg: o.rotation_euler[2] += MROT'): l="for o in _bg: o.matrix_world = Matrix.Rotation(MROT, 4, 'Z') @ o.matrix_world"+e
    elif 'rotation_euler[2] += MROT' in l: l="    o.matrix_world = Matrix.Rotation(MROT, 4, 'Z') @ o.matrix_world"+e
    elif l.startswith('from mathutils import Vector') and 'Matrix' not in l: l='from mathutils import Vector, Matrix'+e
    out.append(l)
s='\n'.join(out);print(s.count('Matrix.Rotation'));open(p,'w',newline='').write(s)
