import sys

with open("modules/module_3d.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "st.set_page_config" in line:
        continue
    
    if line.startswith("import") or line.startswith("from") or line.startswith("import sys") or line.startswith("sys.path.append"):
        new_lines.append(line)
    elif "TRANSLATIONS" in line and "from translations" in line:
        new_lines.append(line)
    else:
        # We will wrap everything else in def run():
        pass

# Let's do it safer:
# Read all file, remove st.set_page_config
# Prepend `def run():` and indent everything below imports

with open("modules/module_3d.py", "r") as f:
    content = f.read()

import ast
try:
    tree = ast.parse(content)
except Exception as e:
    print(e)
    sys.exit(1)

out = []
in_func = False
for line in content.split("\n"):
    if "st.set_page_config" in line:
        continue
    if line.startswith("import ") or line.startswith("from ") or line.startswith("sys.path"):
        out.append(line)
    elif line.strip() == "import sys":
        out.append(line)
    else:
        if not in_func:
            out.append("\ndef run():")
            in_func = True
        
        # Indent the line
        if line == "":
            out.append("")
        else:
            out.append("    " + line)

with open("modules/module_3d.py", "w") as f:
    f.write("\n".join(out))

print("Rewrote module_3d.py")
