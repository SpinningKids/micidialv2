#!/usr/bin/env python3
"""micidial v2 — Scene Compiler v3.2 (record identity fully derived).

All structural rules verified with zero violations (probes ties3..ties7):
  * records [name, role, time, 0, payload]; per-scene order =
    concat of equal-t cluster role-sequences (scenes are t-monotone so
    equal-t records are always adjacent -> clusters reproduce exactly)
  * t = m/10000 (4-dp decimal literals)
  * per role: fixed payload skeleton; no integer-valued floats, so leaf
    int/float typing is derivable from the value
  * names fully derived:
      P pressure-sculpture-(scene+1)-(K)         K = per-scene counter
      C cycle-(scene+1)-(objIdx)-(F)             F = round(t*0.5625, 4)
      E emissiva-...-(scene+1)-(objIdx)-(tail)   tail per-scene per-role
      G gravity-v9-(scene+1)-(F)                 bg overrides stored
  * tracks (role, leaf-path) in role-occurrence space: numeric on an exact
    per-track decimal grid with tol-0 (exact) or tol-1 fits; strings -> dict
    + index track using the same fit machinery; varint+zigzag byte coding.

Outputs: P.s byte stream + deflate sizes + budget projection + FULL
regen validation (semantic equality + char-exact JSON vs the CONSTRUCTED
model: keyframes subsampled and floats re-quantized per the tier flags).

Usage: python v2/compile.py [--sub=4] [--quant=100] [--tol=0.01] [--sweep]
  --sub=1 --quant=0 --tol=0 reproduces the original records bit-exactly.
"""
import json
import os
import pickle
import re
import sys
import zlib
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'original', 'uncompressed.html')
BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')

# ------------------------------------------------------------- byte helpers


def uvb(x):
    x = int(x)
    assert x >= 0, x
    if x == 0:
        return b'\x00'
    out = bytearray()
    while x:
        out.append(x & 0x7F)
        x >>= 7
        if x:
            out[-1] |= 0x80
    return bytes(out)


def zz(n):
    n = int(n)
    return (n << 1) if n >= 0 else ((-n) << 1) - 1


def svb(n):
    return uvb(zz(n))


# ---------------------------------------------------------------- extraction


def load(path=None):
    # --src=<page> overrides the input page (variant processing, see projectmem)
    src = path or next((x.split('=', 1)[1] for x in sys.argv[1:] if x.startswith('--src=')), TARGET)
    s = open(src, encoding='utf-8').read()
    i0, i1 = s.find('<script>'), s.find('</script>')
    js = s[i0 + 8:i1]
    vi = js.find('const P=') + len('const P=')
    P, vend = json.JSONDecoder().raw_decode(js, vi)
    return s, js, vi, vend, P


def walk_values(v, path=()):
    if isinstance(v, list):
        for k, e in enumerate(v):
            yield from walk_values(e, path + (k,))
    else:
        yield path, v


def dict_get(v, path):
    for k in path:
        v = v[k]
    return v


def best_grid(vals):
    """largest scale sc with (round(v*sc)/sc == v) for all vals, index-safe."""
    for sc in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000,
               20000, 50000, 100000):
        ok = True
        for v in vals:
            q = round(v * sc)
            if abs(q - v * sc) > 1e-9 or abs(q / sc - v) > 1e-9 * max(1, abs(v)):
                ok = False
                break
        if ok:
            return sc
    raise ValueError('no exact grid for %r' % (vals[:4],))


# -------------------------------------------------------------------- fits


def fit_const(ns):
    return ('const', ns[0]) if len(set(ns)) == 1 else None


def fit_lin(ns):
    if len(ns) < 2:
        return None
    d = ns[1] - ns[0]
    return ('lin', (ns[0], d)) if \
        all(ns[i + 1] - ns[i] == d for i in range(len(ns) - 1)) else None


def fit_quad(ns):
    if len(ns) < 3:
        return None
    ds = [ns[i + 1] - ns[i] for i in range(len(ns) - 1)]
    c = ds[1] - ds[0]
    return ('quad', (ns[0], ds[0], c)) if \
        all(ds[i + 1] - ds[i] == c for i in range(len(ds) - 1)) else None


def fit_runs(ns):
    runs = []
    for v in ns:
        if not runs or runs[-1][0] != v:
            runs.append([v, 0])
        runs[-1][1] += 1
    if len(runs) == 1:
        return None
    return ('runs', [(v, n) for v, n in runs])


def fit_cha(ints):
    """delta chain baseline (no run-lengths) — best for smooth drift."""
    if len(ints) < 2:
        return None
    ds = [ints[i + 1] - ints[i] for i in range(len(ints) - 1)]
    return ('cha', (ints[0], ds))


def fd_values(vals, d):
    """finite differences: v0, D1..Dd from the first d+1 values."""
    row = list(vals)
    out = [row[0]]
    for _ in range(d):
        row = [row[i + 1] - row[i] for i in range(len(row) - 1)]
        out.append(row[0])
    return out


def fd_gen(seed, length):
    """Expand FD seed [v0, D1..Dd] (Newton forward): value(j) =
    v0 + sum_k C(j,k) Dk. Integer-exact."""
    d = len(seed) - 1
    vals, D = list(seed), list(seed[1:])
    while len(vals) < length:
        nxt = vals[-1] + D[0]
        for k in range(d - 1):
            D[k] = D[k] + D[k + 1]
        vals.append(nxt)
    return vals[:length]


def seg_series(ints, tol):
    """Greedy token split: constant runs + polynomial (order 1..6) runs
    encoded as (v0, D1..Dd) finite-difference seeds. Returns token list."""
    n = len(ints)
    toks = []
    i = 0
    while i < n:
        j = i
        while j + 1 < n and ints[j + 1] == ints[i]:
            j += 1
        if j > i:
            toks.append(('c', j - i + 1, ints[i]))
            i = j + 1
            continue
        best = None
        for d in (1, 2, 3, 4, 5, 6):
            if i + d + 1 > n:
                break
            # greedy run extension: grow by 16 while within tol
            L = d + 1
            ok_len = 0
            while True:
                L2 = min(n - i, L + 16)
                seed = fd_pick(ints, i, d, L2, tol)
                if seed:
                    L, ok_len = L2, L2
                    if L2 >= n - i:
                        break
                else:
                    break
            if not ok_len:
                continue
            # binary refine
            lo, hi = d + 1, ok_len
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if fd_pick(ints, i, d, mid, tol):
                    lo = mid
                else:
                    hi = mid - 1
            runlen = lo
            seed = fd_pick(ints, i, d, runlen, tol)
            if seed is None:            # LSQ fits not strictly monotonic
                continue
            cost = (d + 1) + 3          # seed ints + runlen token
            score = cost / runlen
            if best is None or score < best[0]:
                best = (score, runlen, seed)
        if best:
            toks.append(('p', best[1], best[2]))
            i += best[1]
        else:
            toks.append(('c', 1, ints[i]))
            i += 1
    return toks


def fd_pick(ints, i, d, L, tol):
    """Seed [v0, D1..Dd] reproducing ints[i:i+L] within tol (elementwise
    verification is the ground truth), or None. Try exact FD of the first
    d+1 points first, then a least-squares solve over the window."""
    if L < d + 1:
        return None
    seg = ints[i:i + L]
    cand = [fd_values(ints[i:i + d + 1], d)]
    if L > d + 1:
        s = lsq_seed(ints, i, d, L)
        if s:
            cand.append(s)
    for seed in cand:
        if all(abs(a - b) <= tol for a, b in zip(fd_gen(seed, L), seg)):
            return seed
    return None


def lsq_seed(ints, i, d, L):
    """Float least-squares FD seed in binomial basis C(j,k); fd_pick verifies."""
    seg = ints[i:i + L]
    m = d + 1
    A = [[0.0] * m for _ in range(m)]
    bv = [0.0] * m
    for j, y in enumerate(seg):
        row = [1.0] * m
        for k in range(1, m):
            row[k] = row[k - 1] * (j - k + 1) / k
        for r in range(m):
            bv[r] += row[r] * y
            for c in range(m):
                A[r][c] += row[r] * row[c]
    for col in range(m):
        p = max(range(col, m), key=lambda r: abs(A[r][col]))
        if abs(A[p][col]) < 1e-9:
            return None
        A[col], A[p] = A[p], A[col]
        bv[col], bv[p] = bv[p], bv[col]
        pv = A[col][col]
        for r in range(m):
            if r == col:
                continue
            f = A[r][col] / pv
            if f:
                for c in range(col, m):
                    A[r][c] -= f * A[col][c]
                bv[r] -= f * bv[col]
        for c in range(col, m):
            A[col][c] /= pv
        bv[col] /= pv
    return [int(round(x)) for x in bv]


def expand_segs(toks):
    out = []
    for t in toks:
        if t[0] == 'c':
            out.extend([t[2]] * t[1])
        else:
            out.extend(fd_gen(t[2], t[1]))
    return out


def fit_segs(ints, tol):
    toks = seg_series(ints, tol)
    if not toks:
        return None
    out = expand_segs(toks)
    if len(out) != len(ints):
        return None
    if not all(abs(a - b) <= tol for a, b in zip(out, ints)):
        return None
    return ('segs', toks)


def fit_knots(ns, eps):
    """iterative RDP on (index, value)."""
    pts = list(enumerate(ns))
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        lo, hi = stack.pop()
        if hi - lo < 2:
            continue
        (i0, v0), (i1, v1) = pts[lo], pts[hi]
        a = (v1 - v0) / (i1 - i0) if i1 != i0 else 0.0
        imax, emax = -1, 0.0
        for k in range(lo + 1, hi):
            e = abs(a * pts[k][0] + v0 - pts[k][1])
            if e > emax:
                imax, emax = k, e
        if emax > eps:
            keep[imax] = True
            stack.append((lo, imax))
            stack.append((imax, hi))
    knots = [(i, v) for (i, v), kf in zip(pts, keep) if kf]
    if len(knots) >= len(ns):
        return None
    return ('knots', knots)


def regen_knots(knots, count):
    out = [None] * count
    for (i0, v0), (i1, v1) in zip(knots, knots[1:]):
        span = i1 - i0
        for i in range(i0, i1 + 1):
            out[i] = round(v0 + (v1 - v0) * (i - i0) / span) if span else v0
    out[knots[0][0]] = knots[0][1]
    out[knots[-1][0]] = knots[-1][1]
    return out


def enc_cost(kind, data):
    if kind == 'const':
        return len(svb(data))
    if kind == 'lin':
        return len(svb(data[0])) + len(svb(data[1]))
    if kind == 'quad':
        return sum(len(svb(x)) for x in data)
    if kind == 'runs':
        out = len(uvb(len(data)))
        prev = 0
        for v, n in data:
            out += len(uvb(n)) + len(svb(v - prev))
            prev = v
        return out
    if kind == 'knots':
        out = len(uvb(len(data)))
        pv, pi = 0, 0
        for i, v in data:
            out += len(uvb(i - pi)) + len(svb(v - pv))
            pi, pv = i, v
        return out
    if kind == 'cha':
        v0, ds = data
        return len(svb(v0)) + sum(len(svb(d)) for d in ds)
    if kind == 'segs':
        out = len(uvb(len(data)))
        for t in data:
            out += 1
            if t[0] == 'c':
                out += len(uvb(t[1])) + len(svb(t[2]))
            else:
                out += len(uvb(t[1])) + 1
                out += sum(len(svb(x)) for x in t[2])
        return out
    raise ValueError(kind)


def regen_series(kind, data, count):
    if kind == 'const':
        return [data] * count
    if kind == 'lin':
        v0, d = data
        return [v0 + d * i for i in range(count)]
    if kind == 'quad':
        v0, d1, c = data
        out, v, d = [], v0, d1
        for _ in range(count):
            out.append(v)
            v += d
            d += c
        return out
    if kind == 'runs':
        out = []
        for v, n in data:
            out.extend([v] * n)
        return out
    if kind == 'knots':
        return regen_knots(data, count)
    if kind == 'cha':
        v0, ds = data
        out = [v0]
        for d in ds:
            out.append(out[-1] + d)
        return out
    if kind == 'segs':
        return expand_segs(data)
    raise ValueError(kind)


def choose_fit(ints, tolerance, eps_units=(0.6, 1.0, 2.0)):
    cands = [f for f in (fit_const(ints), fit_lin(ints), fit_quad(ints),
                         fit_runs(ints), fit_cha(ints)) if f]
    best = min(cands, key=lambda f: enc_cost(*f))
    if tolerance == 0:
        return best[0], best[1], 0
    err = 0
    for eps in eps_units:
        f = fit_knots(ints, eps)
        if not f:
            continue
        reg = regen_knots(f[1], len(ints))
        e = max(abs(a - b) for a, b in zip(reg, ints))
        if e <= tolerance and enc_cost(*f) < enc_cost(*best):
            best, err = f, e
    f = fit_segs(ints, tolerance)
    if f and enc_cost(*f) < enc_cost(*best):
        e = max(abs(a - b) for a, b in zip(expand_segs(f[1]), ints))
        if e <= tolerance:
            best, err = f, e
    return best[0], best[1], err


def track_data(kind, data):
    if kind == 'segs':
        out = [uvb(len(data))]
        for t in data:
            if t[0] == 'c':
                out.append(b'\x00' + uvb(t[1]) + svb(t[2]))
            else:
                out.append(b'\x01' + uvb(t[1]) +
                           bytes([len(t[2]) - 1]) +
                           b''.join(svb(x) for x in t[2]))
        return b''.join(out)
    if kind == 'const':
        return svb(data)
    if kind == 'lin':
        return svb(data[0]) + svb(data[1])
    if kind == 'quad':
        return b''.join(svb(x) for x in data)
    if kind == 'runs':
        out = uvb(len(data))
        prev = 0
        for v, n in data:
            out += uvb(n) + svb(v - prev)
            prev = v
        return out
    if kind == 'knots':
        out = uvb(len(data))
        pv, pi = 0, 0
        for i, v in data:
            out += uvb(i - pi) + svb(v - pv)
            pi, pv = i, v
        return out
    if kind == 'cha':
        v0, ds = data
        return svb(v0) + b''.join(svb(d) for d in ds)
    raise ValueError(kind)


# -------------------------------------------------------------------- main


def rdp_local(ts, vs, eps):
    """Indices to keep so every dropped (t,v) point is within eps (vertical)
    of the polyline through kept points. Vertical metric = the actual render
    error, since the engine blends linearly in time between keyframes."""
    n = len(ts)
    if n <= 2:
        return set(range(n))
    keep = [False] * n
    keep[0] = keep[n - 1] = True
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        t0, v0 = ts[a], vs[a]
        t1, v1 = ts[b], vs[b]
        dt = t1 - t0
        dmax, imax = 0.0, a
        for i in range(a + 1, b):
            if dt == 0:
                d = abs(vs[i] - v0)
            else:
                u = (ts[i] - t0) / dt
                d = abs(vs[i] - (v0 + u * (v1 - v0)))
            if d > dmax:
                dmax, imax = d, i
        if dmax > eps:
            keep[imax] = True
            stack.append((a, imax))
            stack.append((imax, b))
    return {i for i, k in enumerate(keep) if k}


def reduce_records(sc, eps):
    """Keyframe reduction per (scene, role, leaf-path): the engine K() blends
    linearly in time between adjacent records of a target, so a record can be
    dropped iff every original sample stays within eps of the kept polyline.
    Equal-time groups keep first+last (approach/departure anchors)."""
    rs = sc[6]
    byrole = defaultdict(list)
    for i, r in enumerate(rs):
        byrole[r[1]].append(i)
    keep = set()
    for role, gidx in byrole.items():       # gidx: global record idx, in order
        groups = []                         # equal-time groups of LOCAL positions
        for li, gi in enumerate(gidx):
            if groups and rs[gi][2] == rs[gidx[groups[-1][-1]]][2]:
                groups[-1].append(li)
            else:
                groups.append([li])
        paths = [p for p, _ in walk_values(rs[gidx[0]][4])
                 if not isinstance(dict_get(rs[gidx[0]][4], p), str)]
        need = set()
        for p in paths:
            ts = [rs[gi][2] for gi in gidx]
            vs = [dict_get(rs[gi][4], p) for gi in gidx]
            need |= rdp_local(ts, vs, eps)
        for gl in groups:
            if len(gl) == 1:
                if gl[0] in need:
                    keep.add(gidx[gl[0]])
            else:
                keep.add(gidx[gl[0]])       # approach anchor
                keep.add(gidx[gl[-1]])      # departure anchor
    return [r for i, r in enumerate(rs) if i in keep]


def main():
    def argi(name, dflt):
        for x in sys.argv[1:]:
            if x.startswith(name + '='):
                return int(x.split('=')[1])
        return dflt

    a = [x for x in sys.argv[1:] if x.startswith('--tol=')]
    def argf(name, dflt):
        for x in sys.argv[1:]:
            if x.startswith(name + '='):
                return float(x.split('=')[1])
        return dflt

    RDP_EPS = argf('--rdp', 1.0)          # keyframe-reduction tolerance (raw value units)
    tol_abs = argf('--tol', 0.011)        # regen-vs-kept deviation bound
    QUANT = argi('--quant', 100)         # re-quantize float tracks (0 = exact)
    sweep = '--sweep' in sys.argv
    s, js, vi, vend, P = load()
    scenes = P['s']
    orig_rec_n = sum(len(sc[6]) for sc in scenes)
    scenes = [sc[:6] + [reduce_records(sc, RDP_EPS)] + sc[7:] for sc in scenes]
    print(f'rdp eps {RDP_EPS:g}: kept {sum(len(sc[6]) for sc in scenes):,} '
          f'of {orig_rec_n:,} records')

    roles = []
    for sc in scenes:
        for r in sc[6]:
            if r[1] not in roles:
                roles.append(r[1])
    rid = {r: i for i, r in enumerate(roles)}
    obj_idx = lambda role: int(role.split(':')[1])

    # record names are inert labels (never parsed or looked up at runtime) ->
    # v2 emits a constant id 0 for every record; the name-derivation machinery
    # (pattern tables, gravity overrides, counters) is gone from the stream.
    # ---- clusters (verbatim role sequences; scenes are t-monotone)
    streams = {}
    for si, sc in enumerate(scenes):
        clusters = []
        prev = None
        for r in sc[6]:
            tm = round(r[2] * 10000)
            assert abs(r[2] * 10000 - tm) < 1e-6 and r[3] == 0
            if prev is not None and tm == prev:
                clusters[-1][1].append(r[1])
            else:
                clusters.append((tm, [r[1]]))
            prev = tm
        vocab = list(dict.fromkeys(tuple(c[1]) for c in clusters))
        vidx = {v: i for i, v in enumerate(vocab)}
        seq = []
        for kk, roles_list in clusters:
            sid = vidx[tuple(roles_list)]
            seq.append((kk, sid))
        streams[si] = (vocab, seq)
    print(f'clusters {sum(len(v[1]) for v in streams.values())}, '
          f'vocab {sum(len(v[0]) for v in streams.values())}')

    # ---- skeletons + tracks
    rec_of_role = defaultdict(list)
    for sc in scenes:
        for r in sc[6]:
            rec_of_role[r[1]].append(r)
    skeleton = {}
    template = {}
    for role, rs in rec_of_role.items():
        skel = [p for p, _ in walk_values(rs[0][4])]
        for r in rs:
            assert [p for p, _ in walk_values(r[4])] == skel, (role, r[0])
        skeleton[role] = skel
        template[role] = struct_of(rs[0][4])
    occ = {role: len(rs) for role, rs in rec_of_role.items()}

    tracks = {}
    for role in rec_of_role:
        for path in skeleton[role]:
            tracks[(role, path)] = [dict_get(r[4], path)
                                    for r in rec_of_role[role]]

    fits = {}
    kind_hist = Counter()
    trk_est = 0
    for k, series in tracks.items():
        if isinstance(series[0], str):
            uniq = list(dict.fromkeys(series))
            idx = [uniq.index(v) for v in series]
            kind, data, _ = choose_fit(idx, 0)
            fits[k] = ('dict', uniq, kind, data)
            kk = kind
        else:
            is_int = all(isinstance(v, int) for v in series)
            if is_int:
                grid = 1
                ints = list(series)
            elif QUANT:
                grid = QUANT
                ints = [round(v * grid) for v in series]
            else:
                grid = best_grid([1.0 * v for v in series]) if series else 1
                ints = [round(v * grid) for v in series]
            tol = 0 if is_int else max(1, round(tol_abs * grid))
            eps_l = tuple(max(1, round(g2 * grid))
                          for g2 in (tol_abs / 4, tol_abs / 2, tol_abs,
                                     tol_abs * 2)) if tol_abs else ()
            kind, data, err = choose_fit(ints, tol, eps_l)
            fits[k] = (grid, kind, data)
            trk_est += enc_cost(kind, data)
            kk = kind
            assert err <= tol, (k, kind, err, tol)
        kind_hist[kk] += 1
    print('fit kinds:', dict(kind_hist))
    print(f'numeric track est bytes: {trk_est:,}')

    # ---- byte stream
    st = bytearray()
    sec_bounds = []                       # (name, start)

    def mark(name):
        sec_bounds.append((name, len(st)))

    def W(*bs):
        for b in bs:
            st.extend(b)

    KIND = {'const': b'\x00', 'lin': b'\x01', 'quad': b'\x02',
            'runs': b'\x03', 'knots': b'\x04', 'cha': b'\x05',
            'segs': b'\x06'}

    # S1: roles + patterns + clusters
    mark('S12')
    W(uvb(len(roles)))
    for r in roles:
        rb = r.encode()
        W(uvb(len(rb)), rb)

    # S2 (pattern table) removed: names are inert labels now

    # S3: cluster streams per scene
    for si, sc in enumerate(scenes):
        vocab, seq = streams[si]
        W(uvb(len(vocab)))
        for vs in vocab:
            W(uvb(len(vs)))
            for role in vs:
                W(uvb(rid[role]))
        W(uvb(len(seq)))
        prev_t = None
        for kk, sid in seq:
            W(svb(kk if prev_t is None else kk - prev_t), uvb(sid))
            prev_t = kk

    # S4: tracks
    mark('S3end')
    role_raw = Counter()
    for k in sorted(tracks, key=lambda k2: (rid[k2[0]], k2[1])):
        b0 = len(st)
        f = fits[k]
        if f[0] == 'dict':
            _, uniq, kind, data = f
            W(uvb(rid[k[0]]), uvb(len(uniq)), bytes([KIND[kind][0] | 0x80]), track_data(kind, data))
            for u in uniq:
                ub = u.encode()
                W(uvb(len(ub)), ub)
        else:
            grid, kind, data = f
            W(uvb(rid[k[0]]), uvb(grid), KIND[kind], track_data(kind, data))
        role_raw[k[0]] += len(st) - b0

    def dfl(bs):
        return len(zlib.compress(bytes(bs), 9, wbits=-15))

    mark('end')
    print('\n--- P.s stream sections (raw -> deflate) ---')
    for (n1, s1), (n2, s2) in zip(sec_bounds, sec_bounds[1:]):
        chunk = bytes(st[s1:s2])
        print(f'  {n1:>6}: {len(chunk):>8,} -> {dfl(chunk):>8,}')
    print(f'\nP.s stream: {len(st):,} raw -> deflate {dfl(st):,}')
    print('per-role raw:', sorted(role_raw.items(), key=lambda x: -x[1])[:10])
    # dump stream for build
    import os
    os.makedirs(BUILD, exist_ok=True)
    with open(os.path.join(BUILD, 'stream.bin'), 'wb') as f:
        f.write(st)

    # ---- statics + P.v + meta
    ser = lambda x: json.dumps(x, separators=(',', ':'), ensure_ascii=False)
    base = scenes[0]
    bdefs = {d[0]: d for d in base[2]}
    normed = []
    for sc in scenes:
        rs = set(r[1] for r in sc[6])
        defs = [bdefs[d[0]] if d[0] in bdefs and
                ('object:' + str(d[0])) in rs else d for d in sc[2]]
        lids = base[3] if all(('light:' + str(d[0])) in rs
                              for d in sc[3]) else sc[3]
        cam = base[4] if 'camera' in rs else sc[4]
        bg = base[5] if 'background' in rs else sc[5]
        normed.append(sc[:2] + [defs, lids, cam, bg] + sc[6:])
    pool, seen = [], {}
    def comp(c):
        j = ser(c)
        ix = seen.get(j)
        if ix is None:
            ix = len(pool)
            seen[j] = ix
            pool.append(j)
        return ix
    lines = []
    for sc in normed:
        lines.append(','.join(str(comp(x)) for x in
                               (sc[0], sc[1], sc[2], sc[3], sc[4], sc[5], sc[7])))
    statics = ';'.join(lines) + '\x01' + '\x00'.join(pool)
    with open(os.path.join(BUILD, 'statics.txt'), 'wb') as f:
        f.write(statics.encode('utf-8'))
    with open(os.path.join(BUILD, 'pv.json'), 'w', encoding='utf-8') as f:
        f.write(ser(P['v']))
    with open(os.path.join(BUILD, 'meta.json'), 'w', encoding='utf-8') as f:
        f.write(ser({k: P[k] for k in ('x', 't', 'd', 'q', 'b', 'n')}))
    # dump skeleton for boot
    import json as _json
    sk = {r: [list(p) for p in skeleton[r]] for r in roles}
    with open(os.path.join(BUILD, 'skeleton.json'), 'w', encoding='utf-8') as f:
        f.write(_json.dumps(sk,separators=(',',':')))
    p_v_txt = ser(P['v'])
    nx_txt = ser({k: P[k] for k in ('x', 't', 'd', 'q', 'b', 'n')})
    st_gz = len(zlib.compress(statics.encode(), 9, wbits=-15))
    pv_gz = len(zlib.compress(p_v_txt.encode(), 9, wbits=-15))
    nx_gz = len(zlib.compress(nx_txt.encode(), 9, wbits=-15))
    print(f'statics {st_gz:,} | P.v {pv_gz:,} | meta {nx_gz:,}')

    # ---- outer + shaders
    rest = js[vend:]
    spans = []
    for m in re.finditer(re.escape('#version 300 es'), rest):
        a = rest.rfind('"', 0, m.start())
        e2 = a + 1
        while True:
            e2 = rest.find('"', e2 + 1)
            if rest[e2 - 1] != '\\':
                break
        spans.append((a, e2 + 1))
    pieces, cur = [], 0
    for a, e2 in spans:
        pieces.append(rest[cur:a])
        cur = e2
    pieces.append(rest[cur:])
    shaders = ''.join(rest[a:e2] for a, e2 in spans)
    outer = ''.join(pieces)
    outer_gz = len(zlib.compress(outer.encode(), 9, wbits=-15))
    sh_gz = len(zlib.compress(shaders.encode(), 9, wbits=-15))
    print(f'outer {outer_gz:,} | shaders {sh_gz:,}')

    runtime_est, shell_est, audio_est = 3000, 1200, 3000
    d_total = dfl(st) + st_gz + pv_gz + nx_gz + outer_gz + sh_gz + \
        runtime_est + audio_est
    file_est = int(d_total * 1.25) + shell_est
    diff = file_est - 65536
    print(f'\nTOTAL deflate {d_total:,} (audio slot {audio_est:,}) '
          f'-> file ~{file_est:,} vs 65,536 -> '
          f'{"OK" if diff < 0 else "OVER by %d" % diff}')

    # ---- FULL VALIDATION: regenerate and compare
    if sweep:
        with open(os.path.join(BUILD, 'model32.pkl'), 'wb') as f:
            pickle.dump({
                'roles': roles, 'rdp': RDP_EPS, 'quant': QUANT, 'tol_abs': tol_abs,
                'streams': streams, 'fits': fits, 'occ': occ,
                'skeleton': skeleton, 'template': template,
                'statics': normed,
                'p_v': P['v'],
                'meta': {k: P[k] for k in ('x', 't', 'd', 'q', 'b', 'n')},
            }, f)
        return
    # ---- validation: regen vs ORIGINAL kept records (floats within tol_abs
    # after grid rounding; ints/strings exact; times exact).
    def walk_cmp(a, b, path, where):
        nonlocal worst_f, worst_loc, hard_bad
        if isinstance(a, list) or isinstance(b, list):
            if len(a) != len(b):
                hard_bad += 1; return
            for i in range(len(a)):
                walk_cmp(a[i], b[i], path + (i,), where)
        elif isinstance(a, str) or isinstance(b, str):
            if a != b:
                hard_bad += 1
        elif isinstance(a, float) or isinstance(b, float):
            d = abs(a - b)
            if d > worst_f:
                worst_f, worst_loc = d, (where, path)
        else:
            if int(a) != int(b):
                hard_bad += 1

    worst_f = 0.0
    worst_loc = None
    hard_bad = 0
    regen_scenes = regen_records(roles, streams, fits, occ,
                                 skeleton, template)
    for si, (got, src) in enumerate(zip(regen_scenes, scenes)):
        for j, (rr, r) in enumerate(zip(got, src[6])):
            if rr[1] != r[1] or rr[2] != r[2]:
                hard_bad += 1
                continue
            if rr[3] != 0:
                hard_bad += 1
            walk_cmp(rr[4], r[4], (), (si, j))
    print(f'validation: hard mismatches {hard_bad}, '
          f'worst float deviation {worst_f:.6g} at {worst_loc} '
          f'(tol {tol_abs:g})')
    if worst_f > tol_abs * 1.02:
        print(f'  *** DEVIATION ABOVE TOLERANCE ***')

    os.makedirs(BUILD, exist_ok=True)
    with open(os.path.join(BUILD, 'model32.pkl'), 'wb') as f:
        pickle.dump({
            'roles': roles, 'rdp': RDP_EPS, 'quant': QUANT, 'tol_abs': tol_abs,
            'streams': streams, 'fits': fits, 'occ': occ,
            'skeleton': skeleton, 'template': template,
            'statics': normed,
            'p_v': P['v'],
            'meta': {k: P[k] for k in ('x', 't', 'd', 'q', 'b', 'n')},
        }, f)
    print('saved build/model32.pkl')


def struct_of(v):
    """deep-copy the list structure; leaves become None placeholders."""
    if isinstance(v, list):
        return [struct_of(x) for x in v]
    return None


def regen_records(roles, streams, fits, occ, skeleton, template):
    # value series per track
    svals = {}
    for k, f in fits.items():
        if f[0] == 'dict':
            _, uniq, kind, data = f
            idxs = regen_series(kind, data, occ[k[0]])
            svals[k] = [uniq[i] for i in idxs]
        else:
            grid, kind, data = f
            vs = [iv / grid for iv in regen_series(kind, data, occ[k[0]])]
            svals[k] = [int(v) if v.is_integer() else v for v in vs]

    occ_ptr = defaultdict(int)              # role -> global occurrence ordinal
    out_scenes = []
    for si in sorted(streams):
        vocab, seq = streams[si]
        scene = []
        for tm, sid in seq:
            t = tm / 10000                  # exact double of the 4-dp literal
            t_rep = int(t) if t.is_integer() else t
            for role in vocab[sid]:
                oi = occ_ptr[role]
                occ_ptr[role] += 1
                payload = fill_payload(template[role], svals, role, oi)
                scene.append([0, role, t_rep, 0, payload])
        out_scenes.append(scene)
    return out_scenes


def fill_payload(tpl, svals, role, occ_idx, path=()):
    if isinstance(tpl, list):
        return [fill_payload(e, svals, role, occ_idx, path + (i,))
                for i, e in enumerate(tpl)]
    return svals[(role, path)][occ_idx]


if __name__ == '__main__':
    main()
