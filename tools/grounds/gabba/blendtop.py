import sys
from PIL import Image
r = Image.open(sys.argv[1]).convert('RGBA'); s = Image.open(sys.argv[2]).convert('RGBA')
b = Image.blend(s, Image.alpha_composite(s, r), 0.5)
W = 1440; c = (80, 80, 1520, 1520)
row = Image.new('RGB', (W * 3, W)); row.paste(s.crop(c).convert('RGB'), (0, 0)); row.paste(Image.alpha_composite(Image.new('RGBA', r.size, (0, 0, 0, 255)), r).crop(c).convert('RGB'), (W, 0)); row.paste(b.crop(c).convert('RGB'), (2 * W, 0))
row.save(sys.argv[3]); b.crop(c).convert('RGB').save(sys.argv[3].replace('.png', '_blend.png'))
