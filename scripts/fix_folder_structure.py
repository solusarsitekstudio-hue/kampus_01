import os
import shutil

base = r"E:\WORKSPACE\KAMPUS_01\data\kurikulum\ARSITEKTUR"

# Move 2024\2025 -> 2024-2025
src = os.path.join(base, "2024", "2025")
dst = os.path.join(base, "2024-2025")
if os.path.exists(src):
    shutil.move(src, dst)
    print("Moved", src, "->", dst)

# Move 2025\2026 -> 2025-2026  
src = os.path.join(base, "2025", "2026")
dst = os.path.join(base, "2025-2026")
if os.path.exists(src):
    shutil.move(src, dst)
    print("Moved", src, "->", dst)

# Move 2026\2027 -> 2026-2027
src = os.path.join(base, "2026", "2027")
dst = os.path.join(base, "2026-2027")
if os.path.exists(src):
    shutil.move(src, dst)
    print("Moved", src, "->", dst)

# Clean up empty parent folders
for p in [os.path.join(base, "2024"), os.path.join(base, "2025"), os.path.join(base, "2026")]:
    if os.path.exists(p) and not os.listdir(p):
        os.rmdir(p)
        print("Removed empty:", p)

print("Done")