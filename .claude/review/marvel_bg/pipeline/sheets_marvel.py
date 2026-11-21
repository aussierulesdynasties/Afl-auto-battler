"""Rebuild the fence, texcheck and stills contact sheets from the current renders."""
from PIL import Image
O = 'out/marvel/'
def sheet(files, out, cols, w=800):
    ims = [Image.open(O + f).convert('RGB') for f in files]; h = int(w * ims[0].size[1] / ims[0].size[0])
    s = Image.new('RGB', (w * cols, h * ((len(ims) + cols - 1) // cols)))
    for i, im in enumerate(ims): s.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
    s.save(O + out, quality=88)
sheet(['fence/fence_%d.png' % a for a in (0, 45, 90, 135, 180, 225, 270, 315)], 'fence/fence_sheet.jpg', 4, 600)
sheet(['texcheck/' + f for f in ('tower_close.png', 'towers_000.png', 'bridge_s.png', 'bridge_bolte.png')], 'texcheck/sheet.jpg', 2)
sheet(['stills/orbit_%03d.png' % i for i in range(4)], 'stills/sheet.jpg', 2)
print('ok')
