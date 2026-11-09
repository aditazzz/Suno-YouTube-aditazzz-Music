"""Short A's 1.5 s end card as a run.py module: frame n >= 1692 is u = (n - 1692) / 30 seconds into the card."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import short_a

def render_frame(t, W, H):
    n = int(round(t * 30)); return short_a.end_card((n - 1692) / 30, W, H, n)
