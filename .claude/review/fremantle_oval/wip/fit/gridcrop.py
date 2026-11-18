import cv2, sys
im = cv2.imread(sys.argv[1]); x0, y0, x1, y1, k, step = map(int, sys.argv[2:8]); out = sys.argv[8]
c = cv2.resize(im[y0:y1, x0:x1], None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
for x in range((x0 // step + 1) * step, x1, step):
    X = (x - x0) * k; cv2.line(c, (X, 0), (X, c.shape[0]), (0, 255, 255), 1); cv2.putText(c, str(x), (X + 2, 12), 0, 0.4, (0, 255, 255), 1)
for y in range((y0 // step + 1) * step, y1, step):
    Y = (y - y0) * k; cv2.line(c, (0, Y), (c.shape[1], Y), (255, 0, 255), 1); cv2.putText(c, str(y), (2, Y - 2), 0, 0.4, (255, 0, 255), 1)
cv2.imwrite(out, c)
