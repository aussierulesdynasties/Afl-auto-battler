# polo field (mown lawn) and sand stockpile north of the north oval, traced on soccer.png (top px = 440+X/2, 60+Y/2)
import json
S='spec/peoplefirst.json'; s=json.load(open(S))
def g(X,Y): return [round(440+X/2-700,1), round(700-(60+Y/2),1)]
field=[g(160,90),g(350,120),g(305,375),g(115,335)]
sand=[g(335,230),g(370,220),g(380,260),g(360,300),g(355,330),g(325,325)]
s['paint_poly']=[p for p in s['paint_poly'] if p[0] not in ('field_lawn','sand')]
s['paint_poly']+=[['lawn_island',field],['sand',sand]]
json.dump(s,open(S,'w'),indent=2); print(field, sand)
