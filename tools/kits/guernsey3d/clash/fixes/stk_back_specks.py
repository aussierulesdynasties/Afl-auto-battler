"""St Kilda clash, back: flecks of the armhole piping (black and white) left inside the red at the shoulders.
    python stk_back_specks.py   (work folder, after trace_clash.py)"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from despeckle import despeckle

print('STK back flecks', despeckle('STK', 'back', 30000, ['#37313A', '#E8E7EF'], None), 'px')
