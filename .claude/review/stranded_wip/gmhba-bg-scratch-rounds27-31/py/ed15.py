import sys
p = sys.argv[1]; s = open(p, newline='').read()
o = """            for fc in ((0, 1, 5, 4), (2, 3, 4, 5), (1, 2, 5), (3, 0, 4)):
                rf.append(tuple(r0 + t_ for t_ in fc)); rcl += [rc] * len(fc)"""
assert o in s
s = s.replace(o, """            _rc3 = np.array(rc)[:3] ** 1.12   # deeper, less pastel roof colour
            for fc, _sh in (((0, 1, 5, 4), 1.0), ((2, 3, 4, 5), 0.74), ((1, 2, 5), 0.88), ((3, 0, 4), 0.80)):   # each hip plane its own shade, so the roof reads as a hip from afar
                rf.append(tuple(r0 + t_ for t_ in fc)); rcl += [tuple(_rc3 * _sh) + tuple(np.array(rc)[3:])] * len(fc)""")
open(p, 'w', newline='').write(s); print('ok')
