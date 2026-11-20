"""drape the Esri orthophoto on z=0 through camera C (cyl) and blend with photo C. usage: drapeC.py cam.json out.jpg"""
import numpy as np, json, math, sys, os
sys.path.insert(0, 'tools')
from esri import m2px
from PIL import Image
c = json.load(open(sys.argv[1])); x0, y0, yaw, f, cy = c['p'][:5]; Z = c.get('eye', 1.6)
ph = np.asarray(Image.open('close/east_gate_2023.jpg').convert('RGB')).astype(float)
M = np.asarray(Image.open('esri/mosaic.jpg').convert('RGB')).astype(float)
s = 4; H, W = 2160 // s, 3840 // s
u = (np.arange(W) * s + s / 2); v = (np.arange(H) * s + s / 2); U, V = np.meshgrid(u, v)
th = (U - 1920) / f; tv = (V - cy) / f
ok = tv > 0.004; rho = np.where(ok, Z / np.maximum(tv, 1e-6), 0); rho = np.minimum(rho, 400)
# camera frame: forward = (cos yaw, sin yaw), right = (sin yaw, -cos yaw)  (projC.R: r = [sy, -cy, 0])
fx, fy = math.cos(yaw), math.sin(yaw); rx, ry = math.sin(yaw), -math.cos(yaw)
gx = x0 + rho * (np.cos(th) * fx + np.sin(th) * rx); gy = y0 + rho * (np.cos(th) * fy + np.sin(th) * ry)
# m2px is scalar; linearise around the camera
a0 = np.array(m2px(x0, y0)); ax = np.array(m2px(x0 + 1, y0)) - a0; ay = np.array(m2px(x0, y0 + 1)) - a0
px = a0[0] + (gx - x0) * ax[0] + (gy - y0) * ay[0]; py = a0[1] + (gx - x0) * ax[1] + (gy - y0) * ay[1]
inb = ok & (px >= 0) & (py >= 0) & (px < M.shape[1] - 1) & (py < M.shape[0] - 1)
G = np.zeros((H, W, 3)); G[inb] = M[py[inb].astype(int), px[inb].astype(int)]
P = np.asarray(Image.fromarray(ph.astype(np.uint8)).resize((W, H))).astype(float)
from scipy import ndimage
gm = G.mean(2); e = np.hypot(ndimage.sobel(gm, 0), ndimage.sobel(gm, 1)); e = (e > float(os.environ.get('ET', '120'))) & inb
grn = (G[..., 1] > G[..., 0] + 8) & (G[..., 1] > G[..., 2] + 8) & inb
out = P.copy(); out[grn] = 0.6 * out[grn] + 0.4 * np.array([255, 255, 0]); out[e] = [255, 0, 255]
Image.fromarray(out.astype(np.uint8)).save(sys.argv[2])
