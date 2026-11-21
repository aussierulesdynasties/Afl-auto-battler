s = open('bake_ground.py', encoding='utf-8', newline='').read()
a = "_l = np.clip(_l / _l.mean() * 210, 0, 255); det = Image.fromarray(np.dstack([_l] * 3).astype(np.uint8)).resize((512, 512), Image.BICUBIC); DS = det.size[0]"
assert s.count(a) == 1
s = s.replace(a, """_st = _l.mean(0); _st = np.asarray(Image.fromarray((_st / _st.max() * 255).astype(np.uint8)[None]).resize((512, 1), Image.BILINEAR), np.float32)[0]; _st /= _st.mean()   # People First mowing stripes only (column profile: seamless)
_od = np.asarray(Image.open(os.path.join(H, 'tex', 'ground_detail.png')).convert('RGB'), np.float32)   # seamless clumps tile
det = Image.fromarray(np.clip(_od * _st[None, :, None], 0, 255).astype(np.uint8)); DS = det.size[0]""")
open('bake_ground.py', 'w', encoding='utf-8', newline='').write(s); print('ok')
