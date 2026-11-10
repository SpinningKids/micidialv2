# #0002 micidial_v2.html fails to load: BDE PACK ERROR · TypeError: Failed to fetch. Root cause appears in assemble.py container/runtime wiring.

- 2026-11-09T20:47:05Z `issue`: micidial_v2.html fails to load: BDE PACK ERROR · TypeError: Failed to fetch. Root cause appears in assemble.py container/runtime wiring. [C:\Users\Luca\Dev\micidial_v2\micidial_v2.html]
- 2026-11-10T06:37:39Z `fix`: Closed by user confirmation: after 2026-11-10 rebuild from a clean v2/build/ via full pipeline rerun (compile.py -> iface.py -> audio_extract.py -> audio.py -> min_synth.js -> assemble.py), micidial_v2.html loads in the browser - 'BDE PACK ERROR · TypeError: Failed to fetch' no longer occurs. Cause: stale build inputs in v2/build/ had mixed generations; clean rebuild resolved it. [micidial_v2.html]
