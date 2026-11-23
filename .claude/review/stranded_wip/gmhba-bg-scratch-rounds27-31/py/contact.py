import sys, glob
from PIL import Image
fs = sorted(glob.glob(sys.argv[1] + '/*.png')); n = 60
for k in range(0, len(fs), n):
    s = Image.new('RGB', (6 * 320, 10 * 180))
    for i, f in enumerate(fs[k:k + n]): s.paste(Image.open(f).convert('RGB').resize((320, 180)), ((i % 6) * 320, (i // 6) * 180))
    s.save('%s_%d.jpg' % (sys.argv[2], k // n), quality=85)
