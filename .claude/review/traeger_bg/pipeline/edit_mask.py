def sub(f, a, b):
    s = open(f, newline='').read(); assert a in s, (f, a[:50]); open(f, 'w', newline='').write(s.replace(a, b, 1))
sub('build.sh', 'probe_outline.py -- "$GLB" data/$g/prep/fence_outline.json $TB 2>&1 | grep OUTLINE', 'fence_mask.py -- "$GLB" data/$g/prep/fence_mask.npy $TB 2>&1 | grep MASK')
sub('scene.py', """FO = os.path.join(D, 'fence_outline.json')
if spec.get('trim_base') and os.path.exists(FO):   # the model's square base stops at its fence (scene copy only, the GLB is untouched)
    RO = np.array(json.load(open(FO)))""", """FO = os.path.join(D, 'fence_mask.npy')
if spec.get('trim_base') and os.path.exists(FO):   # the model's square base stops at its fence (scene copy only, the GLB is untouched)
    FM = np.load(FO); FN = FM.shape[0]""")
sub('scene.py', """            c = M @ f.calc_center_median(); b = int((math.degrees(math.atan2(c.y, c.x)) % 360) // 2)
            if math.hypot(c.x, c.y) > RO[b] + spec.get('trim_margin_m', 3): kill.append(f)""", """            c = M @ f.calc_center_median(); i, j = int((260 - c.y) / 0.5), int((c.x + 260) / 0.5)
            if not (0 <= i < FN and 0 <= j < FN and FM[i, j]): kill.append(f)""")
sub('prep.py', """FO = os.path.join(OUT, 'fence_outline.json')
if spec.get('trim_base') and os.path.exists(FO):
    RO = json.load(open(FO)); dr.polygon(P([((RO[i] + 3) * math.cos(math.radians(2 * i + 1)), (RO[i] + 3) * math.sin(math.radians(2 * i + 1))) for i in range(180)]), fill=tuple(PAL['lawn']))""", """FO = os.path.join(OUT, 'fence_mask.npy')
if spec.get('trim_base') and os.path.exists(FO):
    FM = Image.fromarray((np.load(FO) * 255).astype(np.uint8)); x0_, y0_ = P([(-260, 260)])[0]; x1_, y1_ = P([(260, -260)])[0]
    FM = FM.resize((max(1, round(x1_ - x0_)), max(1, round(y1_ - y0_))), Image.NEAREST)
    img.paste(Image.new('RGB', FM.size, tuple(PAL['lawn'])), (round(x0_), round(y0_)), FM)""")
print('ok')
