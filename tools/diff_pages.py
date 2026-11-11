#!/usr/bin/env python3
"""Compare the P structures of two uncompressed pages: python tools/diff_pages.py <A> <B>"""
import json, sys

def load(path):
    data = open(path, encoding='utf-8').read()
    i = data.find('const P')
    eq = data.index('=', i)
    P, end = json.JSONDecoder().raw_decode(data, eq + 1)
    return data, P, end

args = sys.argv[1:]
if len(args) < 2: sys.exit('usage: python tools/diff_pages.py <A> <B> (see USER_GUIDE §1)')
pA, pB = args[:2]
dA, PA, eA = load(pA)
dB, PB, eB = load(pB)

def stats(tag, d, P, e):
    print(f'== {tag}: file {len(d)} chars, P ends at {e}, tail after P {len(d)-e}')
    print(f'   keys: {sorted(P.keys())}')
    print(f'   scenes: {len(P["s"])}, total dur {sum(s[0] for s in P["s"]):.2f}s')
    recs = sum(len(s[6]) for s in P["s"])
    print(f'   records: {recs}')
    print(f'   a: {len(P["a"]) if isinstance(P["a"], list) else type(P["a"])}', end='')
    if isinstance(P["a"], list) and len(P["a"]) > 1 and isinstance(P["a"][1], list):
        print(f' parts: {[len(x) for x in P["a"][1]]}')
    else:
        print(f' len {len(P["a"]) if hasattr(P["a"],"__len__") else "?"}')
    for k in sorted(P.keys()):
        v = P[k]
        n = len(v) if hasattr(v, '__len__') else 1
        print(f'   {k}: len {n}')

stats(pA, dA, PA, eA)
stats(pB, dB, PB, eB)

# structural diffs per key
for k in sorted(set(PA) | set(PB)):
    v1, v2 = PA.get(k), PB.get(k)
    if v1 == v2:
        print(f'key {k}: IDENTICAL')
    elif isinstance(v1, list) and isinstance(v2, list) and len(v1) == len(v2):
        diffs = [i for i in range(len(v1)) if v1[i] != v2[i]]
        print(f'key {k}: lists same len {len(v1)}, {len(diffs)} differ idx {diffs[:20]}')
    else:
        print(f'key {k}: DIFFERENT (len {len(v1) if hasattr(v1,"__len__") else "?"} vs {len(v2) if hasattr(v2,"__len__") else "?"})')

# shell/head diff (before const P)
headA, headB = dA[:dA.find('const P')], dB[:dB.find('const P')]
print(f'head {len(headA)} vs {len(headB)} identical={headA==headB}')
tailA, tailB = dA[eA:], dB[eB:]
print(f'tail {len(tailA)} vs {len(tailB)} identical={tailA==tailB}')
