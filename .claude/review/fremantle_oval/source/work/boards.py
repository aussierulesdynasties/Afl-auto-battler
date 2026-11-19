# READY boards from a proof dir: camera-matched overlays, seating, joins/facades, turntable mp4.
# usage: boards.py <proof dir> <out dir>
import sys, os, subprocess, glob
from PIL import Image, ImageDraw, ImageFont
P, O = sys.argv[1], sys.argv[2]; os.makedirs(O, exist_ok=True)
try: F = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 24)
except Exception: F = None

def overlay(photo, render, out, label, fy=(0, 1)):
    # photo | model render (sky = magenta) | 50 % blend, photo scaled to the fitted camera's frame size
    r = Image.open(render).convert('RGBA'); a = Image.open(photo).convert('RGB').resize(r.size, Image.LANCZOS)
    bg = Image.new('RGBA', r.size, (255, 0, 255, 255)); rr = Image.alpha_composite(bg, r).convert('RGB')
    bl = Image.blend(a, rr, 0.5)
    cb = (0, int(fy[0] * r.height), r.width, int(fy[1] * r.height)); a, rr, bl = a.crop(cb), rr.crop(cb), bl.crop(cb)
    w, h = 1200, int(a.height * 1200 / a.width)
    o = Image.new('RGB', (w, 3 * h + 2 * 6 + 40), (24, 24, 24)); d = ImageDraw.Draw(o)
    d.text((8, 8), label + '   (top: photo, reference only | middle: model | bottom: 50 % blend)', fill=(255, 255, 255), font=F)
    for i, im in enumerate((a, rr, bl)): o.paste(im.resize((w, h), Image.LANCZOS), (0, 40 + i * (h + 6)))
    o.save(out, quality=88); print(out, o.size)

def grid(files, out, title, cols=2, w=800):
    ims = [Image.open(f).convert('RGB') for f in files]
    h = int(w * ims[0].height / ims[0].width); rows = (len(ims) + cols - 1) // cols
    o = Image.new('RGB', (cols * w, rows * (h + 34) + 40), (24, 24, 24)); d = ImageDraw.Draw(o)
    d.text((8, 8), title, fill=(255, 255, 255), font=F)
    for i, (f, im) in enumerate(zip(files, ims)):
        x, y = (i % cols) * w, 40 + (i // cols) * (h + 34)
        o.paste(im.resize((w, h), Image.LANCZOS), (x, y + 30)); d.text((x + 6, y + 4), os.path.basename(f)[:-4], fill=(220, 220, 120), font=F)
    o.save(out, quality=88); print(out, o.size)

overlay('hunt/a04.jpg', f'{P}/a04.png', f'{O}/overlay_a04.jpg', 'a04 (2024-07-15) high oblique from the south')
overlay('hunt/g34.jpg', f'{P}/g34h.png', f'{O}/overlay_g34.jpg', 'g34 (2023-02-24) from the oval looking south, building band', (0.12, 0.45))
overlay('hunt/a02.jpg', f'{P}/a02s0.png', f'{O}/overlay_a02.jpg', 'a02 (2020-10-04) drone over the north half looking south, building band', (0.28, 0.72))
overlay('hunt/g18.jpg', f'{P}/g18h.png', f'{O}/overlay_g18.jpg', 'g18 (2019-08-10) the former Dockers HQ from the field')
grid([f'{P}/{n}.png' for n in ('seat_nstand', 'seat_gj', 'seat_pav')], f'{O}/seating_empty.jpg',
     'Seating close-ups: every seat empty, real colours, no crowd', cols=1, w=1200)
grid([f'{P}/{n}.png' for n in ('close_pavilion', 'pav_annex', 'close_gate', 'close_nstand', 'close_terrace', 'gj_front', 'gj_nw',
                                 'gj_se', 'gj_fascia', 'gj_air', 'hq_front', 'hq_facade', 'hq_g18', 'hq_air', 'media_oval', 'media_street')],
     f'{O}/facades_joins.jpg', 'Facade and join close-ups', cols=2, w=800)
grid([f'{P}/still_{a:03d}.png' for a in (0, 90, 180, 270)], f'{O}/turntable_stills.jpg', 'Turntable stills 0/90/180/270 deg', cols=2, w=900)
ff = r'C:\Users\DANTE\AppData\Roaming\Python\Python314\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe'
subprocess.run([ff, '-y', '-loglevel', 'error', '-framerate', '15', '-i', f'{P}/turn_%03d.png', '-vf', 'scale=1280:-2',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', f'{O}/turntable.mp4'], check=True)
print(f'{O}/turntable.mp4', os.path.getsize(f'{O}/turntable.mp4'))
