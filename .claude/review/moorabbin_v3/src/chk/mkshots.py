import json,math,numpy as np
exec(open('chk/ringover.py').read().split("cam=np.array")[0])
D='C:/Users/DANTE/AppData/Local/Temp/claude/9f4017b9c485d8cb/fb8d066d-4ddf-4085-adc6-c6288b802d1c/scratchpad/moor/proof/'
R=math.radians
def P(deg,d,z=0):return [round(float(v),2) for v in pt(R(deg),d,z)]
def dd(deg):return d_out(R(deg))
S=[]
def add(n,eye,at,lens=30):S.append({'eye':eye,'at':at,'lens':lens,'out':D+n+'.png'})
# terrace steps: from the boundary looking up the bank, three sectors (east, north, SE)
for n,deg in (('e',10),('n',70),('se',-60)):
    add('close_steps_'+n,P(deg-6,-6,2.2),P(deg,dd(deg)*0.55,1.6),35)
    add('zoom_steps_'+n,P(deg-1.5,dd(deg)*0.3,1.2+0.3),P(deg,dd(deg)*0.5,1.8),40)
add('zoom_stand_pocket_steps',P(-30+0,-4,1.8),P(-30,6,0.6),35) if False else None
# stand pocket (stand runs 139.5 -> 243.7 wrapped, i.e. 139.5..180 and -180..-116)
add('zoom_stand_pocket_steps',P(-160,-5,2.0),P(-163,3,0.5),35)
# crest walkway + chain fence
for deg in (20,-40):add('zoom_crest_fence_%d'%(deg%360),P(deg-3,dd(deg)-1.0,ZT+1.7),P(deg+3,dd(deg),ZT+0.8),35)
add('zoom_crest_fence_back',P(25,dd(25)+5,1.8),P(22,dd(22),ZT+0.6),35)
# fence meets club buildings
add('zoom_crest_fence_meets_building',P(90,dd(90)-4,ZT+2.5),P(97,dd(97),ZT+0.6),30)
add('zoom_crest_fence_between_buildings',P(103,dd(103)-8,ZT+6),P(106,dd(106),ZT+0.6),30)
add('zoom_crest_fence_meets_stand_south',P(-110,dd(-110)-3,ZT+2.5),P(-116.3,dd(-116.3),ZT+0.6),30)
# scoreboard front and back
S_=O['score'];c=np.mean(np.array(S_['ends']),0)
add('close_scoreboard_front',[c[0]-28,c[1]+6,6],[c[0],c[1],8],35)
add('close_scoreboard_back',[c[0]+16,c[1]-8,5],[c[0],c[1],8],35)
add('zoom_scoreboard_post',[c[0]+6,c[1]+9,3],[c[0]-0.5,c[1]+4.6,3],35)
# billboards
add('close_billboards_se',P(-85,-8,4),P(-90,dd(-90),5.5),30)
add('close_billboards_se_back',P(-100,dd(-100)+10,4),P(-95,dd(-95),5.5),30)
add('zoom_billboard_joint',P(-94,dd(-94)-3,5.5),P(-92,dd(-92)+0.6,5.5),35)
add('zoom_billboard_meets_stand',P(-112,dd(-112)-6,6),P(-116,dd(-116),5),30)
add('close_billboard_n',P(79,-6,4),P(79,dd(79),5.5),30)
# bank meets stand ends and Huggins
add('zoom_bank_meets_stand_south',P(-108,-4,4),P(-116.3,12,1.5),30)
add('zoom_bank_meets_stand_north',P(132,-4,4),P(139.5,12,1.5),30)
add('zoom_bank_meets_huggins',P(95,-3,5),P(103,15,2),30)
json.dump([s for s in S if s],open('shots_new.json','w'),indent=0)
print(len(S))
