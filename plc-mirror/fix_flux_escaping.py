import pathlib
import re

p = pathlib.Path(__file__).resolve().parent / "infra" / "grafana" / "provisioning" / "dashboards" / "json" / "oee_starter_corrigido_clean.json"
text = p.read_text(encoding="utf-8")

# We found many Flux query strings inside JSON over-escaped like \\\"processo\\\".
# Grafana sends the *decoded* JSON string to Influx; if we keep the extra backslashes,
# Flux sees \\"processo\\" instead of "processo" and can fail parsing.

before = text.count('\\\\\\"')

# Reduce 3-backslash-escaped quotes (\\\") down to regular JSON-escaped quotes (\").
# In the raw JSON file that means replacing \\\" with \".
fixed = text.replace('\\\\\\"', '\\"')

# Safety: collapse any remaining 4-backslash sequences directly before a quote.
fixed = re.sub(r'\\{4}"', r'\\"', fixed)

after = fixed.count('\\\\\\"')

if fixed != text:
    p.write_text(fixed, encoding="utf-8", newline="")
    print(f"WROTE {p}")
else:
    print(f"NO_CHANGE {p}")

print("over-escaped occurrences before:", before)
print("over-escaped occurrences after:", after)
