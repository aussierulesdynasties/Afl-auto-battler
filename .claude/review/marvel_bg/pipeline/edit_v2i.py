"""Orbit crops: thin white lines across the rail yard = footpaths painted in PAL path (184,178,164). Tone to worn concrete."""
import json
J = json.load(open('spec/marvel.json')); J['palette']['path'] = [150, 146, 136]
json.dump(J, open('spec/marvel.json', 'w'), indent=1); print('ok')
