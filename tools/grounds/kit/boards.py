# Review boards from the proof renders: python3 kit/boards.py tools/grounds/<slug> <render dir> <review dir>
# 1 top-down over the satellite (satellite | model | 50% blend), 2 turntable stills, 3 seats and boundary views, orbit mp4.
import sys, os, glob, json, subprocess, numpy as np, cv2
G = os.path.abspath(sys.argv[1]); SLUG = os.path.basename(G); R = sys.argv[2]; O = sys.argv[3]; os.makedirs(O, exist_ok=True)
def lab(im, t):
    cv2.rectangle(im, (0, 0), (len(t) * 13 + 16, 30), (0, 0, 0), -1); cv2.putText(im, t, (8, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1); return im
sat = cv2.imread(os.path.join(G, 'work', 'sat.png')); top = cv2.imread(os.path.join(R, 'top.png'), cv2.IMREAD_UNCHANGED)
if top is not None:
    top = cv2.resize(top, sat.shape[1::-1]); a = top[..., 3:4] / 255.0; mdl = (top[..., :3] * a + sat * (1 - a) * 0.25).astype(np.uint8)
    bl = (sat * (1 - 0.5 * a) + top[..., :3] * 0.5 * a).astype(np.uint8)
    S = 900; row = [lab(cv2.resize(x, (S, S)), t) for x, t in ((sat, 'satellite (Google, 2026)'), (mdl, 'model, straight down'), (bl, 'model over satellite, 50%'))]
    cv2.imwrite(os.path.join(O, '1_topdown_vs_satellite.jpg'), np.hstack(row), [cv2.IMWRITE_JPEG_QUALITY, 88])
def grid(files, name, cols=2, w=960):
    ims = [lab(cv2.resize(cv2.imread(f), (w, w * 9 // 16)), os.path.basename(f)[:-4]) for f in files]
    while len(ims) % cols: ims.append(np.zeros_like(ims[0]))
    cv2.imwrite(os.path.join(O, name), np.vstack([np.hstack(ims[i:i + cols]) for i in range(0, len(ims), cols)]), [cv2.IMWRITE_JPEG_QUALITY, 88])
st = sorted(glob.glob(os.path.join(R, 'turntable_*.png')))
if st: grid(st, '2_turntable_stills.jpg')
cl = sorted(glob.glob(os.path.join(R, 'seats_*.png'))) + sorted(glob.glob(os.path.join(R, 'low_*.png')))
if cl: grid(cl, '3_seats_and_boundary.jpg')
fr = sorted(glob.glob(os.path.join(R, 'orbit', 'f*.png')))
if fr:
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '12', '-i', os.path.join(R, 'orbit', 'f%03d.png'), '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', '-crf', '26', os.path.join(O, '4_orbit.mp4')], check=True)
print('boards in', O, sorted(os.listdir(O)))
