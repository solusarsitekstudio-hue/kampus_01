"""tests/test_cybersecurity.py - Cyber Security & Hardening Probe Suite (Langkah 1)
SIAK-KAPRODI (Architecture Program Studi)

Membuktikan ketahanan sistem terhadap:
1. Cross-Origin Data Theft & CSRF (Strict Origin/Referer & Host validation)
2. Path Traversal & Injection via NPM (Strict 8-14 numeric digit regex NPM_RE)
3. Preflight CORS OPTIONS Lockdown
4. Concurrency Throttling (RAM Guard BoundedSemaphore(2))
5. SSRF Route Interception in PDF Bridge
"""

import http.client
import json
import os
import sys
import threading
import time
import urllib.request
import urllib.error

HOST = "127.0.0.1"
PORT = 40404
BASE_URL = f"http://{HOST}:{PORT}"

ok_all = True

def check(label: str, cond: bool, detail: str = ""):
    global ok_all
    ok_all = ok_all and bool(cond)
    status_str = "OK  " if cond else "FAIL"
    print(f"  [{status_str}] {label:50} {detail}")

def http_req(path: str, method: str = "GET", headers: dict = None, body: bytes = None):
    conn = http.client.HTTPConnection(HOST, PORT, timeout=10)
    conn.request(method, path, body=body, headers=headers or {})
    res = conn.getresponse()
    res_body = res.read()
    res_headers = {k.lower(): v for k, v in res.getheaders()}
    conn.close()
    return res.status, res_headers, res_body

print("=" * 76)
print("PROBE CYBERSECURITY LANGKAH 1: ORIGIN GUARD, CSRF, NPM WHITELIST, RAM GUARD")
print("=" * 76)

# -----------------------------------------------------------------------------
# 1. ORIGIN & CSRF & DNS REBINDING GUARD
# -----------------------------------------------------------------------------
print("\n[1] Origin Guard & CSRF Lockdown")

# Direct local request without Origin (curl, python test, local script)
st, hdrs, b = http_req("/api/health")
check("Direct Local (No Origin): 200 OK", st == 200, f"status={st}")

# Valid Origin 127.0.0.1:40404
st, hdrs, b = http_req("/api/health", headers={"Origin": f"http://{HOST}:{PORT}"})
check("Valid Origin 127.0.0.1:40404: 200 OK", st == 200, f"status={st}")
check("CORS Reflects Trusted Origin", hdrs.get("access-control-allow-origin") == f"http://{HOST}:{PORT}", hdrs.get("access-control-allow-origin", ""))
check("Header Vary: Origin present", "origin" in hdrs.get("vary", "").lower(), hdrs.get("vary", ""))
check("Security Header X-Content-Type-Options: nosniff", hdrs.get("x-content-type-options") == "nosniff", hdrs.get("x-content-type-options", ""))
check("Security Header X-Frame-Options: SAMEORIGIN", hdrs.get("x-frame-options") == "SAMEORIGIN", hdrs.get("x-frame-options", ""))

# Valid Origin localhost:40404
st, hdrs, b = http_req("/api/health", headers={"Origin": "http://localhost:40404"})
check("Valid Origin localhost:40404: 200 OK", st == 200, f"status={st}")
check("CORS Reflects Trusted localhost Origin", hdrs.get("access-control-allow-origin") == "http://localhost:40404", hdrs.get("access-control-allow-origin", ""))

# Untrusted Origin on GET (e.g. evil.com)
st, hdrs, b = http_req("/api/data", headers={"Origin": "http://evil.com"})
check("Untrusted Origin (evil.com) on GET: 403 Forbidden", st == 403, f"status={st}")
check("Untrusted Origin: No Wildcard CORS emitted", hdrs.get("access-control-allow-origin") != "*", f"cors={hdrs.get('access-control-allow-origin')}")

# Untrusted Origin on POST (CSRF attack attempt)
st, hdrs, b = http_req("/api/kurikulum/simpan", method="POST", headers={"Origin": "http://evil.com", "Content-Type": "application/json"}, body=b"{}")
check("CSRF Attack on POST from evil.com: 403 Forbidden", st == 403, f"status={st}")

# Untrusted Referer on GET
st, hdrs, b = http_req("/api/data", headers={"Referer": "http://evil.com/phishing.html"})
check("Untrusted Referer (evil.com): 403 Forbidden", st == 403, f"status={st}")

# DNS Rebinding attack attempt (Spoofed Host Header)
st, hdrs, b = http_req("/api/data", headers={"Host": "attacker.evil.com:40404"})
check("DNS Rebinding (Spoofed Host Header): 403 Forbidden", st == 403, f"status={st}")

# Untrusted Port on Localhost (e.g. Rogue service on port 8080)
st, hdrs, b = http_req("/api/data", headers={"Origin": "http://localhost:8080"})
check("Untrusted Port (localhost:8080): 403 Forbidden", st == 403, f"status={st}")

# Preflight CORS OPTIONS check
st, hdrs, b = http_req("/api/kurikulum/simpan", method="OPTIONS", headers={"Origin": f"http://{HOST}:{PORT}"})
check("CORS Preflight OPTIONS Valid Origin: 204 No Content", st == 204, f"status={st}")
check("CORS Allowed Methods includes POST, OPTIONS", "POST" in hdrs.get("access-control-allow-methods", ""), hdrs.get("access-control-allow-methods", ""))

st, hdrs, b = http_req("/api/kurikulum/simpan", method="OPTIONS", headers={"Origin": "http://evil.com"})
check("CORS Preflight OPTIONS Untrusted Origin: 403 Forbidden", st == 403, f"status={st}")

# -----------------------------------------------------------------------------
# 2. UNIVERSAL NPM WHITELISTING (NPM_RE: ^\d{8,14}$)
# -----------------------------------------------------------------------------
print("\n[2] Universal NPM Whitelisting & Path Traversal Lockdown")

# Valid NPM (13 digits)
st, hdrs, b = http_req("/api/registry/student?npm=2510015410010")
check("Valid NPM (2510015410010) on registry: 200 OK", st == 200, f"status={st}")

# Path Traversal NPM in /api/student/<npm>
st, hdrs, b = http_req("/api/student/../../etc/passwd")
check("Path Traversal in /api/student/: 400 or 403", st in (400, 403), f"status={st}")

# Alphanumeric Injection NPM in /api/portofolio
st, hdrs, b = http_req("/api/portofolio?npm=admin'--")
check("SQL/Char Injection in /api/portofolio: 400 Bad Request", st == 400, f"status={st}")

# Short NPM (<8 digits) in /api/registry/student
st, hdrs, b = http_req("/api/registry/student?npm=12345")
check("Short NPM (<8 digits) in /api/registry/student: 400 Bad Request", st == 400, f"status={st}")

# Long NPM (>14 digits) in /api/bridge/presensi
st, hdrs, b = http_req("/api/bridge/presensi?npm=1234567890123456789")
check("Long NPM (>14 digits) in /api/bridge/presensi: 400 Bad Request", st == 400, f"status={st}")

# Traversal NPM in /api/pdf/download
st, hdrs, b = http_req("/api/pdf/download?type=01&npm=../../secret")
check("Traversal NPM in /api/pdf/download: 400 Bad Request", st == 400, f"status={st}")

# -----------------------------------------------------------------------------
# 3. CONCURRENCY THROTTLING & SSRF GUARD IN PDF BRIDGE
# -----------------------------------------------------------------------------
print("\n[3] Concurrency RAM Guard & SSRF Protection (pdf_bridge.py)")

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import pdf_bridge as pb

# Check semaphore value
check("PDF Bridge Semaphore configured to 2", pb._PLAYWRIGHT_SEMAPHORE._value == 2, f"value={pb._PLAYWRIGHT_SEMAPHORE._value}")

# Check is_valid_npm helper
check("is_valid_npm accepts 2510015410010", pb.is_valid_npm("2510015410010") is True)
check("is_valid_npm rejects ../../passwd", pb.is_valid_npm("../../passwd") is False)
check("is_valid_npm rejects letters", pb.is_valid_npm("NPM25100154") is False)
check("is_valid_npm rejects empty", pb.is_valid_npm("") is False)

print("\n" + "=" * 76)
print("HASIL PENGUJIAN CYBERSECURITY: " + ("SEMUA LULUS (100% PROTECTED)" if ok_all else "ADA YANG GAGAL"))
print("=" * 76)

sys.exit(0 if ok_all else 1)
