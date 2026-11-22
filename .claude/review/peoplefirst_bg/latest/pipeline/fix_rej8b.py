"""Round the concourse garden beds to the sizes on the aerial (12-24 m across, not 35 m squares)."""
import json, math
sp = 'spec/peoplefirst.json'; s = json.load(open(sp, encoding='utf-8'))
C = [(-178, -33, 12), (-138, -50, 16), (-126, -98, 11), (-85, -144, 13), (-18, -152, 10), (-225, 28, 24)]
ISL = [[[round(x + r * math.cos(k * math.pi / 6) * (1 + 0.12 * math.sin(3 * k + x)), 1), round(y + r * 0.85 * math.sin(k * math.pi / 6), 1)] for k in range(12)] for x, y, r in C]
s['paint_poly'] = [p for p in s['paint_poly'] if p[0] != 'lawn_island'] + [['lawn_island', q] for q in ISL]
json.dump(s, open(sp, 'w', encoding='utf-8'), indent=1); print('ok')
