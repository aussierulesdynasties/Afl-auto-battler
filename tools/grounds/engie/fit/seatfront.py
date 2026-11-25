# The east stand's front row (sunlit in the top-down shot): along rays from the origin, the first red seats out
# from the field (3x3 pixels mostly red), 72 to 140 deg. The front wall stands 0.8 m in front of the first seats'
# middles in the model (0.3 m to the first riser, half a tread less the seat's set-back), so the stand front there
# is that radius less 0.8 m. Writes seatfront.json [[bearing, first-seat radius], ...].
import numpy as np, json, math, cv2
C = json.load(open('cal.json')); S, DX, DY = C['s'], C['dx'], C['dy']
im = cv2.imread('ge/top3000.png').astype(int); red = (im[..., 2] > im[..., 1] + 45) & (im[..., 2] > 110)
out = []
for b in np.arange(72.0, 140.01, 0.5):
    t = math.radians(b)
    for r in np.arange(66.0, 96.0, 0.1):
        e, n = r * math.sin(t), r * math.cos(t); x = int(round(640 + (e - DX) / S)); y = int(round(360 - (n - DY) / S))
        if red[max(0, y - 1):y + 2, max(0, x - 1):x + 2].mean() > 0.6:
            out.append([float(b), float(r)]); break
json.dump(out, open('seatfront.json', 'w'))
a = np.array(out); print(len(a), 'bearings;', [(b, round(r, 1)) for b, r in a[::8]])
