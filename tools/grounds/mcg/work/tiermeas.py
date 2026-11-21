# ID render with one material per seat tier per 30-degree sector (m_t1_000 ...), camera-matched to GE views.
# blender -b --python work/tiermeas.py -- <abs out> views...
import sys, os
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(SP, 'model'))
import mb, build
_mat = mb.mat
def mat2(name):
    if name.startswith('m_'):
        if name in mb.MATS: return mb.MATS[name]
        import bpy; m = bpy.data.materials.new(name); mb.MATS[name] = m; return m
    return _mat(name)
mb.mat = mat2
import importlib
for k in ('t1', 't2', 't3'):
    build.D['mats'][k] = [[s, s + 30, 'm_%s_%03d' % (k, s)] for s in range(0, 360, 30)]
build.build_all = (lambda f: (lambda: f()))(build.build_all)
os.environ['FLAT'] = '2'
sys.argv = [sys.argv[0], '--'] + sys.argv[sys.argv.index('--') + 1:]
exec(open(os.path.join(SP, 'model', 'rv.py')).read().replace('import build, earthcam', 'import earthcam'), {'__file__': os.path.join(SP, 'model', 'rv.py'), 'build': build, '__name__': '__main__'})
