"""Helpers shared by the Shorts D-G modules (short_d/e/f/g*.py). Shorts-only: nothing here is used by the 16:9 film.

private(name, file): loads a section module as a SEPARATE module object (its own globals), so a Short can patch its
layout constants and functions for 9:16 without touching the module the 16:9 film imports. The published film's
modules and their imports are unchanged; a 16:9 render in the same process still gets the original module.
"""
import os, sys, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__)); SONG = os.path.dirname(HERE); ROOT = os.path.dirname(os.path.dirname(SONG))
for p in (ROOT, HERE, SONG):
    if p not in sys.path: sys.path.insert(0, p)

SAFE_R, SAFE_B = 0.88, 0.78          # Shorts safe zone: x <= 0.88 W, y <= 0.78 H for anything that's read


def private(alias, filename):
    """A private copy of sections/<filename> under the module name `alias` (one per process)."""
    if alias in sys.modules: return sys.modules[alias]
    spec = importlib.util.spec_from_file_location(alias, os.path.join(HERE, filename))
    m = importlib.util.module_from_spec(spec); sys.modules[alias] = m
    spec.loader.exec_module(m)
    return m


def end_card(u, W, H, fi=0):
    """The shared Shorts end card (Short A's, read-only import)."""
    import short_a
    return short_a.end_card(u, W, H, fi)
