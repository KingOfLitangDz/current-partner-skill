#!/usr/bin/env python3
"""QQ 聊天记录解析器

支持 QQ 消息管理器导出的 txt 和 mht 格式。

Usage:
    python3 qq_parser.py --file <path> --target <name> --output <output_path>
"""

import argparse
import json
import re
import os
import sys
from datetime import datetime
from collections import Counter
from pathlib import Path


def parse_qq_txt(file_path: str, target_name: str) -> dict:
    """解析 QQ 导出的 txt 格式

    典型格式：
    2024-01-15 20:30:45 张三(123456)
    今天好累啊

    或：
    2024-01-15 20:30:45 张三
    今天好累啊
    """
    messages = []
    current_msg = None

    # QQ 时间戳 + 发送者模式
    patterns = [
        re.compile(r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.+?)(?:\((\d+)\))?\s*$"),
        re.compile(r"^(\d{4}/\d{2}/\d{2}\s+\d{1,2}:\d{2}:\d{2})\s+(.+?)(?:<(.+?)>)?\s*$"),
    ]

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.rstrip("\n")
            matched = False
            for pattern in patterns:
                match = pattern.match(line)
                if match:
                    if current_msg:
                        messages.append(current_msg)
                    timestamp = match.group(1)
                    sender = match.group(2).strip()
                    current_msg = {
                        "timestamp": timestamp,
                        "sender": sender,
                        "content": "",
                    }
                    matched = True
                    break
            if not matched and current_msg and line.strip():
                if current_msg["content"]:
                    current_msg["content"] += "\n"
                current_msg["content"] += line

    if current_msg:
        messages.append(current_msg)

    return analyze_messages(messages, target_name)


def parse_qq_mht(file_path: str, target_name: str) -> dict:
    """解析 QQ 导出的 mht 格式（提取纯文本内容）"""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # 简易 HTML 标签清理
    text = re.sub(r"<[^>]+>", "\n", content)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 尝试按 QQ txt 格式解析清理后的文本
    lines = text.split("\n")
    messages = []
    current_msg = None
    msg_pattern = re.compile(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.+)")

    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = msg_pattern.match(line)
        if match:
            if current_msg:
                messages.append(current_msg)
            timestamp, sender = match.groups()
            current_msg = {
                "timestamp": timestamp,
                "sender": sender.strip(),
                "content": "",
            }
        elif current_msg:
            if current_msg["content"]:
                current_msg["content"] += "\n"
            current_msg["content"] += line

    if current_msg:
        messages.append(current_msg)

    if messages:
        return analyze_messages(messages, target_name)
    else:
        return {
            "raw_text": text,
            "target_name": target_name,
            "format": "mht_fallback",
            "message_count": 0,
            "analysis": {"note": "MHT 格式解析为纯文本，需要 AI 辅助分析"},
        }


def analyze_messages(messages: list, target_name: str) -> dict:
    """分析消息列表"""
    target_msgs = [m for m in messages if target_name in m.get("sender", "")]
    user_msgs = [m for m in messages if target_name not in m.get("sender", "")]

    all_target_text = " ".join([m["content"] for m in target_msgs if m.get("content")])

    # 语气词
    particles = re.findall(r"[哈嗯哦噢嘿唉呜啊呀吧嘛呢吗么]+", all_target_text)
    particle_freq = Counter(particles)

    # Emoji
    emoji_pattern = re.compile(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
        r"\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
        r"\U0001F900-\U0001F9FF]+",
        re.UNICODE,
    )
    emoji_freq = Counter(emoji_pattern.findall(all_target_text))

    # 消息长度
    msg_lengths = [len(m["content"]) for m in target_msgs if m.get("content")]
    avg_length = sum(msg_lengths) / len(msg_lengths) if msg_lengths else 0

    # 标点
    punctuation_counts = {
        "句号": all_target_text.count("。"),
        "感叹号": all_target_text.count("！") + all_target_text.count("!"),
        "问号": all_target_text.count("？") + all_target_text.count("?"),
        "省略号": all_target_text.count("...") + all_target_text.count("…"),
        "波浪号": all_target_text.count("～") + all_target_text.count("~"),
    }

    # 承诺
    promise_patterns = [
        r"我保证.{2,30}", r"我答应你.{2,30}", r"说好了.{2,30}",
        r"下次一定.{2,30}", r"我发誓.{2,30}", r"约定.{2,30}",
    ]
    promises = []
    for pat in promise_patterns:
        promises.extend(re.findall(pat, all_target_text))

    return {
        "target_name": target_name,
        "total_messages": len(messages),
        "target_messages": len(target_msgs),
        "user_messages": len(user_msgs),
        "analysis": {
            "top_particles": particle_freq.most_common(10),
            "top_emojis": emoji_freq.most_common(10),
            "avg_message_length": round(avg_length, 1),
            "punctuation_habits": punctuation_counts,
            "message_style": "short_burst" if avg_length < 20 else "long_form",
            "promises_found": promises[:20],
        },
        "sample_messages": [m["content"] for m in target_msgs[:50] if m.get("content")],
    }


def main():
    parser = argparse.ArgumentParser(description="QQ 聊天记录解析器")
    parser.add_argument("--file", required=True, help="输入文件路径")
    parser.add_argument("--target", required=True, help="对象的名字/昵称")
    parser.add_argument("--output", required=True, help="输出文件路径")

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"错误：文件不存在 {args.file}", file=sys.stderr)
        sys.exit(1)

    ext = Path(args.file).suffix.lower()
    if ext == ".mht":
        result = parse_qq_mht(args.file, args.target)
        fmt = "mht"
    else:
        result = parse_qq_txt(args.file, args.target)
        fmt = "txt"

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(f"# QQ 聊天记录分析 — {args.target}\n\n")
        f.write(f"来源文件：{args.file}\n")
        f.write(f"检测格式：{fmt}\n")
        f.write(f"总消息数：{result.get('total_messages', 'N/A')}\n")
        f.write(f"ta的消息数：{result.get('target_messages', 'N/A')}\n\n")

        analysis = result.get("analysis", {})

        if analysis.get("top_particles"):
            f.write("## 高频语气词\n")
            for word, count in analysis["top_particles"]:
                f.write(f"- {word}: {count}次\n")
            f.write("\n")

        if analysis.get("top_emojis"):
            f.write("## 高频 Emoji\n")
            for emoji, count in analysis["top_emojis"]:
                f.write(f"- {emoji}: {count}次\n")
            f.write("\n")

        if analysis.get("punctuation_habits"):
            f.write("## 标点习惯\n")
            for punct, count in analysis["punctuation_habits"].items():
                f.write(f"- {punct}: {count}次\n")
            f.write("\n")

        f.write("## 消息风格\n")
        f.write(f"- 平均消息长度：{analysis.get('avg_message_length', 'N/A')} 字\n")
        f.write(f"- 风格：{'短句连发型' if analysis.get('message_style') == 'short_burst' else '长段落型'}\n\n")

        if analysis.get("promises_found"):
            f.write("## 发现的承诺语句\n")
            for i, p in enumerate(analysis["promises_found"], 1):
                f.write(f"{i}. {p}\n")
            f.write("\n")

        if result.get("sample_messages"):
            f.write("## 消息样本（前50条）\n")
            for i, msg in enumerate(result["sample_messages"], 1):
                f.write(f"{i}. {msg}\n")

    # JSON 格式
    json_output = args.output.rsplit(".", 1)[0] + ".json"
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"分析完成，结果已写入 {args.output}")
    print(f"JSON 格式已写入 {json_output}")


if __name__ == "__main__":
    main()
