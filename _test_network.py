"""Pure network test — DNS, TCP, TLS to Gemini endpoint."""
import socket
import ssl
import time

HOST = "generativelanguage.googleapis.com"

print(f"Testing raw network to {HOST}:443\n")

# DNS
t0 = time.time()
try:
    ip = socket.gethostbyname(HOST)
    dns_time = time.time() - t0
    print(f"[DNS]   {dns_time:.3f}s  -> {ip}")
except Exception as e:
    print(f"[DNS]   FAIL: {e}")
    raise SystemExit(1)

# TCP
t0 = time.time()
try:
    sock = socket.create_connection((HOST, 443), timeout=15)
    tcp_time = time.time() - t0
    print(f"[TCP]   {tcp_time:.3f}s  connected")
except Exception as e:
    print(f"[TCP]   FAIL: {e}")
    raise SystemExit(1)

# TLS
t0 = time.time()
try:
    ctx = ssl.create_default_context()
    ssock = ctx.wrap_socket(sock, server_hostname=HOST)
    tls_time = time.time() - t0
    print(f"[TLS]   {tls_time:.3f}s  handshake ok")
    ssock.close()
except Exception as e:
    print(f"[TLS]   FAIL: {e}")
    raise SystemExit(1)

total = dns_time + tcp_time + tls_time
print(f"\n[SUM]   {total:.3f}s  just to open connection")
print()

if total < 1.0:
    print("=> Network is FAST. The 52s is from the model or provider queue.")
elif total < 5.0:
    print("=> Network is OK. The 52s is mostly from the model.")
else:
    print("=> Network is SLOW. VPN or ISP is the bottleneck.")
    print("   Switch to a faster VPN, or use AvalAI (no VPN).")