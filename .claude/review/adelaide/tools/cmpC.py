"""cmpC.py RENDER OUT [x0,y0,x1,y1] : photo C | render | 50% blend, stacked, cropped (full-res photo px)"""
import sys, cv2, numpy as np
ph = cv2.imread('close/east_gate_2023.jpg'); r = cv2.imread(sys.argv[1], cv2.IMREAD_UNCHANGED)
if r.shape[2] == 4:
    a = r[..., 3:4] / 255.0; r = (r[..., :3] * a + 255 * (1 - a)).astype(np.uint8)
r = cv2.resize(r, (ph.shape[1], ph.shape[0]))
x0, y0, x1, y1 = map(int, (sys.argv[3] if len(sys.argv) > 3 else '1420,820,3580,1420').split(','))
P, R = ph[y0:y1, x0:x1], r[y0:y1, x0:x1]; B = cv2.addWeighted(P, 0.5, R, 0.5, 0)
out = np.vstack([P, R, B]); s = min(1.0, 1600 / out.shape[1]); cv2.imwrite(sys.argv[2], cv2.resize(out, None, fx=s, fy=s))
