#!/usr/bin/env python3
"""微信聊天记录解析器

支持主流导出工具的格式：
- WeChatMsg 导出（txt/html/csv）
- 留痕导出（json）
- 手动复制粘贴（纯文本）

提取维度：
- 高频词和口头禅
- 表情/emoji 使用偏好
- 回复速度模式
- 语气词和标点符号习惯
- 消息长度风格
- 关键事件和承诺

Usage:
    python3 wechat_parser.py --file <path> --target <name> --output <output_path> [--format auto]
"""

import argparse
import json
import re
import os
import sys
from datetime import datetime
from collections import Counter
from pathlib import Path


def detect_format(file_path: str) -> str:
    """自动检测文件格式"""
    ext = Path(file_path).suffix.lower()

    if ext == ".json":
        return "liuhen"
    elif ext == ".csv":
        return "wechatmsg_csv"
    elif ext in (".html", ".htm"):
        return "wechatmsg_html"
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            first_lines = f.read(2000)
        if re.search(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}", first_lines):
            return "wechatmsg_txt"
        return "plaintext"
    else:
        return "plaintext"


def parse_wechatmsg_txt(file_path: str, target_name: str) -> dict:
    """解析 WeChatMsg 导出的 txt 格式"""
    messages = []
    current_msg = None
    msg_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.+)$")

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.rstrip("\n")
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
            elif current_msg and line.strip():
                if current_msg["content"]:
                    current_msg["content"] += "\n"
                current_msg["content"] += line

    if current_msg:
        messages.append(current_msg)

    return analyze_messages(messages, target_name)


def parse_liuhen_json(file_path: str, target_name: str) -> dict:
    """解析留痕导出的 JSON 格式"""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = []
    msg_list = data if isinstance(data, list) else data.get("messages", data.get("data", []))

    for msg in msg_list:
        messages.append({
            "timestamp": msg.get("time", msg.get("timestamp", "")),
            "sender": msg.get("sender", msg.get("nickname", msg.get("from", ""))),
            "content": msg.get("content", msg.get("message", msg.get("text", ""))),
        })

    return analyze_messages(messages, target_name)


def parse_plaintext(file_path: str, target_name: str) -> dict:
    """解析纯文本粘贴的聊天记录"""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    return {
        "raw_text": content,
        "target_name": target_name,
        "format": "plaintext",
        "message_count": 0,
        "analysis": {"note": "纯文本格式，需要 AI 辅助分析"},
    }


def analyze_messages(messages: list, target_name: str) -> dict:
    """分析消息列表，提取关键特征"""
    target_msgs = [m for m in messages if target_name in m.get("sender", "")]
    user_msgs = [m for m in messages if target_name not in m.get("sender", "")]

    all_target_text = " ".join([m["content"] for m in target_msgs if m.get("content")])

    # 语气词
    particles = re.findall(r"[哈嗯哦噢嘿唉呜啊呀吧嘛呢吗么]+", all_target_text)
    particle_freq = Counter(particles)
    top_particles = particle_freq.most_common(10)

    # Emoji
    emoji_pattern = re.compile(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
        r"\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
        r"\U00002702-\U000027B0\U0000FE00-\U0000FE0F"
        r"\U0001F900-\U0001F9FF]+",
        re.UNICODE,
    )
    emojis = emoji_pattern.findall(all_target_text)
    emoji_freq = Counter(emojis)
    top_emojis = emoji_freq.most_common(10)

    # 消息长度
    msg_lengths = [len(m["content"]) for m in target_msgs if m.get("content")]
    avg_length = sum(msg_lengths) / len(msg_lengths) if msg_lengths else 0

    # 标点习惯
    punctuation_counts = {
        "句号": all_target_text.count("。"),
        "感叹号": all_target_text.count("！") + all_target_text.count("!"),
        "问号": all_target_text.count("？") + all_target_text.count("?"),
        "省略号": all_target_text.count("...") + all_target_text.count("…"),
        "波浪号": all_target_text.count("～") + all_target_text.count("~"),
    }

    # 提取承诺信号
    promise_patterns = [
        r"我保证.{2,30}",
        r"我答应你.{2,30}",
        r"说好了.{2,30}",
        r"下次一定.{2,30}",
        r"我发誓.{2,30}",
        r"约定.{2,30}",
    ]
    promises_found = []
    for pattern in promise_patterns:
        matches = re.findall(pattern, all_target_text)
        promises_found.extend(matches)

    # 提取高频短语（3-8字）
    # 简易方法：滑动窗口
    cn_text = re.sub(r"[^\u4e00-\u9fff]", " ", all_target_text)
    phrases = Counter()
    for segment in cn_text.split():
        if len(segment) < 3:
            continue
        for win in range(3, min(9, len(segment) + 1)):
            for i in range(len(segment) - win + 1):
                phrase = segment[i : i + win]
                phrases[phrase] += 1
    top_phrases = [(p, c) for p, c in phrases.most_common(50) if c >= 3][:15]

    return {
        "target_name": target_name,
        "total_messages": len(messages),
        "target_messages": len(target_msgs),
        "user_messages": len(user_msgs),
        "analysis": {
            "top_particles": top_particles,
            "top_emojis": top_emojis,
            "avg_message_length": round(avg_length, 1),
            "punctuation_habits": punctuation_counts,
            "message_style": "short_burst" if avg_length < 20 else "long_form",
            "top_phrases": top_phrases,
            "promises_found": promises_found[:20],
        },
        "sample_messages": [m["content"] for m in target_msgs[:50] if m.get("content")],
    }


def main():
    parser = argparse.ArgumentParser(description="微信聊天记录解析器")
    parser.add_argument("--file", required=True, help="输入文件路径")
    parser.add_argument("--target", required=True, help="对象的名字/昵称")
    parser.add_argument("--output", required=True, help="输出文件路径")
    parser.add_argument("--format", default="auto", help="文件格式")

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"错误：文件不存在 {args.file}", file=sys.stderr)
        sys.exit(1)

    fmt = args.format
    if fmt == "auto":
        fmt = detect_format(args.file)
        print(f"自动检测格式：{fmt}")

    parsers = {
        "wechatmsg_txt": parse_wechatmsg_txt,
        "liuhen": parse_liuhen_json,
        "plaintext": parse_plaintext,
    }

    parse_func = parsers.get(fmt, parse_plaintext)
    result = parse_func(args.file, args.target)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(f"# 微信聊天记录分析 — {args.target}\n\n")
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

        if analysis.get("top_phrases"):
            f.write("## 高频短语/口头禅\n")
            for phrase, count in analysis["top_phrases"]:
                f.write(f"- {phrase}: {count}次\n")
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

    # 同时输出 JSON 格式供 RAG 导入
    json_output = args.output.rsplit(".", 1)[0] + ".json"
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"分析完成，结果已写入 {args.output}")
    print(f"JSON 格式已写入 {json_output}")


if __name__ == "__main__":
    main()
