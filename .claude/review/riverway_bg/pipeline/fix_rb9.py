p='scene.py'; s=open(p,newline='').read()
a="""            for ii, jj in edge:
                if 0 <= jj < q.shape[0] and 0 <= ii < q.shape[1]: q[jj, ii] = False"""
b="""            part = (ins[:-1, :-1] | ins[1:, :-1] | ins[:-1, 1:] | ins[1:, 1:]) & ~q   # cells the outline only grazes at a corner
            edge |= set(zip(*np.nonzero(part.T)))
            for ii, jj in edge:
                if 0 <= jj < q.shape[0] and 0 <= ii < q.shape[1]: q[jj, ii] = False"""
assert a in s; open(p,'w',newline='').write(s.replace(a,b)); print('ok')
