"""Stack capture_calls3d.gd's frames into one film a call: Balanced left, the call right; the high
whole-ground camera on top, the broadcast camera below. 24 fps, H.264.
    python tools/visual/calls3d_films.py OUTDIR [call ...]
Needs ffmpeg (imageio_ffmpeg's bundled binary is used when ffmpeg is not on PATH).
"""
import os, shutil, subprocess, sys


def ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def main():
    out = sys.argv[1]
    only = sys.argv[2:]
    for call in sorted(os.listdir(out)):
        d = os.path.join(out, call)
        if not os.path.isdir(d) or (only and call not in only):
            continue
        ins = []
        for arm in ("balanced_high", "call_high", "balanced_broadcast", "call_broadcast"):
            ins += ["-framerate", "24", "-i", os.path.join(d, arm, "f%03d.png")]
        film = os.path.join(out, f"{call}.mp4")
        subprocess.run([ffmpeg(), "-y", "-loglevel", "error", *ins, "-filter_complex",
                        "[0][1]hstack[top];[2][3]hstack[bot];[top][bot]vstack,format=yuv420p",
                        "-c:v", "libx264", "-crf", "20", "-preset", "medium", film], check=True)
        print(film)


if __name__ == "__main__":
    main()
