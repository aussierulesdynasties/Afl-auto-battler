"""texstat.py DIR: grey-level stddev (0-255) of every texture probe image, far and near"""
import sys, glob, os, numpy as np
from PIL import Image
rows = {}
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*_*.png'))):
    nm, tag = os.path.basename(f)[:-4].rsplit('_', 1)
    g = np.asarray(Image.open(f).convert('L'), float); rows.setdefault(nm, {})[tag] = (g.std(), g.mean())
for nm, r in rows.items():
    print(f"{nm:16s} far sd {r.get('far',(0,0))[0]:5.1f}  near sd {r.get('near',(0,0))[0]:5.1f}  mean {r.get('far',(0,0))[1]:5.1f}")
