"""本地 HTTP 实验服务。AI 提供服务端样板，学习者实现客户端调用。

参考：https://docs.python.org/3.14/library/http.server.html
服务只生成回显文本，不调用模型。
"""

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class ExperimentHandler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except ConnectionError:
            print("Client disconnected before the reply was sent.", flush=True)

    def do_POST(self):
        if self.path not in {"/generate", "/slow", "/bad-response"}:
            self.send_json(404, {"error": "Unknown endpoint"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 65536:
                raise ValueError("Invalid body length")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            content = payload["messages"][-1]["content"]
        except (ValueError, KeyError, TypeError, IndexError):
            self.send_json(400, {"error": "Expected JSON with messages and content"})
            return

        if self.path == "/slow":
            time.sleep(2)

        result = {"text": 123} if self.path == "/bad-response" else {
            "text": f"本地服务回复：{content}"
        }
        self.send_json(200, result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local HTTP learning fixture")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), ExperimentHandler) as server:
        print(f"Listening on http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
