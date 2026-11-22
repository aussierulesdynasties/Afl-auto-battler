p='fc_scene.py';s=open(p,newline='').read()
old="    _Lk = np.asarray(_PI3.open(os.path.join(HERE, 'data', 'optus', 'sat_hi_plaza.png')).convert('L'), np.float32) / 2.55"
new="""    _im3 = bpy.data.images.load(os.path.join(HERE, 'data', 'optus', 'sat_hi_plaza.png')); _w3, _h3 = _im3.size
    _px3 = np.empty(_w3 * _h3 * 4, np.float32); _im3.pixels.foreach_get(_px3); _px3 = _px3.reshape(_h3, _w3, 4)[::-1]
    _Lk = (0.299 * _px3[..., 0] + 0.587 * _px3[..., 1] + 0.114 * _px3[..., 2]) * 100; bpy.data.images.remove(_im3)"""
assert old in s; s=s.replace(old,new).replace("    from PIL import Image as _PI3\n",""); open(p,'w',newline='').write(s)
