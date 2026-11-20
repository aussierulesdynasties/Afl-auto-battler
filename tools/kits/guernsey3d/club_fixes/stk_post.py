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
# front hem - the trace cut the white panel 8 px short of the red and black; in the photo the hem is one line
#   across all three panels. A smooth curve fitted to the red and black panels' bottoms is the hem for every column.
al = f[..., 3] > 127
bot = np.array([np.nonzero(al[:, c])[0].max() if al[:, c].any() else -1 for c in range(2000)])
cs = np.r_[np.arange(600, 880, 10), np.arange(1170, 1400, 10)]
fit = np.polyfit(cs, bot[cs], 2)
for c in range(600, 1400):
    h = int(round(np.polyval(fit, c)))
    src = min(bot[c], h) - 6
    f[src:h + 1, c] = f[src, c]
    f[h + 1:, c, 3] = 0
# red armhole binding - the game draws it (kits_today.csv armholes, 1.5 cm in from the cut's own edge, as the
#   photo's black band measures 35 px / 2310 px a metre), so the painted copy goes back to the red panel
reg = f[300:800, :720]
blk = (reg[..., 3] > 0) & (np.abs(reg[..., :3].astype(int) - K).sum(-1) < 60)
reg[blk, :3] = R
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
# collar ends - the photo shows the band narrowing at each end only because it turns over the shoulder away from
#   the camera; it is one even band that meets the front's white collar at the shoulder seam (front x 814-857 and
#   1136-1186, mirrored onto the back as 1141-1184 and 812-862), so it runs that far at the middle's 28 px depth
for x in range(812, 1185):
    t = int(np.nonzero(b[:, x, 3] > 127)[0][0])
    bt = max(t + 28, int(round(np.interp(x, X, BOT))) if 830 <= x <= 1170 else 0)
    if not (983 <= x <= 995 or 1007 <= x <= 1019):
        b[t:bt, x, :3] = W
Image.fromarray(b).save('design_STK_back.png')
print('stk_post done')
