"""Close stills: facades varied; at orbit range pale roofs dominate. Darker, more varied flat roofs (membrane, gravel, charcoal)."""
import json
J = json.load(open('spec/marvel.json'))
J['palette']['roofs_flat'] = [[205, 208, 204], [70, 72, 74], [128, 122, 112], [96, 104, 98], [56, 58, 60], [150, 140, 122], [92, 100, 110]]
json.dump(J, open('spec/marvel.json', 'w'), indent=1); print('ok')
