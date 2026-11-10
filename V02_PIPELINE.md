# Micidial v2 Version 0.2 — Pipeline Documentation

This document reconstructs the building blocks and pipeline of **Micidial v2 version 0.2**, recovered by unpacking `micidial_v2_v02.html` (65,288 bytes, under the 65,536 cap) and comparing it with `micidial_v2_v01.html` (67,041 bytes, over cap). The existing repository documentation (`MICIDIAL_V2.md`, `v2/*.py`, `v2/*.js`) describes the v0.1 pipeline; this document describes what v0.2 changed and how it works.

---

## 1. Overview

Micidial v2 is a lossy semantic compression engine for a single-file WebGL demo page (`original/uncompressed.html`, 5,359,781 bytes). The goal: produce a self-contained HTML page (< 64 KiB) that renders identically in a standard browser.

The v0.2 artifact `micidial_v2_v02.html` achieves **65,288 bytes** — 248 bytes under the cap. It is built from **10 container sections**, each individually deflate-raw compressed, embedded page-safe via a `windows-1252` cp1252 inverse-table encoding.

---

## 2. High-Level Comparison: v0.1 vs v0.2

| Aspect | v0.1 (`micidial_v2_v01.html`) | v0.2 (`micidial_v2_v02.html`) |
|--------|-------------------------------|-------------------------------|
| File size | 67,041 B (1,505 B OVER cap) | 65,288 B (248 B UNDER cap) |
| Container encoding | Single deflate-raw + base85 (1.25x expansion) | Per-section deflate-raw + cp1252 inverse table (1.0x expansion) |
| Bootstrap | `ca()` base85 decoder + v1 alphabet splice | Comment-wrapped payload + cp1252 decode + `*` escape pairs |
| Charset | `utf-8` | `windows-1252` |
| Section count | 10 | 10 |
| Section mapping | Identical | Identical |
| Boot code (section 0) | Unminified, 3,798 B source | Minified, 2,948 B source (`boot.min.js`) |
| Audio engine (section 2) | synth.js, 7,939 B raw | Entirely new synth, 50,521 B raw |
| Outer.js (section 1) | 62,843 B (LF line endings) | 62,849 B (CRLF, +6 bytes only) |
| Sections 3–9 | Identical between versions | Identical between versions |

Sections 3–9 (stream.bin, statics.txt, pv.json, meta.json, audio.bin, skeleton.json, shell.html) are **byte-identical** between v0.1 and v0.2. Only sections 0, 1, and 2 changed, plus the container/packaging layer.

---

## 3. The Container and Bootstrap (Section 0 of the page)

### 3.1 Page Structure

```html
<!doctype html>
<meta charset=windows-1252>
<title>BDE Competition Pack</title>
<body style="...">
<script>
  (async()=>{ … bootstrap … })().catch(e=>document.body.textContent="BDE PACK ERROR · "+e)
/* <escaped binary container payload> */
</script>
```

### 3.2 Bootstrap Decoding (v0.2)

The bootstrap reads the page's own `<script>` text, slices between the first `/*` and last `*/`, and decodes the payload:

```javascript
let s = document.currentScript.textContent;
let a = s.indexOf("/*");
let b = s.lastIndexOf("*/");
s = s.slice(a + 2, b);                           // strip comment wrappers

let C = '\x80\x82...\x9f';                        // 27 cp1252-defined bytes (0x80..0x9F minus 5 undefined)
let H = "8082838485868788898A8B8C8E9192939495969798999A9B9C9E9F";  // hex lookup, 54 chars

let cs = [...s], o = [], l = cs.length;
for (let k = 0; k < l; k++) {
    let n = cs[k].codePointAt(0);
    if (n === 42) {                              // '*' = escape marker
        k++;                                      // consume next char
        n = cs[k].codePointAt(0) - 1;             // byte = next char - 1
    } else {
        let j = 0;
        while (j < 27 && C.charCodeAt(j) !== n) j++;  // linear search in C
        n = j < 27 ? parseInt(H.substr(j * 2, 2), 16) : n;  // table lookup or identity
    }
    o.push(n);
}
let u = new Uint8Array(o);                       // raw container bytes
```

**Escape rules** (bytes that would corrupt HTML parsing are escaped as `*` + next_char):

| Escaped byte | Why | Encoded as | Count in real payload |
|-------------|-----|-----------|----------------------|
| 0x00 (NUL) | HTML tokenizer converts NUL → U+FFFD | `*` + char(1) | 242 |
| 0x0D (CR) | Tokenizer normalizes CR → LF | `*` + char(14) | 244 |
| 0x2A (`*`) | Would close `*/`; also escape marker | `*` + char(43) | 226 |

Total overhead: +712 bytes on the payload.

### 3.3 Container Layout (per-section deflate)

After decoding, `u` contains:

```
[u16 BE: sectionCount = 10]
[u32 LE: len_0][u32 LE: len_1]...[u32 LE: len_9]
[deflate-raw body 0][deflate-raw body 1]...[deflate-raw body 9]
```

Each body is independently inflated via `DecompressionStream("deflate-raw")`:

```javascript
let n = u[0] << 8 | u[1], L = [], p = 2;
for (let i = 0; i < n; i++) {
    L.push(u[p] | u[p+1]<<8 | u[p+2]<<16 | u[p+3]<<24); p += 4;
}
let off = 2 + 4 * n, S = [];
for (let i = 0; i < n; i++) {
    let q = off, le = L[i]; off += le;
    S.push(new Uint8Array(
        await new Response(new Blob([u.subarray(q, q+le)]).stream()
        .pipeThrough(new DecompressionStream("deflate-raw"))).arrayBuffer()));
}
```

`S[]` is the array of 10 inflated sections passed to `boot.js`.

### 3.4 Bootstrap Execution

```javascript
let d = new TextDecoder();
await eval(d.decode(S[0]))(S);   // eval boot.js (section 0), pass all sections
```

---

## 4. Section Map (identical in v0.1 and v0.2)

| Index | Section | v0.2 raw size | v0.2 deflated | Description |
|-------|---------|--------------|---------------|-------------|
| 0 | `boot.min.js` | 2,948 B | 1,317 B | Runtime decoder (minified boot.js) |
| 1 | `outer.js` | 62,852 B | 21,912 B | Verbatim outer engine JS (`js[vend:]` from original page) |
| 2 | `synth.js` | 50,521 B | 15,478 B | **V0.2: entirely new audio worklet** (v0.1: 7,939 B) |
| 3 | `stream.bin` | 26,261 B | 15,164 B | P.s scene data stream (uvb/svb encoded tracks) |
| 4 | `statics.txt` | 38,446 B | 2,120 B | Per-scene static component pool |
| 5 | `pv.json` | 102,084 B | 3,708 B | P.v layer definitions |
| 6 | `meta.json` | 4,564 B | 680 B | P.x, P.t, P.d, P.q, P.b, P.n metadata |
| 7 | `audio.bin` | 3,724 B | 1,929 B | Quantized audio pattern blob |
| 8 | `skeleton.json` | 2,033 B | 216 B | Role → leaf-path skeleton templates |
| 9 | `shell.html` | 1,766 B | 960 B | Hand-written DOM shell |

Sum of deflates: 63,484 B + 42 B header = 63,526 container bytes. Embedded as cp1252 raw + 712 escape overhead ≈ 64,238 B + bootstrap wrapper ≈ 65,288 B total.

---

## 5. Building Block: Boot.js (Section 0 — Runtime Decoder)

### 5.1 v0.2 Boot Code (Minified)

Source: 3,798 B → minified: 2,948 B → deflated: 1,317 B.

The minified boot.js (`async r=>{…}`) is functionally identical to v0.1's unminified `(async S=>{…})`; differences are purely lexical (minified variable names, arrow function syntax). The same section mapping applies:

- `r[1]` = outer.js → executed as `new Function('P', '(async()=>{const ' + O.slice(1) + '})()')(P)`
- `r[2]` = synth worklet source → part of `P.a = ['json', [synthSrc, audioBlob]]`
- `r[3]` = stream.bin → scene track data
- `r[4]` = statics.txt → per-scene static defs
- `r[5]` = pv.json → P.v
- `r[6]` = meta.json → P.x, P.t, P.d, P.q, P.b, P.n
- `r[7]` = audio.bin → audio blob
- `r[8]` = skeleton.json → payload skeleton templates
- `r[9]` = shell.html → injected via `document.write`

### 5.2 Byte Coding Primitives

- **uvb**: unsigned LEB128 varint (little-endian groups of 7 bits, continuation bit = 0x80)
- **svb**: signed zigzag varint (`zz(n) = 2n` if `n >= 0` else `2|n| - 1`, then uvb)
- **Strings**: uvb length + raw UTF-8 bytes
- **Banker's rounding `R(x)`**: `floor(x)`, then round-half-to-even — matches Python `round()`

### 5.3 Stream Decoding (Section 3 → P.s records)

1. **Role table**: `uvb nRoles`, then `nRoles × [uvb len + UTF-8 role string]`
2. **Per-scene cluster streams** (until all scenes done):
   - `uvb vocabN`, then `vocabN × [uvb roleCount] (roleCount × uvb rid)` — vocabulary of role sequences
   - `uvb seqLen`, then `seqLen × [svb dt | uvb vocabId]` — `dt` is delta-time from previous record (`t = round(t·10000)/10000`)
3. **Track loop** (until `p >= stream.length`):
   - `uvb rid`, `uvb grid-or-uniqN`, `KIND byte` (bit 0x80 = dict track)
   - `regen(kind, occ[rid])` → numeric series of length `occ[rid]`
   - If dict: read `uniqN` strings; series = `series.map(i => uniq[i])`
   - If numeric: divide every value by `grid`
   - Append series to `leafVals[rid]`

### 5.4 Regen Kinds (0–5)

| Kind | Body | Regeneration |
|------|------|--------------|
| 0 (const) | `svb v` | `v` repeated `occ` times |
| 1 (lin) | `svb v0, svb d` | `v0 + d*i` |
| 2 (quad) | `svb v0, svb d1, svb c` | `v += d; d += c` |
| 3 (runs) | `uvb m`, `m × [uvb runLen, svb deltaV]` | Expand runs, prev-based deltas |
| 4 (knots) | `uvb m`, `m × [uvb indexDelta, svb valueDelta]` | Linear interpolation between knots, banker's `round()`, knot endpoints exact |
| 5 (cha/delta-chain) | `svb v0`, `occ−1 × svb delta` | Cumulative sum |

**Note**: `segs` (kind 6) is documented in the wire format but **not implemented in boot.js** — latent runtime gap (open issue). Current profile never selects kind 6.

### 5.5 Scene Reconstruction

1. `buildTemplate(paths)` builds a nested array payload tree per role from skeleton leaf paths
2. `fill(node, vals, idx)` walks the tree: number → `vals[node][idx]`, array → recurse, else → literal
3. Scenes assembled as `[duration, int, defs[7], lights[2], camera[4], background[20], records, flags]`
4. Records: `[0, roleName, t, 0, payload]` — name is constant `0` (lossless vs runtime; names are inert)
5. `P = {s: scenes, v: JSON.parse(r[5]), a: ['json', [r[2] text, r[7] blob]], ...meta}`
6. `document.open(); document.write(r[9]); document.close();` — inject shell before engine runs
7. Execute outer.js: `await new Function("P", "(async()=>{const " + r[1].slice(1) + "})()")(P)`

---

## 6. Building Block: Audio Engine (Section 2 — Entirely New in v0.2)

### 6.1 v0.2 Synth.js (50,521 B raw, 15,478 B deflated)

This is a **complete rewrite** of the audio worklet compared to v0.1 (7,939 B). Key structural differences:

| Feature | v0.1 (7,939 B) | v0.2 (50,521 B) |
|---------|---------------|-----------------|
| Strict mode | No | `"use strict"` |
| IIFE pattern | `!function(){var …}` | `!function(){function …}` with function declarations |
| RNG | Simple inline xorshift | `class e` with `nextU()`, `next()`, `bipolar()` |
| 32-bit multiply | None | `Math.imul`-based hash with prime constants (2654435761, 2246822507, 3266489909, 2146121005, 2221713035) |
| Filter class | None | `class r` with `reset()`, `set()` (biquad/resonant filter) |
| Classes | ~4 | 11 |
| Voice types | `v0..v3` | Expanded voice architecture |
| `outL`/`outR` | Yes | Yes |
| `registerProcessor("atbs-v04")` | Yes | Yes |

The v0.2 engine speaks the **identical AudioWorklet message protocol** (`{type:'state'\|'play'\|'stop'}`) so `outer.js` requires no changes. Boot sets `P.a = ['json', [synthSrc, audioBlob]]` where `synthSrc` is section 2 text and `audioBlob` is section 7 bytes.

### 6.2 Audio Blob (Section 7 — 3,724 B raw, 1,929 B deflated)

Produced by `v2/audio.py` `blob()`; consumed verbatim by `synth.js` class `D.st(u)`. Layout:

```
[1 byte] nScenes
nScenes × 7 bytes: bars, acidA+1, acidB+1, drums+1, stab+1, drone+1, fx+1
                 (pattern idx -1 stored as 0; real idx i -> i+1)
[1 byte] nAutoTracks
per track: [scene byte][key byte 0..9][nAnchors byte]
  per anchor: [pos byte 0..255][val byte = round(v*100) clamp 0..127]
  anchors = RDP-reduced (pos, val), eps 1.0 (0.01 units)
[acid blocks acidA0, acidB0, acidB1]:
  64 × [note byte = note-24][flag bits: 1=gate,2=accent,4=slide,8=ratchet>=2]
  [nP] [nP × (pos byte, prob byte = round(prob*100))] where prob<1
[drums blocks 0..6]:
  [nRows] per row: [rowIdx byte][8-byte on-bitmap LSB-first over 64 steps]
    per on step: [vel byte = round(vel*100) clamp 0..127 \| 0x80 if ratchet>=2]
  [nP] [nP × (pos, prob)] per NON-EMPTY row
[stab blocks 0..2 then fx blocks 0..2]: per block:
  [8-byte on-bitmap] per on step: [note-24][chord][inversion][vel*100 clamped]
  [gate: enabled byte][rate byte][smooth*100 byte][4 bytes: 16 steps packed 2-bit {0,.5,1}]
```

Automation key map: 0 acidA.cutoff, 1 acidA.res, 2 acidB.cutoff, 3 acidB.res, 4 fx.cutoff, 5 fx.res, 6 drone.cutoff, 7 mixer.drone.level, 8 mixer.stab.level, 9 mixer.fx.level.

---

## 7. Building Block: Other Sections (Identical in v0.1 and v0.2)

### 7.1 stream.bin (Section 3 — 26,261 B raw, 15,164 B deflated)

The P.s scene data stream as described in §5.3. Encodes 26,982 original snapshot records down to ~4,078 kept keyframes via per-track RDP reduction. Wire format: role table → per-scene cluster streams → track series (kinds 0–5).

### 7.2 statics.txt (Section 4 — 38,446 B raw, 2,120 B deflated)

Component-pool text: `lines ';' sep; '\x01'; pool '\x00' sep`. For each of 62 scenes: 7 comma-separated pool indices. Pool entries are JSON of unique component defs (after normalization: record-covered defs replaced by scene-0 canonical).

### 7.3 pv.json / meta.json / skeleton.json (Sections 5, 6, 8)

- `pv.json`: `JSON.stringify(P['v'])` — 102,084 B raw, 3,708 B deflated (largest section)
- `meta.json`: `{x, t, d, q, b, n}` — 4,564 B raw, 680 B deflated
- `skeleton.json`: `{role: [leaf-path lists]}` — 2,033 B raw, 216 B deflated

### 7.4 audio.bin (Section 7)

See §6.2.

### 7.5 shell.html (Section 9 — 1,766 B raw, 960 B deflated)

Hand-written DOM shell: doctype, styles, `<canvas>`, `#setup` panel with `#start`/`#fs` button, hidden `#gpu` div. Injected by boot via `document.write()` **before** outer.js runs (fixes issue #0003: outer.js queries `#start`/`#setup`/`#gpu`/`canvas` and throws if absent).

---

## 8. Pipeline: How v0.2 Is Built

Based on evidence from `micidial_v2_v02.html`, `MICIDIAL_V2.md`, and the repo's v2/ tools:

```
Stage 0:  original/uncompressed.html must exist (5.36 MB input)

Stage 1:  Scene compiler: v2/compile.py
          → v2/build/{stream.bin, statics.txt, pv.json, meta.json, skeleton.json}
          --rdp=1 --quant=100 --tol=0.011 (default lossy profile)

Stage 1b: Outer-JS extractor: v2/iface.py
          → v2/build/outer.js (byte-exact js[vend:] slice from original page)

Stage 2:  Audio extraction: v2/audio_extract.py
          → v2/build/audio.pkl (P.a = [workletSrc, song] from original page)

Stage 3:  Audio blob encoder: v2/audio.py
          → v2/build/audio.bin (quantized blob per §6.2)

Stage 4:  Synth minification: v2/min_synth.js (terser)
          → v2/build/synth.min.js
          **V0.2: section 2 contains a 50,521 B synth — different from repo's v2/synth.js (9,013 B)**

Stage 4b: Boot minification: (min_boot.js — not in repo, was cleaned up)
          → v2/build/boot.min.js (2,948 B, deflates to 1,317 B)

Stage 5:  Assemble: v2/assemble.py
          → micidial_v2_v02.html
          Per-section deflate-raw → cp1252 page-safe embedding → comment-wrapped payload
```

### 8.1 Pipeline Changes in v0.2

| Stage | v0.1 | v0.2 |
|-------|------|------|
| Container | Single deflate-raw + base85 + v1 decoder splice | Per-section deflate-raw + cp1252 inverse table + `*` escapes |
| Bootstrap charset | utf-8 | windows-1252 |
| Boot code | Unminified (3,798 B) | Minified (2,948 B) |
| Audio engine | synth.js (7,939 B) | Entirely new synth (50,521 B) |
| Section 2 deflated size | ~2-3 KB (est.) | 15,478 B |

---

## 9. Ambiguities and Open Questions

The following items could not be fully resolved from `micidial_v2_v02.html` alone because the development tools and intermediate files were lost:

1. **Source of v0.2 audio engine (section 2):** The 50,521-byte synth.js in section 2 has no corresponding source file in the repo. The repo's `v2/synth.js` is 9,013 bytes (v0.1 engine). What source/build process produced the v0.2 50,521-byte engine? Is it terser-minified from a larger source, or hand-written?

2. **`min_boot.js`:** `MICIDIAL_V2.md` §3 mentions `node v2/min_boot.js` but this file was cleaned up and does not exist in the repo. What minification settings were used?

3. **v0.2 compiler flags:** The exact `--rdp`, `--quant`, `--tol` flags used to produce the v0.2 stream.bin are not recorded in v02.html itself (the stream is just binary data). MICIDIAL_V2.md says default profile `--rdp=1 --quant=100 --tol=0.011` but this may or may not match v02.html's actual stream.

4. **CRLF in outer.js:** Section 1 of v02.html has 6 CRLF line endings where v0.1 has LF. Was this intentional or an artifact of the build environment (Windows)?

5. **Kind 6 (segs) support:** Boot.js implements regen kinds 0–5 only. The wire format documents kind 6 but boot.js does not implement it. Is this a latent bug or an intentional omission?

6. **Audio engine fidelity:** The v0.2 synth is "behavioral parity only" (Q7 in MICIDIAL_V2.md) — no error bound. How close does it sound to the original?

---

## 10. Summary: What v0.2 Changed

v0.2 is primarily a **packaging and delivery optimization** over v0.1:

1. **Replaced base85 encoding (1.25x expansion) with cp1252 page-safe encoding (1.0x expansion)**, saving ~13 KB on the container.
2. **Replaced single whole-container deflate with per-section deflate-raw streams**, which costs ~10.7 KB more in raw compressed size but enables per-section decoding.
3. **Minified boot.js** (3,798 → 2,948 B source).
4. **Replaced the audio engine** with a new, larger implementation (7,939 → 50,521 B source; deflates from ~3 KB to 15.5 KB).
5. **Net result:** File size reduced from 67,041 B (over cap) to 65,288 B (under cap by 248 B).

The core compression technology (track fitting, RDP keyframe reduction, varint coding, skeleton templates, statics pool, audio blob format) is **unchanged** between v0.1 and v0.2 — only the container encoding, boot minification, and audio engine implementation differ.
