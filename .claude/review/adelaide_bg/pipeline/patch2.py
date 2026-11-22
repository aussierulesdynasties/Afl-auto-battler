p=r'D:/Temp/claude/b5e56bf702cd3703/4ee81fc3-6cf4-400f-9ad6-28a5df4e19ee/scratchpad/proto/prep.py'
s=open(p,encoding='utf-8').read()
s=s.replace("""    t_ = np.clip((mix - lo) / (hi - lo), 0, 1)[..., None]""","""    t_ = 0.75 * np.clip((mix - lo) / (hi - lo), 0, 1)
    # steep slopes (from the real terrain) paint as rock
    gy_, gx_ = np.gradient(near, NS)
    sl = np.hypot(gx_, gy_)
    slI = np.asarray(Image.fromarray(np.clip(sl * 255 / 1.5, 0, 255).astype(np.uint8)).resize((N, N), Image.BILINEAR)).astype(np.float32) * 1.5 / 255
    rk = np.clip((slI - 0.18) / 0.25, 0, 1)
    t_ = t_[..., None]; rk = rk[..., None]""")
s=s.replace("""    base_rgb = np.array(PAL['ground_default'], np.float32)[None, None, :] * (1 - t_) + np.array(PAL[mk], np.float32)[None, None, :] * t_""","""    base_rgb = np.array(PAL['ground_default'], np.float32)[None, None, :] * (1 - t_) + np.array(PAL[mk], np.float32)[None, None, :] * t_
    base_rgb = base_rgb * (1 - rk) + np.array(PAL['rock'], np.float32)[None, None, :] * rk""")
open(p,'w',encoding='utf-8',newline='').write(s)
