p='scene.py'; s=open(p,newline='').read()
a="""                if len(c) < 3: continue
                C = np.array(c); z = height(C[:, 0], C[:, 1]) + lift; s0 = len(PV)
                PV.extend(zip(C[:, 0], C[:, 1], z))
                for tri in tessellate_polygon([[Vector((a, b, 0)) for a, b in c]]): PF.append(tuple(s0 + t for t in tri))"""
b="""                c = [v for k, v in enumerate(c) if math.hypot(v[0] - c[k - 1][0], v[1] - c[k - 1][1]) > 1e-4]   # drop repeated points
                if len(c) < 3: continue
                C = np.array(c); z = height(C[:, 0], C[:, 1]) + lift; s0 = len(PV)
                PV.extend(zip(C[:, 0], C[:, 1], z))
                T = tessellate_polygon([[Vector((a, b, 0)) for a, b in c]]) or [(0, k, k + 1) for k in range(1, len(c) - 1)]
                for tri in T: PF.append(tuple(s0 + t for t in tri))"""
assert a in s; open(p,'w',newline='').write(s.replace(a,b)); print('ok')
