with open("src/neon_rings/transport.py", "r") as f:
    text = f.read()

import re
text = re.sub(r'^( {4})+', lambda m: '\t' * (len(m.group(0)) // 4), text, flags=re.MULTILINE)

with open("src/neon_rings/transport.py", "w") as f:
    f.write(text)
