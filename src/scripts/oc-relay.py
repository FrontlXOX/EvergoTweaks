#!/usr/bin/env python3
"""
oc-relay.py: Relay server for opencode serve. Runs on WSL.

Starts `opencode serve` itself in a background thread, then serves the
relay API on top of it. One script, one process to keep alive.

Run on WSL:
  OPENCODE_SERVER_PASSWORD="kostom@767coder" python3 oc-relay.py

Then from Muse's side (via proxy tunnel, no SSH):
  POST http://100.73.167.95:8090/send    {"session": "...", "text": "..."}
  GET  http://100.73.167.95:8090/status?session=...
  GET  http://100.73.167.95:8090/watch?session=...&timeout=300
  POST http://100.73.167.95:8090/abort   {"session": "..."}
  GET  http://100.73.167.95:8090/sessions
  GET  http://100.73.167.95:8090/serve-log   (last 50 lines of serve output)

Stdlib only. No pip needed.
"""
import base64
import json
import os
import shutil
import signal
import socket
import subprocess
import threading
import time
import urllib.request
import urllib.error
from collections import deque
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# --- Config ---
SERVE_HOST = os.environ.get("OPENCODE_SERVER_HOST", "100.73.167.95")
SERVE_PORT = os.environ.get("OPENCODE_SERVER_PORT", "4096")
SERVE_USER = os.environ.get("OPENCODE_SERVER_USER", "opencode")
SERVE_PASS = os.environ.get("OPENCODE_SERVER_PASSWORD", "kostom@767coder")
RELAY_PORT = int(os.environ.get("OC_RELAY_PORT", "8090"))
RELAY_TOKEN = os.environ.get("OC_RELAY_TOKEN", "")
OPENCODE_BIN = os.environ.get("OPENCODE_BIN") or shutil.which("opencode")

if not SERVE_PASS:
    print("error: OPENCODE_SERVER_PASSWORD not set", flush=True)
    raise SystemExit(1)
if not OPENCODE_BIN:
    for guess in ["/root/.opencode/bin/opencode",
                  os.path.expanduser("~/.opencode/bin/opencode")]:
        if os.path.isfile(guess) and os.access(guess, os.X_OK):
            OPENCODE_BIN = guess
            break
if not OPENCODE_BIN:
    print("error: opencode binary not found (set OPENCODE_BIN)", flush=True)
    raise SystemExit(1)

AUTH = base64.b64encode(f"{SERVE_USER}:{SERVE_PASS}".encode()).decode()

# --- opencode serve supervisor ---
serve_proc = None
serve_log = deque(maxlen=50)
serve_lock = threading.Lock()

def _drain(pipe):
    for line in iter(pipe.readline, ""):
        with serve_lock:
            serve_log.append(line.rstrip()[:300])
    pipe.close()

def _serve_ready():
    """True if the serve API answers."""
    try:
        req = urllib.request.Request(
            f"http://{SERVE_HOST}:{SERVE_PORT}/api/session",
            headers={"Authorization": f"Basic {AUTH}"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False

def _start_serve():
    global serve_proc
    env = dict(os.environ, OPENCODE_SERVER_PASSWORD=SERVE_PASS)
    serve_proc = subprocess.Popen(
        [OPENCODE_BIN, "serve",
         "--hostname", SERVE_HOST, "--port", str(SERVE_PORT)],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1)
    threading.Thread(target=_drain, args=(serve_proc.stdout,),
                     daemon=True).start()
    print(f"[relay] opencode serve started (pid {serve_proc.pid})",
          flush=True)

def serve_supervisor():
    """Keep opencode serve alive. Restarts it if it dies."""
    _start_serve()
    # Wait for it to come up
    for _ in range(30):
        if _serve_ready():
            break
        time.sleep(1)
    else:
        print("[relay] WARNING: serve did not become ready in 30s",
              flush=True)
    print(f"[relay] serve ready at {SERVE_HOST}:{SERVE_PORT}", flush=True)
    while True:
        rc = serve_proc.wait()
        print(f"[relay] serve exited (rc={rc}), restarting in 3s...",
              flush=True)
        time.sleep(3)
        _start_serve()

# --- Relay API (talks to serve locally) ---
def serve_request(method, path, data=None, timeout=30):
    headers = {"Authorization": f"Basic {AUTH}",
               "Content-Type": "application/json"}
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        f"http://{SERVE_HOST}:{SERVE_PORT}{path}",
        data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def watch_session(sid, timeout=300):
    """Block on the SSE stream until the agent's turn completes."""
    deadline = time.time() + timeout
    backoff = 2
    text_parts = []
    while time.time() < deadline:
        chunk = min(75, int(deadline - time.time()))
        req = urllib.request.Request(
            f"http://{SERVE_HOST}:{SERVE_PORT}/api/event",
            headers={"Authorization": f"Basic {AUTH}",
                     "Accept": "text/event-stream"})
        try:
            with urllib.request.urlopen(req, timeout=chunk + 10) as resp:
                backoff = 2
                for raw in resp:
                    try:
                        line = raw.decode().strip()
                    except Exception:
                        continue
                    if not line.startswith("data:"):
                        continue
                    try:
                        evt = json.loads(line[5:].strip())
                    except Exception:
                        continue
                    etype = evt.get("type", "")
                    edata = evt.get("data", {})
                    if edata.get("sessionID", "") != sid:
                        continue
                    if etype == "session.text.delta":
                        d = edata.get("delta", "")
                        if d:
                            text_parts.append(d)
                    elif etype == "session.text.ended":
                        t = edata.get("text", "")
                        if t:
                            text_parts = [t]
                    elif etype == "session.idle":
                        full = "".join(text_parts).strip()
                        text_parts = []
                        if full:
                            return full
        except Exception as e:
            print(f"[relay] watch reconnect in {backoff}s: {e}", flush=True)
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)
    return None

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _auth_ok(self):
        if not RELAY_TOKEN:
            return True
        return self.headers.get("X-Relay-Token") == RELAY_TOKEN

    def _send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode())

    def do_GET(self):
        if not self._auth_ok():
            return self._send_json(401, {"error": "bad token"})
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path == "/status":
                sid = q.get("session", [""])[0]
                resp = serve_request("GET",
                    f"/api/session/{sid}/message", timeout=15)
                msgs = resp.get("data", [])
                # Find the latest message that actually has text content
                # (the newest entry is often an empty idle marker)
                m, text = {}, ""
                for cand in msgs:
                    t = ""
                    for c in cand.get("content", []):
                        if c.get("type") == "text" and c.get("text", "").strip():
                            t = c["text"]
                            break
                    if t:
                        m, text = cand, t
                        break
                self._send_json(200, {
                    "id": m.get("id"), "type": m.get("type"),
                    "text": text[:4000]})
            elif u.path == "/watch":
                sid = q.get("session", [""])[0]
                timeout = int(q.get("timeout", ["300"])[0])
                text = watch_session(sid, timeout)
                if text:
                    self._send_json(200, {"text": text})
                else:
                    self._send_json(504, {"error": "timeout"})
            elif u.path == "/sessions":
                resp = serve_request("GET", "/api/session", timeout=15)
                self._send_json(200, {"sessions": [
                    {"id": s.get("id"), "agent": s.get("agent"),
                     "model": s.get("model", {}).get("id")}
                    for s in resp.get("data", [])]})
            elif u.path == "/serve-log":
                with serve_lock:
                    lines = list(serve_log)
                self._send_json(200, {"log": lines})
            elif u.path == "/health":
                self._send_json(200, {
                    "ok": True,
                    "serve_up": _serve_ready(),
                    "serve_pid": serve_proc.pid if serve_proc else None,
                })
            else:
                self._send_json(404, {"error": "not found"})
        except Exception as e:
            self._send_json(500, {"error": str(e)[:300]})

    def do_POST(self):
        if not self._auth_ok():
            return self._send_json(401, {"error": "bad token"})
        u = urlparse(self.path)
        try:
            body = self._read_json()
            if u.path == "/send":
                sid, text = body["session"], body["text"]
                resp = serve_request("POST",
                    f"/api/session/{sid}/prompt", {"text": text},
                    timeout=30)
                self._send_json(200, {"id": resp["data"]["id"]})
            elif u.path == "/abort":
                serve_request("POST",
                    f"/api/session/{body['session']}/abort", timeout=15)
                self._send_json(200, {"ok": True})
            else:
                self._send_json(404, {"error": "not found"})
        except Exception as e:
            self._send_json(500, {"error": str(e)[:300]})

def main():
    from socketserver import ThreadingMixIn
    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

    # Start serve supervisor first
    threading.Thread(target=serve_supervisor, daemon=True).start()

    server = ThreadedHTTPServer(("0.0.0.0", RELAY_PORT), Handler)
    print(f"[relay] listening on 0.0.0.0:{RELAY_PORT} "
          f"-> serve at {SERVE_HOST}:{SERVE_PORT}", flush=True)
    print(f"[relay] token auth: {'ON' if RELAY_TOKEN else 'OFF'}",
          flush=True)
    print(f"[relay] opencode bin: {OPENCODE_BIN}", flush=True)

    def shutdown(signum, frame):
        print("\n[relay] shutting down...", flush=True)
        if serve_proc:
            serve_proc.terminate()
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[relay] stopped", flush=True)
        if serve_proc:
            serve_proc.terminate()

if __name__ == "__main__":
    main()
