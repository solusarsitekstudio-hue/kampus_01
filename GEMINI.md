# ⚡ PROTOKOL PENUTUP RESPON WAJIB: QUICK ACCESS & DESKTOP DISPATCH (ADRIAN RIDHOA)

Setiap kali asisten menyelesaikan tugas yang melibatkan:
1. Web server / Web application / Dashboard (seperti port 40404 atau port lainnya)
2. Perubahan kode UI / Frontend / API
3. Pembuatan atau pembaruan berkas / file media / folder / snapshot

Asisten **WAJIB HUKUMNYA** melakukan dua hal ini di setiap akhir respon tanpa kecuali:

---

### 1. 🖥️ Proaktif Buka ke Monitor Pengguna via `windows-gui-display`
Jika ada URL server lokal atau folder yang baru diperbarui/dijalankan, asisten **WAJIB** langsung mengeksekusi script breakaway:
```powershell
& "C:\Users\Adrian Ridhoa\.gemini\config\skills\windows-gui-display\scripts\show_on_desktop.ps1" -Path "http://127.0.0.1:<PORT>"
```
Agar jendela browser / Explorer langsung nampak dan STAY aktif di layar monitor utama pengguna (`WinSta0\Default`).

---

### 2. 📋 Format Penutup Respon Wajib (Quick Access Box)
Di bagian paling akhir dari **SETIAP RESPON**, asisten **DILARANG KERAS** hanya menuliskan teks nomor port samar tanpa link. Asisten **WAJIB** menyertakan kotak akses cepat Markdown klik langsung dengan format baku:

```markdown
---
### ⚡ Quick Access & Live Verification
* 🌐 **Buka Aplikasi (Klik Langsung):** [http://127.0.0.1:<PORT>](http://127.0.0.1:<PORT>)
* 📁 **Folder Workspace:** [e:\WORKSPACE\<PROJECT>](file:///e:/WORKSPACE/<PROJECT>)
* 📸 **Folder Output / Snapshots:** [scratch/snapshots/](file:///e:/WORKSPACE/<PROJECT>/scratch/snapshots)
* 🖥️ **Status Desktop:** [Otomatis diluncurkan ke layar monitor via windows-gui-display]
---
```
Semua URL web harus berformat `[http://...](http://...)` dan semua folder/file lokal harus berformat link markdown GitHub `[label](file:///...)` agar satu kali klik langsung terbuka di browser/desktop Adrian.

---

### 3. 🎯 Adaptasi Kontekstual Mode Diskuss (Zero-Steal Focus & Context-Aware Links)
Khusus saat berada dalam sesi **Mode Diskuss konseptual** (membedah arsitektur, ide, atau berkas skill tanpa perubahan kode UI/server):
1. **Desktop Dispatch:** TAHAN eksekusi `show_on_desktop.ps1` agar tidak merebut fokus layar saat Adrian sedang membaca chat, kecuali jika Adrian secara eksplisit meminta membuka browser atau ada pembaruan UI nyata.
2. **Quick Access Kontekstual:** Format kotak penutup disesuaikan dengan topik yang sedang dibahas:
   ```markdown
   ---
   ### ⚡ Quick Access & Contextual References
   * 📄 **File Catatan Diskusi:** [.diskuss/diskuss_XX.db](file:///e:/WORKSPACE/<PROJECT>/.diskuss/diskuss_XX.db)
   * 🛠️ **Berkas/Skill yang Dibahas:** [<nama_file>](file:///<path>)
   * 🌐 **Server Lokal (Standby):** [http://127.0.0.1:<PORT>](http://127.0.0.1:<PORT>)
   * 🖥️ **Status Desktop:** [Fokus layar tetap pada obrolan / Bebas distraksi pop-up]
   ---
   ```
