"""Manuka's model frame (x east, y north, z up) to the match's space, as GroundModels.fit_transform lays the model:
glTF (x, z, -y), less FIT's centre, turned FIT[3] degrees about the vertical, 0.1 m under the turf."""
import math

import numpy as np

FIT = [4.68, 5.03, 0.0, -80.0, 85.94, 72.31]
UNDER_TURF = 0.1


def to_match(p, fit=FIT):
    x, y, z = p
    g = np.array([x, z, -y]) - np.array([fit[0], fit[2], fit[1]])
    a = math.radians(fit[3])
    # Godot Basis(UP, a): x' = x cos a + z sin a, z' = -x sin a + z cos a
    return np.array([g[0] * math.cos(a) + g[2] * math.sin(a), g[1] - UNDER_TURF, -g[0] * math.sin(a) + g[2] * math.cos(a)])


def spec(name, cam, look, fov):
    c, t = to_match(cam), to_match(look)
    return "%s:%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.2f" % (name, *c, *t, fov)
