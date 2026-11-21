# Column darkness profile of a tierstrip photo band -> candidate aisle bearings (local minima of luminance).
# python work/aislepeaks.py view b0 b1 z0 z1 out.png  (z0..z1 = height band on the rake to average)
import sys, os, subprocess, numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
v, b0, b1, z0, z1, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), sys.argv[6]
PX = 40
subprocess.run([sys.executable, os.path.join(HERE, 'tierstrip.py'), v, str(b0), str(b1), out + '.strip.png', str(PX)], check=True, capture_output=True)
S = Image.open(out + '.strip.png'); W, H2 = S.size; hh = (H2 - 4) // 2
ph = np.asarray(S.crop((0, 0, W, hh)).convert('L'), float)
y0, y1 = int((31 - z1) * 10), int((31 - z0) * 10)
band = ph[y0:y1]; m = np.where(band > 0, band, np.nan); prof = np.nanmedian(m, 0)
k = 3 * PX; tr = np.convolve(np.nan_to_num(prof, nan=np.nanmean(prof)), np.ones(k) / k, 'same'); dp = prof - tr
sm = np.convolve(np.nan_to_num(dp), np.ones(5) / 5, 'same')
mins = [i for i in range(3, len(sm) - 3) if sm[i] == min(sm[max(0, i - 12):i + 13]) and sm[i] < -2.0]
bs = [b0 + i / PX for i in mins]
print(' '.join('%.1f' % (b % 360) for b in bs)); print('gaps', ' '.join('%.1f' % g for g in np.diff(bs)))
crop = S.crop((0, max(0, y0 - 20), W, min(hh, y1 + 20))); im = Image.new('RGB', (W, crop.height + 80)); im.paste(crop, (0, 0)); dr = ImageDraw.Draw(im)
base = crop.height + 60
dr.line([(i, base - 2 * sm[i]) for i in range(len(sm))], fill=(255, 255, 0))
for i in mins: dr.line([(i, 0), (i, crop.height)], fill=(255, 0, 0)); dr.text((i + 1, crop.height + 2), '%.1f' % ((b0 + i / PX) % 360), fill=(255, 80, 80))
im.save(out); print(out)
