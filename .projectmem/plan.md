# micidial_v2 — plan

> Editable **intent** file: ideas + plans — what we *mean to do*.
> This is NOT the event log. `events.jsonl` -> `summary.md` records what
> *happened*; this file records what we *intend*. The AI reads it at
> session start and edits it directly (like `PROJECT_MAP.md`): add ideas
> and plans, check items off, move done work down to Shipped. Plans are
> never logged as events.

## Ideas
_Loose thoughts, not yet committed to._
- Broader entropy coding later: DecompressionStream only offers gzip /
  deflate-raw / deflate — if deflate misses 64k, consider a tiny custom
  LZ/arithmetic decoder shipped in the bootstrap.
- object:9 (5,985 recs = 22%) looks like a beat-synced "cycle" flipbook —
  a pure procedural rule may replace it entirely.

## Active plans
_What we're working toward now. Use `- [ ]` / `- [x]` checklists._

### Stage 2 — micidial v2: Scene compiler (`original/uncompressed.html` → < 64 KiB)

Scope confirmed with user: **visual parity + procedural audio remake**
(full lossless audio is mathematically over budget: fixed floor 74.6 KB
deflate vs the 52.4 KB post-base85 cap).

- [x] Reverse-engineer + recover the uncompressed original (done in stage 1)
- [x] Measure anatomy + entropy floor (tools/budget.py, floor.py)
- [x] Map audio contract (v2/iface2.py): `atbs-v04` worklet, `St` core,
      `{state,play,stop}` message protocol
- [x] Extractor: uncompressed.html → scene model — v2/compile.py load()
      (json.JSONDecoder().raw_decode at `const P=`)
- [x] Compiler v3.3 (v2/compile.py): RDP keyframe reduction per
      (scene, role, leaf-path) (blend-domain, vertical metric = real
      render error; eps=1.0 raw units keeps 4,078/26,982 recs) + name
      collapse to const id 0 + grid=100 re-quantization + const/lin/quad/
      runs/cha/knots fits per track + cluster-stream vocab + component-pool
      statics (record-covered defs normalized to scene-0 canonical: 9.5k→
      2.1k defl). TOTAL 49,636 defl -> file ~63,245 < 65,536 OK
      (margin ~2.3 KB). Validation: 0 hard mismatches, worst float dev 0.01
      (tol 0.011). Supersedes uniform-x4-subsampling + global-timeline model.
- [ ] Assembler: shell + outer JS + shaders + binary stream (streams+tracks)
      + statics component pool + P.v/meta + synth + patterns in ONE
      deflate-raw -> base85 -> < 65,536 bytes; runtime decoder JS (~3 KB
      defl budget: uvb/svb parse, cluster->records, track regen, statics
      pool re-JSON) — must match compile.py stream format exactly
      (NO project-side verifier: user verifies the output themselves)
- [ ] Audio: extract pattern/state JSON from project (`AS` object);
      quantize; write `St_min`+`Lt` wrapper (~2-4 KB) speaking the same
      atbs-v04 protocol; P.a rebuilt in decoder (engine replaced by synth
      strings; project JSON slimmed to what outer.js reads)
- [ ] QUALITY-LOSS POLICY: every accepted design choice that can degrade
      output quality vs the original (keyframe RDP eps, float requant
      grid/tol, audio re-composition quantization/clamping, and any future
      knob) MUST be recorded in project memory (`add_decision`/`add_note`)
      AND listed with its error bound in the final design document
      (`MICIDIAL_V2.md`, "Quality degradation" section) so both stay in
      sync and the schema can be improved against known loss budgets.


## Next
_Queued, but not started._
- Profile object:9 + cycle-* records: find repetition period (beat grid),
  try emitting as generated loop instead of fitted curve.
- Project JSON (308 KB) slimming: names/IDs/defaults inside project — reuse
  same strip/quantize passes.

## Someday / maybe
- Audio-sample payload in engine (U=["kick",...]) — check how many KB of
  the 96.7 KB engine is base64 WAV and whether it survives as-is.

## Shipped
_Move completed plans here so the top stays about the future._
- Stage 1: recovered `original/uncompressed.html` via browser-native
  self-decoder (5,359,781 B, verified 0 console errors, WebGL OK).
