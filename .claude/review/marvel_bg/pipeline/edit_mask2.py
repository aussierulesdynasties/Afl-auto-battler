s = open('mk_pave_mask.py').read()
s = s.replace("inside=np.asarray(im)>0", "inside=np.asarray(im)>0\n# south edge = the Yarra's north bank (traced on pave_check.jpg, 3 m/px): nothing south of the river\nRIV=[(-1500,-300),(-600,-420),(0,-600),(420,-780),(1500,-780)]\ncut=Image.new('L',(n,n),0); ImageDraw.Draw(cut).polygon([((x+NE)/px,(NE-y)/px) for x,y in RIV+[(1500,-1500),(-1500,-1500)]],fill=255)\ninside&=np.asarray(cut)==0")
s = s.replace("<=6\n", "<=20\n")
open('mk_pave_mask.py', 'w').write(s); print('ok')
