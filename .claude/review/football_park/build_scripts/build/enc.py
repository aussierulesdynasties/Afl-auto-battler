import imageio_ffmpeg,subprocess,os
ff=imageio_ffmpeg.get_ffmpeg_exe()
for T in ('AE','BE'):
    subprocess.run([ff,'-y','-loglevel','error','-framerate','24','-i',f'tt{T}/f%03d.png','-c:v','libx264','-pix_fmt','yuv420p','-crf','18',f'tt{T}.mp4'],check=True); print(T,os.path.getsize(f'tt{T}.mp4'))
