base=r'D:/Temp/claude/b5e56bf702cd3703/4ee81fc3-6cf4-400f-9ad6-28a5df4e19ee/scratchpad/proto/'
s=open(base+'prep.py',encoding='utf-8').read()
old_start=s.index("m = np.asarray(mask).astype(np.float32) / 255 * 40000")
old_end=s.index("keep = (rng.random(GX.shape)")
new='''mv = np.asarray(mask).astype(np.float32)   # stores 40000 / (m^2 per tree), 0 = no trees
cell = 6.0
gx = np.arange(-NEAR + cell / 2, NEAR, cell)
GX, GY = np.meshgrid(gx, gx)
GX = GX + rng.uniform(-cell / 2, cell / 2, GX.shape); GY = GY + rng.uniform(-cell / 2, cell / 2, GY.shape)
ix = np.clip(((GX + NEAR) / PX).astype(int), 0, N - 1); iy = np.clip(((NEAR - GY) / PX).astype(int), 0, N - 1)
v = mv[iy, ix]
prob = np.where(v > 0, cell * cell * v / 40000.0, 0)   # cell area / (m^2 per tree)
'''
s=s[:old_start]+new+s[old_end:]
open(base+'prep.py','w',encoding='utf-8',newline='').write(s)
print('ok')
