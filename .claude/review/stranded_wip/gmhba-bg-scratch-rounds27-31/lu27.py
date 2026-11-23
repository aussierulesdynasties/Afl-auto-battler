import numpy as np, sys
from PIL import Image
LU = np.load('data/gmhba/landuse.npy'); FA = 30000
S = np.asarray(Image.open('data/gmhba/sat_far.png').convert('RGB')); print('sat_far', S.shape)
for x, y in [(1728, 7208), (2726, 8288), (3092, 7291), (4531, 8897)]:
    r, c = int((FA - y) / 30), int((x + FA) / 30)
    sr, scc = int((FA - y) / (2 * FA) * S.shape[0]), int((x + FA) / (2 * FA) * S.shape[1])
    print(x, y, 'LU', LU[r, c], 'sat', S[sr, scc])
