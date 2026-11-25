"""Geelong clash, back: flecks of the white armhole binding left inside the navy (one by the number).
    python gee_back_specks.py   (work folder, after trace_clash.py)"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from despeckle import despeckle

print('GEE back flecks', despeckle('GEE', 'back', 20000, ['#DBE0EE'], None), 'px')
