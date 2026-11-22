import json
g=json.load(open('spec/gmhba.json'))
C=[(-135.25,199.4,1.630),(-116.25,201.5,1.630),(-131.5,165.0,1.630),(-112.1,166.25,1.630),
   (-133.1,250.25,1.819),
   (-161.25,293.1,1.983),(-142.5,299.4,1.983),(-174.4,325.6,1.983),(-156.25,331.25,1.983)]
g['netball_courts']['courts']=[['netball',x,y,a,30.5,15.25] for x,y,a in C]
json.dump(g,open('spec/gmhba.json','w'),indent=1); print(len(C))
