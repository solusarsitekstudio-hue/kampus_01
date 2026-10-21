import os
import shutil

base = r"E:\WORKSPACE\KAMPUS_01\data\kurikulum\ARSITEKTUR"

# Move 2025\2026\GANJIL -> 2025-2026\GANJIL
src = os.path.join(base, "2025", "2026", "GANJIL")
dst = os.path.join(base, "2025-2026", "GANJIL")
if os.path.exists(src):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.move(src, dst)
    print("Moved", src, "->", dst)

# Move 2025\2026\GENAP -> 2025-2026\GENAP (but only the new MKs)
src = os.path.join(base, "2025", "2026", "GENAP")
dst = os.path.join(base, "2025-2026", "GENAP")
if os.path.exists(src):
    # Move individual MK folders that don't exist in dst
    if not os.path.exists(dst):
        os.makedirs(dst)
    for mk in os.listdir(src):
        s = os.path.join(src, mk)
        d = os.path.join(dst, mk)
        if not os.path.exists(d):
            shutil.move(s, d)
            print("Moved MK", mk, "->", dst)
    # Remove empty src
    if not os.listdir(src):
        os.rmdir(src)
        print("Removed empty", src)

# Move 2026\2027\GANJIL -> 2026-2027\GANJIL
src = os.path.join(base, "2026", "2027", "GANJIL")
dst = os.path.join(base, "2026-2027", "GANJIL")
if os.path.exists(src):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.move(src, dst)
    print("Moved", src, "->", dst)

# Move 2026\2027\GENAP -> 2026-2027\GENAP
src = os.path.join(base, "2026", "2027", "GENAP")
dst = os.path.join(base, "2026-2027", "GENAP")
if os.path.exists(src):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.move(src, dst)
    print("Moved", src, "->", dst)

# Clean up nested 2025-2026\2026
nested = os.path.join(base, "2025-2026", "2026")
if os.path.exists(nested):
    for item in os.listdir(nested):
        s = os.path.join(nested, item)
        d = os.path.join(base, "2025-2026", item)
        if os.path.exists(d):
            shutil.rmtree(d)
        shutil.move(s, d)
        print("Moved nested", item, "->", d)
    os.rmdir(nested)
    print("Removed nested", nested)

# Clean up empty parent folders
for p in [
    os.path.join(base, "2024"),
    os.path.join(base, "2025"),
    os.path.join(base, "2026"),
    os.path.join(base, "2025-2026", "2026"),
]:
    if os.path.exists(p) and not os.listdir(p):
        os.rmdir(p)
        print("Removed empty:", p)

# Verify
print("\nFinal structure:")
for root, dirs, files in os.walk(base):
    level = root.replace(base, "").count(os.sep)
    indent = "  " * level
    print(f"{indent}{os.path.basename(root)}/")
    if level >= 2:
        for f in files:
            print(f"{indent}  {f}")

print("\nDone")