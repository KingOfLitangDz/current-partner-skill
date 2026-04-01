#!/usr/bin/env python3
"""版本管理器

支持备份、回滚、列出历史版本。

Usage:
    python3 version_manager.py --action backup --data-dir <path>
    python3 version_manager.py --action rollback --version <version_name> --data-dir <path>
    python3 version_manager.py --action list --data-dir <path>
"""

import argparse
import json
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path


def load_json(filepath: str) -> dict:
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath: str, data: dict):
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


DATA_FILES = [
    "profile.json",
    "timeline.jsonl",
    "promises.jsonl",
    "language_patterns.jsonl",
    "emotional_patterns.jsonl",
    "meta.json",
    "index.json",
]


def action_backup(data_dir: str):
    """创建备份"""
    meta = load_json(os.path.join(data_dir, "meta.json"))
    version = meta.get("version", "v1")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{version}_{timestamp}"
    backup_dir = os.path.join(data_dir, "backups", backup_name)

    os.makedirs(backup_dir, exist_ok=True)

    copied = 0
    for filename in DATA_FILES:
        src = os.path.join(data_dir, filename)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(backup_dir, filename))
            copied += 1

    # 备份 raw_materials 目录
    raw_dir = os.path.join(data_dir, "raw_materials")
    if os.path.exists(raw_dir) and os.listdir(raw_dir):
        backup_raw = os.path.join(backup_dir, "raw_materials")
        shutil.copytree(raw_dir, backup_raw)

    # 记录备份信息
    backup_meta = {
        "backup_name": backup_name,
        "version": version,
        "created_at": datetime.now().isoformat(),
        "files_count": copied,
    }
    save_json(os.path.join(backup_dir, "backup_meta.json"), backup_meta)

    print(f"💾 备份完成：{backup_name}")
    print(f"   位置：{backup_dir}")
    print(f"   文件数：{copied}")


def action_rollback(data_dir: str, version_name: str):
    """回滚到指定版本"""
    backup_dir = os.path.join(data_dir, "backups", version_name)

    if not os.path.exists(backup_dir):
        # 尝试模糊匹配
        backups_root = os.path.join(data_dir, "backups")
        if os.path.exists(backups_root):
            candidates = [d for d in sorted(os.listdir(backups_root)) if version_name in d]
            if candidates:
                backup_dir = os.path.join(backups_root, candidates[-1])
                print(f"ℹ️ 模糊匹配到版本：{candidates[-1]}")
            else:
                print(f"❌ 未找到版本：{version_name}", file=sys.stderr)
                print(f"   可用版本：{', '.join(sorted(os.listdir(backups_root)))}")
                sys.exit(1)
        else:
            print(f"❌ 没有可用的备份", file=sys.stderr)
            sys.exit(1)

    # 先备份当前版本
    print("📦 先备份当前版本...")
    action_backup(data_dir)

    # 恢复文件
    restored = 0
    for filename in DATA_FILES:
        src = os.path.join(backup_dir, filename)
        if os.path.exists(src):
            dst = os.path.join(data_dir, filename)
            shutil.copy2(src, dst)
            restored += 1

    # 恢复 raw_materials
    backup_raw = os.path.join(backup_dir, "raw_materials")
    if os.path.exists(backup_raw):
        raw_dir = os.path.join(data_dir, "raw_materials")
        if os.path.exists(raw_dir):
            shutil.rmtree(raw_dir)
        shutil.copytree(backup_raw, raw_dir)

    print(f"✅ 已回滚到版本：{version_name}")
    print(f"   恢复文件数：{restored}")


def action_list(data_dir: str):
    """列出所有备份"""
    backups_dir = os.path.join(data_dir, "backups")

    if not os.path.exists(backups_dir):
        print("📋 没有可用的备份。")
        return

    entries = sorted(os.listdir(backups_dir))
    if not entries:
        print("📋 没有可用的备份。")
        return

    print("💾 历史备份")
    print("=" * 50)

    for entry in entries:
        entry_path = os.path.join(backups_dir, entry)
        if not os.path.isdir(entry_path):
            continue

        meta_path = os.path.join(entry_path, "backup_meta.json")
        meta = load_json(meta_path)

        created = meta.get("created_at", "未知")
        version = meta.get("version", "?")
        files = meta.get("files_count", "?")

        print(f"  📌 {entry}")
        print(f"     版本：{version} | 时间：{created} | 文件数：{files}")
        print()


def main():
    parser = argparse.ArgumentParser(description="版本管理器")
    parser.add_argument("--action", required=True,
                        choices=["backup", "rollback", "list"])
    parser.add_argument("--data-dir", required=True, help="数据目录路径")
    parser.add_argument("--version", help="版本名称（回滚用）")

    args = parser.parse_args()

    if args.action == "backup":
        action_backup(args.data_dir)
    elif args.action == "rollback":
        if not args.version:
            print("❌ rollback 需要 --version 参数", file=sys.stderr)
            sys.exit(1)
        action_rollback(args.data_dir, args.version)
    elif args.action == "list":
        action_list(args.data_dir)


if __name__ == "__main__":
    main()
