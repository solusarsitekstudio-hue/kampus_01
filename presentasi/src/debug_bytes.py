with open('presentasi/src/deck.html', 'rb') as f:
    content = f.read()

old_bytes = (
    b"Prodi Arsitektur \xc2\xb7 F. Teknik & Desain</span><span><b>04 / 05</b></span></div>\n"
    b"</section>\n"
    b"\n"
    b"<!-- ================= SLIDE 5 ================= -->\n"
    b"<section class=\"slide\">\n"
    b"  <div class=\"grid\"></div><div class=\"vignette\"></div>\n"
    b"  <div class=\"edge top\"></div>\n"
    b"\n"
    b"  <div class=\"run\"><span>SIAK-KAPRODI</span><span class=\"dotline\"></span><span>04 \xe2\x80\x94 Otomasi & Skala</span></div>"
)

print("OLD BYTES LENGTH:", len(old_bytes))
print("OLD BYTES:")
print(repr(old_bytes))

# Check if it's in content
idx = content.find(old_bytes)
print("FOUND AT:", idx)

if idx == -1:
    # Try to find each line
    lines = old_bytes.split(b"\n")
    for i, line in enumerate(lines):
        pos = content.find(line)
        print(f"Line {i}: {pos} - {repr(line[:60])}")
    
    # Also check what the actual content looks like around the target
    target_idx = content.find(b"04 / 05</b></span></div>")
    print("\nActual content at target:")
    print(repr(content[target_idx:target_idx+len(old_bytes)]))