#!/usr/bin/env python3
"""YouTube cover for Get Off War Thunder. Usage: python3 cover.py out.png [variant]"""
import sys, math
from PIL import Image, ImageDraw, ImageFilter
sys.argv_backup = sys.argv
sys.argv = ["x"]
import render as R
from render import *

W, H = 1920, 1080


def cover(variant=1):
    img = Image.new("RGB", (W, H), (16, 20, 16))
    d = ImageDraw.Draw(img)
    # subtle grid
    for x in range(0, W, 80):
        d.line((x, 0, x, H), fill=(24, 32, 26), width=1)
    for y in range(0, H, 80):
        d.line((0, y, W, y), fill=(24, 32, 26), width=1)
    # radial glow behind the action (warm)
    glow = Image.new("L", (W // 8, H // 8), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse((60, 30, 220, 150), fill=160)
    glow = glow.resize((W, H)).filter(ImageFilter.GaussianBlur(90))
    warm = Image.new("RGB", (W, H), (120, 50, 20))
    img = Image.composite(warm, img, glow)
    d = ImageDraw.Draw(img)
    # hazard stripes top and bottom
    hazard_band(d, 0, 46, c1=AMBER, c2=INK, step=70, offset=20)
    hazard_band(d, H - 46, H, c1=AMBER, c2=INK, step=70, offset=50)

    # door on the far right (behind Alex)
    draw_door(d, 1600, 100, 1880, 880)

    # tank bottom-left with BOOM
    draw_boom(d, 520, 790, 240, 0.55, txt="")
    draw_tank(d, 520, 1000, 1.7, (110, 125, 95), wobble=-10)
    # plane going down, top middle
    for i in range(1, 9):
        qx, qy = 1100 - i * 46, 110 - i * 10
        r = 10 + i * 3
        g = 90 + i * 10
        d.ellipse((qx - r, qy - r, qx + r, qy + r), fill=(g, g, g))
    draw_plane(d, 1100, 110, 0.8, (160, 170, 180), rot=-40)

    # Alex big, yelling
    draw_kid(d, 1380, 930, 520, JERSEY, 6, arm_up=True)
    d.ellipse((1358, 452, 1402, 494), fill=INK)
    d.ellipse((1366, 478, 1394, 492), fill=(220, 90, 90))
    draw_ball(d, 1170, 880, 56, rot=20)
    bubble(d, (1230, 250), "OWEN!!", 100, col=RED)

    # title block
    stamp(img, "GET OFF", font(F_STENCIL, 150), (520, 150), WHITE, rot=-2, stroke=14)
    stamp(img, "WAR THUNDER", fit_font(F_STENCIL, "WAR THUNDER", 920, 130), (560, 300), AMBER, rot=-2, stroke=14)
    # sub line
    fnt = font(F_HUD, 46)
    s = "a song by a 6-year-old about his big brother"
    w = fnt.getlength(s) + 50
    rrect(d, (90, 420 - 36, 90 + w, 420 + 36), 12, fill=INK, outline=HUD, width=4)
    text(d, (90 + w / 2, 420), s, fnt, HUD)

    # badge: animated by Claude Fable 5.1
    s2 = "ANIMATED BY CLAUDE FABLE 5.1"
    bf = fit_font(F_STENCIL, s2, 900, 58)
    w2 = bf.getlength(s2) + 70
    bx, by = 720, 990
    rrect(d, (bx, by - 46, bx + w2, by + 46), 16, fill=RED, outline=WHITE, width=6)
    text(d, (bx + w2 / 2, by), s2, bf, WHITE)
    return img


if __name__ == "__main__":
    out = sys.argv_backup[1]
    v = int(sys.argv_backup[2]) if len(sys.argv_backup) > 2 else 1
    im = cover(v)
    im.save(out.replace(".png", "_1080.png"))
    im.resize((1280, 720), Image.LANCZOS).save(out)
