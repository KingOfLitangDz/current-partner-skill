#!/usr/bin/env python3
"""图片目录扫描器

扫描指定目录下的所有图片文件，输出文件列表供 look_at 工具逐张解读。
支持递归扫描子目录。

Usage:
    python3 image_scanner.py --dir <path> --output <output_path> [--recursive]
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".heic", ".heif"}


def scan_directory(dir_path: str, recursive: bool = True) -> list:
    images = []
    dir_path = os.path.expanduser(dir_path)

    if not os.path.isdir(dir_path):
        print(f"❌ 目录不存在：{dir_path}", file=sys.stderr)
        sys.exit(1)

    if recursive:
        for root, _, files in os.walk(dir_path):
            for fname in sorted(files):
                if Path(fname).suffix.lower() in IMAGE_EXTENSIONS:
                    full_path = os.path.join(root, fname)
                    images.append(build_image_entry(full_path))
    else:
        for fname in sorted(os.listdir(dir_path)):
            if Path(fname).suffix.lower() in IMAGE_EXTENSIONS:
                full_path = os.path.join(dir_path, fname)
                if os.path.isfile(full_path):
                    images.append(build_image_entry(full_path))

    return images


def build_image_entry(full_path: str) -> dict:
    stat = os.stat(full_path)
    return {
        "path": full_path,
        "filename": os.path.basename(full_path),
        "extension": Path(full_path).suffix.lower(),
        "size_kb": round(stat.st_size / 1024, 1),
        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
    }


def guess_image_type(filename: str) -> str:
    """根据文件名猜测图片类型，用于生成合适的 look_at goal"""
    name_lower = filename.lower()
    if any(k in name_lower for k in ["chat", "聊天", "微信", "wechat", "qq", "msg"]):
        return "chat_screenshot"
    elif any(k in name_lower for k in ["朋友圈", "moment", "微博", "weibo", "小红书", "ins"]):
        return "social_media"
    elif any(k in name_lower for k in ["转账", "红包", "transfer", "pay"]):
        return "transaction"
    elif any(k in name_lower for k in ["备忘", "memo", "note", "便签"]):
        return "memo"
    elif any(k in name_lower for k in ["合照", "约会", "date", "photo", "IMG_", "DSC"]):
        return "photo"
    return "unknown"


GOAL_TEMPLATES = {
    "chat_screenshot": "这是一张聊天截图。请提取：1.每条消息的发送者和内容 2.时间信息 3.语气和情绪 4.承诺或约定 5.口头禅或反复出现的表达 6.称呼方式",
    "social_media": "这是一张社交媒体截图。请提取：1.文案内容 2.发布时间 3.心情/状态 4.兴趣爱好线索 5.地点信息 6.评论互动",
    "transaction": "这是一张转账/红包截图。请提取：1.金额 2.备注/留言 3.时间 4.发送方和接收方",
    "memo": "这是一张备忘录/便签截图。请提取：1.完整文字内容 2.计划/愿望/承诺 3.时间信息",
    "photo": "这是一张照片。请描述：1.场景和地点 2.活动内容 3.时间线索（季节、节日等）4.物品或食物 5.整体氛围",
    "unknown": "分析这张图片，提取所有与恋爱关系相关的信息：对话内容、情绪、承诺、地点、时间、口头禅、喜好等",
}


def main():
    parser = argparse.ArgumentParser(description="图片目录扫描器")
    parser.add_argument("--dir", required=True, help="要扫描的目录路径")
    parser.add_argument("--output", required=True, help="输出 JSON 文件路径")
    parser.add_argument("--recursive", action="store_true", default=True,
                        help="递归扫描子目录（默认开启）")
    parser.add_argument("--no-recursive", action="store_true", help="不递归扫描")

    args = parser.parse_args()
    recursive = not args.no_recursive

    images = scan_directory(args.dir, recursive=recursive)

    if not images:
        print(f"📂 目录 {args.dir} 中没有找到图片文件。")
        print(f"   支持的格式：{', '.join(sorted(IMAGE_EXTENSIONS))}")
        return

    for img in images:
        img_type = guess_image_type(img["filename"])
        img["guessed_type"] = img_type
        img["suggested_goal"] = GOAL_TEMPLATES[img_type]

    result = {
        "scan_dir": os.path.abspath(os.path.expanduser(args.dir)),
        "scan_time": datetime.now().isoformat(),
        "total_images": len(images),
        "images": images,
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"📸 扫描完成：找到 {len(images)} 张图片")
    print(f"   目录：{args.dir}")
    print(f"   结果：{args.output}")
    print()

    type_counts = {}
    for img in images:
        t = img["guessed_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    type_labels = {
        "chat_screenshot": "💬 聊天截图",
        "social_media": "📱 社交媒体",
        "transaction": "💰 转账/红包",
        "memo": "📝 备忘录",
        "photo": "📷 照片",
        "unknown": "❓ 其他",
    }

    print("   类型分布：")
    for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        label = type_labels.get(t, t)
        print(f"     {label}：{count} 张")

    print()
    print("接下来对每张图片调用 look_at 工具解读，suggested_goal 已在 JSON 中提供。")


if __name__ == "__main__":
    main()
