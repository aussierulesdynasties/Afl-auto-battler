"""Pinhole camera matched to a photo (2000-px wide working copy).
Camera frame on the ground: X right, Z forward (level), height EYE. Pitch from the horizon row."""
import math
W = 2000

class Cam:
    def __init__(self, H, fov_h=69.4, horizon=None, eye=1.6, roll=0.0):
        self.f = (W / 2) / math.tan(math.radians(fov_h) / 2); self.cx = W / 2; self.cy = H / 2
        self.hz = horizon if horizon is not None else self.cy
        self.pitch = math.atan((self.hz - self.cy) / self.f)   # + = looking up
        self.eye = eye; self.fov_h = fov_h
    def ray(self, u, v):
        # direction in the level frame (X right, Y up, Z fwd)
        x = (u - self.cx) / self.f; y = -(v - self.cy) / self.f; z = 1.0
        c, s = math.cos(self.pitch), math.sin(self.pitch)
        return (x, y * c + z * s, -y * s + z * c)
    def back(self, u, v, H=0.0):
        """pixel -> (X, Z) of the point at height H"""
        dx, dy, dz = self.ray(u, v)
        t = (H - self.eye) / dy
        return (dx * t, dz * t)
    def height(self, u, v, Z):
        """pixel at known forward depth Z -> height"""
        dx, dy, dz = self.ray(u, v)
        return self.eye + dy * Z / dz
    def proj(self, X, Y, Z):
        """level-frame point (Y = height) -> pixel"""
        y = Y - self.eye; c, s = math.cos(self.pitch), math.sin(self.pitch)
        yc = y * c - Z * s; zc = y * s + Z * c
        return (self.cx + self.f * X / zc, self.cy - self.f * yc / zc)
