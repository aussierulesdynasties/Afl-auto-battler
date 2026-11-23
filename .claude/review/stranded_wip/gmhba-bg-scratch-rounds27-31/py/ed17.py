p='py_mk_far_land.py'; s=open(p,newline='').read()
old="""        t = R.choice([0.74, 0.82, 0.9, 0.98, 1.06, 0.86]); hue = R.uniform(-0.10, 0.06)
        c = tuple(int(v) for v in np.clip(np.array([t * (1 + hue), t, t * (1 - hue) * 0.86]) * 205, 0, 255))
        rect_wrap(x0, y0, x1, y1, c)"""
new="""        PAD = [(196, 178, 118), (210, 192, 134), (122, 140, 82), (98, 124, 70), (150, 156, 96), (146, 120, 92), (176, 168, 120)]  # dry gold, stubble, irrigated green, dark pasture, mid pasture, ploughed brown, pale grass
        c = tuple(int(v) for v in np.clip(np.array(PAD[R.integers(0, len(PAD))], float) * R.uniform(0.92, 1.08), 0, 255))
        rect_wrap(x0, y0, x1, y1, c)
        rect_wrap(x0, y0, x1, y0 + 1, (84, 80, 66)); rect_wrap(x0, y0, x0 + 1, y1, (84, 80, 66))   # fence line on every boundary"""
assert old in s; s=s.replace(old,new); open(p,'w',newline='').write(s)
