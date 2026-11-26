"""The near scene's tiling textures, drawn here (no photos): greyscale detail that each building's own
colour tints (GroundModels' backdrop shader multiplies them). Alpha 0 everywhere (no glass in them).

- brick.png: stretcher bond, 230 x 76 mm bricks, 10 mm joints; one tile 1.2 m x 1.2 m at 256 px.
- render.png: painted block or render, 390 x 190 mm block joints barely showing; 1.2 m.
- corrugated.png: corrugated iron, a rib every 76 mm across the sheet (u) and sheet laps every 0.76 m;
  1.52 m tile; the ribs run down the slope (v).
"""
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
S = 256


def save(a, name):
    a = np.clip(a, 0, 255).astype(np.uint8)
    rgba = np.dstack([a, a, a, np.zeros_like(a)])
    Image.fromarray(rgba, "RGBA").save(os.path.join(HERE, "tex", name))


def brick():
    rng = np.random.default_rng(1)
    m = 1.2 / S                     # metres a pixel
    y, x = np.mgrid[0:S, 0:S] * m
    course = (y // 0.086).astype(int)
    off = (course % 2) * 0.12
    u = (x + off) % 0.24
    v = y % 0.086
    joint = (u < 0.01) | (v < 0.01)
    bid = ((x + off) // 0.24).astype(int) * 131 + course * 7
    tone = 1.0 + 0.07 * np.sin(bid * 12.9898) * np.cos(bid * 4.1)
    a = np.where(joint, 214.0, 236.0 * tone)
    a += rng.normal(0, 4, a.shape)
    save(a, "brick.png")


def render():
    rng = np.random.default_rng(2)
    m = 1.2 / S
    y, x = np.mgrid[0:S, 0:S] * m
    course = (y // 0.2).astype(int)
    off = (course % 2) * 0.2
    joint = (((x + off) % 0.4) < 0.006) | ((y % 0.2) < 0.006)
    a = np.where(joint, 236.0, 246.0) + rng.normal(0, 2.5, (S, S))
    save(a, "render.png")


def corrugated():
    rng = np.random.default_rng(3)
    m = 1.52 / S
    y, x = np.mgrid[0:S, 0:S] * m
    ph = (x % 0.076) / 0.076 * 2 * np.pi
    a = 228 + 18 * np.cos(ph)                     # a sine profile catching the light
    a = np.where((x % 0.76) < 0.012, a - 22, a)    # sheet laps
    a += rng.normal(0, 2.0, (S, S))
    save(a, "corrugated.png")


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "tex"), exist_ok=True)
    brick()
    render()
    corrugated()
    print("textures written")
