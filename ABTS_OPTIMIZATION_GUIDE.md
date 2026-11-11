# ABTS → Micidial v2 Compression Optimization Guide

**Audience**: AI agentic coder developing **ABTS** (the demo system that generates the uncompressed HTML files micidial v2 compresses).

**Goal**: Modify ABTS so its output HTML is **maximally compressible by micidial v2**, minimizing the final `micidial_v2.html` size while preserving visual/audio fidelity.

**Context**: Micidial v2 is a *lossy semantic compressor*. It doesn't just zip bytes — it **re-models** your animation data as parametric tracks. The more your data follows the patterns micidial v2 expects, the smaller the output.

---

## 1. What Micidial v2 Actually Compresses

Micidial v2 targets **three massive data blobs** in your HTML:

| Source | Original Size | Micidial v2 Strategy |
|--------|---------------|----------------------|
| `P.s` snapshots (26,982 records) | ~5 MB | **RDP keyframe reduction** → parametric fits (const/lin/quad/runs/cha/knots/segs) |
| Audio worklet (96 KB) + project JSON (308 KB) | ~400 KB | **Procedural synth remake** + quantized pattern blob (3.7 KB) |
| Outer engine JS + GLSL shaders | ~91 KB | Kept verbatim, deflate-raw per-section |

**Everything else** (shell, static config, layer defs `P.v`) is small or already compresses well.

---

## 2. Structural Invariants Micidial v2 Relies On

**Your ABTS output MUST preserve these** (verified zero violations in current data):

| # | Invariant | Why It Matters |
|---|-----------|----------------|
| 1 | **Times are exact 4-decimal literals**: `t = m/10000` | Enables lossless time storage as `round(t*10000)` + delta encoding |
| 2 | **Equal-time record clusters**: records at same `t` are adjacent; role sequence repeats from small per-scene vocabulary | Cluster stream encodes role sequences as vocab IDs + time deltas (tiny) |
| 3 | **Fixed payload skeleton per role**: every record of role `R` has identical leaf-path structure; no integer-valued floats | Track fitting works per `(role, leaf-path)`; typing is derivable |
| 4 | **Record names are inert**: never read by engine (matched patterns like `pressure-sculpture-…`, `cycle-…` but ignored) | Names replaced by constant `0` — saves all name bytes |
| 5 | **Statics redundancy**: scene-level defs duplicate scene-0 canonical when role has snapshot records | Replaced by scene-0 ref (196/439 exceptions keep real values) |

**Breaking any of these forces micidial v2 to fall back to less efficient encoding or lose compression.**

---

## 3. ABTS Output Optimizations (Ranked by Impact)

### 🥇 Tier 1: Animation Data (`P.s`) — Biggest Lever

#### 3.1 Keep Times on 1/10000 Grid
```javascript
// GOOD: exact 4-decimal literal
const t = 1.2345;

// BAD: floating point drift
const t = 1.23456789;  // micidial must quantize → deviation
```
**Reason**: Times stored as `round(t*10000)` → exact recovery. Off-grid times force quantization error.

#### 3.2 Minimize Unique Keyframes per (Scene, Role, Leaf-Path)
Micidial v2 runs **RDP (Ramer-Douglas-Peucker)** per `(scene, role, leaf-path)` with vertical tolerance `--rdp` (default 1.0 raw units).

**What helps**:
- **Smooth curves** (sinusoidal, exponential, polynomial) → fit as `cha` (delta chain) or `lin`/`quad` — extremely compact
- **Piecewise-constant** (step functions) → fit as `runs` (run-length encoding)
- **Linear ramps** → fit as `lin` (2 numbers for entire track)

**What hurts**:
- **High-frequency noise/jitter** → RDP keeps many keyframes
- **Chaotic per-frame values** → no fit wins, falls back to `const` per keyframe (expensive)

**ABTS action**: Generate animation curves analytically where possible. Avoid per-frame randomness unless it's a controlled noise function that compresses as `cha`.

#### 3.3 Reduce Record Count at Source
Current: 26,982 records → 4,078 kept (RDP eps=1.0).

If ABTS emits **fewer snapshot records initially**, RDP has less to reduce and the stream is smaller.

- **Consolidate equal-time records**: One record per target per timestamp (already true by invariant #2)
- **Remove redundant static snapshots**: If a property doesn't change across a scene, don't emit records for it — let the static def carry it
- **Merge roles where possible**: Fewer roles = smaller role table + vocab + track count

#### 3.4 Favor Compressible Value Patterns

| Pattern | Best Fit | Bytes per Sample (est.) |
|---------|----------|------------------------|
| Constant | `const` | ~0.1 |
| Linear ramp | `lin` | ~0.2 |
| Quadratic | `quad` | ~0.3 |
| Smooth drift (sin, exp, smooth noise) | `cha` (delta chain) | ~0.5–1 |
| Step function | `runs` | ~0.5–2 |
| Smooth curve with inflections | `knots` (RDP on index) | ~1–3 |
| **High-frequency noise** | *none* (falls back) | **5+** |

**ABTS guideline**: Design animations using the left-side patterns. If you need "organic" variation, use **low-frequency noise** (compresses as `cha`) not per-frame random.

---

### 🥈 Tier 2: Audio Data (`P.a`) — Second Biggest Lever

Micidial v2 **completely replaces** your audio worklet + project JSON with a procedural synth (`v2/synth.js`) + quantized pattern blob (`audio.bin`, 3.7 KB).

**The contract ABTS must honor**:
```javascript
P.a = ['json', [workletSourceString, projectObject]];
```
- `workletSourceString` — any string (micidial ignores content, replaces with its own synth)
- `projectObject` — must match the **schema expected by `v2/audio_extract.py`**

#### Schema for `projectObject` (from `audio_extract.py`):
```json
{
  "scenes": [
    {
      "bars": 1,
      "patterns": {
        "acidA": [patternDef, patternDef, ...],
        "acidB": [patternDef, patternDef, ...],
        "drums": [patternDef, patternDef, ...],
        "stab": [patternDef, patternDef, ...],
        "drone": [patternDef, patternDef, ...],
        "fx": [patternDef, patternDef, ...]
      },
      "automation": {
        "acidA.cutoff": [floatArray],
        "acidA.res": [floatArray],
        "acidB.cutoff": [floatArray],
        "acidB.res": [floatArray],
        "fx.cutoff": [floatArray],
        "fx.res": [floatArray],
        "drone.cutoff": [floatArray],
        "mixer.drone.level": [floatArray],
        "mixer.stab.level": [floatArray],
        "mixer.fx.level": [floatArray]
      }
    }
  ],
  "patterns": { ... }  // full pattern library referenced by scenes
}
```

#### Pattern Definitions (must match `audio.py` expectations):

**Acid (acidA/acidB)**: 64 steps each
```json
{
  "steps": [
    {"note": 60, "gate": true, "accent": false, "slide": false, "ratchet": 1, "prob": 1.0, "lock": -1}
  ]
}
```
- `note`: 24–152 (stored as `note-24` in 1 byte)
- `ratchet`: ≥2 → boolean flag (collapses to 1 bit)
- `prob`: <1 → stored as sparse (pos, prob×100); ==1 → implicit (not stored)

**Drums**: 12 rows × 64 steps
```json
{
  "rows": {
    "kick": [{"on": true, "vel": 0.8, "ratchet": 1, "prob": 1.0}, ...],
    "snare": [...], ...
  }
}
```
- Row order fixed: `kick,snare,clap,rim,ch,oh,lt,mt,ht,perc,crash,ride`
- `vel`: ×100 clamped 0..127
- `ratchet`≥2 → bit flag in vel byte

**Stab/FX**: 64 steps + gate
```json
{
  "steps": [{"on": true, "note": 60, "chord": 0, "inversion": 0, "vel": 0.8, "prob": 1.0}, ...],
  "gate": {"enabled": true, "rate": 4, "smooth": 0.5, "steps": [0, 0.5, 1, ...]}  // 16 steps, 2-bit each
}
```

#### ABTS Audio Optimization Tips:

| Change | Effect |
|--------|--------|
| **Reduce pattern count** (fewer unique acid/drums/stab/fx/drone patterns) | Smaller scene table (7 bytes/scene) |
| **Use `prob=1.0` wherever possible** | Implicit — not stored in blob |
| **Limit automation tracks** (10 keys max) | Each track = scene+key+anchors; RDP reduces anchors |
| **Keep automation smooth** | RDP eps=1.0 on `round(v*100)` → fewer anchors kept |
| **Avoid ratchet ≥ 3** | Collapses to boolean; no distinction stored |
| **Gate steps only from {0, 0.5, 1}** | 2-bit packing exact; other values quantized |

**Critical**: The procedural synth (`v2/synth.js`) is a **remake**, not a perfect replica. Audio parity is **by ear only** (user verifies). If ABTS changes the sound design drastically, micidial v2's synth may not match — but the blob size stays tiny regardless.

---

### 🥉 Tier 3: Outer Engine JS + Shaders — Fixed Cost

Micidial v2 keeps `outer.js` **byte-identical** (62.8 KB → 21.9 KB deflated). Only packing levers apply.

**What ABTS can do**:
- **Deduplicate GLSL shader strings**: Current outer.js has 8 inline shader literals. If ABTS can share them (e.g., common preamble), terser/deflate compresses better.
- **Minify before handing to micidial**: Micidial runs terser on boot.js/synth.js but **not** on outer.js (user requirement: byte-identical). Pre-minify your engine code.
- **Avoid large string literals** in engine code that aren't shaders.

**What ABTS cannot change**: The outer.js slice is `js[vend:]` — everything after `const P=` in the original script. This includes the engine bootstrap, render loop, and all shader strings.

---

### Tier 4: Layer Defs (`P.v`) — 102 KB Raw → 3.7 KB Deflated

`P.v` = 62 layer-def records. Currently stored verbatim as JSON (`pv.json`).

**Optimization**: If ABTS makes layer defs **derivable from scene data** (like statics), micidial v2 could fold them into the track model. Currently they're opaque JSON.

**ABTS action**: Use consistent, minimal layer def structures. Avoid per-layer unique IDs or large nested objects.

---

## 4. Anti-Patterns That Kill Compression

| Anti-Pattern | Why It Hurts | Fix |
|--------------|--------------|-----|
| Per-frame random values (`Math.random()` per frame) | No parametric fit matches → falls back to per-keyframe storage | Use seeded noise function (compresses as `cha`) |
| Unique record names per frame | Names already dropped (invariant #4), but if engine starts reading them, breaks | Keep names derivable or constant |
| Time values off 1/10000 grid | Forces quantization → deviation | Snap times to 0.0001 grid |
| Varying payload skeleton per record of same role | Breaks invariant #3 → compile.py asserts fail | Fixed schema per role |
| Many unique static defs per scene | Statics normalization only works when defs match scene-0 | Reuse scene-0 defs where possible |
| Large inline JSON blobs in outer.js | Not recompressed by micidial | Move to `P` structure where micidial can model it |

---

## 5. Validation Checklist for ABTS Output

Before handing HTML to micidial v2, verify:

```bash
# 1. Times on grid
grep -oP '(?<=time: )[\d.]+' output.html | while read t; do
  python -c "assert abs(float('$t')*10000 - round(float('$t')*10000)) < 1e-6"
done

# 2. Role set matches expected
# Expected: background, camera, light:1, light:2, object:1..10

# 3. Payload skeleton constant per role
# (compile.py will assert this)

# 4. Audio contract present
# P.a = ['json', [string, object]]

# 5. Scene count = 62 (or update micidial's scene loop)
```

---

## 6. If You Change ABTS Output Structure

**Micidial v2 probes are baked into `compile.py` asserts**. If you change:
- Number of scenes
- Role names/counts
- Payload skeleton per role
- Audio project schema

You **must update** `v2/compile.py` and `v2/audio_extract.py` accordingly. The probes (`walk_values`, `skeleton` extraction, `reduce_records` grouping) assume the current structure.

**Key locations in `compile.py` to update**:
- Line 54: `load()` — parsing `const P=` (robust, uses `raw_decode`)
- Line 119–124: Scene structure unpacking
- Line 507–538: `reduce_records()` — groups by role, expects `r[1]` = role string
- Line 605–619: Skeleton extraction — `walk_values(rs[0][4])`
- Line 726–792: Statics normalization — expects `sc[2]=objectDefs`, `sc[3]=lights`, etc.

**Key locations in `audio_extract.py`**:
- Line 178: `song = P['a'][1][1]` — expects project object at that path
- Line 83–94: Automation key list (must match `audio.py`)

---

## 7. Size Budget Targets for ABTS

| Component | Current micidial v2 cost | Target for ABTS changes |
|-----------|--------------------------|-------------------------|
| Scene stream (stream.bin) | 15,164 B deflated | < 12 KB with smoother curves |
| Audio blob (audio.bin) | 1,929 B deflated | Already minimal |
| Outer.js | 21,912 B deflated | Pre-minify → ~18 KB |
| Synth.min.js | 15,478 B deflated | Fixed (procedural remake) |
| Statics | 2,120 B deflated | Reduce unique defs |
| P.v (pv.json) | 3,708 B deflated | Fold into tracks if possible |
| **Total container** | **63,526 B** | **< 55 KB** (gives margin) |

---

## 8. Quick Experiment: Test Compression Locally

If you have micidial v2 repo:
```bash
# 1. Place your ABTS output as original/uncompressed.html
cp /path/to/abts/output.html original/uncompressed.html

# 2. Run pipeline
python v2/compile.py --rdp=1 --quant=100 --tol=0.011
python v2/iface.py
python v2/audio_extract.py
python v2/audio.py
node v2/min_synth.js
node v2/min_boot.js
python v2/assemble.py

# 3. Check size
ls -la micidial_v2.html

# 4. Check validation output from compile.py
#    "validation: hard mismatches 0, worst float deviation X.XX (tol 0.011)"
```

---

## 9. Summary: ABTS Developer Cheat Sheet

| Do | Don't |
|----|-------|
| ✅ Emit times as `m/10000` exactly | ❌ Use `Date.now()` or floating-point accumulation |
| ✅ Generate smooth parametric curves (sin, exp, polynomial) | ❌ Per-frame `Math.random()` |
| ✅ Reuse static defs from scene 0 | ❌ Unique defs per scene for same role |
| ✅ Keep payload skeleton identical per role | ❌ Conditional payload fields |
| ✅ Use `prob=1.0` for deterministic patterns | ❌ Sparse probabilities everywhere |
| ✅ Limit automation to 10 keys, keep smooth | ❌ Per-frame automation envelopes |
| ✅ Pre-minify outer engine JS | ❌ Ship unminified engine with large string literals |
| ✅ Match audio project schema exactly | ❌ Add custom fields to pattern defs |

---

*Generated from micidial_v2 project memory and MICIDIAL_V2.md §5/§6/§8/§11/§13. The invariants in §5 are enforced by `compile.py` asserts — violating them breaks the pipeline.*