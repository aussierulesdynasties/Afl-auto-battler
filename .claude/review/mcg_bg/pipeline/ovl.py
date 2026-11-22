"""Top-down check: scene ortho render vs straight-down satellite (same frame, north up). ovl.py top.png sat.png out_prefix"""
import sys
import numpy as np
from PIL import Image, ImageDraw
T = Image.open(sys.argv[1]).convert('RGB'); S = Image.open(sys.argv[2]).convert('RGB').resize(T.size, Image.LANCZOS)
B = Image.blend(T, S, 0.5); B.save(sys.argv[3] + '_blend.png')
# checkerboard 100 px squares: alternating scene / satellite, so edges can be traced across the seams
W, H = T.size; m = np.zeros((H, W), bool); yy, xx = np.mgrid[0:H, 0:W]; m = ((xx // 100 + yy // 100) % 2) == 0
C = np.where(m[..., None], np.asarray(T), np.asarray(S)); Image.fromarray(C.astype(np.uint8)).save(sys.argv[3] + '_check.png')
print('ok')
