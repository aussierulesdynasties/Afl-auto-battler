"""Self-check fixes after first v2 orbit: track beds read as pale ribbons -> ballast-coloured bed with dark rail pairs;
station roof humps too steep/white; platforms too white; glass washed out by sky specular."""
def sub(path, pairs):
    s = open(path, newline='').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, a[:60]); s = s.replace(a, b)
    open(path, 'w', newline='').write(s)
sub('mk_facades.py', [
 ("A[:] = (np.array([84, 76, 68]) * (0.8 + 0.4 * n[..., None]))", "A[:] = (np.array([92, 84, 76]) * (0.82 + 0.36 * n[..., None]))"),
 ("np.array([150, 146, 138]) * (0.92", "np.array([108, 102, 94]) * (0.92"),
 ("A[:, x - 4:x + 4] = (92, 70, 56); A[:, x - 1:x + 2] = (196, 196, 194)", "A[:, x - 7:x + 7] = (34, 32, 30); A[:, x - 1:x + 1] = (120, 118, 116)")])
sub('facade_mix.py', [
 ("z0 + 15.0 + 6.5 * np.abs(np.sin(np.pi * (UU - u0) / HUMP_U) * np.sin(np.pi * (VV - v0) / HUMP_V)) ** 0.8",
  "z0 + 15.0 + 3.5 * (0.5 - 0.5 * np.cos(2 * np.pi * (UU - u0) / HUMP_U)) * (0.5 - 0.5 * np.cos(2 * np.pi * (VV - v0) / HUMP_V))"),
 ("sh = 0.86 + 0.14 * (ZZ[r_, c_] - z0 - 15.0) / 6.5; C_.extend([lin((226, 228, 224)) * sh] * 4)",
  "sh = 0.9 + 0.1 * (ZZ[r_, c_] - z0 - 15.0) / 3.5; C_.extend([lin((200, 204, 202)) * sh] * 4)"),
 ("zc = z0 + 21.5;", "zc = z0 + 18.3;"), ("rr = 2.6", "rr = 1.8"), ("zc + 3.2))", "zc + 2.0))"),
 ("C_.extend([lin((178, 174, 166))] * kk)", "C_.extend([lin((138, 136, 130))] * kk)")])
f = open('facade_mix.py', newline='').read()
f += ("\nfor _m in bpy.data.materials:   # glass: less sky specular so each tint reads\n"
      "    if _m.name.startswith('facade_') and _m.node_tree and 'Principled BSDF' in _m.node_tree.nodes:\n"
      "        _m.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.25\n")
open('facade_mix.py', 'w', newline='').write(f)
sub('scene.py', [("steel_c = lin((150, 150, 152))", "steel_c = lin((48, 46, 44))")])
print('ok')
