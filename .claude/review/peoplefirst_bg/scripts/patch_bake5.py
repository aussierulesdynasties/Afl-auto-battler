s = open('bake_ground.py', encoding='utf-8', newline='').read()
# grass detail: the People First grass set (4 m tile, 1 m mown stripes, clumps), normalised to a multiplier with the old mean
a = "det = Image.open(os.path.join(H, 'tex', 'ground_detail.png')).convert('RGB'); DS = det.size[0]"
assert s.count(a) == 1
s = s.replace(a, """_pg = np.asarray(Image.open(os.path.join(H, 'tex', 'pf_grass.png')).convert('RGB'), np.float32); _l = _pg @ np.array([0.299, 0.587, 0.114])
_l = np.clip(_l / _l.mean() * 210, 0, 255); det = Image.fromarray(np.dstack([_l] * 3).astype(np.uint8)).resize((512, 512), Image.BICUBIC); DS = det.size[0]""")
# water: deeper and darker toward the channel, 30 m tone noise, a pale muddy shoreline edge
b = "p = os.path.join(D, 'ground_baked.png')"
assert s.count(b) == 1
s = s.replace(b, """o3 = out.astype(np.int16); wm = (o3[..., 2] > o3[..., 1] + 4) & (o3[..., 2] > o3[..., 0] + 12)
WM = Image.fromarray((wm * 255).astype(np.uint8))
deep = np.asarray(WM.filter(ImageFilter.GaussianBlur(14 / m_)), np.float32) / 255     # ~1 in mid channel, ~0.5 at the bank
edge = np.asarray(WM.filter(ImageFilter.GaussianBlur(1.5 / m_)), np.float32) / 255
tn = np.asarray(Image.fromarray((R_.random((int(2 * NE / 30) + 2,) * 2) * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), np.float32) / 255
shallow = np.array([96, 120, 118], np.float32); chan = np.array([40, 66, 82], np.float32); mud = np.array([150, 140, 112], np.float32)
for r0 in range(0, S, 512):
    rr = slice(r0, min(S, r0 + 512)); t = np.clip((deep[rr] - 0.5) / 0.45, 0, 1)[..., None]
    w = shallow * (1 - t) + chan * t; w = w * (0.92 + 0.16 * tn[rr][..., None])
    w = np.where(((edge[rr] < 0.75) & wm[rr])[..., None], mud * 0.6 + w * 0.4, w)
    sh = (~wm[rr]) & (edge[rr] > 0.06)                                                  # wet bank just outside the water line
    o = out[rr].astype(np.float32); o = np.where(sh[..., None], o * 0.5 + mud * 0.5, o)
    out[rr] = np.where(wm[rr][..., None], w, o).clip(0, 255).astype(np.uint8)
p = os.path.join(D, 'ground_baked.png')""")
open('bake_ground.py', 'w', encoding='utf-8', newline='').write(s); print('ok')
