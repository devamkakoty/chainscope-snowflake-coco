"""ChainScope local server and CLI. Python standard library only."""

import argparse
import hashlib
import json
import secrets
import sqlite3
import sys
import threading
from collections import deque
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

from chainscope.metrics import (ROLES, QueryError, answer, catalog, get_record,
                               ontology, overview, resolve)
from chainscope.model import AS_OF, DB_PATH, ROOT, connect

STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/static/style.css": ("style.css", "text/css; charset=utf-8"),
    "/static/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/static/icons.svg": ("icons.svg", "image/svg+xml"),
}


class State:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.RLock()

    def session(self, token):
        with self.lock:
            if token not in self.sessions:
                if len(self.sessions) >= 256:
                    del self.sessions[next(iter(self.sessions))]
                token = secrets.token_urlsafe(32)
                self.sessions[token] = {"role": "operations", "audit": deque(maxlen=100),
                                        "tail": "0"*64, "sequence": 0}
            return token

    def log(self, token, question, decision, response):
        with self.lock:
            session = self.sessions[token]
            try:
                metric = resolve(question)["id"]
            except QueryError:
                metric = "outside_catalog"
            session["sequence"] += 1
            entry = {
                "sequence": session["sequence"], "at": datetime.now(timezone.utc).isoformat(),
                "metric_id": metric, "role": session["role"], "decision": decision,
                "result_sha256": hashlib.sha256(json.dumps(response, sort_keys=True).encode()).hexdigest(),
                "previous_sha256": session["tail"],
            }
            digest = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
            entry["sha256"] = digest
            session["tail"] = digest
            session["audit"].append(entry)
            return entry["sequence"]


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, db_path=DB_PATH):
        self.state = State()
        self.db_path = db_path
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = "ChainScope/1.0"
    timeout = 8

    def log_message(self, fmt, *args):
        # Do not record raw user prompts, source URLs, or headers.
        pass

    def reply(self, status, payload, content_type="application/json; charset=utf-8"):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; script-src 'self'; style-src 'self'; "
                         "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
                         "base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        if getattr(self, "token", None):
            self.send_header("Set-Cookie", f"chainscope={self.token}; Path=/; HttpOnly; SameSite=Strict")
        self.end_headers()
        self.wfile.write(body)

    def guard(self, post=False):
        port = self.server.server_port
        allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if self.headers.get("Host") not in allowed_hosts:
            raise QueryError("Only the local loopback host is allowed.", 403, "invalid_host")
        origin = self.headers.get("Origin")
        if origin and origin not in {f"http://{host}" for host in allowed_hosts}:
            raise QueryError("Cross-origin requests are not allowed.", 403, "invalid_origin")
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            raise QueryError("Cross-site requests are not allowed.", 403, "invalid_origin")
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:
            cookie = SimpleCookie()
        self.token = self.server.state.session(cookie["chainscope"].value if "chainscope" in cookie else "")
        if post:
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                raise QueryError("JSON content type is required.", 415, "invalid_content_type")
            if self.headers.get("Transfer-Encoding"):
                raise QueryError("Transfer encoding is not supported.", 400, "invalid_body")

    def do_GET(self):
        try:
            self.guard()
            path = urlsplit(self.path).path
            if path in STATIC:
                filename, content_type = STATIC[path]
                self.reply(200, (ROOT / "static" / filename).read_bytes(), content_type)
                return
            role = self.server.state.sessions[self.token]["role"]
            if path == "/api/health":
                payload = {"status": "ok", "mode": "local-deterministic", "as_of": AS_OF}
            elif path == "/api/session":
                payload = {"role": role, "roles": ROLES, "simulated_identity": True}
            elif path == "/api/catalog":
                payload = {"metrics": catalog(role)}
            elif path == "/api/audit":
                with self.server.state.lock:
                    payload = {"entries": list(self.server.state.sessions[self.token]["audit"]),
                               "retention": "Last 100 decisions per in-memory browser session",
                               "durability": "Not durable or externally attested"}
            else:
                with connect(self.server.db_path) as db:
                    if path == "/api/overview":
                        payload = overview(db, role)
                    elif path == "/api/ontology":
                        payload = ontology(db)
                    elif path.startswith("/api/records/"):
                        bits = path.split("/")
                        if len(bits) != 5:
                            raise QueryError("Not found.", 404, "not_found")
                        payload = get_record(db, unquote(bits[3]), unquote(bits[4]), role)
                    else:
                        raise QueryError("Not found.", 404, "not_found")
            self.reply(200, payload)
        except QueryError as exc:
            self.reply(exc.status, {"error": exc.code, "message": str(exc)})
        except (ValueError, OSError, sqlite3.Error):
            self.reply(500, {"error": "local_data_error", "message": "Local files are unavailable. Run the data generator."})

    def do_POST(self):
        question = None
        try:
            self.guard(post=True)
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                raise QueryError("Invalid request length.", 400, "invalid_body")
            if length < 2 or length > 4096:
                raise QueryError("Request must be a JSON object of at most 4096 bytes.", 413, "invalid_body")
            try:
                body = json.loads(self.rfile.read(length))
            except (ValueError, UnicodeDecodeError):
                raise QueryError("Invalid JSON.", 400, "invalid_body")
            if not isinstance(body, dict):
                raise QueryError("Expected a JSON object.", 400, "invalid_body")
            path = urlsplit(self.path).path
            with self.server.state.lock:
                session = self.server.state.sessions[self.token]
                if path == "/api/session":
                    if set(body) != {"role"} or not isinstance(body["role"], str) or body["role"] not in ROLES:
                        raise QueryError("Choose a valid demo role.", 400, "invalid_role")
                    session["role"] = body["role"]
                    payload = {"role": session["role"], "simulated_identity": True}
                elif path == "/api/ask":
                    if set(body) != {"question"}:
                        raise QueryError("Only the question field is accepted.", 400, "invalid_body")
                    question = body["question"]
                    with connect(self.server.db_path) as db:
                        payload = answer(db, question, session["role"])
                    payload["audit_sequence"] = self.server.state.log(self.token, question, "allowed", payload)
                else:
                    raise QueryError("Not found.", 404, "not_found")
            self.reply(200, payload)
        except QueryError as exc:
            payload = {"error": exc.code, "message": str(exc), "status": "refused"}
            if question is not None:
                self.server.state.log(self.token, question, "denied" if exc.status == 403 else "refused", payload)
            self.reply(exc.status, payload)
        except (OSError, sqlite3.Error):
            self.reply(500, {"error": "local_data_error", "message": "Local query failed. Check the generated database."})


def ensure_data():
    if not DB_PATH.exists():
        from scripts.generate_data import generate
        generate()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")
    serve = sub.add_parser("serve", help="Run the loopback-only web app")
    serve.add_argument("--port", type=int, default=8765)
    ask = sub.add_parser("ask", help="Ask one approved question")
    ask.add_argument("question")
    ask.add_argument("--role", choices=ROLES, default="operations")
    ask.add_argument("--json", action="store_true")
    sub.add_parser("catalog", help="Print approved questions")
    args = parser.parse_args()
    ensure_data()
    if args.command == "catalog":
        for item in catalog("operations"):
            print(f"{item['id']}: {item['question']} [{', '.join(item['roles'])}]")
        return 0
    if args.command == "ask":
        try:
            with connect() as db:
                result = answer(db, args.question, args.role)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"{result['title']}: {result['metric']['display']}\n{result['summary']}")
                print(f"Snapshot: {AS_OF} | Role: {args.role} | Sources: {len(result['citations'])}")
                for row in result["rows"]:
                    print(" | ".join(str(row.get(key, "")) for key, _ in result["columns"]))
                    print("  Sources: " + ", ".join(s["id"] for s in row["sources"]))
            return 0
        except QueryError as exc:
            print(f"{exc.code}: {exc}", file=sys.stderr)
            return 2
    port = getattr(args, "port", 8765)
    try:
        server = Server(("127.0.0.1", port))
    except OSError as exc:
        print(f"Cannot bind port {port}: {exc}. Choose --port with an unused port.", file=sys.stderr)
        return 1
    print(f"ChainScope: http://127.0.0.1:{port} | synthetic snapshot {AS_OF}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
