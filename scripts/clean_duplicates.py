import os
import shutil

base = r"E:\WORKSPACE\KAMPUS_01\data\kurikulum\ARSITEKTUR"

# Remove slash-format duplicates (keep dash-format)
for slash_fmt, dash_fmt in [
    ("2024/2025", "2024-2025"),
    ("2025/2026", "2025-2026"),
    ("2026/2027", "2026-2027"),
]:
    src = os.path.join(base, slash_fmt.replace("/", "\\"))
    dst = os.path.join(base, dash_fmt)
    if os.path.exists(src):
        # If dash format exists, merge unique MKs then remove
        if os.path.exists(dst):
            for item in os.listdir(src):
                s = os.path.join(src, item)
                d = os.path.join(dst, item)
                if not os.path.exists(d):
                    shutil.move(s, d)
                    print(f"Moved {item} -> {dst}")
        else:
            shutil.move(src, dst)
            print(f"Moved {slash_fmt} -> {dash_fmt}")

# Remove empty 2026/2027
empty_2026 = os.path.join(base, "2026", "2027")
if os.path.exists(empty_2026) and not os.listdir(empty_2026):
    os.rmdir(empty_2026)
    os.rmdir(os.path.join(base, "2026"))
    print("Removed empty 2026/2027")

# Remove empty 2025/2026
empty_2025 = os.path.join(base, "2025", "2026")
if os.path.exists(empty_2025) and not os.listdir(empty_2025):
    os.rmdir(empty_2025)
    os.rmdir(os.path.join(base, "2025"))
    print("Removed empty 2025/2026")

# Remove empty 2024/2025
empty_2024 = os.path.join(base, "2024", "2025")
if os.path.exists(empty_2024) and not os.listdir(empty_2024):
    os.rmdir(empty_2024)
    os.rmdir(os.path.join(base, "2024"))
    print("Removed empty 2024/2025")

print("Done cleaning duplicates")