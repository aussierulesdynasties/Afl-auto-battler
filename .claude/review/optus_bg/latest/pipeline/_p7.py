import json
p='spec/optus.json'; s=json.load(open(p))
s['forecourt_tones']=[[186,140,124],[210,192,168],[170,160,148]]
json.dump(s,open(p,'w'),indent=1)
