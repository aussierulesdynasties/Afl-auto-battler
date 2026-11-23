import sys, glob
from PIL import Image
fs = sorted(glob.glob(sys.argv[1] + '/*.png')); out = sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 2
ims = [Image.open(f).convert('RGB').resize((800, 450)) for f in fs]; rows = (len(ims) + cols - 1) // cols
s = Image.new('RGB', (800 * cols, 450 * rows))
for i, im in enumerate(ims): s.paste(im, ((i % cols) * 800, (i // cols) * 450))
s.save(out, quality=88); print(out, len(ims))
