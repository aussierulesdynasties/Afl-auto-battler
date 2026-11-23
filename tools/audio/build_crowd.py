#!/usr/bin/env python3
"""Build the match crowd and the ground siren in assets/audio/crowd/ (FL-004).

    python tools/audio/build_crowd.py [out_dir]

Needs numpy, scipy and pyloudnorm, and ffmpeg on the PATH (to decode the takes).

The siren is synthesised. Every AFL ground we measured (MCG 2021 and 2022,
Optus, the 2023 and 2026 Grand Finals, and a country ground) sounds the same
siren: two notes at once, about 329 Hz and 441 Hz (E4 and A4), each with its
own row of overtones. The two rows meet near 1317 and 1323 Hz, and those two
partials beat about six times a second, which is the siren's waver. It starts
in about 40 ms (no wind-up), holds, and stops. The tables below are the
average overtone levels of the three MCG recordings. The recordings were only
measured; none of them is in the game or in this repository.

The crowd is five takes made with ElevenLabs Sound Effects on the director's
own account (tools/audio/crowd_sources/, prompts in its README). Here they
are trimmed, faded and set to one loudness scale, so CrowdSound.gd's levels
are the only mix.

Writes 44100 Hz mono 16-bit WAVs:
  crowd_bed.wav     30 s seamless loop: the crowd during general play
  crowd_goal.wav    ~5.5 s: the roar for a goal
  crowd_behind.wav  ~4 s: "ohhh" into a groan, for a behind
  crowd_ball.wav    ~3.5 s: "BALL!" at a holding-the-ball tackle
  crowd_siren.wav   ~7.5 s: the siren in the stadium, and the crowd rising under it
"""
import os
import subprocess
import sys

import numpy as np
import pyloudnorm as pyln
from scipy import signal
from scipy.io import wavfile

RATE = 44100
SEED = 2026
HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.join(HERE, "crowd_sources")

# The siren (measured: see the docstring).
SIREN_E = 329.4
SIREN_A = 441.05
# Overtone n (1, 2, ...) of each note, in dB under the loudest partial.
SIREN_E_DB = [-12, -8.3, -5, -5.5, -12, -21, -25, -23, -31, -28, -40, -41]
SIREN_A_DB = [-7.3, -3.7, 0, -8.3, -23, -20, -29, -34, -43, -35]
SIREN_HOLD = 4.0          # s: the timekeeper's blast at the 2026 Grand Final was about four seconds
SIREN_ATTACK = 0.04       # s: full volume in 40 ms
SIREN_RELEASE = 0.12      # s
STADIUM_RT60 = 2.2        # s: an open bowl of 90,000 seats
FAR_STAND = 0.47          # s: the echo back off the far side of the ground (about 160 m)

# Loudness of each file (LUFS: integrated for the bed, the loudest 3 s for the
# rest). CrowdSound.gd adds its own levels on top of these; together a home
# goal roars about 14 dB over the murmur, the siren sits about 12 dB over it
# (as it did from the stands at the 2026 Grand Final), a behind about 9 and a
# "BALL!" about 8.
LOUD_BED = -24.0
LOUD_GOAL = -18.0
LOUD_BEHIND = -20.0
LOUD_BALL = -21.0
LOUD_SIREN = -20.0
PEAK_CEIL = 10 ** (-3 / 20)   # CrowdSound lifts a roar up to +4.5 dB: keep that headroom


def decode(name: str) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(SOURCES, name),
            "-ac", "1", "-ar", str(RATE), "-f", "s16le", "-"], check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0


def fade(x: np.ndarray, fin: float, fout: float) -> np.ndarray:
    x = x.copy()
    a, b = int(fin * RATE), int(fout * RATE)
    if a > 0:
        x[:a] *= np.linspace(0.0, 1.0, a) ** 2
    if b > 0:
        x[-b:] *= np.linspace(1.0, 0.0, b) ** 2
    return x


def max_short_term(x: np.ndarray) -> float:
    meter = pyln.Meter(RATE)
    w, hop = 3 * RATE, RATE // 4
    if len(x) <= w:
        return meter.integrated_loudness(np.pad(x, (0, w - len(x) + 1)))
    return max(meter.integrated_loudness(x[i:i + w]) for i in range(0, len(x) - w, hop))


def to_loudness(x: np.ndarray, target: float, integrated=False) -> np.ndarray:
    now = pyln.Meter(RATE).integrated_loudness(x) if integrated else max_short_term(x)
    y = x * 10 ** ((target - now) / 20)
    peak = np.abs(y).max()
    if peak > PEAK_CEIL:
        raise SystemExit("loudness %.1f would clip (peak %.2f): lower the target" % (target, peak))
    return y


def slow_wobble(rng, n: int, rate_hz: float, depth_db: float) -> np.ndarray:
    """A smooth random gain around 1 (the air moving the sound about)."""
    k = int(n / RATE * rate_hz) + 4
    pts = rng.normal(0.0, 1.0, k)
    v = signal.resample(pts, n)
    v /= max(1e-9, np.abs(v).max())
    return 10 ** (depth_db * v / 20)


def siren_dry(rng) -> np.ndarray:
    n = int((SIREN_HOLD + SIREN_RELEASE + 0.05) * RATE)
    t = np.arange(n) / RATE
    env = np.clip(t / SIREN_ATTACK, 0.0, 1.0) ** 1.5
    env *= np.where(t < SIREN_HOLD, 1.0, np.exp(-(t - SIREN_HOLD) / (SIREN_RELEASE / 4)))
    # The supply sags a little as it is cut.
    sag = np.where(t < SIREN_HOLD, 1.0, 1.0 - 0.03 * (1.0 - np.exp(-(t - SIREN_HOLD) / 0.08)))
    y = np.zeros(n)
    for base, table in ((SIREN_E, SIREN_E_DB), (SIREN_A, SIREN_A_DB)):
        phase = 2 * np.pi * np.cumsum(base * sag) / RATE
        for k, level in enumerate(table, 1):
            y += 10 ** (level / 20) * slow_wobble(rng, n, 6.0, 1.2) * np.sin(k * phase + rng.uniform(0, 2 * np.pi))
    y /= np.abs(y).max()
    # One horn driver for both notes: driven hard, it adds the faint
    # in-between partials (every ~112 Hz) the recordings have.
    y = np.tanh(2.2 * y) / np.tanh(2.2)
    b, a = signal.butter(2, 220, btype="high", fs=RATE)
    return signal.lfilter(b, a, y) * env


def stadium_ir(rng) -> np.ndarray:
    n = int((STADIUM_RT60 * 1.4) * RATE)
    t = np.arange(n) / RATE
    tail = np.zeros(n)
    # Seats and air take the top off first: the higher bands die sooner.
    for lo, hi, rt in ((0, 1000, 1.0), (1000, 3000, 0.75), (3000, 9000, 0.5)):
        if lo == 0:
            b, a = signal.butter(2, hi, btype="low", fs=RATE)
        else:
            b, a = signal.butter(2, [lo, hi], btype="band", fs=RATE)
        tail += signal.lfilter(b, a, rng.normal(0, 1, n)) * np.exp(-6.91 * t / (STADIUM_RT60 * rt))
    ir = tail * np.clip((t - 0.035) / 0.08, 0, 1) * 0.06
    ir[0] = 1.0
    # The nearer stands, the roof over you, and the far side of the ground.
    for delay, gain in ((0.018, 0.35), (0.041, 0.25), (0.073, 0.2), (0.11, 0.15), (FAR_STAND, 0.22), (2 * FAR_STAND, 0.09)):
        i = int(delay * RATE)
        w = signal.windows.hann(int(0.012 * RATE))
        ir[i:i + len(w)] += gain * w * rng.normal(0, 0.6, len(w))
    return ir


def siren_in_stadium(rng) -> np.ndarray:
    dry = siren_dry(rng)
    ir = stadium_ir(rng)
    wet = signal.fftconvolve(dry, ir)
    wet /= np.abs(wet).max()
    d = np.concatenate([dry / np.abs(dry).max(), np.zeros(len(wet) - len(dry))])
    return 0.45 * d + 0.55 * wet


def build(out_dir: str) -> None:
    rng = np.random.default_rng(SEED)
    os.makedirs(out_dir, exist_ok=True)

    bed = decode("bed.mp3")          # generated as a seamless 30 s loop: left whole
    bed = to_loudness(bed, LOUD_BED, integrated=True)

    goal = fade(decode("goal.mp3")[: int(5.5 * RATE)], 0.0, 1.5)
    behind = fade(decode("behind.mp3")[: int(4.0 * RATE)], 0.0, 1.2)
    ball = fade(decode("ball.mp3")[: int(3.5 * RATE)], 0.0, 1.2)

    # The siren goes on the tick; the crowd comes up under it a moment later
    # (0.8 s at the 2026 Grand Final) and carries on after it stops.
    siren = siren_in_stadium(rng)
    swell = fade(decode("siren_swell.mp3")[: int(6.7 * RATE)], 0.6, 1.8)
    lag = int(0.8 * RATE)
    n = max(len(siren), lag + len(swell))
    mix = np.zeros(n)
    mix[: len(siren)] += siren
    swell_gain = 10 ** ((max_short_term(siren) - max_short_term(swell) - 4.0) / 20)   # crowd 4 dB under the siren
    mix[lag: lag + len(swell)] += swell * swell_gain
    mix = fade(mix[: int(7.5 * RATE)], 0.0, 1.0)

    files = {
        "crowd_bed.wav": bed,
        "crowd_goal.wav": to_loudness(goal, LOUD_GOAL),
        "crowd_behind.wav": to_loudness(behind, LOUD_BEHIND),
        "crowd_ball.wav": to_loudness(ball, LOUD_BALL),
        "crowd_siren.wav": to_loudness(mix, LOUD_SIREN),
    }
    for name, x in files.items():
        wavfile.write(os.path.join(out_dir, name), RATE, np.round(x * 32767).astype(np.int16))
        print("%-18s %5.1f s  peak %5.1f dBFS" % (name, len(x) / RATE, 20 * np.log10(np.abs(x).max())))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "assets", "audio", "crowd"))
