# Fix 2/3 (2026-11-18): shades matched to the photo by the measured photo/render ratio per channel.
import numpy as np
from PIL import Image
exec(open('seattex.py',encoding='utf-8').read().split('s=np.asarray')[0])
COL=['rose','rose','rose','Y','G','R','B','Y','R','sage','Y','B','B','B','B','Y','R','R','R','B','G','Y','M','M','G','M','M','Y','G','B','R','Y','sage','L','rose','rose','rose','K','W','P','L','K','rose','sage','B','Y','R','G']
# right-end blocks: median photo colour vs median render colour (d 1.5-17.5 of each block)
PHO={33:(135,124,136),34:(214,127,128),35:(199,115,118),36:(193,127,129),37:(185,156,141),38:(182,174,163),39:(197,145,145),40:(187,169,171),41:(220,191,157),42:(203,119,119),43:(134,151,129),44:(113,104,111),45:(195,156,106),46:(162,59,65),47:(85,95,82)}
REN={33:(94,92,116),34:(129,56,62),35:(131,61,66),36:(147,73,79),37:(175,151,119),38:(170,171,168),39:(174,132,134),40:(138,135,160),41:(174,161,128),42:(158,84,91),43:(89,114,95),44:(54,67,119),45:(187,145,72),46:(150,48,53),47:(44,75,52)}
s=np.asarray(Image.open('tex2/seat.png')).astype(float)/238.0
for k in PHO:
    c=np.clip(np.array(PAL[COL[k]],float)*np.array(PHO[k])/np.array(REN[k]),0,255)
    Image.fromarray(np.clip(s*c,0,255).astype(np.uint8)).save(f'tex2/seat_bk{k}.png');print(k,COL[k],np.round(c).astype(int))
def tint(src,dst,f):
    a=np.asarray(Image.open(f'tex2/{src}.png').convert('RGB')).astype(float)*np.array(f)
    Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(f'tex2/{dst}.png')
# pave is scaled in place, so rebuild its base first (keeps this script safe to re-run)
import subprocess,sys;subprocess.run([sys.executable,'mktex3.py'],check=True,capture_output=True)
tint('pave','pave_n',(0.18,0.125,0.125))      # near side under the members' opposite stand: photo (30,24,25)
tint('pave','pave_nl',(0.56,0.38,0.27))     # near side either end: photo (56,38,36) and (83,77,53)
for m in('fvoid','fcol','fslab','underside','facade','aislec'):tint(m,m+'_n',(0.30,0.18,0.19))
tint('pave','pave',(0.62,0.50,0.45))        # elsewhere: photo (90,73,60) vs render 115   # near undercroft: photo (22,17,18) vs render (44,45,45)
# gap terrace rows: photo (135..148,113..122,113..121) vs render (80..94,77..85,79..85)
# treads and risers scaled apart so the row contrast matches too (photo 10-90% spread 50..177)
tint('bowllight','bowlgap',(1.10,1.08,1.07));tint('seat_grey','seat_gapg',(2.19,2.08,2.08))
# near paving blend steps: b0 = the lighter ends (pave_nl), b4 = the darker middle (pave_n)
_a=np.asarray(Image.open('tex2/pave_nl.png').convert('RGB')).astype(float);_b=np.asarray(Image.open('tex2/pave_n.png').convert('RGB')).astype(float)
for _k in range(5):Image.fromarray(np.clip(_a+(_b-_a)*_k/4,0,255).astype(np.uint8)).save(f'tex2/pave_b{_k}.png')
