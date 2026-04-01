#!/usr/bin/env python3
"""现任.skill Web UI 服务器

启动本地 HTTP 服务，提供可视化管理界面。
零外部依赖，仅使用 Python 3 标准库。

Usage:
    python3 web_server.py --data-dir ~/.local/share/current-partner [--port 8765]
"""

import argparse
import json
import os
import sys
import re
import webbrowser
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# ── 常量 ──────────────────────────────────────────────

CATEGORIES = ["profile", "timeline", "promises", "language_patterns", "emotional_patterns"]

ID_PREFIX = {
    "timeline": "t",
    "promises": "p",
    "language_patterns": "l",
    "emotional_patterns": "e",
}

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


# ── 数据操作 ──────────────────────────────────────────

def load_jsonl(filepath: str) -> list:
    if not os.path.exists(filepath):
        return []
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def save_jsonl(filepath: str, records: list):
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load_json(filepath: str) -> dict:
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath: str, data: dict):
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def gen_id(prefix: str, existing_ids: set) -> str:
    n = 1
    while True:
        new_id = f"{prefix}{n:03d}"
        if new_id not in existing_ids:
            return new_id
        n += 1


def update_meta(data_dir: str):
    meta_path = os.path.join(data_dir, "meta.json")
    meta = load_json(meta_path)
    meta["updated_at"] = datetime.now().isoformat()
    total = 0
    for cat in CATEGORIES:
        if cat == "profile":
            profile = load_json(os.path.join(data_dir, "profile.json"))
            count = 1 if profile.get("name") else 0
        else:
            count = len(load_jsonl(os.path.join(data_dir, f"{cat}.jsonl")))
        meta.setdefault("categories", {})[cat] = count
        total += count
    meta["total_records"] = total
    save_json(meta_path, meta)


# ── HTTP 请求处理 ──────────────────────────────────────

class PartnerHandler(BaseHTTPRequestHandler):

    data_dir = ""

    def log_message(self, format, *args):
        # 静默日志，只打印错误
        if args and len(args) >= 2 and str(args[1]) not in ("200", "304"):
            try:
                msg = format % args if args else format
                print(f"  [{args[1]}] {msg}")
            except:
                pass

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        self.send_json({"error": message}, status=status)

    def serve_static(self, path):
        if path == "/" or path == "":
            path = "/index.html"
        filepath = os.path.join(STATIC_DIR, path.lstrip("/"))
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            self.send_response(404)
            self.end_headers()
            return
        ext = os.path.splitext(filepath)[1]
        mime = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".png": "image/png",
            ".ico": "image/x-icon",
        }.get(ext, "application/octet-stream")
        with open(filepath, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # API 路由
        if path == "/api/all":
            self._api_get_all()
        elif path == "/api/profile":
            self._api_get_profile()
        elif path.startswith("/api/records/"):
            category = path.split("/api/records/")[-1].split("?")[0]
            self._api_get_records(category)
        elif path == "/api/status":
            self._api_get_status()
        else:
            self.serve_static(path)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        if path == "/api/profile":
            self._api_update_profile(body)
        elif path.startswith("/api/records/"):
            category = path.split("/api/records/")[-1]
            self._api_add_record(category, body)
        else:
            self.send_error_json("Not found", 404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        # PUT /api/records/{category}/{id}
        parts = path.split("/")
        if len(parts) >= 5 and parts[1] == "api" and parts[2] == "records":
            category = parts[3]
            record_id = parts[4]
            self._api_update_record(category, record_id, body)
        else:
            self.send_error_json("Not found", 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # DELETE /api/records/{category}/{id}
        parts = path.split("/")
        if len(parts) >= 5 and parts[1] == "api" and parts[2] == "records":
            category = parts[3]
            record_id = parts[4]
            self._api_delete_record(category, record_id)
        else:
            self.send_error_json("Not found", 404)

    # ── API 实现 ──────────────────────────────────────

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def _api_get_all(self):
        result = {}
        result["profile"] = load_json(os.path.join(self.data_dir, "profile.json"))
        for cat in CATEGORIES:
            if cat == "profile":
                continue
            result[cat] = load_jsonl(os.path.join(self.data_dir, f"{cat}.jsonl"))
        result["meta"] = load_json(os.path.join(self.data_dir, "meta.json"))
        self.send_json(result)

    def _api_get_profile(self):
        profile = load_json(os.path.join(self.data_dir, "profile.json"))
        self.send_json(profile)

    def _api_get_records(self, category: str):
        if category not in CATEGORIES:
            self.send_error_json(f"无效分类: {category}")
            return
        if category == "profile":
            self.send_json(load_json(os.path.join(self.data_dir, "profile.json")))
        else:
            records = load_jsonl(os.path.join(self.data_dir, f"{category}.jsonl"))
            self.send_json(records)

    def _api_get_status(self):
        meta = load_json(os.path.join(self.data_dir, "meta.json"))
        profile = load_json(os.path.join(self.data_dir, "profile.json"))
        counts = {}
        for cat in CATEGORIES:
            if cat == "profile":
                counts[cat] = 1 if profile.get("name") else 0
            else:
                counts[cat] = len(load_jsonl(os.path.join(self.data_dir, f"{cat}.jsonl")))
        self.send_json({
            "partner_name": profile.get("name", ""),
            "together_since": profile.get("together_since", ""),
            "counts": counts,
            "total": sum(counts.values()),
            "updated_at": meta.get("updated_at", ""),
            "data_dir": self.data_dir,
        })

    def _api_update_profile(self, body: dict):
        profile_path = os.path.join(self.data_dir, "profile.json")
        profile = load_json(profile_path)
        profile.update(body)
        save_json(profile_path, profile)
        update_meta(self.data_dir)
        self.send_json({"ok": True, "profile": profile})

    def _api_add_record(self, category: str, body: dict):
        if category not in CATEGORIES or category == "profile":
            self.send_error_json(f"无效分类: {category}")
            return
        filepath = os.path.join(self.data_dir, f"{category}.jsonl")
        records = load_jsonl(filepath)
        existing_ids = {r.get("id", "") for r in records}
        if "id" not in body or not body["id"]:
            body["id"] = gen_id(ID_PREFIX.get(category, "x"), existing_ids)
        body["_added_at"] = datetime.now().isoformat()
        records.append(body)
        save_jsonl(filepath, records)
        update_meta(self.data_dir)
        self.send_json({"ok": True, "record": body})

    def _api_update_record(self, category: str, record_id: str, body: dict):
        if category not in CATEGORIES or category == "profile":
            self.send_error_json(f"无效分类: {category}")
            return
        filepath = os.path.join(self.data_dir, f"{category}.jsonl")
        records = load_jsonl(filepath)
        found = False
        for r in records:
            if r.get("id") == record_id:
                r.update(body)
                r["id"] = record_id  # 保持 ID 不变
                r["_updated_at"] = datetime.now().isoformat()
                found = True
                break
        if not found:
            self.send_error_json(f"记录不存在: {record_id}", 404)
            return
        save_jsonl(filepath, records)
        update_meta(self.data_dir)
        self.send_json({"ok": True})

    def _api_delete_record(self, category: str, record_id: str):
        if category not in CATEGORIES or category == "profile":
            self.send_error_json(f"无效分类: {category}")
            return
        filepath = os.path.join(self.data_dir, f"{category}.jsonl")
        records = load_jsonl(filepath)
        new_records = [r for r in records if r.get("id") != record_id]
        if len(new_records) == len(records):
            self.send_error_json(f"记录不存在: {record_id}", 404)
            return
        save_jsonl(filepath, new_records)
        update_meta(self.data_dir)
        self.send_json({"ok": True})


# ── 启动服务 ──────────────────────────────────────────

def start_server(data_dir: str, port: int = 8765, open_browser: bool = True):
    data_dir = os.path.expanduser(data_dir)

    if not os.path.exists(data_dir):
        print(f"❌ 数据目录不存在：{data_dir}")
        print("   请先运行 /init-partner 初始化知识库。")
        sys.exit(1)

    # 注入 data_dir 到 handler
    PartnerHandler.data_dir = data_dir

    server = HTTPServer(("127.0.0.1", port), PartnerHandler)
    url = f"http://127.0.0.1:{port}"

    print(f"\n💕 现任.skill Web UI 已启动")
    print(f"   地址：{url}")
    print(f"   数据：{data_dir}")
    print(f"   按 Ctrl+C 停止服务\n")

    if open_browser:
        def _open():
            import time
            time.sleep(0.5)
            webbrowser.open(url)
        threading.Thread(target=_open, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 服务已停止。")
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="现任.skill Web UI 服务器")
    parser.add_argument(
        "--data-dir",
        default="~/.local/share/current-partner",
        help="数据目录路径（默认：~/.local/share/current-partner）",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="监听端口（默认：8765）",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="不自动打开浏览器",
    )
    args = parser.parse_args()
    start_server(args.data_dir, port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
