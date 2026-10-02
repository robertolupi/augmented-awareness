#!/usr/bin/env python3
# Run: python3 echo_server.py --port 8484 --log echo_requests.jsonl
"""Deterministic OpenAI-compatible echo server for AI Providers smoke tests.

POST /v1/chat/completions concatenates all request messages in order as
"role: content" blocks into the assistant reply, and appends the raw request
body as one JSON line to the log file. GET /v1/models returns a trivial list
so provider setup UIs that probe models do not break.
"""

import argparse
import json
import signal
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def build_reply_text(body: dict) -> str:
    parts = []
    for message in body.get("messages", []):
        role = message.get("role", "")
        content = message.get("content", "")
        if isinstance(content, list):
            content = "".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )
        parts.append(f"{role}: {content}")
    return "\n".join(parts)


class EchoHandler(BaseHTTPRequestHandler):
    log_path = "echo_requests.jsonl"

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length else b""

    def do_GET(self) -> None:
        if self.path == "/v1/models":
            self._send_json(
                200,
                {
                    "object": "list",
                    "data": [
                        {
                            "id": "echo-model",
                            "object": "model",
                            "created": 0,
                            "owned_by": "echo",
                        }
                    ],
                },
            )
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/v1/chat/completions":
            self._send_json(404, {"error": "not found"})
            return
        raw = self._read_body()
        try:
            body = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._send_json(400, {"error": f"invalid JSON: {exc}"})
            return

        with open(self.log_path, "a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(body, ensure_ascii=False) + "\n")

        self._send_json(
            200,
            {
                "id": "chatcmpl-echo",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": body.get("model", ""),
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": build_reply_text(body),
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            },
        )

    def log_message(self, format: str, *args) -> None:
        print(f"[echo] {self.address_string()} - {format % args}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8484)
    parser.add_argument("--log", default="echo_requests.jsonl")
    args = parser.parse_args()

    EchoHandler.log_path = args.log
    server = ThreadingHTTPServer(("127.0.0.1", args.port), EchoHandler)

    def shutdown(signum, frame):
        del signum, frame
        # Shutdown from a thread so the handler thread is not blocked.
        import threading

        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    print(f"Echo server listening on http://127.0.0.1:{args.port}", file=sys.stderr)
    server.serve_forever()
    server.server_close()


if __name__ == "__main__":
    main()
