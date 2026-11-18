"""Encode a frames folder to mp4: python py/enc.py frames_dir out.mp4 [fps]"""
import sys, glob, cv2
fs = sorted(glob.glob(sys.argv[1] + "/f_*.png")); fps = float(sys.argv[3]) if len(sys.argv) > 3 else 24
h, w = cv2.imread(fs[0]).shape[:2]
for cc in ("avc1", "mp4v"):
    vw = cv2.VideoWriter(sys.argv[2], cv2.VideoWriter_fourcc(*cc), fps, (w, h))
    if vw.isOpened(): break
for f in fs: vw.write(cv2.imread(f))
vw.release(); print("ENCODED", len(fs), "frames", cc, sys.argv[2])
