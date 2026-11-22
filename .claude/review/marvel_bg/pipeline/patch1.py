p=r'D:/Temp/claude/b5e56bf702cd3703/4ee81fc3-6cf4-400f-9ad6-28a5df4e19ee/scratchpad/proto/prep.py'
s=open(p,encoding='utf-8').read()
s=s.replace("""CLASS = spec['cover']  # list of [tagkey, tagvalue-or-*, palette key]""","""CLASS = spec['cover']  # list of [tagkey, tagvalue-or-*, palette key]
if spec.get('rivers_dry'): CLASS = [[k, v, 'sand' if pk == 'water' else pk] for k, v, pk in CLASS]
# open land: blend the default ground with a second cover by soft noise (patches 30-150 m)
if spec.get('open_mix'):
    def soft(cells, seed):
        r = np.random.default_rng(seed)
        return np.asarray(Image.fromarray((r.random((cells, cells)) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)).astype(np.float32) / 255
    mix = 0.6 * soft(int(2 * NEAR / 150), 11) + 0.4 * soft(int(2 * NEAR / 35), 12)
    mk, lo, hi = spec['open_mix']
    t_ = np.clip((mix - lo) / (hi - lo), 0, 1)[..., None]
    base_rgb = np.array(PAL['ground_default'], np.float32)[None, None, :] * (1 - t_) + np.array(PAL[mk], np.float32)[None, None, :] * t_
    img = Image.fromarray(base_rgb.astype(np.uint8)); dr = ImageDraw.Draw(img)""")
open(p,'w',encoding='utf-8',newline='').write(s)
