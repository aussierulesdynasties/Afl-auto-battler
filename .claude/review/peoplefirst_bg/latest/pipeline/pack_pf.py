import os, shutil, subprocess, imageio_ffmpeg
from PIL import Image
P = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(P, 'out', 'peoplefirst', 'video', 'orbit_frames')
N = r'C:\Users\DANTE\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_a479dc03-8848-4245-9544-2b0221533a84\peoplefirst_bg'
os.makedirs(os.path.join(N, 'frames30'), exist_ok=True)
ff = imageio_ffmpeg.get_ffmpeg_exe()
mp4 = os.path.join(N, 'peoplefirst_orbit.mp4')
subprocess.run([ff, '-y', '-framerate', '30', '-i', os.path.join(F, 'f_%04d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', mp4], check=True, capture_output=True)
picks = list(range(1, 241, 30))
for n in picks: shutil.copy(os.path.join(F, 'f_%04d.png' % n), os.path.join(N, 'frames30'))
W, H = 640, 360; sheet = Image.new('RGB', (W * 4, H * 2))
for i, n in enumerate(picks):
    sheet.paste(Image.open(os.path.join(F, 'f_%04d.png' % n)).convert('RGB').resize((W, H)), ((i % 4) * W, (i // 4) * H))
sheet.save(os.path.join(N, 'peoplefirst_ring.png')); print('ok', mp4)
