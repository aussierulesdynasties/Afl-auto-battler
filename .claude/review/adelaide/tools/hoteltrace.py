"""trace the hotel's outer (east) facade on the Level 4 plan (h10): per plan column, the lowest pixel of the big
connected building mass (room fills + walls). Writes grid/hotel_outer.json (plan px) and an overlay to check."""
import numpy as np, cv2, json
im = cv2.imread('hplans/h10.png'); u0, u1, v0, v1 = 380, 4700, 1100, 2160
c = im[v0:v1, u0:u1].astype(int)
sat = c.max(2) - c.min(2); val = c.max(2)
mask = ((sat > 22) | (val < 110)).astype(np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(mask, 8)
big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); M = lab == big
out = []
for x in range(0, u1 - u0, 4):
    ys = np.nonzero(M[:, x])[0]
    if len(ys): out.append((u0 + x, v0 + int(ys.max())))
json.dump(out, open('grid/hotel_outer.json', 'w'))
o = im.copy()
cv2.polylines(o, [np.array(out, np.int32)], False, (0, 0, 255), 4)
cv2.imwrite('grid/hotel_outer.jpg', cv2.resize(o[1000:2300, 0:4967], None, fx=0.3, fy=0.3, interpolation=cv2.INTER_AREA))
