# St Kilda, run after trace.py:
# front - the CMC Invest box's vertical fill reached the St Kilda shield just below it and drew its colours up the
#   black panel; the panels are straight up and down there, so the rows between the box and the shield take the
#   colours of the clean row just above the box.
# back - the collar band and its red/white/black tab, smoothed out of shape by the trace, are drawn again from the
#   photo's measured edges (top of the band, top of the black cloth, the tab's three stripes).
import numpy as np
from PIL import Image

W = (0xE6, 0xE8, 0xEE); K = (0x1C, 0x1A, 0x1D); R = (0xB0, 0x05, 0x24)

f = np.array(Image.open('design_STK_front.png').convert('RGBA'))
f[552:722, 1030:1310] = f[551, 1030:1310][None]
Image.fromarray(f).save('design_STK_front.png')

b = np.array(Image.open('design_STK_back.png').convert('RGBA'))
X = list(range(830, 1171, 10))
TOP = [261, 258, 254, 249, 246, 247, 251, 253, 255, 257, 258, 260, 261, 262, 263, 263, 263, 263, 263, 263, 263,
       262, 261, 260, 258, 256, 255, 253, 250, 247, 246, 249, 254, 259, 261]
BOT = [263, 267, 273, 278, 281, 283, 285, 286, 288, 288, 289, 290, 290, 290, 291, 291, 291, 291, 291, 290, 292,
       292, 291, 290, 289, 288, 287, 286, 284, 282, 279, 275, 272, 267, 263]
for x in range(835, 1166):
    t = int(round(np.interp(x, X, TOP))); bt = int(round(np.interp(x, X, BOT)))
    b[:t, x, 3] = 0
    b[t:bt, x, :3] = W; b[t:bt, x, 3] = 255
    b[bt:bt + 40, x, :3] = K; b[bt:bt + 40, x, 3] = 255
    if 983 <= x <= 995:
        b[t:bt, x, :3] = R
    elif 1007 <= x <= 1019:
        b[t:bt, x, :3] = K
Image.fromarray(b).save('design_STK_back.png')
print('stk_post done')
