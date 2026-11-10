# MICIDIAL_V2.md — Micidial v2: complete operating specification

Status snapshot (verified 2026-11-10): shipped artifact `micidial_v2.html` =
**67,041 bytes on disk** (10 container sections, inflated container 253,504 B,
blob 65,990 base85 chars) — i.e. **1,505 B OVER the 65,536 cap**. Page load
now OK: the clean-tree rebuild of 2026-11-10 resolved `BDE PACK ERROR ·
TypeError: Failed to fetch` — issue #0002 FIXED in memory (user-verified). See
§12 for exact status and §13 improvement levers.

---

## 1. What Micidial v2 is

Micidial v2 is a **lossy semantic compression engine** for the single-file
WebGL demo page `original/uncompressed.html` (5,359,781 B). Contract: produce a
self-contained HTML page that a standard browser runs with identical *observable*
behavior, at **< 64 KiB** (65,536 bytes total).

A lossless codec cannot reach the cap: the gzip-9 entropy floor of the raw page
data is ~508 KB (measured with `tools/budget.py`, since deleted — findings
preserved in §1 and project memory), and the fixed-cost measurement logged in
project memory (everything except the scene payload, deflated) already costs
~74 KB — above the ~52.4 KB available after base85 expansion. v2 therefore
**re-models the content**:

- the 26,982 animation snapshot records in `P.s` are replaced by **parametric
  fitted tracks** re-expanded at load time by a small JS runtime decoder;
- the 96,684-char `atbs-v04` audio worklet + 308,452-B editor project JSON are
  replaced by a **procedural synth remake** (`v2/synth.js`) plus a **compact
  quantized pattern blob** (`v2/audio.py` → `audio.bin`);
- everything else (outer engine JS, GLSL shaders, static scene config) is kept
  byte-identical and pooled into ONE deflate-raw stream.

All lossy choices have explicit, bounded error tolerances (§8).

## 2. Lineage and prior art

| Stage | Artifact | Size | Method |
|---|---|---|---|
| v1 (micidial) | `original/PRESSURE_ATBS135_v13.html` | 657,106 B | lossless entropy packing (terser + single gzipped payload + ~450 B bootstrap). Fully documented in `micidial/REBUILD.md` — DO NOT modify that folder. |
| Stage 1 | `original/uncompressed.html` | 5,359,781 B | the v1 page browser-self-decoded back to its original uncompressed form; v2's input. `tools/decompress.py` is the static stage-1 decoder. |
| v2 | `micidial_v2.html` | 67,041 B (current) | this document. |

The v2 container **reuses v1's bootstrap head**: `assemble.py` locates
`original/PRESSURE_ATBS135_v13.html`'s decoder-function prefix and keeps it
verbatim, because v1 already ships a compact base85 decoder with a custom
85-char alphabet. v2 only swaps the payload, the alphabet close, and the
post-inflate handling.

## 3. Pipeline: how to run Micidial v2

There is no single runner script; the stages and their order (all paths
relative to the repo root; all stages are idempotent):

```text
# 0. (input only: original/uncompressed.html must exist)

# 1. scene compiler: writes v2/build/{stream.bin,statics.txt,pv.json,meta.json,
#    skeleton.json,model32.pkl} + budget report
python v2/compile.py --rdp=1 --quant=100 --tol=0.011
#    (flags: --rdp eps keyframe reduction raw units; --quant float grid 0=exact;
#     --tol deviation bound; --sweep dumps model32.pkl only.
#     --rdp=1 --quant=0 --tol=0 style exact modes exist for bit-exact replay)

# 2. audio model extraction: original page P.a -> v2/build/audio.pkl
python v2/audio_extract.py

# 3. audio blob encoder: v2/build/audio.pkl -> v2/build/audio.bin
python v2/audio.py

# 4. synth minification: v2/synth.js -> v2/build/synth.min.js (needs root
#    node_modules terser)
node v2/min_synth.js

# 4b. boot minification: v2/boot.js -> v2/build/boot.min.js (3,798 B source
#     -> 2,948 B minified / 1,317 deflated; compress:false keeps the eval
#     completion value usable)
node v2/min_boot.js

# 5. assemble: section container + page-safe embedding -> micidial_v2.html
#    (repo root); output written as BYTES (no CRLF translation)
python v2/assemble.py
```

Runtime *sources* embedded by assemble.py, not generated:
`v2/boot.js` (decoder, section 0; shipped minified as section 0) and
`v2/build/shell.html` (DOM shell, section 9 — hand-written, see §7.4). Inputs
`v2/build/outer.js` comes from stage 1b:

```text
# 1b. outer-JS extractor: writes v2/build/outer.js (byte-exact js[vend:] slice)
python v2/iface.py
```

A rerun of the §3 pipeline (2026-11-10, ported-synth profile, windows-1252
embedding) produces `micidial_v2.html` at **65,288 B — 248 B under the
65,536 cap**. The page's 10 sections were verified round-trip byte-exact
through the shipped embed + split + inflate path in headless Chrome. After a rerun all regeneratable artifacts can be
deleted again: at final cleanup `v2/build/` holds **only `shell.html`** (the
hand-written input); the §3 commands recreate everything else on demand.
`iface.py` rewrites `engine.js` and `project.json` and `compile.py` rewrites
`model32.pkl` on every run — these three are diagnostic outputs read by no
pipeline stage, so delete them after any rerun.

## 4. Anatomy of the input page (`original/uncompressed.html`)

Single `<script>` containing `const P={...}` (5,295,109 chars) + outer engine
code (~34 KB after shader-literal removal; 62,843 chars verbatim) + GLSL shader
string literals (~28.6 KB). The `P` object keys:

| Key | Meaning | Size (chars) |
|---|---|---|
| `x` | 64 × 13 extra table | ~4.5 K |
| `t`,`d`,`q`,`b`,`n` | transport / config tables (b = BPM 135 etc.) | shared meta blob 4,564 |
| `s` | **SCENES**: list of 62 scenes | most of the payload |
| `v` | 62 layer-def records | 102,084 |
| `a` | audio: `['json', [workletSrc, projectObj]]` | 96,684 + 308,452 |

Scene = `[duration, int, objectDefs(7-ish), lights(2), camera(4), background(20),
SNAPSHOTS, [1,0.5,0.8,0.6]]`. Snapshot record =
`[name, role, time, 0, payload]`; 26,982 total over 62 scenes. Roles seen:
`background`, `camera`, `light:1`, `light:2`, `object:1..5,9,10` (11 role
strings). Payload = nested list of numeric/string leaves; shape is **fixed per
role** (verified: constant leaf-path list across all records of a role).

Parsing note (gotcha): to re-extract `P` use
`json.JSONDecoder().raw_decode(js, js.find('const P=')+8)` — brace matching
breaks on escaped quotes inside `P`'s strings.

## 5. Structural invariants exploited (probes ties3..ties7, zero violations)

The scene compiler (v3.3 lineage) may only rely on verified invariants; these
were established by one-off probes and are re-asserted inline (`assert`) in
`compile.py`:

1. **Times are exact 4-decimal literals on grid 1/10000**: `t = m/10000`.
   Scenes are t-monotone, so equal-time records are always adjacent.
2. **Equal-time clusters**: records group into clusters sharing one time; each
   cluster's role sequence repeats from a small per-scene vocabulary (stored
   as vocab + ids, not per-record role bytes).
3. **Fixed payload skeleton per role**; leaf int/float typing is derivable
   (no integer-valued floats exist in the data).
4. **Record names are inert**: never parsed/looked up at runtime (they matched
   derivable patterns `pressure-sculpture-…`, `cycle-…`, `emissiva-…`,
   `gravity-v9-…`, but the engine ignores them). v2 therefore emits a **constant
   id `0`** for every name; the whole name-derivation table was removed from
   the stream (this is lossless w.r.t. runtime behavior, verified by probe).
5. **Statics redundancy**: many scene-level object/light/camera/background
   defs duplicate the scene-0 canonical def when that def's role has snapshot
   records in the scene — the engine's `K()` blend always overrides the base
   def when a target record exists, so such defs can be replaced by the scene-0
   canonical (verified; defs with no record coverage in the scene keep their
   real value — 196/439 exceptions).

## 6. The scene compiler (`v2/compile.py`, main stage)

Pipeline inside `main()`:

1. **Keyframe reduction** — `reduce_records(sc, eps)`: per (scene, role,
   leaf-path) RDP in (time, value) space with the **vertical distance metric**
   (`rdp_local`). Chosen because the engine `K()` blends linearly in time
   between adjacent records of a target, so vertical deviation of dropped
   points = actual render error bound. Equal-time groups keep first+last
   (approach/departure anchors). Default eps = 1.0 raw value units → keeps
   4,078 / 26,982 records.
2. **Cluster streams** — per scene: time grid `tm = round(t*10000)` (svb
   deltas) + role-sequence vocabulary ids.
3. **Tracks** — one track per (role, leaf-path) over the role's **occurrence
   space** (occurrence ordinal = index within all kept records of that role,
   global across scenes, not per scene). Numeric tracks: ints exact on grid 1;
   floats re-quantized on grid = `--quant` (100) with tolerance
   `tol_abs*grid`. String tracks: dictionary + index track through the same
   fit machinery.
4. **Fit search** per track — `choose_fit()` picks the cheapest encoding among:
   `const`, `lin` (arithmetic progression), `quad` (constant second
   difference), `runs` (run-length pairs), `cha` (delta chain — best for
   smooth drift), `knots` (iterative RDP on (index,value) with linear
   regeneration + banker's rounding), `segs` (greedy token split: constant
   runs + order-1..6 polynomial runs encoded as finite-difference seeds
   `v0,D1..Dd` with Newton forward regeneration; exact seed first, then
   float least-squares in binomial basis, both elementwise-verified). All fits
   are verified against the kept series within tolerance before selection.
   Current profile histogram (model32.pkl, 2026-11-10 run): numeric
   const 191 / runs 119 / cha 5 / knots 1 (of 338 tracks: lin 0, quad 0, segs
   0); string dict-tracks const 6 / runs 15 / cha 1.
5. **Stream serialization + validation** — writes `stream.bin` (see §7.1) and
   re-validates by regenerating records from the model (`regen_records`) and
   deep-comparing vs kept records: 0 hard mismatches, worst float deviation
   0.01 (bound 0.011).

Note: `boot.js`'s runtime `regen()` implements kinds 0–5 only. `segs` (kind
6) is currently never selected (histogram above) but `choose_fit` may pick it
in other profiles — latent runtime gap (logged as an open issue; §10).

## 7. Wire formats (byte-exact)

Byte coding primitives: **uvb** = unsigned LEB128 varint; **svb** = signed
zigzag varint (`zz(n) = 2n if n>=0 else 2|n|-1`, then uvb); strings = uvb byte
length + raw UTF-8.

### 7.1 `build/stream.bin` (the P.s stream — 26,261 B now, 15,164 deflated)

```text
[uvb nRoles]  (nRoles × [uvb len + role utf8])          # S12: role table
              per scene × {                              # S3: cluster streams
  [uvb vocabN] (vocabN × [uvb roleCount] (roleCount × uvb rid))
  [uvb seqLen] (seqLen × [svb dt | uvb vocabId])         # dt vs prev t (m/10000)
}
              until EOF:                                 # S4: tracks
  [uvb rid]
  if dict-track: [uvb uniqN] [KIND|0x80] <fit bytes> (uniqN × [uvb len+utf8])
  else:          [uvb grid]  [KIND]        <fit bytes>
```

KIND byte values: 0 const, 1 lin, 2 quad, 3 runs, 4 knots, 5 cha, 6 segs.
Per-kind body (all numbers via svb unless noted):

| kind | body | regeneration (occ = role occurrence count) |
|---|---|---|
| const | `v` | `v` repeated occ times |
| lin | `v0, d` | `v0 + d*i` |
| quad | `v0, d1, c` | first differences of differences constant: `v+=d; d+=c` |
| runs | `uvb m`, m × (`uvb runLen`, `svb deltaV` prev-based) | expand runs |
| knots | `uvb m`, m × (`uvb indexDelta`, `svb valueDelta`) | linear interpolation between knots, `round()` banker's, knot endpoints exact |
| cha | `svb v0`, occ−1 × `svb delta` | cumulative sum (delta chain) |
| segs | `uvb mTokens`, each: 1B type (0 const / 1 poly) + `uvb runLen` + (poly: 1B order + order+1 svb seed; const: svb value) | Newton forward regen. **Not implemented in boot.js** |

Track ordering at encode time: sorted by `(rid, leaf-path tuple)`. Tracks are
consumed by boot.js until `p >= stream.length` (no track-count prefix).

### 7.2 `build/statics.txt` (38,446 B raw → 2,120 deflated)

Component-pool text of per-scene static fields. Format:
`lines ';' sep; '\x01'; pool '\x00' sep`. For each of 62 scenes: 7
comma-separated pool indices `(sc[0], sc[1], sc[2], sc[3], sc[4], sc[5],
sc[7])`; pool entries are `json.dumps(..., separators=(',',':'),
ensure_ascii=False)` of each unique component (after §5 invariant 5
normalization: record-covered defs replaced by scene-0 canonical). Runtime
boot parses: split at `\x01`, lines split `;`, pool split `\x00` + JSON.parse.

### 7.3 Verbatim JSON sections

- `pv.json` = `json.dumps(P['v'])` — 102,084 B raw → 3,708 deflated (biggest
  raw section; strongest compression lever candidate, see §11).
- `meta.json` = `{x,t,d,q,b,n}` (everything but s/v/a) — 4,564 B.
- `skeleton.json` = `{role: [leaf-path lists]}` in skeleton order — 2,033 B;
  boot rebuilds payload trees from it (`buildTemplate`).

### 7.4 `shell.html` (hand-written, 1,766 B — NOT generated)

DOM shell (doctype, styles, `<canvas>`, `#setup` panel with `#start`/`#fs`,
hidden `#gpu`), injected by boot via `document.write` **before** the engine
runs (fix #0003: the outer JS queries `#start`/`#setup`/`#gpu`/`canvas` and
throws if absent — it recreates the original page's DOM-injection behavior).
Tune its class names/ids against what `outer.js` queries if it is rewritten.

## 8. Audio side: blob + procedural worklet

`audio.pkl` provenance (regained): `audio_extract.py` extracts from the
original page `P.a = ['json', [w, song]]` — w = the 96,684-char atbs-v04
worklet source, song = full editor project JSON (deep-equal to
`build/project.json`). This makes the previously-orphan producer step
reproducible.

`audio.py` `blob()` layout (documented verbatim in its header; consumed
**verbatim** by `synth.js` class `D.st(u)`; 3,724 B raw → 1,929 deflated):

```text
[byte nScenes]  nScenes×7 bytes: bars, acidA+1, acidB+1, drums+1, stab+1,
                drone+1, fx+1 (idx −1 stored as 0)
[byte nAutoTracks] per track: [scene byte][key byte 0..9][nAnchors byte]
    per anchor: [pos byte 0..255][val byte = round(v·100) clamp 0..127]
    anchors = RDP-reduced (pos,val), eps 1.0 (0.01 units)
[acid blocks acidA0, acidB0, acidB1]: 64× [note byte note−24][flag bits
    1 gate|2 accent|4 slide|8 ratchet≥2] + [nP] sparse (pos, prob·100) where
    prob<1
[drums blocks 0..6]: [nRows]; per row: [rowIdx 0..11][8-byte on-bitmap
    LSB-first over 64 steps] + per on step: [vel·100 clamped 0..127 |
    0x80 if ratchet≥2] + [nP] sparse probs per NON-EMPTY row
[stab blocks 0..2 then fx blocks 0..2]: [8-byte on-bitmap] per on step:
    [note−24][chord][inversion][vel·100 clamped] then gate: [enabled][rate]
    [smooth·100] [4 bytes: 16 gate-steps packed 2 bits {0,.5,1}→{0,1,2}]
```

Automation key map: 0 acidA.cutoff 1 acidA.res 2 acidB.cutoff 3 acidB.res
4 fx.cutoff 5 fx.res 6 drone.cutoff 7 mixer.drone.level 8 mixer.stab.level
9 mixer.fx.level. Row idx: kick0 snare1 clap2 rim3 ch4 oh5 lt6 mt7 ht8
perc9 crash10 ride11.

`synth.js` (minified by `min_synth.js` → `synth.min.js`, 7,939 B → 3,649
deflated) is a **procedural remake** of the atbs-v04 worklet, speaking the
identical AudioWorklet message protocol so `outer.js` needs no changes:
`registerProcessor("atbs-v04", Lt)`; messages `{type:'state'|'play'|'stop'}`
(state carries the audio blob as the payload — boot puts it in
`P.a = ['json',[synthSrc, audioBlob]]`). Class `D.st(u)` parses the blob
above; `build()` schedules acid events (k=0), drum hits (k=1), stab/fx chord
notes (k=2), drone (k=3) with `sS = sr*60/135/4` per-step timing; voices
`v0..v3` implement acid bass, electronic-kit snare tables, poly chord stack,
drone — approximating the original engine's sound.

## 9. Container and bootstrap assembly (`v2/assemble.py`)

### 9.1 Container

**Per-section deflate.** The container is *not* deflated as a whole. It is:

```text
[u16 BE sectionCount][u32 LE len ×N][section body ×N]
```

where **each body is its own deflate-raw stream** (`zlib.compress(b, 9,
wbits=-15)`) and each `len` is the *compressed* length; there is no 4-byte
padding (no base85 alignment anymore). The page bootstrap splits by lens and
inflates each section separately before running boot.js. Measured today the
10 per-section streams sum to **63,484 deflated** vs 65,110 for the old
single stream — compressing separately avoids deflate's 32 KB window not
crossing section boundaries (the old §9.1 shipped 51,938 B per-section vs
52,792 single; same ~1.6–2 % effect, now realized instead of documented).

Section order (index is contractual between assemble.py and boot.js):

| idx | section | current raw | current deflate-alone |
|---|---|---|---|
| 0 | boot.min.js (terser of v2/boot.js) | 2,948 | 1,317 |
| 1 | outer.js verbatim (v2/build/outer.js) | 62,852 | 21,912 |
| 2 | synth.min.js text | 50,521 | 15,478 |
| 3 | stream.bin (§7.1) | 26,261 | 15,164 |
| 4 | statics.txt (§7.2) | 38,446 | 2,120 |
| 5 | pv.json (§7.3) | 102,084 | 3,708 |
| 6 | meta.json | 4,564 | 680 |
| 7 | audio.bin (§8) | 3,724 | 1,929 |
| 8 | skeleton.json | 2,033 | 216 |
| 9 | shell.html | 1,766 | 960 |

Sum of per-section deflates 63,484 + 42 B header = **63,526 container bytes**
(embedded same size, see §9.2), vs 65,110 for a single whole-container
stream. boot.js receives the plain (inflated) sections, exactly like before.

### 9.2 Page-safe embedding

The html declares **`<meta charset=windows-1252>`** (v13's own pre is reused
verbatim with only that attribute swapped). The payload rides the page
**nearly raw (1.0 bytes/byte)** inside a single-byte encoding window instead
of base85's 1.25.

**Why windows-1252 and not x-user-defined:** the first shipped build used
`charset=x-user-defined` (byte↔U+F780 arithmetic) — current Chrome does not
honor that label and decodes the file as cp1252 anyway (verified 2026-11-10
by probe: raw 0x80→U+20AC, 0x9F→U+0178, while undefined slots 0x81/0x8D/0x8F/
0x90/0x9D stay identity). The fix keeps the same layout but treats the DOM as
what it really is:

```text
cp1252 payload chars (DOM side, c = codePointAt(0)):
  c === 42 ('*')  -> escaped pair, byte = next char's code − 1, consume 2
  c in CP (27 chars from bytes 0x80..0x9F minus the 5 undefined slots)
                  -> byte = hex table H[2j..2j+1]    (embedded 54-char lookup)
  else            -> byte = c            (identity incl. 0x00..0x7F, 0xA0..0xFF
                                          and the 5 undefined cp1252 slots)
```

`CP` is embedded as a 27-char JS literal of the *raw* bytes 0x80..0x9F — at
runtime `C.charCodeAt(j)` reads exactly the chars cp1252 decoding produced
for those same bytes (self-referential but consistent). Both table lookups
are **bound-guarded** (`j<27`): without the guard, any payload byte outside
CP (e.g. 0x81) spins the `while` forever — this hang was caught by the first
headless debug run before shipping.

Transport: the payload lives inside a JS block comment
`/* PAYLOAD */` in the one `<script>`; the bootstrap reads it via
`document.currentScript.textContent`, slices between the first `/*` and last
`*/`, and applies the decode above.

Assemble escapes exactly the bytes the HTML tokenizer would corrupt, with 1
byte of overhead each (`'*' + (b+1)&0xFF`):

| escaped byte | why | count in real payload |
|---|---|---|
| 0x00 (NUL) | HTML tokenizer turns NUL into U+FFFD | 242 |
| 0x0D (CR) | tokenizer normalizes CR→LF (and CRLF→LF) | 244 |
| 0x2A (`*`) | would close the `*/` wrapper; also serves as escape marker | 226 |

Total +712 B on the real payload. Two script-data traps are *asserted
absent* at assemble time (probability ~2⁻³² per build of a hit):
`<!--` (enters script-data-escaped state) and `</script` (closes the
element). The marker-vs-payload scheme is unambiguous because the escaped
bytes `(b+1)&0xFF` are 0x01/0x0E/0x2B — all tokenizer-safe, outside the
marker itself.

This replaces the old base85 packing (Q10's v1-legacy splice). The v1 decoder
head (`function ca…})('BLOB','ALPHABET')`) is **no longer spliced** — the
shipped page carries its own ~630 B bootstrap:

```text
<v13 pre verbatim (charset=windows-1252)>
<script>
  (async()=>{ … unwrap comment -> bytes (marker pairs + cp1252 inverse table) ->
    split by u16/u32 lens -> per-section DecompressionStream("deflate-raw") -> S[] …
    await eval(TextDecoder().decode(S[0]))(S);
  })().catch(e=>document.body.textContent="BDE PACK ERROR · "+e)
/*
<BASE85 REPLACED BY: escaped binary container payload>
*/
</script>
<post verbatim>
```

The final file is written with `Path.write_bytes` — **no CRLF translation**
(the old 6-CRLF-pairs artifact of §9.2's `write_text` is gone). All page-side
code is ASCII-only except the 27-byte CP table literal (asserted). Verified
2026-11-10 in headless Chrome via an instrumented bootstrap: all 10 sections
round-trip byte-exact through the shipped decode+split+inflate path, and the
real page boots to the shell (setup screen, no BDE PACK error).

## 10. Runtime decoder (`v2/boot.js`, section 0 — source 3,798 B; shipped minified as `v2/build/boot.min.js`, 2,948 B)

boot.js is `(async S=>{…})`: an async IIFE receiving the section array.
Step order (must mirror §7 exactly):

1. Parse `S[4]` statics: split `\x01` → lines `;`/`,`→Numbers, pool `\x00`+JSON.parse.
2. Parse `S[8]` skeleton JSON.
3. Decode `S[3]` stream: uvb/svb readers over a byte array + banker's `R()`
   (matches Python `round()` for the knots regen); role table; per-scene
   cluster decode → `scenesRec[si] = [{r:rid, t:tm/1e4}]` while counting
   `occ[rid]` (occurrence counts needed before track regen).
4. Track loop until EOF: `rid, grid-or-uniqN, KIND byte (0x80 bit = dict)`;
   `regen(kind, occ[rid])` (kinds 0–5 only — see §6 note); dict tracks map
   indices over the trailing UTF-8 string table, numeric tracks divide by
   grid; each series appended to `leafVals[rid]` in skeleton-path order.
5. `buildTemplate(paths)` builds a payload tree per role (leaf = path index);
   `fill(node, vals, occIdx)` rebuilds payloads.
6. Scenes assembled as `[dur,int,defs…,lights…,cam…,bg…,records,flags]` with
   records `[0, roles[r], t, 0, payload]` (name const 0 — §5.4).
7. `P = {s, v:JSON(S[5]), a:['json',[S[2] text, S[7] blob]], x,t,d,q,b,n:meta}`
   — audio protocol per §8; outer.js sees `a[0]=='json'`.
8. `document.open(); document.write(S[9]); document.close()` — DOM shell first
   (fix #0003).
9. `new Function('P','(async()=>{const '+O.slice(1)+'})()')(P)` where
   `O = S[1]` text: `outer.js` is byte-exactly `js[vend:]` (everything after
   the `P` literal in the original page, INCLUDING the 8 inline shader string
   literals); it begins `,V="#version 300 es…"` so `O.slice(1)` drops the
   leading comma and `const ` re-opens the original `const P=…,V=…` statement
   with P injected as a parameter. The engine then runs exactly as in the
   original page.

## 11. Quality-degradation policy (MANDATORY companion to any change)

Project decision: every accepted choice that can degrade output quality vs the
original must be recorded BOTH in project memory AND in this document, with its
error bound, so future improvements can reason about the loss budget instead of
re-deriving it. The table below is that record (verified values, default
profile `--rdp=1 --quant=100 --tol=0.011`):

| # | Accepted choice | Where | Error bound (verified) |
|---|---|---|---|
| Q1 | Keyframe reduction: RDP eps **1.0 raw units** per (scene,role,path) drops 26,982→4,078 records | `compile.py reduce_records/rdp_local` | every dropped sample ≤ 1.0 raw unit from the kept-polyline blend (vertical metric = engine blend error). Worst observed render deviation from this alone: ≤1.0 units. |
| Q2 | Float tracks **re-quantized to grid 100** (`--quant=100`) | `compile.py` fits + `boot.js` divide by grid | rounding ≤ 0.005 per value; combined validator bound tol_abs=0.011, measured worst deviation **0.01** (0 hard mismatches). |
| Q3 | `knots` fits regenerate by **linear interpolation + banker's rounding** between knots | `regen_knots` / boot kind 4 | bounded by tol check per track (same 0.011); only 1 track uses knots now. |
| Q4 | Times stored as `round(t·10000)` | cluster streams | **lossless** — invariants prove t is an exact 4-dp literal. |
| Q5 | Record names → constant `0` | §5.4 | **lossless vs runtime** — names provably inert (never read by engine). Not a quality loss, but flagged: any future feature that parses record names would break. |
| Q6 | Static defs normalized to scene-0 canonical when role has records | §5.5 | **behavior-preserving, verified** (K() overrides base when target exists; 196/439 uncovered defs keep real values). |
| Q7 | Audio **full re-composition**: original atbs-v04 worklet (96,684 chars) + project JSON (308,452 B) replaced by procedural `synth.js` + blob | §8 | **Behavioral parity only** — no bound; sound is an approximation. User verifies by ear. The single biggest intentional loss. |
| Q8 | Audio quantization: automation anchors RDP eps 1.0 on `round(v·100)` (i.e. 0.01 units); vel/prob `round(v·100)` **clamped 0..127** (caps at 1.27); acid/drums `ratchet≥2` boolean flag (≥2 collapses); gate steps 2-bit {0,.5,1} | `audio.py blob()` | ≤0.005 per quantized value + clamp; ratchet values ≥2 indistinguishable; {0,.5,1} universe exact (asserted). |
| Q9 | Audio sparse-probability encoding: only `prob<1` entries stored (prob==1 implicit) | `audio.py` + `synth.js st()` | **lossless** over the assert-verified data universe. |
| Q10 | Container: **per-section deflate-raw streams** + windows-1252 page-safe embedding (cp1252 inverse table for 27 special bytes, NUL/CR/`*` escape pairs, §9.2) | `assemble.py` | **lossless** — all 10 sections verified byte-exact through the shipped decode+split+inflate path in headless Chrome; real page boots to shell. Supersedes the old whole-container deflate + base85 splice. x-user-defined variant was shipped once and FAILED in-browser (#0007): Chrome ignores that label. |

Improvement rules: (a) any new lossy knob gets a table row in memory + here;
(b) tightening a Q-bound buys size proportionally — budget headroom/deficit is
tracked in §12; (c) prefer raising grid/tol ONLY with a measured deviation
number.

## 12. Current state and open issues (as of 2026-11-10)

- `micidial_v2.html`: **65,288 B on disk — 248 B UNDER cap** (65,536).
  Profile: ported narrowed synth (§8, Q7) + per-section deflate container +
  windows-1252 embedding with cp1252 inverse table (§9). Earlier numbers in
  this section (67,041 B, "1,505 B over") were measured against the 7,939 B
  draft synth slot and were stale — the ported synth costs 15,478 deflated;
  with base85 the file would have been 82,425 B. Logged in memory as issue
  #0006; resolution = Q10 packing replacement + boot.min.js (user-approved
  decision, 2026-11-10). The x-user-defined variant of that decision shipped
  at 65,137 B and FAILED in-browser (#0007, Chrome ignores the label); the
  windows-1252 rebuild costs +151 B (inverse table + bounds) and was verified
  by browser-side per-section ledger + headless DOM boot.
  Earlier 9-section build (no shell section) was 65,361 B.
- Issue #0002 FIXED (memory, 2026-11-10): after wiping `v2/build/` (stale,
  mixed-generation inputs) and re-running the full §3 pipeline from scratch,
  `micidial_v2.html` loads with no `BDE PACK ERROR · TypeError: Failed to
  fetch` (user-verified). The pipeline wiring itself was not at fault.
- Issue #0003 FIXED: shell injection via section 9 + `document.write` (§7.4).
- Latent gap (§6): boot.js regen implements kinds 0–5; if `choose_fit` ever
  emits kind 6 (`segs`), the shipped page breaks at runtime. Currently safe
  (0 segs tracks) but unguarded. Logged in memory as open issue.
- Superseded design (memory): uniform ×4 subsampling and the global-timeline
  model (compiler.py/compiler2.py prototypes) — replaced by per-track RDP
  (Q1); prototypes removed 2026-11-10.

## 13. Improvement levers (analysis starting points)

1. ~~Per-section deflate~~ **CONSUMED 2026-11-10** — shipped (§9.1): the
   10-section container now compresses each section separately.
2. `pv.json` (102,084 raw / 3,708 deflated): P.v layer defs are record data
   the compiler could fold into the track model like statics (§5.5), or strip
   defaults as v1's MINIFY_PLAN did.
3. `segs` (kind 6) is never selected in the default profile (zero cost in the
   stream today), but boot.js `regen()` cannot decode it — either implement
   kind 6 in boot.js (≈15 lines) or forbid kind 6 in `choose_fit`. Closes
   latent gap #0005.
4. `object:9` (5,985 records ≈ 22% of records, cycle names) — candidate for a
   procedural loop rule instead of fitted curves (memory idea).
5. ~~Broader entropy coding behind the 64 KiB cap~~ — the cap is met
   (65,288 B, 248 B headroom) with the §9.2 embedding; revisit only if content
   grows.
6. Rerun knobs sweep: `--sweep` writes model32.pkl per profile; compare
   deflated stream + deviation per Q-bound before shipping.
7. `outer.js` (62.8 KB → 21.9 KB): only remaining non-remade big asset;
   terser savings were only ~300 chars pre-deflate, but shader-literal
   dedup vs the GLSL pool (8 literals) and cross-section pooling may help
   (try: shaders as their own section for pool isolation). Constraint: outer.js
   must stay byte-identical (user requirement) — only pooling/packing levers.

## 14. Reproduction appendix + repo inventory (post-cleanup)

ACTIVE pipeline files (keep, needed to rerun):
`v2/compile.py`, `v2/iface.py`, `v2/audio_extract.py` (new producer for
audio.pkl), `v2/audio.py`, `v2/min_synth.js` (uses root `node_modules`
terser), `v2/min_boot.js` (same, for boot.js — `compress:false` keeps the
eval completion arrow alive), `v2/synth.js`, `v2/boot.js`, `v2/assemble.py`,
`v2/build/shell.html` (hand-written input),
`original/uncompressed.html` (input), `original/PRESSURE_ATBS135_v13.html`
(pre/post donor), `micidial_v2.html` (output).

Deleted 2026-11-10 (superseded probes/prototypes/drafts + stale or
regeneratable build artifacts — each was superseded by an active file, see
§3/§6):
`v2/compiler.py`, `v2/compiler2.py`, `v2/build.py` (dead container prototype,
syntax error; replaced by `compile.py` + `assemble.py`), `v2/floor.py`, `v2/iface2.py`,
`v2/interp_err.py`, `v2/protocol.py`, `v2/shapes.py`, `v2/ties.py`–`v2/ties7.py`
(invariant probes whose invariants now live in §5 and compile.py asserts),
`v2/synth_draft{,2,3}.js.txt`, `v2/test_synth.js`, `v2/boot.min.js`,
`v2/unpack_orig.py`, `v2/__pycache__/`, root `nul` (0-byte shell artifact),
`v2/build/{engine.js,engine.min.js,project.json,audio_engine.js,audio_stats.txt,
audio_stats2.txt,debug_container.bin,model32.pkl,audio.pkl,audio.bin,stream.bin,
statics.txt,pv.json,meta.json,skeleton.json,synth.min.js,outer.js,
section_*.bin}` — all regenerated by the §3 commands.
`tools/{analyze_scene.py,budget.py,probe_inner.py,snap_count.py,scene_census.py}`
(one-shot probes / diagnostics; their findings live in §1/§4/§5/§8/§11 and
project memory; `scene_census.py`'s input `original/scene.json` was itself
generated from `uncompressed.html`, so both were removed together).
Kept in `tools/`: `decompress.py` only — the stage-1 decoder that regenerates
`original/uncompressed.html` from the v1 page if that pipeline input is ever
missing, and doubles as the container inspector for rerun verification.

`model32.pkl` and per-section debug dumps are gone; rerun `python
v2/compile.py --sweep` to regenerate `model32.pkl` for validation work.
Validation is built into compile.py's main run (regen-vs-kept deep compare,
prints `hard mismatches` + worst float deviation).
