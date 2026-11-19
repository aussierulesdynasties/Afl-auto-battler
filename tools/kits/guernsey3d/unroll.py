# Geodesic unroll of the torso: s = distance round the body from the front (or back) centreline,
# h = distance up the body from a waist line. Usage: from unroll import unroll
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

def unroll(P, tris, y_ref=1.10):
    key = np.round(P * 1e5).astype(np.int64)
    _, wid = np.unique(key, axis=0, return_inverse=True); wid = wid.ravel()
    n = wid.max() + 1
    Q = np.zeros((n, 3)); Q[wid] = P
    T = wid[tris]
    E = np.r_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]
    E = np.unique(np.sort(E, 1), axis=0)
    w = np.linalg.norm(Q[E[:, 0]] - Q[E[:, 1]], axis=1)
    G = coo_matrix((np.r_[w, w], (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()
    torso = (Q[:, 1] > 0.95) & (Q[:, 1] < 1.62)
    zc = Q[torso & (np.abs(Q[:, 0]) < 0.01), 2].mean()
    mid = torso & (np.abs(Q[:, 0]) < 0.006)
    front = np.where(mid & (Q[:, 2] > zc))[0]
    back = np.where(mid & (Q[:, 2] < zc))[0]
    waist = np.where((np.abs(Q[:, 1] - y_ref) < 0.006) & (np.abs(Q[:, 0]) < 0.25))[0]
    sf = dijkstra(G, indices=front, min_only=True)
    sb = dijkstra(G, indices=back, min_only=True)
    h = dijkstra(G, indices=waist, min_only=True) * np.sign(Q[:, 1] - y_ref)
    u = sf / np.maximum(sf + sb, 1e-9)
    ax = np.abs(Q[:, 0])
    seam = np.where((np.abs(u - 0.5) < 0.012) & (Q[:, 1] > 1.50) & (ax > 0.075) & (ax < 0.21))[0]
    ds = dijkstra(G, indices=seam, min_only=True)
    return Q, wid, sf, sb, h, zc, ds
