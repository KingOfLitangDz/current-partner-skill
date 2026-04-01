#!/usr/bin/env python3
"""承诺追踪器

追踪双方在关系中做出的承诺，支持状态管理。

Usage:
    python3 promise_tracker.py --action add --who <ta/me> --content <text> [--date <date>] [--deadline <date>] [--status <status>] [--context <text>] --data-dir <path>
    python3 promise_tracker.py --action list [--who <ta/me>] [--status <status>] --data-dir <path>
    python3 promise_tracker.py --action update --id <id> --status <status> --data-dir <path>
    python3 promise_tracker.py --action remind --data-dir <path>
"""

import argparse
import json
import os
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path


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


def gen_id(existing_ids: set) -> str:
    n = 1
    while True:
        new_id = f"p{n:03d}"
        if new_id not in existing_ids:
            return new_id
        n += 1


def action_add(data_dir: str, who: str, content: str, date: str = "",
               deadline: str = "", status: str = "pending", context: str = ""):
    """添加承诺"""
    filepath = os.path.join(data_dir, "promises.jsonl")
    records = load_jsonl(filepath)
    existing_ids = {r.get("id", "") for r in records}

    record = {
        "id": gen_id(existing_ids),
        "who": who,
        "content": content,
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "deadline": deadline,
        "status": status,
        "context": context,
        "_added_at": datetime.now().isoformat(),
    }

    records.append(record)
    save_jsonl(filepath, records)
    print(f"✅ 承诺已记录：[{record['id']}] ({who}) {content}")


def action_list(data_dir: str, who: str = "", status: str = ""):
    """列出承诺"""
    filepath = os.path.join(data_dir, "promises.jsonl")
    records = load_jsonl(filepath)

    if who:
        records = [r for r in records if r.get("who") == who]
    if status:
        records = [r for r in records if r.get("status") == status]

    if not records:
        print("📋 没有找到匹配的承诺记录。")
        return

    # 按状态分组
    status_groups = {"pending": [], "completed": [], "broken": [], "expired": []}
    for r in records:
        s = r.get("status", "pending")
        status_groups.setdefault(s, []).append(r)

    status_emoji = {
        "pending": "⏳",
        "completed": "✅",
        "broken": "💔",
        "expired": "⌛",
    }

    print("🤝 承诺追踪")
    print("=" * 50)

    for s, group in status_groups.items():
        if not group:
            continue
        emoji = status_emoji.get(s, "📌")
        print(f"\n{emoji} {s.upper()} ({len(group)})")
        print("-" * 30)
        for r in group:
            who_label = "ta承诺" if r.get("who") == "ta" else "我承诺"
            print(f"  [{r['id']}] {who_label}：{r['content']}")
            if r.get("date"):
                print(f"         📅 日期：{r['date']}")
            if r.get("deadline"):
                print(f"         ⏰ 截止：{r['deadline']}")
            if r.get("context"):
                print(f"         💬 场景：{r['context']}")
            print()


def action_update(data_dir: str, record_id: str, status: str):
    """更新承诺状态"""
    filepath = os.path.join(data_dir, "promises.jsonl")
    records = load_jsonl(filepath)

    found = False
    for r in records:
        if r.get("id") == record_id:
            old_status = r.get("status", "pending")
            r["status"] = status
            r["_updated_at"] = datetime.now().isoformat()
            found = True
            print(f"✅ 承诺 [{record_id}] 状态已更新：{old_status} → {status}")
            break

    if not found:
        print(f"❌ 未找到承诺记录：{record_id}", file=sys.stderr)
        sys.exit(1)

    save_jsonl(filepath, records)


def action_remind(data_dir: str):
    """提醒即将到期或过期的承诺"""
    filepath = os.path.join(data_dir, "promises.jsonl")
    records = load_jsonl(filepath)

    today = datetime.now().date()
    pending = [r for r in records if r.get("status") == "pending"]

    overdue = []
    upcoming = []
    no_deadline = []

    for r in pending:
        deadline = r.get("deadline", "")
        if not deadline:
            no_deadline.append(r)
            continue
        try:
            dl = datetime.strptime(deadline, "%Y-%m-%d").date()
            if dl < today:
                overdue.append(r)
            elif dl <= today + timedelta(days=7):
                upcoming.append(r)
        except ValueError:
            no_deadline.append(r)

    if not overdue and not upcoming:
        print("✅ 没有即将到期或过期的承诺。")
        if no_deadline:
            print(f"ℹ️ 有 {len(no_deadline)} 条承诺没有设置截止日期。")
        return

    if overdue:
        print("⚠️ 已过期的承诺：")
        for r in overdue:
            who_label = "ta承诺" if r.get("who") == "ta" else "我承诺"
            print(f"  [{r['id']}] {who_label}：{r['content']}（截止 {r['deadline']}）")
        print()

    if upcoming:
        print("⏰ 即将到期的承诺（7天内）：")
        for r in upcoming:
            who_label = "ta承诺" if r.get("who") == "ta" else "我承诺"
            days_left = (datetime.strptime(r["deadline"], "%Y-%m-%d").date() - today).days
            print(f"  [{r['id']}] {who_label}：{r['content']}（还剩 {days_left} 天）")


def main():
    parser = argparse.ArgumentParser(description="承诺追踪器")
    parser.add_argument("--action", required=True,
                        choices=["add", "list", "update", "remind"])
    parser.add_argument("--data-dir", required=True, help="数据目录路径")
    parser.add_argument("--who", help="谁的承诺：ta / me")
    parser.add_argument("--content", help="承诺内容")
    parser.add_argument("--date", help="承诺日期 (YYYY-MM-DD)")
    parser.add_argument("--deadline", help="截止日期 (YYYY-MM-DD)")
    parser.add_argument("--status", default="pending",
                        help="状态：pending/completed/broken/expired")
    parser.add_argument("--context", default="", help="承诺的场景/上下文")
    parser.add_argument("--id", help="记录 ID（更新用）")

    args = parser.parse_args()

    if args.action == "add":
        if not args.who or not args.content:
            print("❌ add 需要 --who 和 --content 参数", file=sys.stderr)
            sys.exit(1)
        action_add(args.data_dir, args.who, args.content,
                   date=args.date or "", deadline=args.deadline or "",
                   status=args.status, context=args.context)
    elif args.action == "list":
        action_list(args.data_dir, who=args.who or "", status=args.status if args.status != "pending" else "")
    elif args.action == "update":
        if not args.id or not args.status:
            print("❌ update 需要 --id 和 --status 参数", file=sys.stderr)
            sys.exit(1)
        action_update(args.data_dir, args.id, args.status)
    elif args.action == "remind":
        action_remind(args.data_dir)


if __name__ == "__main__":
    main()
