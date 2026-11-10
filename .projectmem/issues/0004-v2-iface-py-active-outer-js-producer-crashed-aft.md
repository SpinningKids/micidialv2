# #0004 v2/iface.py (active outer.js producer) crashed after writing outputs: probe regex 'on("ci|on(\'ci' has unbalanced parens -> re.PatternError breaks &&-chained pipeline runs

- 2026-11-10T00:35:33Z `issue`: v2/iface.py (active outer.js producer) crashed after writing outputs: probe regex 'on("ci|on(\'ci' has unbalanced parens -> re.PatternError breaks &&-chained pipeline runs [v2/iface.py]
- 2026-11-10T00:37:22Z `fix`: escaped parens in iface.py probe pattern -> r'on\("ci|on\(\'ci'; outputs were already written pre-crash; iface.py now exits 0 and pipeline &&-chain completes
