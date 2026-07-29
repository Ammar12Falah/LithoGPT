#!/usr/bin/env python3
"""G2: template filler. Reads manuscript/manuscript.template.md, substitutes every
{{key}} or {{key:FORMATSPEC}} token with the FULL-PRECISION value stored under `key`
in analysis/FROZEN_RESULTS.json, rounding ONCE at injection time using Python's
format() (never re-rounds an already-rounded value, since the source is always full
precision). Writes manuscript/manuscript.md. Any token whose key is not in
FROZEN_RESULTS.json is left as {{MISSING:key}} in the output and reported on stderr --
no number is ever hand-typed into the manuscript; a missing key is a build failure to
fix in the template/JSON, not something to paper over by typing a literal."""
import json
import re
import sys

FROZEN_PATH = "analysis/FROZEN_RESULTS.json"
TEMPLATE_PATH = "manuscript/manuscript.template.md"
OUT_PATH = "manuscript/manuscript.md"

TOKEN_RE = re.compile(r"\{\{([a-zA-Z0-9_\-\.]+)(?::([^}]+))?\}\}")


def main():
    with open(FROZEN_PATH) as f:
        frozen = json.load(f)
    with open(TEMPLATE_PATH) as f:
        template = f.read()

    missing = []

    def repl(m):
        key, fmt = m.group(1), m.group(2)
        if key not in frozen:
            missing.append(key)
            return f"{{{{MISSING:{key}}}}}"
        val = frozen[key]["value"]
        if fmt:
            try:
                return format(val, fmt)
            except (ValueError, TypeError) as e:
                missing.append(f"{key} (format error: {e})")
                return f"{{{{FORMAT_ERROR:{key}}}}}"
        return str(val)

    filled = TOKEN_RE.sub(repl, template)
    with open(OUT_PATH, "w") as f:
        f.write(filled)

    if missing:
        print(f"FILL.PY: {len(missing)} token(s) unresolved (see {{{{MISSING:...}}}} markers in output):", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        sys.exit(1)
    n_tokens = len(TOKEN_RE.findall(template))
    print(f"FILL.PY: {n_tokens} token(s) substituted, 0 missing. Wrote {OUT_PATH}.")


if __name__ == "__main__":
    main()
