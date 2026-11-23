s = open('scene.py', newline='').read()
a = s[s.index('    from PIL import Image as _PI'):s.index('    TILE = 7.2')]
s = s.replace(a, "    def _tint(rgb, fn): return os.path.join(HERE, 'tex', fn)   # made by mk_road_tex.py (Blender has no PIL)\n")
s = s.replace("    from PIL import Image as _PI\n", "")
open('scene.py', 'w', newline='').write(s); print('ok')
