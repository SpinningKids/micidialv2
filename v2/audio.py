# micidial v2 - audio blob encoder
# Compact procedural-audio data: scene table + RDP'd automation anchors
# + quantized pattern grids (acid / drums / stab / fx).
# Blob is consumed verbatim by the synth worklet (v2/synth.js).
#
# BLOB LAYOUT (all little-endian-friendly byte sequences):
#   [1] nScenes
#   scenes: nScenes*7 bytes: bars, acidA+1, acidB+1, drums+1, stab+1, drone+1, fx+1
#         (pattern idx -1 stored as 0; real idx i -> i+1)
#   [1] nAutoTracks, per track: [scene byte][key byte][nAnchors byte]
#         then per anchor: [pos byte (0..255)][val byte = round(v*100) clamp 0..127]
#         anchors = RDP-reduced (pos, val) over the non-(>=0) prefix runs
#   [acid blocks in file order acidA0, acidB0, acidB1]:
#     64 x [note byte = note-24][flag: 1 gate,2 accent,4 slide,8 ratchet>=2]
#     [nP][nP x (pos byte, prob byte = round(prob*100))]
#   [drums blocks 0..6 in order]:
#     [nRows] then per row: [rowIdx byte][8 bytes on-bitmap LSB-first]
#       for each on step (ascending): [vel byte = round(vel*100) clamp 0..127
#         | (ratchet>=2 ? 0x80:0)]
#     then [nP][nP x (pos byte, prob byte)] per NON-EMPTY row
#   [stab blocks 0..2 then fx blocks 0..2]: per block:
#     [8 bytes on-bitmap LSB-first] for each on step ascending:
#       [note byte = note-24][chord byte][inv byte][vel byte round(vel*100) clamped]
#     [gate: enabled byte, rate byte, smooth byte=round(smooth*100),
#      4 bytes: steps16 packed 2 bits each (0=0,1=.5,2=1) step0 in low bits]
# Key bytes for automation: 0 acidA.cutoff 1 acidA.res 2 acidB.cutoff
#   3 acidB.res 4 fx.cutoff 5 fx.res 6 drone.cutoff 7 mixer.drone.level
#   8 mixer.stab.level 9 mixer.fx.level
# Row idx: kick0 snare1 clap2 rim3 ch4 oh5 lt6 mt7 ht8 perc9 crash10 ride11

import json
import os
import pickle
import zlib
import re
from collections import Counter

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, 'build')


def rdp(ts, vs, eps):
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
        t0, v0, dt = ts[a], vs[a], ts[b] - ts[a]
        dmax, imax = 0.0, a
        for i in range(a + 1, b):
            d = abs(vs[i] - v0) if dt == 0 else \
                abs(vs[i] - (v0 + (ts[i] - t0) / dt * (vs[b] - v0)))
            if d > dmax:
                dmax, imax = d, i
        if dmax > eps:
            keep[imax] = True
            stack.append((a, imax))
            stack.append((imax, b))
    return {i for i, k in enumerate(keep) if k}


def cl(v, hi=127):
    return max(0, min(hi, int(round(v))))


def emit(b):
    b.append(None)  # placeholder; real value patched at write time


def blob(song, auto_eps=1.0):
    out = bytearray()
    sc = song['scenes']
    out.append(len(sc))
    for s in sc:
        out.append(s.get('bars', 1))
        for g in ('acidA', 'acidB', 'drums', 'stab', 'drone', 'fx'):
            out.append(s['patterns'].get(g, -1) + 1)
    # automation
    tracks = []
    for si, s in enumerate(sc):
        for k, arr in sorted(s.get('automation', {}).items()):
            nz = [(j, v) for j, v in enumerate(arr) if v >= 0]
            if not nz:
                continue
            key = ['acidA.cutoff', 'acidA.res', 'acidB.cutoff', 'acidB.res',
                   'fx.cutoff', 'fx.res', 'drone.cutoff', 'mixer.drone.level',
                   'mixer.stab.level', 'mixer.fx.level'].index(k)
            ps = [j for j, _ in nz]
            vs = [cl(v * 100) for _, v in nz]
            keep = sorted(rdp(ps, vs, auto_eps))
            tracks.append((si, key, [(ps[i], vs[i]) for i in keep]))
    out.append(len(tracks))
    for si, key, anch in tracks:
        out.append(si)
        out.append(key)
        out.append(len(anch))
        for p, v in anch:
            assert p < 256
            out.append(p)
            out.append(v)
    # acid
    stats = {}
    for g in ('acidA', 'acidB'):
        for bi, b in enumerate(song['patterns'][g]):
            if not b:
                continue
            rr = b['steps']
            assert len(rr) == 64
            for r in rr:
                assert 24 <= r['note'] <= 152 and r['lock'] == -1
                out.append(r['note'] - 24)
                out.append((1 if r['gate'] else 0) | (2 if r['accent'] else 0)
                           | (4 if r['slide'] else 0) | (8 if r['ratchet'] >= 2 else 0))
            pe = [(j, r['prob']) for j, r in enumerate(rr) if r['prob'] < 1]
            out.append(len(pe))
            for j, v in pe:
                out.append(j)
                out.append(cl(v * 100))
            stats[g + str(bi)] = dict(n=len(rr), acc=sum(r['accent'] for r in rr),
                                      sl=sum(r['slide'] for r in rr), gt=sum(r['gate'] for r in rr))
    # drums
    rows = ['kick', 'snare', 'clap', 'rim', 'ch', 'oh', 'lt', 'mt', 'ht', 'perc', 'crash', 'ride']
    for bi, b in enumerate(song['patterns']['drums']):
        if not b:
            continue
        ne = [(rows.index(rn), rr) for rn, rr in b['rows'].items() if any(r['on'] for r in rr)]
        ne.sort(key=lambda x: x[0])
        out.append(len(ne))
        for ri, rr in ne:
            assert len(rr) == 64
            out.append(ri)
            bm = bytearray(8)
            for j, r in enumerate(rr):
                if r['on']:
                    bm[j >> 3] |= 1 << (j & 7)
            out += bm
            for j, r in enumerate(rr):
                if r['on']:
                    out.append(cl(r['vel'] * 100) | (128 if r['ratchet'] >= 2 else 0))
            pe = [(j, r['prob']) for j, r in enumerate(rr) if r['prob'] < 1]
            out.append(len(pe))
            for j, v in pe:
                out.append(j)
                out.append(cl(v * 100))
    # stab + fx
    for g in ('stab', 'fx'):
        for bi, b in enumerate(song['patterns'][g]):
            if not b:
                continue
            rr = b['steps']
            assert len(rr) == 64
            assert all(r['prob'] == 1 for r in rr)
            bm = bytearray(8)
            for j, r in enumerate(rr):
                if r['on']:
                    bm[j >> 3] |= 1 << (j & 7)
            out += bm
            for r in rr:
                if r['on']:
                    assert 24 <= r['note'] <= 152
                    out.append(r['note'] - 24)
                    out.append(r['chord'])
                    out.append(r['inversion'])
                    out.append(cl(r['vel'] * 100))
            gt = b['gate']
            out.extend([1 if gt['enabled'] else 0, gt['rate'], cl(gt['smooth'] * 100)])
            pack = 0
            for j, sv in enumerate(gt['steps']):
                pack |= {0: 0, 0.5: 1, 1: 2}[sv] << (2 * j)
            out.extend((pack >> (8 * i)) & 255 for i in range(4))
    return bytes(out)


def main():
    song = pickle.load(open(os.path.join(BUILD, 'audio.pkl'), 'rb'))['song']
    b = blob(song)
    d = len(zlib.compress(b, 9, wbits=-15))
    print(f'audio blob: {len(b):,} raw -> deflate {d:,}')
    open(os.path.join(BUILD, 'audio.bin'), 'wb').write(b)
    # per-section deflate estimate
    print('sha:', re.escape(''))


if __name__ == '__main__':
    main()
