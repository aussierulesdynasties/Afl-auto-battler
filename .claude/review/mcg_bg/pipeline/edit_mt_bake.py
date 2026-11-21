p='bake_ground.py'; s=open(p).read()
s=s.replace("""out = np.empty((S, S, 3), np.uint8); ga = np.asarray(g)""","""out = np.empty((S, S, 3), np.uint8); ga = np.asarray(g)
# road pixels: ground.png colour within the prep grain envelope (x0.85..1.15, same hue) of the spec's road colour
RC = np.array(json.load(open(os.path.join(H, 'spec', name + '.json')))['palette']['road'], np.float32)
g0 = np.asarray(Image.open(os.path.join(D, 'ground.png')).convert('RGB'), np.float32); q = g0 / RC
rm = ((q.min(2) > 0.85) & (q.max(2) < 1.15) & (q.max(2) - q.min(2) < 0.06)).astype(np.uint8) * 255
rm = Image.fromarray(rm).filter(ImageFilter.MedianFilter(3)).resize((S, S), Image.BILINEAR)
RM = np.asarray(rm, np.float32) / 255.0; print('road px %.1f%%' % (100 * RM.mean()))
# road_asphalt.png: one 512 px tile = 8 m, multiplier lifted so its mean (linear) is 1: the road keeps its colour on average
rt = 2 * NE / 8.0; rppt = S / rt; ra = Image.open(os.path.join(H, 'tex', 'road_asphalt.png')).convert('RGB'); RS = ra.size[0]
rsig = max(0.0, RS / rppt / 2); rbig = Image.fromarray(np.tile(np.asarray(ra), (3, 3, 1)))
ral = dec(np.asarray(rbig.filter(ImageFilter.GaussianBlur(rsig)), np.float32)[RS:2 * RS, RS:2 * RS]); ral = ral / ral.mean()
rc_ = (np.arange(S) + 0.5) / S * rt; rfx = (rc_ % 1.0) * RS - 0.5; rfy = (1.0 - (rc_ % 1.0)) * RS - 0.5
ri0 = np.floor(rfx).astype(int); rax = (rfx - ri0)[None, :, None]""")
s=s.replace("""    out[rr] = np.round(enc(dec(ga[rr].astype(np.float32)) * d * 1.21)).astype(np.uint8)""","""    rj0 = np.floor(rfy[rr]).astype(int); ray = (rfy[rr] - rj0)[:, None, None]
    K0, K1 = rj0 % RS, (rj0 + 1) % RS; L0, L1 = ri0 % RS, (ri0 + 1) % RS
    e = (ral[K0][:, L0] * (1 - rax) + ral[K0][:, L1] * rax) * (1 - ray) + (ral[K1][:, L0] * (1 - rax) + ral[K1][:, L1] * rax) * ray
    m_ = RM[rr][..., None]; e = 1 + (e - 1) * m_
    out[rr] = np.round(enc(dec(ga[rr].astype(np.float32)) * d * 1.21 * e)).astype(np.uint8)""")
open(p,'w').write(s)
