"""Sentinel-2's true colour graded to Google Earth's Alice Springs: one 3x4 colour matrix that matches the two
colour distributions (qa/grade_fit.py) on the open land (river bed, hills, parks) where both see the same ground at 10 m. The
satellite's TCI is stretched hot and red; Google Earth's land is a duller tan with olive scrub. Applied to
the far scene's texture and the near map's base alike, so the two meet without a seam."""
import numpy as np

# rows: out R, G, B = M @ (r, g, b, 1)
M = np.array([[0.841, 0.119, -0.021, -20.711],
              [0.119, 0.812, -0.007, 5.958],
              [-0.021, -0.007, 1.223, 8.526]], np.float32)


# Sentinel-2's 10 m cells over the suburbs past the near scene mix bright tin roofs into near white; Google
# Earth's same suburbs, seen from the ground's cameras, are a grey of roofs and gums. Past KNEE the
# brightness is pressed down (by 0.3), keeping the hue.
KNEE = 168.0


def grade(img):
    a = np.asarray(img, np.float32)
    out = a @ M[:, :3].T + M[:, 3]
    L = out.mean(-1, keepdims=True)
    Lk = np.where(L > KNEE, KNEE + (L - KNEE) * 0.3, L)
    out = out * (Lk / np.maximum(L, 1.0))
    return np.clip(out, 0, 255).astype(np.uint8)
