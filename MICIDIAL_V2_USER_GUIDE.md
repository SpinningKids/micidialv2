# Micidial v2 — AI Agent User Guide

**Purpose**: Compress a single-file WebGL demo HTML (like `original/uncompressed.html`, 5.36 MB) into a self-contained HTML page **< 64 KiB** that renders identically in a standard browser.

**Current status**: Pipeline produces `micidial_v2.html` at **65,288 B** (248 B under cap) with the default profile.

---

## 1. Prerequisites

- Python 3.10+ with standard library (`json`, `zlib`, `pickle`, `re`, `os`, `sys`)
- Node.js with `terser` in project root `node_modules` (for minification steps)
- Input file: `original/uncompressed.html` (5.36 MB) — NOT committed anymore;
  functionally regen it: `python tools/decompress_any.py
  original/PRESSURE_ATBS135_v13.html tmp/payload.js` then `node
  tools/unwrite_page.js tmp/payload.js original/uncompressed.html` (byte-exact
  copy stays in git history), or skip it entirely and build from any compressed
  ABTS page (§10b).

---

## 2. Pipeline Overview

The pipeline has **5 stages** (all idempotent, run from repo root):

```bash
# Stage 1: Scene compiler (RDP keyframe reduction + parametric track fitting)
python v2/compile.py --rdp=1 --quant=100 --tol=0.011

# Stage 1b: Extract outer engine JS (byte-exact slice after P literal)
python v2/iface.py

# Stage 2: Extract audio model from P.a → v2/build/audio.pkl
python v2/audio_extract.py

# Stage 3: Encode audio pattern blob → v2/build/audio.bin
python v2/audio.py

# Stage 4: Minify synth worklet (terser)
node v2/min_synth.js

# Stage 4b: Minify boot.js (terser, compress:false keeps eval completion)
node v2/min_boot.js

# Stage 5: Assemble container + windows-1252 embedding → micidial_v2.html
python v2/assemble.py
```

**Output**: `micidial_v2.html` in repo root.

---

## 3. Tuning Parameters (Compile Stage)

| Flag | Default | Meaning | Size/Quality Trade-off |
|------|---------|---------|------------------------|
| `--rdp` | `1.0` | Keyframe reduction tolerance (raw value units). Vertical metric = engine linear blend error. | ↑ → fewer keyframes, smaller stream, higher visual deviation. |
| `--quant` | `100` | Float track re-quantization grid (0 = exact). Values stored as `round(v * grid)`. | ↑ → smaller track data, rounding error ≤ 0.5/grid. |
| `--tol` | `0.011` | Max allowed deviation between regenerated and kept records (after grid rounding). | ↑ → allows cheaper fits (knots/segs), more deviation. |

**Current sweet spot** (verified 2026-11-10):
```bash
python v2/compile.py --rdp=1 --quant=100 --tol=0.011
```
- Keeps **4,078 / 26,982** records (RDP)
- Worst float deviation: **0.01** (bound 0.011)
- 0 hard mismatches
- Stream: 26,261 B raw → 15,164 B deflated

**Exact-replay mode** (bit-exact original records):
```bash
python v2/compile.py --rdp=0 --quant=0 --tol=0
```
→ ~157 KB projected (OVER budget)

---

## 4. What to Do If Output Exceeds 64 KiB

The assemble stage reports final size. If `micidial_v2.html` > 65,536 B:

### Quick levers (no code changes)

1. **Tighten RDP tolerance** (accept more visual loss):
   ```bash
   python v2/compile.py --rdp=2 --quant=100 --tol=0.011
   ```
   Each +1.0 eps typically saves ~1–2 KB in stream.

2. **Raise quantization grid**:
   ```bash
   python v2/compile.py --rdp=1 --quant=200 --tol=0.011
   ```
   Saves ~0.5–1 KB in track data.

3. **Raise validation tolerance** (allows cheaper fits):
   ```bash
   python v2/compile.py --rdp=1 --quant=100 --tol=0.02
   ```

4. **Run sweep to explore profiles**:
   ```bash
   python v2/compile.py --rdp=1 --quant=100 --tol=0.011 --sweep
   ```
   Writes `v2/build/model32.pkl` per profile; compare deflated stream sizes.

### Structural levers (require code changes)

| Lever | File | Est. Savings | Notes |
|-------|------|--------------|-------|
| Fold `P.v` layer defs into track model | `compile.py` | ~3 KB deflated | Largest raw section (102 KB → 3.7 KB deflated) |
| Implement `segs` (kind 6) in `boot.js` | `boot.js` + `compile.py` | ~1–2 KB | Currently never selected; latent runtime gap |
| Pool shader literals as separate section | `assemble.py` | ~1 KB | Outer.js has 8 inline GLSL strings |
| Procedural `object:9` cycle tracks | `compile.py` | ~2–3 KB | 5,985 records (22% of total) |

---

## 5. Key Files to Understand

| File | Role |
|------|------|
| `v2/compile.py` | Scene compiler: RDP reduction, track fitting, stream serialization |
| `v2/assemble.py` | Container packing, per-section deflate, windows-1252 embedding |
| `v2/boot.js` | Runtime decoder: inflates sections, rebuilds P, injects shell, runs engine |
| `v2/iface.py` | Extracts outer.js (byte-exact `js[vend:]` slice) |
| `v2/audio.py` + `v2/synth.js` | Procedural audio engine + quantized pattern blob |
| `MICIDIAL_V2.md` | Complete operating spec (wire formats, quality table, improvement levers) |

---

## 6. Validation

The compile stage **always runs full validation**:
```
validation: hard mismatches 0, worst float deviation 0.01 at (...) (tol 0.011)
```
- **Hard mismatches** = int/string/time differences (must be 0)
- **Worst float deviation** = max |regen - kept| after grid rounding (must ≤ `--tol`)

If validation fails, the profile is invalid.

---

## 7. Cleanup

After successful build, `v2/build/` contains only **`shell.html`** (hand-written input). All other files are regenerated by the pipeline. Delete them freely:

```bash
rm -rf v2/build/{stream.bin,statics.txt,pv.json,meta.json,skeleton.json,audio.bin,synth.min.js,outer.js,model32.pkl}
```

---

## 8. Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `BDE PACK ERROR · TypeError: Failed to fetch` | Stale `v2/build/` mixing generations | Wipe `v2/build/` (keep `shell.html`) and rerun full pipeline |
| `re.PatternError: unbalanced parens` | `iface.py` probe regex bug | Fixed in current version (issue #0004) |
| `Cannot set properties of null (onclick)` | Missing DOM shell injection | Fixed: boot.js now writes shell.html via `document.write` first (issue #0003) |
| `segs` kind selected but boot.js can't decode | `choose_fit` emits kind 6 | Either implement kind 6 in boot.js (~15 lines) or forbid in `choose_fit` |

---

## 9. Size Budget Breakdown (Current Profile)

| Section | Raw | Deflated | % of Container |
|---------|-----|----------|----------------|
| 0: boot.min.js | 2,948 | 1,317 | 2% |
| 1: outer.js | 62,852 | 21,912 | 34% |
| 2: synth.min.js | 50,521 | 15,478 | 24% |
| 3: stream.bin | 26,261 | 15,164 | 24% |
| 4: statics.txt | 38,446 | 2,120 | 3% |
| 5: pv.json | 102,084 | 3,708 | 6% |
| 6: meta.json | 4,564 | 680 | 1% |
| 7: audio.bin | 3,724 | 1,929 | 3% |
| 8: skeleton.json | 2,033 | 216 | <1% |
| 9: shell.html | 1,766 | 960 | 2% |
| **Container total** | | **63,526** | |
| **+ embedding overhead** | | | **65,288 B final** |

**Headroom**: 248 B under 65,536 cap.

---

## 10. Modifying for a New Input HTML

### 10a. Plain uncompressed page (`uncompressed.html`-shaped)

1. Replace `original/uncompressed.html` with the new file
2. Run the full pipeline (§2)
3. If output > 64 KiB, apply tuning (§4)
4. Validate visually in browser (no automated verifier per user directive)

### 10b. Any v1-compressed ABTS demo page (`PRESSURE_ATBS135_vN.html`)

Start from the compressed file; variant tools live in `tools/`, working outputs
in `tmp/` (repo hygiene):

1. **Unpack the v1 container**: base85 blob inside `<script>` → deflate-raw:
   `python tools/decompress_any.py original/PRESSURE_ATBS135_vN.html tmp/payload_vN.js`
2. **Recover the real page**. v13 AND v21+ payloads are a
   `document.open();document.write("…")` bootstrap — evaluate it with a stubbed
   DOM: `node tools/unwrite_page.js tmp/payload_vN.js tmp/uncompressed_vN.html`
   (Node's stub misses the browser's auto-inserted `<html>/<head>/<body>` tags —
   a 27 B gap harmless to the pipeline's anchors).
3. **Scope the change** vs the v13 baseline (regen it per §1 — the baseline file
   is not committed): `python tools/diff_pages.py <new> tmp/v13_page.html`
   prints per-P-key diffs, record counts, head/tail lengths. Anything `IDENTICAL`
   (in v21 that was `a,b,d,n,q,t,x`) needs no stage re-run.
4. **Compile from the variant without touching the baseline input** — all three
   source-reading stages take `--src=`:
   `python v2/compile.py --src=tmp/uncompressed_vN.html --rdp=1 --quant=100 --tol=0.011`
   `python v2/iface.py --src=tmp/uncompressed_vN.html`
   `python v2/audio_extract.py --src=tmp/uncompressed_vN.html`
5. **Audio**: re-run `v2/audio.py` + `v2/min_synth.js` only if `P.a` differs
   (diff step 3 tells you); otherwise the existing `audio.bin` is reusable.
6. **Runtime sections**: repo `v2/boot.js`/`v2/synth.js` may not match the
   shipped runtime (`v2/synth.js` is a stale draft — issue #0020). Safest: reuse
   byte-exact shipped sections: `python tools/extract_shipped.py micidial_v2.html tmp/shipped`,
   then copy `boot.min.js` + `synth.min.js` into `v2/build/`. (Regenerating
   `boot.min.js` with `node v2/min_boot.js` IS byte-exact; `outer.js` from
   `iface.py` is byte-exact by construction.)
7. **Shell**: extract the DOM head of the variant page — everything before
   `<script>` — to `tmp/shell_vN.html` (the hand-written `v2/build/shell.html`
   is v13-specific).
8. **Assemble**: `python v2/assemble.py --out=micidial_v2_vN.html --shell=tmp/shell_vN.html`
   (carrier pre/post + decoder code are harvested from `--carrier`, default
   `micidial_v2.html`).
9. **Over cap?** Sweep `--rdp` down-fit per §4 and ship the smallest eps with
   **0 hard mismatches** in compile.py's validation. Mandatory: record the
   measured deviation in MICIDIAL_V2.md §11 Q-table AND project memory
   (v21: eps 1.8 → 65,299 B, worst deviation 0.01; eps 1.0 was 2,026 B over,
   eps 1.75 missed by 25 B — see Q11).
10. **Verify offline** (browser check is user-side):
    `python tools/extract_shipped.py micidial_v2_vN.html tmp/vN_sections` — every
    decoded section must byte-match its `build/`/shell input (`cmp`), then
    `node tools/verify_page.js micidial_v2_vN.html tmp/shell_vN.html` — Chrome-
    faithful windows-1252 decode + carrier decoder + boot stub must print
    `shell written: EXACT`; the engine dying at WebGL offline is expected.

**Assumptions that must hold for the new input**:
- Same `P` structure: keys `x,t,d,q,b,n,s,v,a` with `s` = 62 scenes
- Same fixed payload skeleton per role (verified by `compile.py` asserts)
- Times on 4-decimal grid (`t = m/10000`)
- Audio contract: `P.a = ['json', [workletSrc, projectObj]]` with same pattern schema
- Roles are NOT fixed — compile.py handles any role set generically (v21 added
  `light:3`); only the skeleton per role must match.

If structure differs, you'll need to update probes in `compile.py` (walk_values, skeleton extraction, statics normalization).

---

## 11. Quick Reference Commands

```bash
# Full rebuild from clean (baseline v13 input)
rm -rf v2/build/*
python v2/compile.py --rdp=1 --quant=100 --tol=0.011
python v2/iface.py
python v2/audio_extract.py
python v2/audio.py
node v2/min_synth.js
node v2/min_boot.js         # stage 4b; byte-exact vs shipped boot.min.js
python v2/assemble.py

# Variant build from a compressed ABTS page (v21 example, full flow §10b)
python tmp/decompress_any.py original/PRESSURE_ATBS135_v21.html tmp/v21_payload.js
node tools/unwrite_page.js tmp/v21_payload.js tmp/uncompressed_v21.html
python tools/decompress_any.py original/PRESSURE_ATBS135_v13.html tmp/v13_payload.js
node tools/unwrite_page.js tmp/v13_payload.js tmp/v13_page.html
python tools/diff_pages.py tmp/uncompressed_v21.html tmp/v13_page.html
python v2/compile.py --src=tmp/uncompressed_v21.html --rdp=1.8 --quant=100 --tol=0.011
python v2/iface.py --src=tmp/uncompressed_v21.html
python v2/audio_extract.py --src=tmp/uncompressed_v21.html && python v2/audio.py
python tools/extract_shipped.py micidial_v2.html tmp/shipped
cp tmp/shipped/boot.min.js tmp/shipped/synth.min.js v2/build/
python -c "p=open('tmp/uncompressed_v21.html',encoding='utf-8').read();open('tmp/shell_v21.html','w',encoding='utf-8').write(p[:p.find('<script')])"
python v2/assemble.py --out=micidial_v2_v21.html --shell=tmp/shell_v21.html
python tools/extract_shipped.py micidial_v2_v21.html tmp/v21_sections   # cmp each section
node tools/verify_page.js micidial_v2_v21.html tmp/shell_v21.html       # shell EXACT

# Size check
ls -la micidial_v2*.html

# Explore profiles
python v2/compile.py --rdp=2 --quant=200 --tol=0.02 --sweep
```

---

*Generated from project memory (micidial_v2) and MICIDIAL_V2.md §3/§11/§12.*