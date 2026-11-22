p='scene.py'; s=open(p,encoding='utf-8',newline='').read()
a="H = np.array(hull, float); z = height(H[:, 0], H[:, 1]).max() + 0.04"
assert a in s; s=s.replace(a,a+"; SLZ = z",1)
a="z = float(height(np.array([cx]), np.array([cy]))[0]) + 0.08; nc += 1"
assert a in s; s=s.replace(a,"z = SLZ + 0.04; nc += 1",1)
open(p,'w',encoding='utf-8',newline='').write(s); print('ok')
